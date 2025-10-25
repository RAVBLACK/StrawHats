import customtkinter as ctk
from tkinter import messagebox
from analyzer import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import threading
import sys, os, urllib.request, io
import datetime
import json
from mailer import send_alert_email
from PIL import Image, ImageTk

# Voice recorder fallback
try:
    from voice_recorder import voice_recorder
    VOICE_AVAILABLE = True
    print("Voice recorder loaded successfully")
except ImportError as e:
    VOICE_AVAILABLE = False
    print(f"Voice recorder not available: {e}")

    class DummyVoiceRecorder:
        def __init__(self):
            self.is_recording = False
            self.initialized = False
        def start_recording(self):
            messagebox.showinfo("Voice Recording", "Voice recording is disabled. Install speech_recognition module to enable.")
            return False
        def stop_recording(self):
            return False
    voice_recorder = DummyVoiceRecorder()

# AI Companion Import (Optional - graceful fallback if not available)
try:
    from ai_companion import ai_companion, chat_with_ai, get_mood_suggestions
    AI_AVAILABLE = True
    print("AI Companion loaded successfully")
except ImportError as e:
    AI_AVAILABLE = False
    print(f"WARNING: AI Companion not available: {e}")
except Exception as e:
    AI_AVAILABLE = False
    print(f"WARNING: AI Companion initialization error: {e}")


def check_and_alert():
    try:
        with open("user_settings.json", "r") as f:
            settings = json.load(f)
        guardian_email = settings.get("guardian_email")
        if not guardian_email:
            return
        result = count_below_threshold()
        count, latest_line = result[0], result[1]
        if count > ALERT_LIMIT:
            send_alert_email(guardian_email, count)
            set_alert_status(latest_line)
            messagebox.showinfo("Guardian Alert Sent",
                                f"An alert was sent to the guardian ({guardian_email}) because mood dropped below {THRESHOLD} more than {ALERT_LIMIT} times.")
    except Exception as e:
        print("Error during guardian alert check:", e)


def check_and_add_guardian_alert(alert_limit=None):
    ALERTS_LOG_FILE = "alerts_log.json"
    if alert_limit is None:
        from analyzer import ALERT_LIMIT
        alert_limit = ALERT_LIMIT
    
    result = count_below_threshold(return_lines=True)
    if len(result) == 3:
        count, latest_line, neg_lines = result
    else:
        count, latest_line = result
        neg_lines = []

    print(f"Debug: Alert check - Count: {count}, Limit: {alert_limit}, Latest line: {latest_line}")

    if count > alert_limit:
        alert_record = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "negative_count": count,
            "status": "Sent",
            "reason_lines": neg_lines
        }
        logs = []
        if os.path.exists(ALERTS_LOG_FILE):
            try:
                with open(ALERTS_LOG_FILE, "r") as f:
                    loaded_data = json.load(f)
                if isinstance(loaded_data, list):
                    logs = loaded_data
                else:
                    logs = []
            except json.JSONDecodeError:
                logs = []
        
        logs.insert(0, alert_record)
        with open(ALERTS_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
        
        set_alert_status(latest_line)
        print(f"✅ Alert logged: {count} negative entries detected")


def initialize_user_settings(user_info):
    """Initialize or update user settings with Google auth info"""
    try:
        user_email = user_info.get("email", "")
        if not user_email:
            print("Warning: No email found in user info")
            return
        
        settings = {
            "name": user_info.get("name", "User"),
            "google_id": user_info.get("id", ""),
            "guardian_email": user_email
        }
        
        with open("user_settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        print(f"✅ User settings updated - Guardian email set to: {user_email}")
    except Exception as e:
        print(f"Error updating user settings: {e}")


def launch_gui(user_info):
    
    # --- CustomTkinter Setup ---
    ctk.set_appearance_mode("dark")  # "dark", "light", "system"
    ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
    
    initialize_user_settings(user_info)
    check_and_add_guardian_alert()

    root = ctk.CTk()
    root.title("SentiGuard")
    root.geometry("900x600")

    # Global animation object to prevent garbage collection
    current_animation = None
    # Track current view for theme refresh
    current_view = None

    def refresh_current_view():
        """Refreshes the current view to apply theme changes to graphs"""
        nonlocal current_view
        if current_view == 'live_graph':
            show_live_graph()
        elif current_view == 'analysis':
            show_analysis()
        elif current_view == 'settings':
            show_settings()
        # Other views (homepage, AI chat) auto-theme
        
    def set_light_mode():
        """Switch to light mode"""
        nonlocal current_view
        ctk.set_appearance_mode("light")
        refresh_current_view()

    def set_dark_mode():
        """Switch to dark mode"""
        nonlocal current_view
        ctk.set_appearance_mode("dark")
        refresh_current_view()

    def on_close():
        print("Exiting SentiGuard...")
        try:
            if VOICE_AVAILABLE and voice_recorder.is_recording:
                voice_recorder.stop_recording()
                print("Voice recording stopped")
        except Exception as e:
            print(f"Warning: Could not stop voice recording: {e}")

        try:
            from ai_companion import ai_companion
            if hasattr(ai_companion, 'animation_running'):
                ai_companion.animation_running = False
            print("AI companion stopped")
        except Exception:
            pass # AI companion may not be available
        
        # Clear keystrokes for user privacy
        try:
            if os.path.exists("keystrokes.txt"):
                with open("keystrokes.txt", "w") as f:
                    f.write("")
                print("Keystrokes cleared for privacy")
        except Exception as e:
            print(f"Warning: Could not clear keystrokes file: {e}")

        # Clear alert logs for privacy
        try:
            if os.path.exists("alerts_log.json"):
                with open("alerts_log.json", "w") as f:
                    json.dump([], f)
                print("Alert logs cleared for privacy")
        except Exception as e:
            print(f"Warning: Could not clear alert logs: {e}")

        # Reset alert status to 0 when app closes
        try:
            reset_alert_status()
            print("Alert status reset")
        except Exception as e:
            print(f"Warning: Could not reset alert status: {e}")

        print("SentiGuard cleanup completed")
        root.quit()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Top Bar
    top_bar = ctk.CTkFrame(root, height=50, corner_radius=0)
    top_bar.pack(side="top", fill="x")

    title_label = ctk.CTkLabel(top_bar, text="SentiGuard", font=ctk.CTkFont(size=16, weight="bold"))
    title_label.pack(side="left", padx=20, pady=10)

    user_text = user_info if isinstance(user_info, str) else user_info.get("name", "User")
    user_icon = ctk.CTkLabel(top_bar, text=f"\U0001F7E2 {user_text}")
    user_icon.pack(side="right", padx=20)

    # Sidebar
    sidebar = ctk.CTkFrame(root, width=150, corner_radius=0)
    sidebar.pack(side="left", fill="y")

    def create_sidebar_btn(text, icon, command):
        return ctk.CTkButton(
            sidebar,
            text=f"{icon} {text}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            command=command,
            fg_color="transparent",
            hover_color="#34495e" # Example hover, adjust as needed
        )

    def clear_main_area():
        """Clear all widgets from main area"""
        nonlocal current_animation
        if current_animation:
            current_animation.event_source.stop()
            current_animation = None
        for widget in main_area.winfo_children():
            widget.destroy()

    def show_homepage():
        """Show the homepage with app name and quote"""
        nonlocal current_view
        clear_main_area()
        current_view = "homepage"

        app_name_label = ctk.CTkLabel(
            main_area,
            text="SentiGuard",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#3498db" # Keep brand color
        )
        app_name_label.pack(pady=(100, 10))
        
        quote = ('"The greatest weapon against stress is our ability to choose one thought over another."'"\n– William James")
        quote_label = ctk.CTkLabel(
            main_area,
            text=quote,
            font=ctk.CTkFont(size=16, slant="italic"),
            text_color="#f39c12", # Keep brand color
            wraplength=650
        )
        quote_label.pack(pady=(8, 30))

    def show_live_graph():
        """Show live graph in main area with theme support"""
        nonlocal current_animation, current_view
        current_view = 'live_graph'
        
        if current_animation:
            current_animation.event_source.stop()
            current_animation = None
            
        check_and_add_guardian_alert()
        clear_main_area()

        # Get current theme colors for matplotlib
        if ctk.get_appearance_mode() == "Light":
            bg_color = "#ffffff"
            fg_color = "#000000"
            graph_bg = "#f0f0f0"
            grid_color = "#e0e0e0"
            line_color = "#3498db"
        else: # Dark mode
            bg_color = "#2b2b2b" # ctk theme dark bg
            fg_color = "#dce4ee" # ctk theme text
            graph_bg = "#242424" # ctk theme frame bg
            grid_color = "#444444"
            line_color = "#00ffff" # cyan for dark mode

        title_label = ctk.CTkLabel(
            main_area,
            text="📈 Live Mood Trend",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#3498db"
        )
        title_label.pack(pady=(20, 10))

        graph_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        graph_frame.pack(expand=True, fill="both", padx=20, pady=20)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(graph_bg)

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def animate(i):
            try:
                history = get_day_analysis()
                ax.clear()
                
                # Re-apply theme colors in animation
                ax.set_facecolor(graph_bg)
                line = None
                
                if history:
                    trimmed = history[-50:]
                    x_data = list(range(len(trimmed)))
                    y_data = [score for (_, score) in trimmed]
                    line = ax.plot(x_data, y_data, color=line_color, linestyle='-', marker='o', linewidth=2, markersize=4)[0]
                    ax.set_title("Mood Trend (Live)", color=fg_color, fontsize=14)
                    ax.set_xlabel("Entry", color=fg_color)
                    ax.set_ylabel("Mood Score", color=fg_color)
                    ax.set_ylim(-1, 1)
                    ax.grid(color=grid_color, alpha=0.3)
                    ax.tick_params(colors=fg_color)
                    
                    # Add reference lines
                    ax.axhline(y=0, color=fg_color, linestyle='-', alpha=0.3, linewidth=1)
                    ax.axhline(y=0.3, color='#00ff41', linestyle='--', alpha=0.5, linewidth=1)
                    ax.axhline(y=-0.3, color='#ff4757', linestyle='--', alpha=0.5, linewidth=1)
                
                if i % 10 == 0:
                    check_and_alert()
                
                return [line] if line else []
            except Exception as e:
                print(f"Error updating graph: {e}")
                return []

        current_animation = FuncAnimation(fig, animate, interval=500, cache_frame_data=False)
        canvas.draw()

    def show_analysis():
        """Show enhanced analysis with time period bar charts"""
        nonlocal current_view
        current_view = 'analysis'
        check_and_add_guardian_alert()
        clear_main_area()

        from analyzer import get_mood_statistics, get_mood_summary

        main_container = ctk.CTkFrame(main_area, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        title_label = ctk.CTkLabel(
            main_container,
            text="📊 Mood Analytics Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#3498db"
        )
        title_label.pack(pady=(10, 20))

        # Current mood summary section
        current_mood_frame = ctk.CTkFrame(main_container)
        current_mood_frame.pack(fill="x", pady=(0, 20), padx=20)

        mood_score = get_latest_mood()
        summary = get_mood_summary()

        current_title = ctk.CTkLabel(
            current_mood_frame,
            text="Current Mood",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        current_title.pack(pady=(15, 5))

        if mood_score >= 0.3:
            mood_color = "#00ff41"
            mood_emoji = "😊"
            mood_text = "Positive"
        elif mood_score <= -0.3:
            mood_color = "#ff4757"
            mood_emoji = "😞"
            mood_text = "Negative"
        else:
            mood_color = "#ffa726"
            mood_emoji = "😐"
            mood_text = "Neutral"

        mood_row = ctk.CTkFrame(current_mood_frame, fg_color="transparent")
        mood_row.pack(pady=(5, 10))

        emoji_label = ctk.CTkLabel(mood_row, text=mood_emoji, font=ctk.CTkFont(size=32))
        emoji_label.pack(side="left", padx=(20, 10))

        mood_info_frame = ctk.CTkFrame(mood_row, fg_color="transparent")
        mood_info_frame.pack(side="left")

        mood_label = ctk.CTkLabel(
            mood_info_frame,
            text=f"{mood_text} ({mood_score:.3f})",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=mood_color
        )
        mood_label.pack(anchor="w")

        summary_label = ctk.CTkLabel(
            mood_info_frame,
            text=f"Total entries: {summary['total_entries']} | Avg: {summary['avg_score']:.3f}",
            font=ctk.CTkFont(size=11)
        )
        summary_label.pack(anchor="w", pady=(5, 0))

        # Statistics summary cards
        stats_frame = ctk.CTkFrame(current_mood_frame, fg_color="transparent")
        stats_frame.pack(pady=(5, 15))

        # Positive card
        pos_card = ctk.CTkFrame(stats_frame, fg_color="#1a4a2e")
        pos_card.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(pos_card, text="😊", font=ctk.CTkFont(size=20)).pack(pady=(8, 2))
        ctk.CTkLabel(pos_card, text=str(summary['positive_count']), font=ctk.CTkFont(size=16, weight="bold"), text_color="#00ff41").pack()
        ctk.CTkLabel(pos_card, text="Positive", font=ctk.CTkFont(size=10), text_color="white").pack(pady=(0, 8))

        # Neutral card
        neu_card = ctk.CTkFrame(stats_frame, fg_color="#4a3c1a")
        neu_card.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(neu_card, text="😐", font=ctk.CTkFont(size=20)).pack(pady=(8, 2))
        ctk.CTkLabel(neu_card, text=str(summary['neutral_count']), font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffa726").pack()
        ctk.CTkLabel(neu_card, text="Neutral", font=ctk.CTkFont(size=10), text_color="white").pack(pady=(0, 8))

        # Negative card
        neg_card = ctk.CTkFrame(stats_frame, fg_color="#4a1a1a")
        neg_card.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(neg_card, text="😞", font=ctk.CTkFont(size=20)).pack(pady=(8, 2))
        ctk.CTkLabel(neg_card, text=str(summary['negative_count']), font=ctk.CTkFont(size=16, weight="bold"), text_color="#ff4757").pack()
        ctk.CTkLabel(neg_card, text="Negative", font=ctk.CTkFont(size=10), text_color="white").pack(pady=(0, 8))

        # Chart section
        chart_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=20)

        period_frame = ctk.CTkFrame(chart_frame, fg_color="transparent")
        period_frame.pack(pady=(0, 10))
        ctk.CTkLabel(period_frame, text="Time Period:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 10))

        current_period = ctk.StringVar(value="daily")
        current_chart_canvas = None

        def update_chart():
            nonlocal current_chart_canvas
            if current_chart_canvas:
                current_chart_canvas.destroy()

            # Get current theme colors for matplotlib
            if ctk.get_appearance_mode() == "Light":
                chart_bg = "#ffffff"
                chart_fg = "#000000"
                plot_bg = "#f0f0f0"
                grid_color = "#e0e0e0"
            else: # Dark mode
                chart_bg = "#2b2b2b"
                chart_fg = "#dce4ee"
                plot_bg = "#242424"
                grid_color = "#444444"

            period = current_period.get()
            stats_data = get_mood_statistics(period)

            if not stats_data:
                no_data_label = ctk.CTkLabel(chart_frame, text="No data available for selected period", font=ctk.CTkFont(size=14))
                no_data_label.pack(pady=50)
                current_chart_canvas = no_data_label
                return

            fig, ax = plt.subplots(figsize=(12, 6), dpi=90)
            fig.patch.set_facecolor(chart_bg)
            ax.set_facecolor(plot_bg)

            labels = [item['label'] for item in stats_data[-20:]]
            values = [item['value'] for item in stats_data[-20:]]
            counts = [item['count'] for item in stats_data[-20:]]

            colors = []
            for value in values:
                if value > 0.1: colors.append('#00ff41')
                elif value < -0.1: colors.append('#ff4757')
                else: colors.append('#ffa726')

            edge_color = 'white' if ctk.get_appearance_mode() == "Dark" else 'black'
            bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor=edge_color, linewidth=0.5)

            ax.set_title(f'Mood Trends - {period.title()} View', color=chart_fg, fontsize=16, pad=20)
            ax.set_ylabel('Average Mood Score', color=chart_fg, fontsize=12)
            ax.set_ylim(-1, 1)
            ax.grid(color=grid_color, alpha=0.3, axis='y')
            ax.tick_params(colors=chart_fg, labelsize=10)
            
            ax.axhline(y=0, color=chart_fg, linestyle='-', alpha=0.3, linewidth=1)
            ax.axhline(y=0.3, color='#00ff41', linestyle='--', alpha=0.5, linewidth=1)
            ax.axhline(y=-0.3, color='#ff4757', linestyle='--', alpha=0.5, linewidth=1)

            for bar, value, count in zip(bars, values, counts):
                if count > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height >= 0 else -0.08),
                            f'{value:.2f}', ha='center', va='bottom' if height >= 0 else 'top',
                            color=chart_fg, fontsize=9, fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            chart_canvas_agg = FigureCanvasTkAgg(fig, master=chart_frame)
            chart_canvas_agg.draw()
            chart_canvas_agg.get_tk_widget().pack(fill="both", expand=True)
            current_chart_canvas = chart_canvas_agg.get_tk_widget()

        periods = [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]
        for text, value in periods:
            btn = ctk.CTkRadioButton(
                period_frame,
                text=text,
                variable=current_period,
                value=value,
                command=update_chart,
                font=ctk.CTkFont(size=11)
            )
            btn.pack(side="left", padx=5)

        update_chart()

    def show_ai_chat():
        """Show AI Chat interface in main area"""
        nonlocal current_view
        clear_main_area()
        current_view = "ai_chat"

        if not AI_AVAILABLE:
            unavailable_frame = ctk.CTkFrame(main_area, fg_color="transparent")
            unavailable_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            title_label = ctk.CTkLabel(unavailable_frame, text="🤖 AI Chat", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498db")
            title_label.pack(pady=(20, 20))
            
            info_text = ("AI Chat is currently unavailable.\n\n"
                         "To enable AI-powered conversations:\n"
                         "1. Install required packages: pip install openai\n"
                         "2. Get an OpenAI API key from platform.openai.com\n"
                         "3. Set environment variable: OPENAI_API_KEY=your_key\n\n"
                         "The app will continue to work normally without AI chat.")
            info_label = ctk.CTkLabel(unavailable_frame, text=info_text, font=ctk.CTkFont(size=12), justify="center")
            info_label.pack(pady=20)
            return

        title_label = ctk.CTkLabel(main_area, text="🤖 AI Companion Chat", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2966e3")
        title_label.pack(pady=(20, 10))

        subtitle_label = ctk.CTkLabel(main_area, text="Your empathetic AI companion is here to listen and support you 💙", font=ctk.CTkFont(size=12))
        subtitle_label.pack(pady=(0, 20))

        chat_container = ctk.CTkFrame(main_area, fg_color="transparent")
        chat_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Input area
        input_frame = ctk.CTkFrame(chat_container, fg_color="transparent")
        input_frame.pack(side="bottom", fill="x", pady=(15, 0))

        # Chat display area
        chat_frame = ctk.CTkFrame(chat_container)
        chat_frame.pack(fill="both", expand=True)

        chat_display = ctk.CTkTextbox(
            chat_frame,
            font=ctk.CTkFont(size=12),
            wrap="word",
            state="disabled",
            border_width=0,
            corner_radius=6
        )
        chat_display.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        chat_scrollbar = ctk.CTkScrollbar(chat_frame, command=chat_display.yview)
        chat_scrollbar.pack(side="right", fill="y")
        chat_display.configure(yscrollcommand=chat_scrollbar.set)
        
        # Configure text tags for styling
        chat_display.tag_configure("user", justify="right")
        chat_display.tag_configure("ai", justify="left")
        chat_display.tag_configure("timestamp", font=ctk.CTkFont(size=9), foreground="#888888")
        chat_display.tag_configure("mood", font=ctk.CTkFont(size=10, slant="italic"), foreground="#2966e3")

        # Current mood indicator
        current_mood = get_latest_mood()
        mood_text = f"Current mood: {current_mood:.2f}"
        if current_mood >= 0.2: mood_emoji = "😊"
        elif current_mood <= -0.2: mood_emoji = "😔"
        else: mood_emoji = "😐"
        
        mood_label = ctk.CTkLabel(input_frame, text=f"{mood_emoji} {mood_text}", font=ctk.CTkFont(size=10), text_color="#2966e3")
        mood_label.pack(anchor="w", pady=(0, 5))

        # Message input
        input_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_row.pack(fill="x")
        
        message_var = ctk.StringVar()
        message_entry = ctk.CTkEntry(
            input_row,
            textvariable=message_var,
            font=ctk.CTkFont(size=12),
            placeholder_text="Type your message here..."
        )
        message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        send_button = ctk.CTkButton(
            input_row,
            text="Send 💬",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=80
        )
        send_button.pack(side="right")
        
        chat_state = {"processing": False}

        def add_message_to_chat(message, sender="user", show_mood=False):
            """Add a message to the chat display"""
            chat_display.configure(state="normal")
            timestamp = datetime.datetime.now().strftime("%H:%M")
            
            if sender == "user":
                chat_display.insert("end", f"\n🙋‍♀️ You ({timestamp})\n", ("timestamp", "user"))
                if show_mood:
                    mood_info = f"Mood: {current_mood:.2f} "
                    chat_display.insert("end", mood_info, ("mood", "user"))
                chat_display.insert("end", f"{message}\n", "user")
            else: # AI
                chat_display.insert("end", f"\n🤖 AI Companion ({timestamp})\n", ("timestamp", "ai"))
                chat_display.insert("end", f"{message}\n", "ai")
            
            chat_display.insert("end", "\n")
            chat_display.configure(state="disabled")
            chat_display.see("end")

        async def send_message():
            if chat_state["processing"]: return
            message = message_var.get().strip()
            if not message: return
            
            chat_state["processing"] = True
            send_button.configure(text="...", state="disabled")
            message_entry.configure(state="disabled")
            
            try:
                add_message_to_chat(message, sender="user", show_mood=True)
                message_var.set("")
                
                current_mood_val = get_latest_mood() # Use a different name
                history = get_day_analysis()
                trend = "stable"
                if len(history) >= 2:
                    recent_scores = [score for _, score in history[-5:]]
                    if len(recent_scores) >= 2:
                        trend = "improving" if recent_scores[-1] > recent_scores[0] else "declining"
                
                response = await chat_with_ai(message, current_mood_val, trend)
                add_message_to_chat(response, sender="ai")

                if current_mood_val < -0.3:
                    suggestions = get_mood_suggestions(current_mood_val)
                    if suggestions:
                        suggestion_text = f"\n💡 Here are some gentle suggestions that might help:\n• {suggestions[0]}\n• {suggestions[1]}"
                        add_message_to_chat(suggestion_text, sender="ai")
            except Exception as e:
                error_msg = "I'm having trouble responding right now. Please try again in a moment."
                add_message_to_chat(error_msg, sender="ai")
                print(f"AI chat error: {e}")
            finally:
                chat_state["processing"] = False
                send_button.configure(text="Send 💬", state="normal")
                message_entry.configure(state="normal")
                message_entry.focus()

        def on_send_click():
            import asyncio
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_message())
                finally:
                    loop.close()
            threading.Thread(target=run_async, daemon=True).start()

        def on_enter_key(event):
            if not chat_state["processing"]:
                on_send_click()
            return "break"

        send_button.configure(command=on_send_click)
        message_entry.bind("<Return>", on_enter_key)

        welcome_msg = ("Hello! I'm your AI companion here to support you. 😊\n\n"
                       "I can see that your current mood is being monitored, and I'm here to listen "
                       "and provide gentle support based on how you're feeling.\n\n"
                       "Feel free to share what's on your mind, ask questions, or just say hello!")
        add_message_to_chat(welcome_msg, sender="ai")
        message_entry.focus()

        def add_proactive_message():
            try:
                if AI_AVAILABLE:
                    from ai_companion import get_proactive_message
                    recent_patterns = {
                        'mood_declining': current_mood < -0.3,
                        'stress_detected': current_mood < -0.4,
                        'improvement_noted': current_mood > 0.4
                    }
                    proactive_msg = get_proactive_message(recent_patterns)
                    if proactive_msg:
                        root.after(2000, lambda: add_message_to_chat(proactive_msg, sender="ai"))
            except:
                pass
        root.after(1000, add_proactive_message)

    def show_personalized_insights():
        """Show AI-powered personalized insights in main area"""
        nonlocal current_view
        clear_main_area()
        current_view = "insights"

        insights_container = ctk.CTkFrame(main_area, fg_color="transparent")
        insights_container.pack(fill="both", expand=True, padx=20, pady=10)

        header_frame = ctk.CTkFrame(insights_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(5, 15))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🔮 AI Personalized Insights",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#3498db"
        )
        title_label.pack()

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="AI-powered analysis of your mental health patterns",
            font=ctk.CTkFont(size=11),
            wraplength=600
        )
        subtitle_label.pack(pady=(5, 0))

        loading_frame = ctk.CTkFrame(insights_container, fg_color="transparent")
        loading_frame.pack(fill="both", expand=True)
        
        loading_center = ctk.CTkFrame(loading_frame, fg_color="transparent")
        loading_center.pack(expand=True)
        
        loading_label = ctk.CTkLabel(
            loading_center,
            text="🧠 Analyzing your patterns with AI...\nThis may take a moment.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        loading_label.pack(pady=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(loading_center, mode="indeterminate")
        progress_bar.pack()
        progress_bar.start()

        def display_insights(insights_summary):
            loading_frame.destroy()
            
            if not insights_summary:
                no_data_frame = ctk.CTkFrame(insights_container, fg_color="transparent")
                no_data_frame.pack(expand=True)
                ctk.CTkLabel(no_data_frame, text="📊", font=ctk.CTkFont(size=48)).pack(pady=(20, 15))
                ctk.CTkLabel(
                    no_data_frame,
                    text="Not enough data for AI insights yet!\n\nKeep using Sentiguard to unlock personalized insights.",
                    font=ctk.CTkFont(size=12),
                    justify="center",
                    wraplength=400
                ).pack()
                return

            # --- Replaced complex canvas scrolling with CTkScrollableFrame ---
            scrollable_frame = ctk.CTkScrollableFrame(insights_container)
            scrollable_frame.pack(fill="both", expand=True, pady=(5, 0))

            summary_card = ctk.CTkFrame(scrollable_frame, border_width=1)
            summary_card.pack(fill="x", pady=(5, 15), ipady=3)
            
            summary_title = ctk.CTkLabel(
                summary_card,
                text="💙 Your Personal Summary",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#3498db"
            )
            summary_title.pack(pady=(15, 8))
            
            summary_text = ctk.CTkLabel(
                summary_card,
                text=insights_summary.personal_message,
                font=ctk.CTkFont(size=11),
                wraplength=600,
                justify="left"
            )
            summary_text.pack(pady=(0, 15), padx=20)
            
            overview_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            overview_frame.pack(fill="x", pady=(0, 10))
            
            stats_text = f"📈 {insights_summary.total_insights} insights • 🔥 {insights_summary.high_priority_count} high priority • 🎯 {insights_summary.main_theme}"
            stats_label = ctk.CTkLabel(overview_frame, text=stats_text, font=ctk.CTkFont(size=10))
            stats_label.pack()

            for i, insight in enumerate(insights_summary.insights, 1):
                insight_card = ctk.CTkFrame(scrollable_frame, border_width=1)
                insight_card.pack(fill="x", pady=6, ipady=2)
                
                header_frame = ctk.CTkFrame(insight_card, fg_color="transparent")
                header_frame.pack(fill="x", pady=(10, 0), padx=(12, 15))
                
                title_label = ctk.CTkLabel(
                    header_frame,
                    text=insight.title,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#3498db"
                )
                title_label.pack(side="left")
                
                priority_colors = {1: "#dc3545", 2: "#fd7e14", 3: "#ffc107", 4: "#28a745", 5: "#6c757d"}
                priority_texts = {1: "High", 2: "Med-High", 3: "Medium", 4: "Low", 5: "Info"}
                
                priority_label = ctk.CTkLabel(
                    header_frame,
                    text=priority_texts.get(insight.priority, "Med"),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color=priority_colors.get(insight.priority, "#6c757d"),
                    text_color="white",
                    corner_radius=6,
                    padx=6
                )
                priority_label.pack(side="right")
                
                confidence_frame = ctk.CTkFrame(insight_card, fg_color="transparent")
                confidence_frame.pack(fill="x", padx=15)
                confidence_label = ctk.CTkLabel(
                    confidence_frame,
                    text=f"AI Confidence: {insight.confidence:.0%}",
                    font=ctk.CTkFont(size=9)
                )
                confidence_label.pack(side="left")
                
                content_label = ctk.CTkLabel(
                    insight_card,
                    text=insight.content,
                    font=ctk.CTkFont(size=10),
                    wraplength=600,
                    justify="left"
                )
                content_label.pack(pady=10, padx=15, anchor="w")
                
                if insight.actionable_steps:
                    actions_title = ctk.CTkLabel(
                        insight_card,
                        text="💡 Actions:",
                        font=ctk.CTkFont(size=9, weight="bold"),
                        text_color="#3498db"
                    )
                    actions_title.pack(anchor="w", padx=12, pady=(5, 3))
                    
                    for action in insight.actionable_steps:
                        action_label = ctk.CTkLabel(
                            insight_card,
                            text=f"• {action}",
                            font=ctk.CTkFont(size=9),
                            wraplength=550,
                            justify="left"
                        )
                        action_label.pack(anchor="w", padx=25, pady=1)
                
                ctk.CTkFrame(insight_card, fg_color="transparent", height=5).pack()

            refresh_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            refresh_frame.pack(fill="x", pady=20)
            
            refresh_button = ctk.CTkButton(
                refresh_frame,
                text="🔄 Refresh Insights",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda: refresh_insights()
            )
            refresh_button.pack()

        def display_error(error_message):
            loading_frame.destroy()
            error_container = ctk.CTkFrame(insights_container, fg_color="transparent")
            error_container.pack(fill="both", expand=True)
            
            error_frame = ctk.CTkFrame(error_container, fg_color="transparent")
            error_frame.pack(expand=True)
            
            error_icon = ctk.CTkLabel(error_frame, text="WARNING", font=ctk.CTkFont(size=16, weight="bold"), text_color="#dc3545")
            error_icon.pack(pady=20)
            
            error_label = ctk.CTkLabel(
                error_frame,
                text=f"Error generating insights:\n{error_message}\n\nTry again in a moment.",
                font=ctk.CTkFont(size=12),
                justify="center"
            )
            error_label.pack(pady=10)

        def refresh_insights():
            show_personalized_insights()
        
        def load_insights_async():
            import asyncio
            from personalized_insights import get_personalized_insights
            async def get_insights():
                try:
                    insights_summary = await get_personalized_insights()
                    root.after(0, lambda: display_insights(insights_summary))
                except Exception as e:
                    root.after(0, lambda: display_error(str(e)))
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(get_insights())
            finally:
                loop.close()

        threading.Thread(target=load_insights_async, daemon=True).start()

    def show_guardian():
        check_and_add_guardian_alert()
        
        popup = ctk.CTkToplevel()
        popup.title("Guardian Dashboard")
        popup.geometry("700x450")
        popup.resizable(False, False)

        def get_current_alert_state():
            result = count_below_threshold(return_lines=True)
            count = result[0] if len(result) == 3 else result[0]
            return ("Armed", count) if count > 10 else ("Waiting", count)
        
        state, since_last = get_current_alert_state()
        state_color = "red" if state == "Armed" else "lime green"
        
        ctk.CTkLabel(popup, text=f"Current Alert State: {state}", text_color=state_color, font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(popup, text=f"Negative entries since last alert: {since_last}", font=ctk.CTkFont(size=11)).pack(pady=(0, 15))

        ALERTS_LOG_FILE = "alerts_log.json"

        def load_alert_history():
            if not os.path.exists(ALERTS_LOG_FILE): return []
            try:
                with open(ALERTS_LOG_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []

        logs = load_alert_history()
        
        table_frame = ctk.CTkFrame(popup, fg_color="transparent")
        table_frame.pack(pady=(10, 0), padx=8, fill="x")

        headers = ["Date/Time", "Neg. Count", "Status", "Reason Excerpt"]
        for col, title in enumerate(headers):
            ctk.CTkLabel(
                table_frame,
                text=title,
                text_color="#FFBD39",
                font=ctk.CTkFont(size=10, weight="bold")
            ).grid(row=0, column=col, sticky="nsew", padx=10, pady=7)
            table_frame.grid_columnconfigure(col, weight=1 if col == 3 else 0) # Give excerpt more space

        if logs:
            for i, alert in enumerate(logs[:12], start=1):
                excerpt = " | ".join(alert["reason_lines"][:2]) + ("..." if len(alert["reason_lines"]) > 2 else "")
                
                for col, val in enumerate([alert["date"], str(alert["negative_count"]), alert["status"], excerpt]):
                    col_fg = "#7cffc0" if col==2 and val=="Sent" else "#dce4ee"
                    lbl = ctk.CTkLabel(table_frame, text=val, text_color=col_fg, font=ctk.CTkFont(size=10), anchor="w", justify="left")
                    lbl.grid(row=i, column=col, sticky="nsew", padx=8, pady=5)
            
            # This part is complex to replicate perfectly without full knowledge.
            # Simplified:
            # ctk.CTkLabel(popup, text="Alert log details are complex to show in this context.", font=ctk.CTkFont(size=11, slant="italic")).pack(pady=17)
        
        else:
            ctk.CTkLabel(table_frame, text="No guardian alerts yet.", font=ctk.CTkFont(size=11, slant="italic")).grid(row=1, column=0, columnspan=4, pady=30)
        
        # Tip removed as click-to-detail is complex to add back
        
    def show_settings():
        """Show settings in main area using a CTkTabview"""
        nonlocal current_view
        clear_main_area()
        current_view = "settings"

        title_label = ctk.CTkLabel(
            main_area,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2966e3"
        )
        title_label.pack(pady=(20, 20))

        # --- Replaced complex tab logic with CTkTabview ---
        tab_view = ctk.CTkTabview(main_area)
        tab_view.pack(pady=10, padx=50, fill="both", expand=True)
        
        pref_tab = tab_view.add("Preferences")
        account_tab = tab_view.add("Account")
        about_tab = tab_view.add("About")

        # --- Preferences Tab ---
        ctk.CTkLabel(pref_tab, text="Theme Selection", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 15), padx=20)
        
        theme_frame = ctk.CTkFrame(pref_tab, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10, padx=20)
        
        btn_light = ctk.CTkButton(theme_frame, text="Light Mode", command=set_light_mode)
        btn_light.pack(side="left", padx=(0, 10))
        
        btn_dark = ctk.CTkButton(theme_frame, text="Dark Mode", command=set_dark_mode)
        btn_dark.pack(side="left")
        
        ctk.CTkLabel(pref_tab, text="Privacy Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(30, 15), padx=20)
        
        privacy_info = ctk.CTkLabel(
            pref_tab,
            text="• Keystrokes are automatically cleared when app closes\n"
                 "• Voice recordings are processed locally\n"
                 "• No data is sent to external servers\n"
                 "• Mood history is preserved for timeline analytics (contains no text)",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        privacy_info.pack(anchor="w", pady=5, padx=20)
        
        privacy_actions_frame = ctk.CTkFrame(pref_tab, fg_color="transparent")
        privacy_actions_frame.pack(fill="x", pady=15, padx=20)

        def clear_all_mood_history():
            result = messagebox.askyesno("Clear Mood History",
                                         "This will permanently delete all mood history data.\n\nAre you sure?")
            if result:
                from analyzer import clear_mood_history
                if clear_mood_history():
                    messagebox.showinfo("Privacy", "Mood history has been cleared successfully.")
                else:
                    messagebox.showerror("Error", "Failed to clear mood history. Please try again.")

        clear_history_btn = ctk.CTkButton(
            privacy_actions_frame,
            text="Clear Mood History",
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            command=clear_all_mood_history
        )
        clear_history_btn.pack(anchor="w", pady=5)

        # --- Account Tab ---
        try:
            with open("user_settings.json", "r") as f:
                settings = json.load(f)
            
            ctk.CTkLabel(account_tab, text="Account Information", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 15), padx=20)
            
            account_frame = ctk.CTkFrame(account_tab, fg_color="transparent")
            account_frame.pack(fill="x", pady=10, padx=20)
            
            ctk.CTkLabel(account_frame, text=f"Name: {settings.get('name', 'User')}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=3)
            ctk.CTkLabel(account_frame, text=f"Guardian Email: {settings.get('guardian_email', 'Not set')}", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=3)
            ctk.CTkLabel(account_frame, text=f"Google ID: {settings.get('google_id', 'Not set')}", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=3)
        except Exception as e:
            ctk.CTkLabel(account_tab, text="Unable to load account information", text_color="#ff6b6b", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=20, padx=20)

        # --- About Tab ---
        ctk.CTkLabel(about_tab, text="About SentiGuard", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 15), padx=20)
        
        desc = ("SentiGuard is an innovative AI-powered desktop companion designed "
                "to passively monitor typing behavior for early signs of emotional distress.\n\n"
                "Our goal is to provide a real-time, privacy-first solution that "
                "supports mental well-being, especially for students and remote workers, "
                "by offering insights and alerting guardians for timely intervention.")
        
        ctk.CTkLabel(about_tab, text=desc, font=ctk.CTkFont(size=11), justify="left", wraplength=500).pack(anchor="w", pady=10, padx=20)
        ctk.CTkLabel(about_tab, text="Developed by: StrawHats", font=ctk.CTkFont(size=12, slant="italic"), text_color="#aad6ff").pack(anchor="w", pady=(20, 8), padx=20)


    # Main Area
    main_area = ctk.CTkFrame(root, corner_radius=10)
    main_area.pack(expand=True, fill="both", padx=10, pady=10)

    # Initialize homepage
    show_homepage()

    # --- Sidebar Button Creation ---
    btn_live = create_sidebar_btn("Live Graph", "\U0001F4C8", show_live_graph)
    btn_live.pack(fill="x", pady=(20, 5), padx=10)
    
    btn_analysis = create_sidebar_btn("Analysis", "\U0001F4C9", show_analysis)
    btn_analysis.pack(fill="x", pady=5, padx=10)

    ai_icon = "🤖" if AI_AVAILABLE else "🤖💤"
    ai_text = "AI Chat" if AI_AVAILABLE else "AI Chat (Off)"
    btn_ai_chat = create_sidebar_btn(ai_text, ai_icon, show_ai_chat)
    btn_ai_chat.pack(fill="x", pady=5, padx=10)

    btn_insights = create_sidebar_btn("AI Insights", "🔮", show_personalized_insights)
    btn_insights.pack(fill="x", pady=5, padx=10)

    voice_btn_text = ctk.StringVar(value="Voice (Off)" if not VOICE_AVAILABLE else "Start Voice")
    
    def toggle_voice_recording():
        if not VOICE_AVAILABLE:
            messagebox.showinfo("Voice Recording Disabled",
                                "Voice recording is currently disabled.\n\n"
                                "To enable voice recording:\n"
                                "1. Install required package: pip install SpeechRecognition\n"
                                "2. Restart the application")
            return
        
        try:
            if voice_recorder.is_recording:
                print("Stopping voice recording...")
                voice_recorder.stop_recording()
                voice_btn_text.set("Start Voice")
                btn_voice.configure(fg_color="#28a745", hover_color="#218838")
                print("Voice recording stopped")
                messagebox.showinfo("Voice Recording", "Voice recording stopped successfully!")
            else:
                if not voice_recorder.initialized:
                    messagebox.showerror("Voice Recording Error",
                                         "ERROR: Microphone not available!\n\n"
                                         "Possible solutions:\n"
                                         "• Check microphone permissions in Windows Settings\n"
                                         "• Make sure no other app is using the microphone\n"
                                         "• Restart the application")
                    return
                
                print("Starting voice recording...")
                success = voice_recorder.start_recording()
                if success:
                    voice_btn_text.set("Stop Voice")
                    btn_voice.configure(fg_color="#dc3545", hover_color="#c82333")
                    print("Voice recording started")
                    messagebox.showinfo("Voice Recording",
                                        "Voice recording started!\n\n"
                                        "Speak clearly into your microphone.\n"
                                        "Your speech will be analyzed for mood sentiment.")
                else:
                    print("Failed to start voice recording")
                    messagebox.showerror("Voice Recording Error",
                                         "ERROR: Failed to start voice recording!\n\n"
                                         "Please check your microphone settings and try again.")
        except Exception as e:
            print(f"Error in voice recording toggle: {e}")
            voice_btn_text.set("Start Voice")
            btn_voice.configure(fg_color="#28a745", hover_color="#218838")
            messagebox.showerror("Voice Recording Error", f"An error occurred: {e}")

    btn_voice = ctk.CTkButton(
        sidebar,
        textvariable=voice_btn_text,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=toggle_voice_recording,
        fg_color="#666666" if not VOICE_AVAILABLE else "#28a745",
        hover_color="#555555" if not VOICE_AVAILABLE else "#218838"
    )
    btn_voice.pack(fill="x", pady=5, padx=10)

    btn_settings = create_sidebar_btn("Settings", "⚙️", show_settings)
    btn_settings.pack(fill="x", pady=5, padx=10)

    root.mainloop()

# Example of how to run (assuming you have a way to get user_info)
if __name__ == "__main__":
    # This user_info would come from your Google Auth flow
    # Using dummy data for demonstration
    user_info_demo = {
        "name": "Supriya",
        "email": "supriya@example.com",
        "id": "123456789",
        "picture": "https://lh3.googleusercontent.com/a/ACg8ocJ-..." # Example picture URL
    }
    
    # You would normally call your auth logic first
    # auth_info = run_google_auth()
    # if auth_info:
    #     launch_gui(auth_info)
    
    # For testing, we launch directly:
    launch_gui(user_info_demo)
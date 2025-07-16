import os
import time
import threading
from datetime import datetime, timedelta
import customtkinter

shutdown_scheduled_event = threading.Event()
shutdown_monitor_thread = None
countdown_update_job = None  # ⬅️ New: Reference for cancelling countdown
target_time = None           # ⬅️ Store shutdown time globally

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

def shutdown():
    print("Simulating system shutdown...")
    os.system("shutdown /s /t 1")

def cancel_shutdown():
    global countdown_update_job
    if shutdown_scheduled_event.is_set():
        shutdown_scheduled_event.clear()
        app.after(0, lambda: status_label.configure(text="✅ Shutdown cancelled."))
        app.after(0, lambda: countdown_label.configure(text=""))  # ⬅️ Clear countdown
        if countdown_update_job:
            app.after_cancel(countdown_update_job)
        os.system("shutdown /a")
    else:
        app.after(0, lambda: status_label.configure(text="No shutdown currently scheduled."))

def schedule_shutdown():
    global shutdown_monitor_thread, target_time
    if shutdown_scheduled_event.is_set():
        status_label.configure(text="⚠️ A shutdown is already scheduled. Cancel first.")
        return

    try:
        hour = int(hour_spinbox.get())
        minute = int(minute_spinbox.get())
        now = datetime.now()
        target_time = datetime.combine(now.date(), datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time())
        if target_time <= now:
            target_time += timedelta(days=1)
    except ValueError:
        status_label.configure(text="❌ Invalid time selection.")
        return

    shutdown_scheduled_event.set()
    status_label.configure(text=f"⏳ Shutdown scheduled at {target_time.strftime('%H:%M')}")
    update_countdown()  # ⬅️ Start countdown immediately

    def monitor_time():
        while shutdown_scheduled_event.is_set():
            now = datetime.now()
            if now >= target_time:
                app.after(0, lambda: status_label.configure(text="💻 Shutting down..."))
                app.after(0, lambda: countdown_label.configure(text=""))
                shutdown()
                shutdown_scheduled_event.clear()
                break
            time.sleep(10)

    shutdown_monitor_thread = threading.Thread(target=monitor_time, daemon=True)
    shutdown_monitor_thread.start()

def update_countdown():
    global countdown_update_job
    if not shutdown_scheduled_event.is_set():
        countdown_label.configure(text="")
        return

    now = datetime.now()
    remaining = target_time - now
    if remaining.total_seconds() <= 0:
        countdown_label.configure(text="Shutting down...")
        return

    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_label.configure(text=f"⏳ Time remaining: {hours:02}:{minutes:02}:{seconds:02}")
    countdown_update_job = app.after(1000, update_countdown)

# --- GUI SETUP ---

app = customtkinter.CTk()
app.title("Shutdown Scheduler")
app.geometry("300x260")
app.resizable(False, False)

customtkinter.CTkLabel(app, text="Select shutdown time (24-hr):", font=customtkinter.CTkFont(size=15)).pack(pady=10)

time_frame = customtkinter.CTkFrame(app)
time_frame.pack()

hour_spinbox = customtkinter.CTkComboBox(
    time_frame,
    values=[f"{i:02d}" for i in range(24)],
    width=60,
    font=customtkinter.CTkFont(size=14)
)
hour_spinbox.pack(side="left", padx=(0, 2))
hour_spinbox.set(f"{datetime.now().hour:02d}")

customtkinter.CTkLabel(time_frame, text=":", font=customtkinter.CTkFont(size=16, weight="bold")).pack(side="left")

minute_spinbox = customtkinter.CTkComboBox(
    time_frame,
    values=[f"{i:02d}" for i in range(60)],
    width=60,
    font=customtkinter.CTkFont(size=14)
)
minute_spinbox.pack(side="left", padx=(2, 0))
minute_spinbox.set(f"{datetime.now().minute:02d}")

schedule_button = customtkinter.CTkButton(
    app, text="Schedule Shutdown", command=schedule_shutdown,
    font=customtkinter.CTkFont(size=14, weight="bold")
)
schedule_button.pack(pady=15)

cancel_button = customtkinter.CTkButton(
    app, text="Cancel Shutdown", command=cancel_shutdown,
    fg_color="red", hover_color="darkred",
    font=customtkinter.CTkFont(size=14, weight="bold")
)
cancel_button.pack(pady=5)

status_label = customtkinter.CTkLabel(
    app, text="", text_color="green", font=customtkinter.CTkFont(size=13)
)
status_label.pack(pady=5)

# ⬇️ NEW: Countdown Label
countdown_label = customtkinter.CTkLabel(
    app, text="", text_color="orange", font=customtkinter.CTkFont(size=13)
)
countdown_label.pack(pady=5)

app.mainloop()

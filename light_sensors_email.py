import serial
from datetime import datetime
import os
import time as t
import smtplib
from email.mime.text import MIMEText

# === CONFIGURATION ===
BAUD_RATE = 9600
THRESHOLD = 130
READ_INTERVAL = 1
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"

EMAIL_ADDRESS = "carolina.langaro@gmail.com"
EMAIL_PASSWORD = "feeh unpb sxtu ehtm"
RECIPIENT_EMAILS = ["carolinalangaro@berkeley.edu", "carter_bower@berkeley.edu"]

# === EMAIL FUNCTION ===
def send_email_notification(sensor, event, timestamp):
    subject = f"Light {event} Detected - {sensor}"
    body = f"{sensor} turned {event} at {timestamp}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(RECIPIENT_EMAILS)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAILS, msg.as_string())
        print(f" Email sent to {len(RECIPIENT_EMAILS)} recipients.")
    except Exception as e:
        print(f" Email failed: {e}")

# === SETUP SERIAL PORT ===
try:
    ser = serial.Serial("COM21", BAUD_RATE, timeout=2)
    print("Serial connection established.")
except Exception as e:
    print(f" Failed to open serial port: {e}")
    exit()

prev_state = {'sensor1': None, 'sensor2': None, 'sensor3': None, 'sensor4': None}
current_date = None

# === MONITORING LOOP ===
while True:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H-%M-%S")

    if date_str != current_date:
        current_date = date_str
        data_file = os.path.join(DATA_DIR, f"{current_date}_124C_Light_sensor.csv")
        transitions_file = os.path.join(DATA_DIR, f"{current_date}_light_transitions.csv")

        if not os.path.exists(data_file):
            with open(data_file, 'w') as f:
                f.write("timestamp,sensor1,sensor2,sensor3,sensor4\n")
        if not os.path.exists(transitions_file):
            with open(transitions_file, 'w') as f:
                f.write("timestamp,sensor,event\n")

    try:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if not raw:
            print(" Skipped empty line.")
            continue

        values = [int(x) for x in raw.split(',') if x.strip().isdigit()]
        if len(values) != 4:
            print(f" Skipped malformed line: {raw}")
            continue

        # Log full sensor values
        with open(data_file, 'a') as f:
            f.write(f"{timestamp_str},{values[0]},{values[1]},{values[2]},{values[3]}\n")

        # Detect transitions
        for i, sensor in enumerate(['sensor1', 'sensor2', 'sensor3', 'sensor4']):
            value = values[i]
            current_state = value > THRESHOLD
            if prev_state[sensor] is not None and current_state != prev_state[sensor]:
                event = "ON" if current_state else "OFF"
                print(f"⚡ {sensor} turned {event} at {timestamp_str}")
                with open(transitions_file, 'a') as f:
                    f.write(f"{timestamp_str},{sensor},{event}\n")
                send_email_notification(sensor, event, timestamp_str)
            prev_state[sensor] = current_state

    except Exception as e:
        print(f" Serial error: {e}")
        continue

    t.sleep(READ_INTERVAL)

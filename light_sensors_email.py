import serial
from datetime import datetime
import os
import time
import smtplib
from email.mime.text import MIMEText
import pandas as pd

# --- CONFIGURATION ---
BAUD_RATE = 9600
SERIAL_PORT = "COM21"
DATA_DIR = r"C:\Users\krieg\Desktop\UCB Age Light Records"
THRESHOLDS = [15, 121, 856, 100]  # Updated thresholds for sensors 1,2,4
EMAIL_ADDRESS = "labkriegsfeld@gmail.com"
EMAIL_PASSWORD = "mgoi bkyd dhil iwfq"
RECIPIENTS = ["carolinalangaro@berkeley.edu", "carter_bower@berkeley.edu"]

# --- SETUP FILES ---
date_str = datetime.now().strftime("%Y-%m-%d")
csv_file = os.path.join(DATA_DIR, f"{date_str}_light_data.csv")
css_file = os.path.join(DATA_DIR, f"{date_str}_light_log.css")
if not os.path.exists(csv_file):
    with open(csv_file, 'w') as f:
        f.write("timestamp,sensor1,sensor2,sensor3,sensor4\n")
if not os.path.exists(css_file):
    with open(css_file, 'w') as f:
        f.write("/* Light Sensor Log */\n")

# --- EMAIL FUNCTION ---
def send_email(sensor, event, timestamp):
    subject = f"Light {event} Detected - {sensor}"
    body = f"{sensor} turned {event} at {timestamp}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(RECIPIENTS)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())
        print(f"📧 Email sent for {sensor} {event}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

# --- SERIAL SETUP ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    print(f"✅ Connected to {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Serial error: {e}")
    exit()

prev_state = [None, None, None, None]

while True:
    try:
        print("Waiting for data...")
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            print("⚠️ Empty line")
            continue
        parts = [int(x) for x in line.split(',') if x.strip().isdigit()]
        if len(parts) != 4:
            print(f"⚠️ Malformed line: {line}")
            continue
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp}: {parts}")

        with open(csv_file, 'a') as f:
            f.write(f"{timestamp},{','.join(map(str, parts))}\n")

        with open(css_file, 'a') as f:
            for i, val in enumerate(parts):
                if THRESHOLDS[i] is not None:
                    status = "ON" if val > THRESHOLDS[i] else "OFF"
                    f.write(f"/* {timestamp} Sensor {i+1}: {status} */\n")
                    if prev_state[i] is not None and (val > THRESHOLDS[i]) != prev_state[i]:
                        send_email(f"Sensor {i+1}", status, timestamp)
                    prev_state[i] = val > THRESHOLDS[i]
                else:
                    # Sensor 3 is ignored or logged differently
                    f.write(f"/* {timestamp} Sensor {i+1}: IGNORED */\n")

        print("Sleeping for 10 minutes...")
        time.sleep(600)  # 10 minutes

    except KeyboardInterrupt:
        print("🛑 User stopped")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")


    t.sleep(READ_INTERVAL)

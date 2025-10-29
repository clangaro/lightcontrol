#!/usr/bin/env python3
"""
Light Sensor Data Logger and Alert System
-----------------------------------------
Reads data from a serial port connected to multiple light sensors,
logs readings to CSV and CSS files, and sends email alerts when
threshold crossings are detected.

Author: Carolina Chedid Langaro
Date: 2025-05-01
"""

import os
import time
import serial
import smtplib
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from typing import List, Optional

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

BAUD_RATE: int = 9600
SERIAL_PORT: str = "COM21"
DATA_DIR: str = r"C:\Users\krieg\Desktop\UCB Age Light Records"

# Thresholds for each sensor (None disables alert for that sensor)
THRESHOLDS: List[Optional[int]] = [15, 121, None, 856]

EMAIL_ADDRESS: str = "labkriegsfeld@gmail.com"
EMAIL_PASSWORD: str = "mgoi bkyd dhil iwfq"
RECIPIENTS: List[str] = [
    "carolinalangaro@berkeley.edu",
    "carter_bower@berkeley.edu",
]

READ_INTERVAL: int = 600  # seconds (10 minutes)

# ---------------------------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------------------------

date_str = datetime.now().strftime("%Y-%m-%d")
csv_path = os.path.join(DATA_DIR, f"{date_str}_light_data.csv")
css_path = os.path.join(DATA_DIR, f"{date_str}_light_log.css")

os.makedirs(DATA_DIR, exist_ok=True)

# Initialize CSV file if it doesn’t exist
if not os.path.exists(csv_path):
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("timestamp,sensor1,sensor2,sensor3,sensor4\n")

# Initialize CSS log file if it doesn’t exist
if not os.path.exists(css_path):
    with open(css_path, "w", encoding="utf-8") as f:
        f.write("/* Light Sensor Log */\n")

# ---------------------------------------------------------------------
# EMAIL FUNCTION
# ---------------------------------------------------------------------


def send_email(sensor: str, event: str, timestamp: str) -> None:
    """
    Sends an email alert when a light sensor changes state.

    Args:
        sensor: The sensor label (e.g., "Sensor 1").
        event: The event that occurred ("ON" or "OFF").
        timestamp: The time the event occurred.
    """
    subject = f"Light {event} Detected - {sensor}"
    body = f"{sensor} turned {event} at {timestamp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(RECIPIENTS)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, RECIPIENTS, msg.as_string())
        print(f"📧 Email sent for {sensor} {event}")
    except Exception as exc:
        print(f"❌ Failed to send email for {sensor}: {exc}")


# ---------------------------------------------------------------------
# SERIAL CONNECTION
# ---------------------------------------------------------------------


def initialize_serial(port: str, baud_rate: int) -> serial.Serial:
    """
    Initializes and returns a serial connection.

    Args:
        port: Serial port name (e.g., 'COM21').
        baud_rate: Communication speed in bits per second.

    Returns:
        A configured serial.Serial object.
    """
    try:
        ser = serial.Serial(port, baud_rate, timeout=5)
        print(f"✅ Connected to {port}")
        return ser
    except serial.SerialException as exc:
        print(f"❌ Serial connection failed: {exc}")
        raise SystemExit(1)


# ---------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------


def log_sensor_data(ser: serial.Serial) -> None:
    """
    Continuously reads from serial port, logs data, and triggers alerts.

    Args:
        ser: The active serial connection.
    """
    prev_state = [None] * 4  # Track previous ON/OFF states

    while True:
        try:
            print("Waiting for data...")
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                print("⚠️ No data received.")
                continue

            # Parse comma-separated sensor values
            parts = [int(x) for x in line.split(",") if x.strip().isdigit()]
            if len(parts) != 4:
                print(f"⚠️ Malformed line skipped: {line}")
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{timestamp}: {parts}")

            # Append data to CSV
            with open(csv_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp},{','.join(map(str, parts))}\n")

            # Append log to CSS and trigger emails
            with open(css_path, "a", encoding="utf-8") as f:
                for i, value in enumerate(parts):
                    if THRESHOLDS[i] is None:
                        f.write(f"/* {timestamp} Sensor {i+1}: IGNORED */\n")
                        continue

                    is_on = value > THRESHOLDS[i]
                    status = "ON" if is_on else "OFF"
                    f.write(f"/* {timestamp} Sensor {i+1}: {status} */\n")

                    # Send alert only on state change
                    if prev_state[i] is not None and is_on != prev_state[i]:
                        send_email(f"Sensor {i+1}", status, timestamp)
                    prev_state[i] = is_on

            print(f"Sleeping for {READ_INTERVAL / 60:.0f} minutes...")
            time.sleep(READ_INTERVAL)

        except KeyboardInterrupt:
            print("🛑 Stopped by user.")
            break
        except Exception as exc:
            print(f"⚠️ Runtime error: {exc}")
            time.sleep(10)


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    serial_connection = initialize_serial(SERIAL_PORT, BAUD_RATE)
    log_sensor_data(serial_connection)

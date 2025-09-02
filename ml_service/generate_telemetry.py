import csv
import random
import time
from datetime import datetime

# List of IoMT devices
DEVICES = [
    "glucose_monitor_01",
    "heart_rate_sensor_02",
    "insulin_pump_01",
    "smart_inhaler_01",
    "pacemaker_01",
    "blood_pressure_monitor_01"
]

# Possible IPs (some normal, some suspicious like public DNS)
NORMAL_IPS = ["192.168.1.5", "192.168.1.8", "10.0.0.3"]
SUSPICIOUS_IPS = ["8.8.8.8", "123.45.67.89"]

CSV_FILE = "telemetry.csv"

def generate_event():
    """Generate one fake IoMT telemetry record"""
    device = random.choice(DEVICES)
    timestamp = datetime.now().isoformat(timespec="seconds")
    packets_sent = random.randint(50, 1000)
    packets_received = packets_sent - random.randint(0, 20)

    # 10% chance of being suspicious
    if random.random() < 0.1:
        dest_ip = random.choice(SUSPICIOUS_IPS)
        status = "suspicious"
        packets_sent *= 5  # abnormal spike
    else:
        dest_ip = random.choice(NORMAL_IPS)
        status = "normal"

    return [device, timestamp, packets_sent, packets_received, dest_ip, status]


def write_header():
    """Write CSV header if file is empty"""
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id", "timestamp", "packets_sent", "packets_received", "dest_ip", "status"])


def append_event(event):
    """Append one row to CSV"""
    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(event)


if __name__ == "__main__":
    # Start fresh with a header
    write_header()
    print("Generating IoMT telemetry... (Ctrl+C to stop)")

    while True:
        event = generate_event()
        append_event(event)
        print("Added:", event)
        time.sleep(2)  # new event every 2 seconds

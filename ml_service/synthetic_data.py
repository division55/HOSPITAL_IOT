# ml_service/synthetic_data.py
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_FILE = os.path.join(DATA_DIR, "telemetry.csv")

def generate(device_type, n_normal=300, n_anom=30, start_ts=None):
    rows = []
    start_ts = start_ts or datetime.utcnow()
    if device_type == "glucose_monitor":
        normal_pkt = lambda : max(0.5, np.random.normal(1.0, 0.3))
        normal_bytes = lambda: max(300, np.random.normal(500, 80))
        normal_avg = lambda: max(100, np.random.normal(200, 40))
        for i in range(n_normal):
            rows.append({
                "ts": (start_ts + timedelta(seconds=i)).isoformat(),
                "device_id": f"G-{device_type[:3]}-{i}",
                "device_type": device_type,
                "pkt_sec": round(normal_pkt(), 3),
                "bytes_sec": round(normal_bytes(), 1),
                "dest_count": 1,
                "avg_payload": round(normal_avg(), 1),
                "protocol": "HTTPS",
                "patch_status": "patched",
                "maintenance_days": np.random.randint(1, 90),
                "is_anomaly": False
            })
        for i in range(n_anom):
            rows.append({
                "ts": (start_ts + timedelta(seconds=n_normal + i)).isoformat(),
                "device_id": f"G-{device_type[:3]}-ANOM-{i}",
                "device_type": device_type,
                "pkt_sec": float(np.random.randint(60, 300)),
                "bytes_sec": float(np.random.randint(20000, 120000)),
                "dest_count": np.random.randint(3, 8),
                "avg_payload": float(np.random.randint(800, 5000)),
                "protocol": "unknown",
                "patch_status": "unpatched",
                "maintenance_days": np.random.randint(200, 800),
                "is_anomaly": True
            })
    # Add other device types with simple rules if you want
    return rows

def main():
    types = ["glucose_monitor", "infusion_pump", "ventilator", "patient_monitor"]
    all_rows = []
    for t in types:
        all_rows.extend(generate(t, n_normal=200, n_anom=20))
    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_FILE, index=False)
    print("Wrote", OUT_FILE)

if __name__ == "__main__":
    main()

# ml_service/data_utils.py
import os
import pandas as pd
from datetime import datetime

DEFAULT_COLUMNS = [
    "ts","device_id","device_type","pkt_sec","bytes_sec","dest_count",
    "avg_payload","protocol","patch_status","maintenance_days","is_anomaly"
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "telemetry.csv")

def extract_features(payload: dict):
    """
    Convert incoming telemetry dict into feature vector for the model.
    Returns (features_list, meta_dict)
    """
    pkt = float(payload.get("pkt_sec", 0.0))
    bps = float(payload.get("bytes_sec", 0.0))
    dest = int(payload.get("dest_count", 0) or 0)
    avg_payload = float(payload.get("avg_payload", 0.0))
    protocol = payload.get("protocol", "unknown")
    meta = {
        "protocol": protocol,
        "patch_status": payload.get("patch_status", "unknown"),
        "maintenance_days": int(payload.get("maintenance_days", 0))
    }
    features = [pkt, bps, dest, avg_payload]
    return features, meta

def append_telemetry_row(payload: dict):
    """Append telemetry payload (dict) to CSV for later training/inspection."""
    row = {
        "ts": payload.get("ts") or datetime.utcnow().isoformat(),
        "device_id": payload.get("device_id"),
        "device_type": payload.get("device_type", "unknown"),
        "pkt_sec": payload.get("pkt_sec", 0.0),
        "bytes_sec": payload.get("bytes_sec", 0.0),
        "dest_count": payload.get("dest_count", 0),
        "avg_payload": payload.get("avg_payload", 0.0),
        "protocol": payload.get("protocol", "unknown"),
        "patch_status": payload.get("patch_status", "unknown"),
        "maintenance_days": payload.get("maintenance_days", 0),
        "is_anomaly": payload.get("is_anomaly", False)
    }
    df = pd.DataFrame([row])
    write_header = not os.path.exists(DATA_FILE)
    df.to_csv(DATA_FILE, mode="a", header=write_header, index=False)

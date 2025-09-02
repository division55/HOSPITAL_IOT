# ml_service/model_manager.py
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Tuple
from .data_utils import DATA_FILE
import math

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "model_store")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = ["pkt_sec", "bytes_sec", "dest_count", "avg_payload"]

# Default small synthetic baselines (used if no training data exists)
DEFAULT_BASELINES = {
    "glucose_monitor": np.array([[1.0, 500.0, 1, 200.0],
                                 [1.2, 520.0, 1, 210.0],
                                 [0.9, 480.0, 1, 190.0]]),
    "infusion_pump": np.array([[0.2, 120.0, 1, 80.0],
                               [0.3, 150.0, 1, 90.0],
                               [0.25, 130.0, 1, 85.0]]),
    "ventilator": np.array([[5.0, 2000.0, 1, 500.0],
                            [4.8, 1900.0, 1, 480.0],
                            [5.2, 2100.0, 1, 510.0]]),
    "patient_monitor": np.array([[2.0, 800.0, 1, 300.0],
                                 [2.2, 820.0, 1, 310.0]])
}

def model_path(device_type: str):
    safe = device_type.replace(" ", "_").lower()
    return os.path.join(MODEL_DIR, f"{safe}_if.joblib")

class ModelManager:
    def __init__(self, contamination=0.05):
        self.contamination = contamination

    def load_model(self, device_type: str):
        path = model_path(device_type)
        if os.path.exists(path):
            return joblib.load(path)
        # else train a tiny model from default baselines
        baseline = DEFAULT_BASELINES.get(device_type)
        if baseline is None:
            # fallback: use patient_monitor baseline if unknown
            baseline = DEFAULT_BASELINES["patient_monitor"]
        model = IsolationForest(contamination=self.contamination, random_state=42)
        model.fit(baseline)
        joblib.dump(model, path)
        return model

    def train_model(self, device_type: str, contamination: float = None) -> dict:
        """Train model for one device_type from CSV telemetry data (low-pkt as proxy for normal)."""
        if contamination is None:
            contamination = self.contamination
        if not os.path.exists(DATA_FILE):
            # nothing to train on
            return {"status":"no_data", "trained": False}

        df = pd.read_csv(DATA_FILE)
        df = df[df["device_type"] == device_type]
        # naive filter for 'normal' samples: pkt_sec < 10 (tweak for your devices)
        df_norm = df[df["pkt_sec"] < 10]
        if df_norm.shape[0] < 10:
            # fallback to default baseline
            baseline = DEFAULT_BASELINES.get(device_type)
            if baseline is None:
                baseline = DEFAULT_BASELINES["patient_monitor"]
            model = IsolationForest(contamination=contamination, random_state=42)
            model.fit(baseline)
            joblib.dump(model, model_path(device_type))
            return {"status":"trained_on_default", "trained": True, "samples": baseline.shape[0]}
        X = df_norm[FEATURE_COLS].values
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(X)
        joblib.dump(model, model_path(device_type))
        return {"status":"trained", "trained": True, "samples": X.shape[0]}

    def predict(self, telemetry: dict) -> dict:
        """
        telemetry: full dict including device_type, pkt_sec, bytes_sec, dest_count, avg_payload, patch_status, maintenance_days
        returns: {anomaly_score, risk_score, reasons}
        """
        device_type = telemetry.get("device_type", "unknown")
        features = [
            float(telemetry.get("pkt_sec", 0.0)),
            float(telemetry.get("bytes_sec", 0.0)),
            int(telemetry.get("dest_count", 0) or 0),
            float(telemetry.get("avg_payload", 0.0))
        ]
        model = self.load_model(device_type)
        arr = np.array([features])
        pred = int(model.predict(arr)[0])   # 1 normal, -1 anomaly
        raw = float(model.decision_function(arr)[0])  # higher = more normal
        # map raw -> anomaly confidence 0..1 (lower raw => higher anomaly)
        anomaly_score = float(1.0 / (1.0 + math.exp(raw)))  # simple logistic mapping

        # reasons: simple heuristics + model flag
        reasons = []
        if pred == -1:
            reasons.append("model_outlier")
        if features[0] > 50:
            reasons.append("high_pkt_rate")
        if features[2] > 3:
            reasons.append("many_destinations")
        protocol = telemetry.get("protocol", "unknown")
        if protocol == "unknown":
            reasons.append("unknown_protocol")
        if telemetry.get("patch_status", "unknown") != "patched":
            reasons.append("unpatched_firmware")

        # compute risk score (0..100) using formula described earlier
        patch_factor = 1.0 if telemetry.get("patch_status") == "patched" else 0.0
        maintenance_days = int(telemetry.get("maintenance_days") or 0)  # days since last maintenance
        maintenance_factor = min(1.0, maintenance_days / 365.0)

        risk = anomaly_score * 70.0 + (1.0 - patch_factor) * 20.0 + maintenance_factor * 10.0
        risk_score = int(max(0, min(100, round(risk))))

        return {
            "device_id": telemetry.get("device_id"),
            "device_type": device_type,
            "anomaly_score": round(anomaly_score, 4),
            "risk_score": risk_score,
            "pred": pred,
            "reasons": reasons
        }

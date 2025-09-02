# ml_service/train.py
from .model_manager import ModelManager
import os
import pandas as pd

def retrain_all():
    mm = ModelManager()
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.csv")
    if not os.path.exists(data_file):
        print("No telemetry data found. Run synthetic_data.py first.")
        return
    df = pd.read_csv(data_file)
    types = df["device_type"].dropna().unique().tolist()
    for t in types:
        print("Training model for:", t)
        res = mm.train_model(t)
        print(" -> ", res)

if __name__ == "__main__":
    retrain_all()

# ml_service/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import TelemetryIn, ScoreOut
from .data_utils import append_telemetry_row
from .model_manager import ModelManager
import uvicorn
import os

app = FastAPI(title="IoMT ML Scoring Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ModelManager()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/ml/score", response_model=ScoreOut)
def ml_score(t: TelemetryIn):
    payload = t.dict()
    # persist raw telemetry for later retraining / audit
    append_telemetry_row(payload)
    # get prediction
    res = manager.predict(payload)
    # convert to ScoreOut format
    out = {
        "device_id": res["device_id"],
        "device_type": res["device_type"],
        "anomaly_score": res["anomaly_score"],
        "risk_score": res["risk_score"],
        "reasons": res["reasons"]
    }
    return out

@app.post("/ml/retrain")
def ml_retrain(device_type: str = None):
    """
    Retrain model. If device_type is None -> returns training status for each known type.
    """
    if device_type:
        r = manager.train_model(device_type)
        return {"status":"ok", "result": r}
    # else try to retrain for any device types present in data file
    # naive: read data file to find types
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.csv")
    if not os.path.exists(data_file):
        return {"status":"no_data_file"}
    import pandas as pd
    df = pd.read_csv(data_file)
    types = df["device_type"].dropna().unique().tolist()
    results = {}
    for t in types:
        results[t] = manager.train_model(t)
    return {"status":"ok", "results": results}

@app.get("/ml/models")
def list_models():
    model_dir = os.path.join(os.path.dirname(__file__), "model_store")
    files = [f for f in os.listdir(model_dir) if f.endswith(".joblib")]
    return {"models": files}

if __name__ == "__main__":
    uvicorn.run("ml_service.main:app", host="0.0.0.0", port=9000, reload=True)

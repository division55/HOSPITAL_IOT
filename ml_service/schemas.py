# ml_service/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TelemetryIn(BaseModel):
    device_id: str
    device_type: Optional[str] = "unknown"
    ts: Optional[datetime] = None
    pkt_sec: float
    bytes_sec: float
    dest_count: int
    avg_payload: float
    protocol: Optional[str] = "unknown"
    patch_status: Optional[str] = "unknown"   # patched | unpatched
    maintenance_days: Optional[int] = 0       # days since last maintenance
    is_anomaly: Optional[bool] = False

class ScoreOut(BaseModel):
    device_id: str
    device_type: str
    anomaly_score: float
    risk_score: int
    reasons: List[str]

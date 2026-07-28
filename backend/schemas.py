from pydantic import BaseModel
from typing import List, Optional

class AnomalyReport(BaseModel):
    user_id: str
    anomaly_type: str # e.g. "mouthAsym", "headTilt", "eyesClosed"
    timestamp: float
    evidence_image: Optional[str] = None  # base64 JPEG snapshot

class VerificationResponse(BaseModel):
    user_id: str
    status: str # "ok" or "timeout"

class AuthRequest(BaseModel):
    username: str
    password: str

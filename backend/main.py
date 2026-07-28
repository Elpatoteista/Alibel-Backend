import json
import os
import base64
import uuid
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing import Dict, List, Optional
import asyncio

try:
    from passlib.context import CryptContext
    from jose import JWTError, jwt
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

# --- Auth Config ---
SECRET_KEY = "alibel-super-secret-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "static", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

if AUTH_ENABLED:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    if AUTH_ENABLED:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return str(data.get("sub"))

app = FastAPI(title="ALIBEL Backend")

# Keep track of last heartbeat
last_seen: Dict[str, float] = {}

# WebSocket Connections
class ConnectionManager:
    def __init__(self):
        # Maps user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
            
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

async def check_timeouts():
    while True:
        await asyncio.sleep(5)
        current_time = time.time()
        for client_id, last_time in list(last_seen.items()):
            if current_time - last_time > 12:  # 12 seconds without heartbeat = offline
                if client_id in last_seen:
                    del last_seen[client_id]
                manager.disconnect(client_id)
                await manager.broadcast({"type": "dashboard_update", "user_id": client_id, "status": "offline"})

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_timeouts())

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# --- Auth Endpoints ---
@app.post("/api/register")
async def register(form: schemas.AuthRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.id == form.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    user = models.User(id=form.username)
    if AUTH_ENABLED:
        user.hashed_password = pwd_context.hash(form.password)
    db.add(user)
    db.commit()
    token = create_access_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer", "user_id": form.username}

@app.post("/api/login")
async def login(form: schemas.AuthRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == form.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if AUTH_ENABLED and user.hashed_password:
        if not pwd_context.verify(form.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    token = create_access_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer", "user_id": form.username}

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/mobile", response_class=HTMLResponse)
async def get_mobile_app(request: Request):
    return templates.TemplateResponse(request=request, name="mobile.html")

@app.post("/api/anomaly")
async def report_anomaly(data: schemas.AnomalyReport, db: Session = Depends(get_db)):
    # Save evidence image if provided
    evidence_url = None
    if data.evidence_image:
        try:
            # Strip data:image/jpeg;base64, prefix if present
            img_data = data.evidence_image
            if "," in img_data:
                img_data = img_data.split(",", 1)[1]
            img_bytes = base64.b64decode(img_data)
            filename = f"{data.user_id}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(EVIDENCE_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            evidence_url = f"/static/evidence/{filename}"
        except Exception as e:
            print(f"Error saving evidence image: {e}")

    # Save to db
    record = models.AnomalyRecord(
        user_id=data.user_id,
        timestamp=data.timestamp,
        anomaly_type=data.anomaly_type,
        evidence_image_url=evidence_url
    )
    db.add(record)
    
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    is_new_user = False
    if not user:
        user = models.User(id=data.user_id)
        db.add(user)
        is_new_user = True
    
    db.commit()
    
    if is_new_user:
        await manager.broadcast({"type": "dashboard_update", "user_id": data.user_id, "status": "normal"})
    
    # Trigger verification flow immediately, because the client already waited for the time threshold
    user.status = "verifying"
    db.commit()
    
    event = models.Event(user_id=data.user_id, event_type="verification_requested")
    db.add(event)
    db.commit()
    
    # Send WebSocket message to app to show the "¿ESTÁS BIEN?" screen
    await manager.send_message({"type": "verification_requested"}, data.user_id)
    
    # Broadcast to dashboard with anomaly type AND evidence image
    await manager.broadcast({
        "type": "dashboard_update", 
        "user_id": data.user_id, 
        "status": "verifying",
        "anomaly_type": data.anomaly_type,
        "evidence_url": evidence_url
    })

    return {"status": "ok", "action": "verifying"}

@app.post("/api/verify")
async def verify_response(response: schemas.VerificationResponse, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == response.user_id).first()
    if not user:
        return {"status": "user_not_found"}
        
    if response.status == "ok":
        user.status = "normal"
        event = models.Event(user_id=response.user_id, event_type="user_verified")
        db.add(event)
    elif response.status == "timeout":
        user.status = "alert"
        event = models.Event(user_id=response.user_id, event_type="alert_triggered")
        db.add(event)
        
    db.commit()
    await manager.broadcast({"type": "dashboard_update", "user_id": response.user_id, "status": user.status})
    return {"status": "updated"}

# WebSocket for the Flutter App and Dashboard
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    if client_id != "dashboard":
        last_seen[client_id] = time.time()
        await manager.broadcast({"type": "dashboard_update", "user_id": client_id, "status": "normal"})
    try:
        while True:
            data_text = await websocket.receive_text()
            if client_id != "dashboard":
                last_seen[client_id] = time.time()
                
                # Parse JSON to check if it's a video frame
                try:
                    payload = json.loads(data_text)
                    if payload.get("type") == "video_frame":
                        # Send only to dashboard to save bandwidth
                        if "dashboard" in manager.active_connections:
                            await manager.active_connections["dashboard"].send_json({
                                "type": "video_frame",
                                "user_id": client_id,
                                "frame": payload.get("frame")
                            })
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        if client_id in last_seen:
            del last_seen[client_id]
        await manager.broadcast({"type": "dashboard_update", "user_id": client_id, "status": "offline"})

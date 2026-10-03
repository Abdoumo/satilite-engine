from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from database.session import get_db
from database.models import Pipeline, PipelineSegment, VideoAsset, Alert, SatelliteAnomaly
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Pipeline Monitoring Platform API")

import asyncio
from satellite.adapter import start_satellite_cron
from video.ingest import VideoPipeline

global_pipeline = None

@app.on_event("startup")
async def startup_event():
    start_satellite_cron()
    global global_pipeline
    global_pipeline = VideoPipeline(source=0, asset_id=1, manager=manager)
    asyncio.create_task(global_pipeline.run())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Pipeline Monitoring MVP"}

from fastapi.responses import StreamingResponse

async def video_stream():
    while True:
        if global_pipeline and global_pipeline.latest_jpg:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_pipeline.latest_jpg + b'\r\n')
        await asyncio.sleep(0.05)

async def thermal_stream():
    while True:
        if global_pipeline and hasattr(global_pipeline, 'latest_thermal_jpg') and global_pipeline.latest_thermal_jpg:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_pipeline.latest_thermal_jpg + b'\r\n')
        await asyncio.sleep(0.05)

@app.get("/api/video_feed")
async def video_feed():
    return StreamingResponse(video_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/thermal_feed")
async def thermal_feed():
    return StreamingResponse(thermal_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/pipelines")
def get_pipelines(db: Session = Depends(get_db)):
    pipelines = db.query(
        Pipeline.id,
        Pipeline.name,
        Pipeline.operator,
        func.ST_AsGeoJSON(Pipeline.geometry).label("geometry")
    ).all()
    
    features = []
    for p in pipelines:
        features.append({
            "type": "Feature",
            "properties": {
                "id": p.id,
                "name": p.name,
                "operator": p.operator
            },
            "geometry": json.loads(p.geometry)
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/api/pipelines/{pipeline_id}/segments")
def get_pipeline_segments(pipeline_id: int, db: Session = Depends(get_db)):
    segments = db.query(
        PipelineSegment.id,
        PipelineSegment.segment_name,
        PipelineSegment.risk_level,
        func.ST_AsGeoJSON(PipelineSegment.geometry).label("geometry")
    ).filter(PipelineSegment.pipeline_id == pipeline_id).all()
    
    features = []
    for s in segments:
        features.append({
            "type": "Feature",
            "properties": {
                "id": s.id,
                "name": s.segment_name,
                "risk_level": s.risk_level
            },
            "geometry": json.loads(s.geometry)
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/api/cameras")
def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(
        VideoAsset.id,
        VideoAsset.name,
        VideoAsset.status,
        VideoAsset.stream_url,
        func.ST_AsGeoJSON(VideoAsset.location).label("location")
    ).filter(VideoAsset.asset_type == 'CAMERA').all()
    
    features = []
    for c in cameras:
        features.append({
            "type": "Feature",
            "properties": {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "stream_url": c.stream_url
            },
            "geometry": json.loads(c.location) if c.location else None
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/drones")
def get_drones(db: Session = Depends(get_db)):
    drones = db.query(
        VideoAsset.id,
        VideoAsset.name,
        VideoAsset.status,
        VideoAsset.stream_url,
        func.ST_AsGeoJSON(VideoAsset.location).label("location")
    ).filter(VideoAsset.asset_type == 'DRONE').all()
    
    features = []
    for d in drones:
        features.append({
            "type": "Feature",
            "properties": {
                "id": d.id,
                "name": d.name,
                "status": d.status,
                "stream_url": d.stream_url
            },
            "geometry": json.loads(d.location) if d.location else None
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(
        Alert.id,
        Alert.alert_type,
        Alert.severity,
        Alert.status,
        func.ST_AsGeoJSON(Alert.location).label("location")
    ).order_by(Alert.created_at.desc()).limit(100).all()
    
    features = []
    for a in alerts:
        features.append({
            "type": "Feature",
            "properties": {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status
            },
            "geometry": json.loads(a.location) if a.location else None
        })
    return {"type": "FeatureCollection", "features": features}

class SatelliteAnomalyPayload(BaseModel):
    source: str
    product: str
    anomaly_type: str
    severity: str
    confidence: float
    latitude: float
    longitude: float

@app.post("/api/satellite/anomalies")
async def create_satellite_anomaly(payload: SatelliteAnomalyPayload, db: Session = Depends(get_db)):
    point_wkt = f"SRID=4326;POINT({payload.longitude} {payload.latitude})"
    anomaly = SatelliteAnomaly(
        source=payload.source,
        product=payload.product,
        anomaly_type=payload.anomaly_type,
        severity=payload.severity,
        confidence=payload.confidence,
        latitude=payload.latitude,
        longitude=payload.longitude,
        geometry=point_wkt
    )
    
    # Simple spatial correlation to find closest pipeline segment within 500m
    closest_segment = db.query(PipelineSegment).filter(
        func.ST_DWithin(
            PipelineSegment.geometry, 
            func.ST_GeomFromEWKT(point_wkt), 
            0.005 # rough degree approximation for 500m
        )
    ).first()
    
    if closest_segment:
        anomaly.pipeline_segment_id = closest_segment.id
        
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    
    # Broadcast event if a segment was affected
    if closest_segment:
        await manager.broadcast({
            "event": "alert.created",
            "payload": {
                "type": "SATELLITE_ANOMALY",
                "severity": anomaly.severity,
                "segment_id": closest_segment.id,
                "confidence": anomaly.confidence
            }
        })
        
    return {"status": "created", "anomaly_id": anomaly.id}

# WebSocket Manager
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/monitoring")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Can handle incoming messages if necessary
    except WebSocketDisconnect:
        manager.disconnect(websocket)

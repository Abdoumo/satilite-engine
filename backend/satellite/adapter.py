from apscheduler.schedulers.background import BackgroundScheduler
import httpx
import logging
from database.session import SessionLocal
from database.models import PipelineSegment

def start_satellite_cron():
    scheduler = BackgroundScheduler()
    
    def check_pipelines():
        logging.info("Running satellite background check for pipelines...")
        db = SessionLocal()
        try:
            segments = db.query(PipelineSegment).all()
            for seg in segments:
                if seg.risk_level == "HIGH":
                    payload = {
                        "source": "Sentinel-2",
                        "product": "HLS S30",
                        "anomaly_type": "NDVI_DROP",
                        "severity": "HIGH",
                        "confidence": 0.88,
                        "latitude": 36.901,
                        "longitude": 7.765
                    }
                    
                    try:
                        httpx.post("http://localhost:8000/api/satellite/anomalies", json=payload)
                        logging.info("Created satellite anomaly via adapter cron.")
                    except Exception as e:
                        logging.error(f"Failed to push anomaly: {e}")
                    
                    break
        finally:
            db.close()

    # Run every 1 minute for local testing MVP
    scheduler.add_job(check_pipelines, 'interval', minutes=1)
    scheduler.start()

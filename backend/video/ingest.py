import cv2
import asyncio
import threading
import logging
from video.inference import DetectionModel
from datetime import datetime
import json

class VideoPipeline:
    def __init__(self, source, asset_id, manager, mock_telemetry=None):
        self.source = source
        self.asset_id = asset_id
        self.manager = manager
        self.mock_telemetry = mock_telemetry or {"latitude": 36.901, "longitude": 7.765}
        self.model = DetectionModel(confidence_threshold=0.6)
        self.running = False
        self.latest_jpg = None
        self.latest_thermal_jpg = None
        self.latest_thermal_jpg = None
        self.loop = None
        
    async def run(self):
        self.running = True
        self.loop = asyncio.get_running_loop()
        thread = threading.Thread(target=self._run_sync, daemon=True)
        thread.start()

    def _run_sync(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            logging.warning(f"Failed to open source {self.source}, falling back to demo video")
            self.source = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
            cap = cv2.VideoCapture(self.source)

        logging.info(f"Started video pipeline for asset {self.asset_id} on source {self.source}")

        frame_count = 0
        while self.running:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            detections = []
            if frame_count % 5 == 0:
                detections = self.model.predict(frame)
                
                for det in detections:
                    if det["class"] in ["car", "truck", "person"]:
                        payload = {
                            "event": "detection.created",
                            "payload": {
                                "class": det["class"].upper(),
                                "confidence": det["confidence"],
                                "bbox": det["bbox"],
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "camera_id": self.asset_id,
                                "latitude": self.mock_telemetry["latitude"],
                                "longitude": self.mock_telemetry["longitude"]
                            }
                        }
                        if self.loop:
                            asyncio.run_coroutine_threadsafe(self.manager.broadcast(payload), self.loop)

                    # Draw bbox on frame for visual feed
                    x1, y1, x2, y2 = map(int, det["bbox"])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, f"{det['class'].upper()} {int(det['confidence']*100)}%", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

            # Resize for stream efficiency
            frame = cv2.resize(frame, (640, 360))
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                self.latest_jpg = buffer.tobytes()
                
            # Simulate thermal by applying a colormap
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            thermal = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
            ret_t, buffer_t = cv2.imencode('.jpg', thermal)
            if ret_t:
                self.latest_thermal_jpg = buffer_t.tobytes()
            
            
            frame_count += 1
            import time
            time.sleep(0.03)

        cap.release()
        
    def stop(self):
        self.running = False

from ultralytics import YOLO
import logging

class DetectionModel:
    def __init__(self, model_path="yolov8n.pt", confidence_threshold=0.5):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        logging.info(f"Loaded YOLO model from {model_path}")

    def predict(self, frame):
        """
        Runs YOLOv8 on a single frame.
        Returns a list of detections: [{"class": "name", "confidence": float, "bbox": [x1, y1, x2, y2]}]
        """
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = float(box.conf[0])
                if conf >= self.confidence_threshold:
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names[cls_id]
                    bbox = box.xyxy[0].tolist() # [x1, y1, x2, y2]
                    detections.append({
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": bbox
                    })
        return detections

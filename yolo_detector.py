# yolo_detector.py
# Simple wrapper for YOLOv8 detection (person class only)
from ultralytics import YOLO
import numpy as np

class YOLODetector:
    def __init__(self, model_path="yolov8n.pt", device="cpu"):
        # device can be "cpu" or "cuda"
        self.model = YOLO(model_path)
        self.model.fuse() # optional speedup
        self.device = device

    def detect(self, frame, conf_thresh=0.3):
        """
        Runs YOLO on a BGR OpenCV frame.
        Returns a list of detections: each is [x1, y1, x2, y2, score, class_id]
        Only returns detections whose class is 'person' (class_id == 0 for COCO).
        """
        # model expects either numpy or PIL — pass frame directly
        results = self.model(frame, imgsz=640, conf=conf_thresh, verbose=False)
        detections = []
        # results is a list (one item per batch image). We have single image.
        r = results[0]
        boxes = r.boxes # Boxes object
        if boxes is None:
            return detections

        for box, cls, conf in zip(boxes.xyxy.cpu().numpy(), boxes.cls.cpu().numpy(), boxes.conf.cpu().numpy()):
            class_id = int(cls)
            score = float(conf)
            x1, y1, x2, y2 = [int(x) for x in box]
            # COCO class 0 == person (ultralytics default COCO)
            if class_id == 0:
                detections.append([x1, y1, x2, y2, score, class_id])
        return detections

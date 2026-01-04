# tracker_deepsort.py
# Wrapper for deep-sort-realtime
from deep_sort_realtime.deepsort_tracker import DeepSort
import numpy as np

class DeepSortTracker:
    def __init__(self, max_age=30, n_init=3):
        # Create a DeepSort tracker instance - default metric is cosine with ReID model
        self.tracker = DeepSort(max_age=max_age, n_init=n_init)

    def update(self, detections, frame):
        """
        detections: list of [x1,y1,x2,y2,score,class_id]
        frame: current frame (RGB or BGR) - deep_sort_realtime accepts BGR
        Returns a list of tracks where each track is a dict:
            { 'track_id': int, 'bbox': [x1,y1,x2,y2], 'det_conf': float, 'class_id': int }
        """
        # deep_sort_realtime expects detection dictionaries or list entries.
        # We'll convert to format: (xyxy, confidence, class_name)
        dets_for_ds = []
        for d in detections:
            x1, y1, x2, y2, score, class_id = d
            # class name optional — pass "person"
            dets_for_ds.append(((x1, y1, x2, y2), score, "person"))

        tracks = self.tracker.update_tracks(dets_for_ds, frame=frame)
        out_tracks = []
        for t in tracks:
            if not t.is_confirmed():
                continue
            tid = t.track_id
            ltrb = t.to_ltrb() # left, top, right, bottom
            conf = t.det_conf
            out_tracks.append({
                "track_id": tid,
                "bbox": [int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])],
                "det_conf": conf
            })
        return out_tracks
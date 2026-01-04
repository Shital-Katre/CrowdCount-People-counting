import cv2
import numpy as np

class HeatMap:
    def __init__(self, shape):
        self.h, self.w = shape[:2]
        self.map = np.zeros((self.h, self.w), dtype=np.float32)

    def update(self, objects):
        for _, (x, y) in objects.items():
            if 0 <= x < self.w and 0 <= y < self.h:
                self.map[y, x] += 10 # 🔴 increase intensity

    def draw(self, frame):
        heat = cv2.GaussianBlur(self.map, (31,31), 0)
        heat = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX)
        heat = heat.astype(np.uint8)
        heat = cv2.applyColorMap(heat, cv2.COLORMAP_JET)

        # 🔴 strong overlay
        return cv2.addWeighted(frame, 0.6, heat, 0.4, 0)
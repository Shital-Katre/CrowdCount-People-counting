import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import os

ZONE_FILE = "zones.npy"

# Safe load
zones = []
if Path(ZONE_FILE).exists():
    try:
        zones = np.load(ZONE_FILE, allow_pickle=True).tolist()
    except:
        zones = []

drawing = False
ix, iy = -1, -1
current_zone = None

# ------------------- MOUSE CALLBACK -------------------
def mouse_draw(event, x, y, flags, param):
    global ix, iy, drawing, current_zone, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        current_zone = [(ix, iy), (ix, iy)]
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        current_zone[1] = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current_zone[1] = (x, y)

# ------------------- DRAW ZONES -------------------
def draw_existing_zones(frame):
    for i, zone in enumerate(zones):
        cv2.rectangle(frame, zone[0], zone[1], (0, 255, 255), 3)
        cv2.putText(frame, f"Zone {i+1}", (zone[0][0], zone[0][1]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    if current_zone:
        cv2.rectangle(frame, current_zone[0], current_zone[1], (0, 200, 255), 2)

def point_in_zone(point, zone):
    x1, y1 = zone[0]
    x2, y2 = zone[1]
    return x1 <= point[0] <= x2 and y1 <= point[1] <= y2

# ------------------- YOLO MODEL -------------------
model = YOLO("yolov8n.pt")

# ------------------- VIDEO LOOP -------------------
cap = cv2.VideoCapture("Pedestrians Detection Dataset.mp4")
cv2.namedWindow("video")
cv2.setMouseCallback("video", mouse_draw)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    detection_data = results[0].boxes.data.cpu().numpy()

    draw_existing_zones(frame)

    zone_counts = [0 for _ in range(len(zones))]

    for idx, det in enumerate(detection_data):
        x1, y1, x2, y2, conf, cls = det
        if int(cls) != 0:
            continue
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        cx, cy = int((x1+x2)/2), int((y1+y2)/2)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {idx+1}", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)

        for i, zone in enumerate(zones):
            if point_in_zone((cx, cy), zone):
                zone_counts[i] += 1

    # show counts
    y_offset = 40
    for i, count in enumerate(zone_counts):
        cv2.putText(frame, f"Zone {i+1} Count: {count}",
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 3)
        y_offset += 60

    cv2.imshow("video", frame)
    key = cv2.waitKey(1)

    if key == ord('q'): # quit
        break
    elif key == ord('n') and current_zone: # save current rectangle
        zones.append(current_zone)
        np.save(ZONE_FILE, zones)
        current_zone = None
    elif key == ord('d') and zones: # delete last zone
        zones.pop()
        np.save(ZONE_FILE, zones)
    elif key == ord('c'): # clear all zones
        zones = []
        current_zone = None
        if os.path.exists(ZONE_FILE):
            os.remove(ZONE_FILE)
    elif key == ord('l'): # load zones
        if Path(ZONE_FILE).exists():
            zones = np.load(ZONE_FILE, allow_pickle=True).tolist()

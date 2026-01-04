import cv2
import json
import threading
import numpy as np
import pandas as pd
import time
from flask import Flask, render_template, jsonify, send_file
from ultralytics import YOLO
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
VIDEO_FILE = "videos/Entrance area.mp4"
ZONE_FILE = "zones.json"
THRESHOLD = 4

app = Flask(__name__)
model = YOLO("yolov8n.pt", verbose=False)

zone_data = {}
zone_names = ["Entrance", "Exit", "Common"]

counts = {"Entrance": 0, "Exit": 0, "Common": 0}
heatmap = {"Entrance": None, "Exit": None, "Common": None}

history = []
start_time = time.time()

# ---------- ZONE DRAW ----------
drawing = False
ix, iy = -1, -1
current_zone_name = None

def draw_zone(event, x, y, flags, param):
    global ix, iy, drawing, zone_data, current_zone_name
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        zone_data[current_zone_name] = [ix, iy, x, y]

def save_zones():
    with open(ZONE_FILE, "w") as f:
        json.dump(zone_data, f)

def load_zones():
    global zone_data
    try:
        with open(ZONE_FILE) as f:
            zone_data = json.load(f)
    except:
        zone_data = {}

# ---------- VIDEO LOOP ----------
def video_loop():
    global counts, heatmap

    load_zones()
    cap = cv2.VideoCapture(VIDEO_FILE)

    for z in zone_names:
        heatmap[z] = np.zeros((480, 640), dtype=np.float32)

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = cv2.resize(frame, (640, 480))
        results = model.track(frame, persist=True, classes=[0])

        for z in zone_names:
            counts[z] = 0

        if results and results[0].boxes.id is not None:
            for box, tid in zip(results[0].boxes.xyxy, results[0].boxes.id):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1+x2)//2, (y1+y2)//2

                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.circle(frame, (cx,cy), 4, (0,255,0), -1)
                cv2.putText(frame, f"ID {int(tid)}", (x1,y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

                for z in zone_names:
                    if z in zone_data:
                        zx1, zy1, zx2, zy2 = zone_data[z]
                        if zx1 < cx < zx2 and zy1 < cy < zy2:
                            counts[z] += 1
                            heatmap[z][cy, cx] += 2

        for z in zone_names:
            if z in zone_data:
                zx1, zy1, zx2, zy2 = zone_data[z]
                cv2.rectangle(frame, (zx1,zy1), (zx2,zy2), (0,0,255), 2)
                cv2.putText(frame, z, (zx1,zy1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        # 🔥 HEATMAP OVERLAY FIX
        combined = np.zeros((480,640), dtype=np.float32)
        for z in zone_names:
            combined += heatmap[z]

        combined = cv2.GaussianBlur(combined, (31,31), 0)
        norm = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX)
        color = cv2.applyColorMap(norm.astype(np.uint8), cv2.COLORMAP_JET)
        frame = cv2.addWeighted(frame, 0.6, color, 0.4, 0)

        # VIDEO ALERT TEXT
        for i, z in enumerate(zone_names):
            if counts[z] > THRESHOLD:
                cv2.putText(frame, f"{z} area is crowded",
                            (10, 30+30*i), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (0,0,255), 2)

        cv2.imshow("Crowd Analytics", frame)
        if cv2.waitKey(30) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# ---------- FLASK ----------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/data")
def data():
    alerts = []
    for z in zone_names:
        if counts[z] > THRESHOLD:
            alerts.append(f"{z} area is crowded")

    history.append({
        "time_sec": int(time.time() - start_time),
        "Entrance": counts["Entrance"],
        "Exit": counts["Exit"],
        "Common": counts["Common"],
        "crowded": "YES" if alerts else "NO"
    })

    return jsonify({
        "Entrance": counts["Entrance"],
        "Exit": counts["Exit"],
        "Common": counts["Common"],
        "alert": " | ".join(alerts)
    })

@app.route("/download_csv")
def download_csv():
    df = pd.DataFrame(history)
    return send_file(
        BytesIO(df.to_csv(index=False).encode()),
        mimetype="text/csv",
        download_name="crowd_data.csv",
        as_attachment=True
    )

@app.route("/download_pdf")
def download_pdf():
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        fig, ax = plt.subplots()
        ax.bar(counts.keys(), counts.values())
        ax.set_title("Crowd Occupancy Summary")
        pdf.savefig(fig)
        plt.close(fig)

    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        download_name="crowd_report.pdf",
        as_attachment=True
    )

if __name__ == "__main__":
    load_zones()

    if not zone_data:
        for z in zone_names:
            current_zone_name = z
            cap = cv2.VideoCapture(VIDEO_FILE)
            ret, frame = cap.read()
            frame = cv2.resize(frame, (640,480))
            cv2.namedWindow(f"Draw Zone - {z}")
            cv2.setMouseCallback(f"Draw Zone - {z}", draw_zone)
            while True:
                temp = frame.copy()
                if z in zone_data:
                    zx1,zy1,zx2,zy2 = zone_data[z]
                    cv2.rectangle(temp,(zx1,zy1),(zx2,zy2),(0,0,255),2)
                cv2.imshow(f"Draw Zone - {z}", temp)
                if cv2.waitKey(1) & 0xFF == ord("s"):
                    save_zones()
                    break
            cap.release()
            cv2.destroyAllWindows()

    threading.Thread(target=video_loop, daemon=True).start()
    app.run(debug=False)

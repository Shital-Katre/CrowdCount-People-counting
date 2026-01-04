import cv2, csv
import os

from datetime import datetime
from flask import Flask, render_template, request, redirect, session, Response, jsonify, send_file, url_for

from vision.detector import PersonDetector
from vision.tracker import SimpleTracker
from vision.heatmap import HeatMap

from models.camera_model import Camera
from models.zone_model import zones, save_zones
from models.count_model import counts
from models.threshold_model import thresholds

from models.log_model import logs , add_alert

app = Flask(__name__)
app.secret_key = "milestone4_admin"

# ---------------- DATA ----------------
cameras = []
active_camera =None
cap=None
# ----------------------
# ALERTS & THRESHOLDS
# ----------------------
alerts = [] # Stores alert events
thresholds_dict = {} # Admin-set limits per zone


# ---------------- VISION ----------------
detector = PersonDetector()
tracker = SimpleTracker()
heatmap = None

def generate_frames():
    global heatmap, cap

    if cap is None:
            return
    while True:
        ret,frame=cap.read()
        if not ret:       

            break

        if heatmap is None:
            heatmap = HeatMap(frame.shape)

        boxes = detector.detect(frame)
        objects = tracker.update(boxes)

        counts.clear()
        for obj_id, (cx, cy) in objects.items():
            counts.append(type('Obj', (), {
                'id': obj_id,
                'zone': 'N/A',
                'time': datetime.now()
            }))

        for (x1, y1, x2, y2) in boxes:
            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 2)

        for obj_id, (cx, cy) in objects.items():
            cv2.circle(frame, (cx,cy), 4, (0,255,0), -1)
            cv2.putText(frame, f"ID {obj_id}", (cx+5, cy-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        for z in zones:
            coords = z.get("coords", [])
            if len(coords) == 2:
                cv2.rectangle(frame, coords[0], coords[1], (0,0,255), 2)

        for t in thresholds:
            for z in zones:
             if z['name'] == t['zone']:
                coords = z['coords']
             if len(coords) == 2:
                x1, y1 = coords[0]
                x2, y2 = coords[1]

                count_inside = sum(
                    1 for _, (cx, cy) in objects.items()
                    if x1 <= cx <= x2 and y1 <= cy <= y2
                )

                if count_inside >= t['value']:
                    cv2.putText(
                        frame,
                        f"ALERT {z['name']}!",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2
                    )

                    logs.append({
                        "message": f"Threshold exceeded in {z['name']}",
                        "time": datetime.now()
                    })
         # Draw zones + check thresholds
        for z in zones:
            coords = z.get('coords',[])
            if len(coords)==2:
                x1,y1 = coords[0]
                x2,y2 = coords[1]
                cv2.rectangle(frame, coords[0], coords[1], (0,0,255),2)
                cv2.putText(frame, z.get('name','Zone'), (x1,y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),2)

        heatmap.update(objects)
        frame = heatmap.draw(frame)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

@app.route("/video_feed")
def video_feed():
    if "admin" not in session:
        return redirect("/")
    return Response(generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["admin"] = True
            return redirect("/dashboard")
        error = "Invalid credentials"
    return render_template("login.html", error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")
    return render_template(
        "dashboard.html",
        cameras=cameras,
        zones=zones,
        thresholds=thresholds,
        counts=counts,
        logs=logs
    )

# ---------------- CAMERA PAGE ----------------
@app.route("/camera", methods=["GET","POST"])
def camera_page():
    global cameras, active_camera , cap

    if request.method == "POST":
        id= request.form.get("id")
        name = request.form.get("name")
        source = request.form.get("source")
        

        if not os.path.exists(source):
            return f"video file not found:{source}",400

        cam = Camera(name, source)
        cameras.append(cam)

        active_camera=cam # 🔥 KEY LINE
        if cap is not None:
            cap.release()

        cap=cv2.VideoCapture(cam.source)

        return redirect(url_for("dashboard"))

    return render_template("camera.html", cameras=cameras)

# ZONE


@app.route("/zone", methods=["GET", "POST"])
def zone():
    if 'admin' not in session:
        return redirect('/')

    if request.method == "POST":
        name = request.form.get("name")
        x1 = request.form.get("x1")
        y1 = request.form.get("y1")
        x2 = request.form.get("x2")
        y2 = request.form.get("y2")

        # validation
        if not name or not x1 or not y1 or not x2 or not y2:
            return render_template("zone.html", zones=zones, error="All fields required")

        zone_data = {
            "name": name,
            "coords": [(int(x1), int(y1)), (int(x2), int(y2))]
        }

        zones.append(zone_data)
        save_zones(zones)

        return redirect("/zone")

    return render_template("zone.html", zones=zones)


@app.route("/delete_zone/<int:index>")
def delete_zone(index):
    if 'admin' not in session:
        return redirect('/')

    if 0 <= index < len(zones):
        zones.pop(index)
        save_zones(zones)

    return redirect("/zone")

@app.route('/threshold')
def threshold_page():
    if 'admin' not in session: return redirect('/')
    return render_template('threshold.html', thresholds=thresholds_dict, alerts=logs)

@app.route('/threshold', methods=['GET', 'POST'])
def threshold():
    if 'admin' not in session:
        return redirect('/')

    if request.method == 'POST':
        zone_name = request.form.get('zone')
        value = request.form.get('value')

        if not zone_name or not value:
            return render_template(
                'threshold.html',
                thresholds=thresholds,
                zones=zones,
                error="Zone and value required"
            )

        thresholds.append({
            "zone": zone_name,
            "value": int(value)
        })

    return render_template(
        'threshold.html',
        thresholds=thresholds,
        zones=zones
    )
@app.route('/analytics')
def analytics():
    if 'admin' not in session:
        return redirect('/')
    
    # Safe default if zones or counts empty
    zone_names = [z.get('name','Zone') for z in zones] if zones else ['Zone1']
    zone_counts = [len(counts) for _ in zone_names] if counts else [0 for _ in zone_names]
    
    return render_template('analytics.html',
                           zone_names=zone_names,
                           zone_counts=zone_counts)



@app.route('/reports')
def reports():
    if 'admin' not in session:
        return redirect('/')
    return render_template('reports.html')


@app.route('/export/daily')
def export_daily():
    path = 'exports/daily.csv'
    with open(path,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID','Zone','Time'])
        for c in counts:  # counts model से data
            writer.writerow([c.id, c.zone, c.time])
    return send_file(path, as_attachment=True)

@app.route('/export/threshold')
def export_threshold():
    path = 'exports/threshold.csv'
    with open(path,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Zone','Threshold','Time'])
        for t in thresholds:
            writer.writerow([t['zone'], t['value'], t['time']])
    return send_file(path, as_attachment=True)

@app.route('/export/camera')
def export_camera():
    path = 'exports/camera.csv'
    with open(path,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id','name','source','status'])
        for cam in cameras:
            writer.writerow([cam.id ,cam.name, cam.source, cam.status])
    return send_file(path, as_attachment=True)
  
 


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
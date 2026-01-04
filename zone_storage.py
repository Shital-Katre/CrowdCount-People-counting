import json
import os

ZONE_FILE = "zones.json"

def normalize(z):
    return [min(z[0], z[2]), min(z[1], z[3]), max(z[0], z[2]), max(z[1], z[3])]

def save_zones(zones):
    with open(ZONE_FILE, "w") as f:
        json.dump([normalize(z) for z in zones], f)
    print("✔ Zones saved.")

def load_zones():
    if os.path.exists(ZONE_FILE):
        with open(ZONE_FILE, "r") as f:
            data = json.load(f)
        print("✔ Zones loaded.")
        return [normalize(z) for z in data]
    else:
        print("❌ No zone file found.")
        return []


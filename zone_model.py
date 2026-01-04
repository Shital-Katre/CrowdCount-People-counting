import json
import os

ZONE_FILE = "data/zones.json"

def load_zones():
    if not os.path.exists(ZONE_FILE):
        return []
    with open(ZONE_FILE, "r") as f:
        return json.load(f)

def save_zones(zones):
    with open(ZONE_FILE, "w") as f:
        json.dump(zones, f, indent=4)

zones = load_zones()


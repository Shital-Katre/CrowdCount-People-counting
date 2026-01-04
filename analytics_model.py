# models/analytics_model.py

from datetime import datetime

# Dummy in-memory storage for Analytics
analytics_data = []

class AnalyticsEntry:
    def __init__(self, zone_name, timestamp=None, count=0):
        self.zone_name = zone_name
        self.timestamp = timestamp if timestamp else datetime.now()
        self.count = count

def add_entry(zone_name, count):
    entry = AnalyticsEntry(zone_name, count)
    analytics_data.append(entry)

# models/reports_model.py

from datetime import datetime

# Dummy in-memory storage for reports
reports_data = []

class ReportEntry:
    def __init__(self, report_type, description, status="Generated", timestamp=None):
        self.report_type = report_type
        self.description = description
        self.status = status
        self.timestamp = timestamp if timestamp else datetime.now()

def add_report(report_type, description, status="Generated"):
    entry = ReportEntry(report_type, description, status)
    reports_data.append(entry)
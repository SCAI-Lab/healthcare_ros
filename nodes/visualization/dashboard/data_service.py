#!/usr/bin/env python3
"""
EEG Data Service Layer

Central gateway for all telemetry:
- EEG raw + processed data
- latency metrics (mean, windowed)
- derived analytics

Frontend MUST NOT query InfluxDB directly.
"""

from fastapi import FastAPI
from influxdb_client import InfluxDBClient
import time

app = FastAPI()

# ---------------- CONFIG ----------------
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_TOKEN"
INFLUX_ORG = "healthcare"
INFLUX_BUCKET = "eeg_data"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()
# ----------------------------------------


# ---------------- LATENCY ----------------
@app.get("/latency/mean")
def latency_mean():
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -10s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_latency_raw_to_processed")
  |> filter(fn: (r) => r["_field"] == "value")
  |> mean()
'''

    tables = query_api.query(query)

    values = []
    for t in tables:
        for r in t.records:
            values.append(r.get_value())

    if not values:
        return {"mean_ms": None}

    return {"mean_ms": sum(values) / len(values)}
# ----------------------------------------


# ------------- EEG RAW DATA -------------
@app.get("/eeg/raw")
def eeg_raw(window: int = 2):
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -{window}s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["_field"] == "value")
'''

    tables = query_api.query(query)

    data = []
    for t in tables:
        for r in t.records:
            data.append({
                "time": r.get_time().isoformat(),
                "value": r.get_value(),
                "channel": r.values.get("channel")
            })

    return {"data": data}
# ----------------------------------------


# -------- EEG PROCESSED DATA -----------
@app.get("/eeg/processed")
def eeg_processed(window: int = 2):
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -{window}s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_preprocessed")
  |> filter(fn: (r) => r["_field"] == "value")
'''

    tables = query_api.query(query)

    data = []
    for t in tables:
        for r in t.records:
            data.append({
                "time": r.get_time().isoformat(),
                "value": r.get_value(),
                "channel": r.values.get("channel")
            })

    return {"data": data}
# ----------------------------------------


# -------- SYSTEM METRICS (FUTURE) -------
@app.get("/system/status")
def system_status():
    return {
        "timestamp": time.time(),
        "services": {
            "influx": True,
            "eeg_pipeline": True
        }
    }
# ----------------------------------------
#!/usr/bin/env python3
"""
EEG Data Service Layer

Central gateway for all telemetry:
- EEG raw + processed data
- latency metrics (mean, windowed)
- derived analytics

"""

from fastapi import FastAPI
from influxdb_client import InfluxDBClient
import time

app = FastAPI()

# ---------------- CONFIG ----------------
INFLUX_URL = "http://127.0.0.1:8086"
INFLUX_TOKEN = "hc-eeg-secure-t0ken!2026@api"
INFLUX_ORG = "7af19ab14561ec38"
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

    try:
        query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -10s)
'''

        tables = query_api.query(query)

        rows = []

        for t in tables:
            for r in t.records:
                rows.append({
                    "measurement": r.get_measurement(),
                    "field": r.get_field(),
                    "value": r.get_value(),
                    "time": str(r.get_time())
                })

        return {
            "count": len(rows),
            "sample": rows[:20]
        }

    except Exception as e:
        return {
            "error": str(e),
            "type": str(type(e))
        }
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

@app.get("/debug/influx")
def debug_influx():
    try:
        return client.query_api().query('from(bucket:"eeg_data") |> range(start: -10s) |> limit(n:1)')
    except Exception as e:
        return {"error": str(e)}
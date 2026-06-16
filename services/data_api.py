#!/usr/bin/env python3

from fastapi import FastAPI
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
import os
import time

app = FastAPI()

# Load .env
load_dotenv()

# ---------------- CONFIG ----------------
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# Safety check (VERY useful for debugging)
if not all([INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET]):
    raise RuntimeError("Missing InfluxDB environment variables")

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()
# ----------------------------------------


@app.get("/latency/mean")
def latency_mean():
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


@app.get("/eeg/raw")
def eeg_raw(window: int = 2):
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -{window}s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_raw")
  |> filter(fn: (r) => r["_field"] == "value")
'''

    tables = query_api.query(query)

    return {
        "data": [
            {
                "time": r.get_time().isoformat(),
                "value": r.get_value(),
                "channel": r.values.get("channel")
            }
            for t in tables
            for r in t.records
        ]
    }


@app.get("/eeg/processed")
def eeg_processed(window: int = 2):
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -{window}s)
  |> filter(fn: (r) => r["_measurement"] == "eeg_preprocessed")
  |> filter(fn: (r) => r["_field"] == "value")
'''

    tables = query_api.query(query)

    return {
        "data": [
            {
                "time": r.get_time().isoformat(),
                "value": r.get_value(),
                "channel": r.values.get("channel")
            }
            for t in tables
            for r in t.records
        ]
    }


@app.get("/system/status")
def system_status():
    return {
        "timestamp": time.time(),
        "services": {
            "influx": True,
            "eeg_pipeline": True
        }
    }
#!/usr/bin/env python3
"""
Latency API Service

Provides /latency/mean endpoint that returns mean latency from InfluxDB
in the format expected by the dashboard: {"mean_ms": value}
"""

import os
import json
from flask import Flask, jsonify
from influxdb_client import InfluxDBClient

app = Flask(__name__)

# InfluxDB configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', os.getenv('INFLUXDB_ADMIN_TOKEN', ''))
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'healthcare')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'eeg_data')

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

@app.route('/latency/mean')
def get_mean_latency():
    try:
        # Query for mean latency over last minute
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -1m)
        |> filter(fn: (r) => r["_measurement"] == "eeg_latency")
        |> filter(fn: (r) => r["_field"] == "value")
        |> mean()
        '''

        result = query_api.query(query)

        # Extract mean value
        if result and len(result) > 0 and len(result[0].records) > 0:
            mean_value = result[0].records[0].get_value()
            return jsonify({"mean_ms": round(mean_value, 1)})
        else:
            return jsonify({"mean_ms": None})

    except Exception as e:
        print(f"Error querying latency: {e}")
        return jsonify({"mean_ms": None}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
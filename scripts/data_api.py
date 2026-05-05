#!/usr/bin/env python3
"""
EEG Data API Service

Provides /eeg/raw and /eeg/processed endpoints that return EEG data
from InfluxDB in the format expected by the dashboard.
"""

import os
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

@app.route('/eeg/raw')
def get_raw_eeg():
    return _get_eeg_data('eeg_raw')

@app.route('/eeg/processed')
def get_processed_eeg():
    return _get_eeg_data('eeg_preprocessed')

def _get_eeg_data(measurement):
    try:
        # Query for EEG data over last 2 seconds
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -2s)
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        |> filter(fn: (r) => r["_field"] == "value")
        |> sort(columns: ["_time"], desc: false)
        '''

        result = query_api.query(query)

        # Transform to expected format
        data = []
        if result and len(result) > 0:
            for table in result:
                for record in table.records:
                    data.append({
                        'time': record.get_time().isoformat(),
                        'channel': record.values.get('channel', 'unknown'),
                        'value': record.get_value()
                    })

        return jsonify({"data": data})

    except Exception as e:
        print(f"Error querying {measurement}: {e}")
        return jsonify({"data": []}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
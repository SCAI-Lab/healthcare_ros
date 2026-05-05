# EEG End-to-End Latency Monitoring

A comprehensive system for measuring end-to-end latency throughout the entire EEG data processing pipeline.

## Overview

The latency monitoring system measures latency times between different stages of the EEG pipeline:

```
EEG Acquisition -> Raw Data Storage
      |
   Preprocessing
      |
  Processed Data Storage
      |
  Visualization (Dashboard)
```

Latency metrics are continuously measured and updated:

- **Raw > Processed**: Time between raw EEG publishing and preprocessing
- **Total E2E**: Total latency from acquisition to final display
- **Exponential Moving Average (EMA)**: Smoothed average over the last 100 samples

## System Architecture

### Components

1. **Latency Monitor Node** (`eeg_latency_monitor.py`)
   - Subscribes to `/eeg/raw` and `/eeg/processed` topics
   - Compares ROS2 header timestamps
   - Calculates latencies in milliseconds
   - Stores metrics in InfluxDB

2. **InfluxDB Time-Series Database**
   - Stores historical latency data
   - Enables aggregation and statistics
   - Supports trend analysis

3. **Web Dashboard** (`influxdb_realtime_dashboard.html`)
   - Displays current latency values
   - Updates every 200ms with latest metrics
   - Status badges: Raw>Proc latency, Total E2E latency

## Activation

The latency monitoring is automatically activated when you start the InfluxDB integration:

### With InfluxDB (recommended for visualization):
```bash
USE_INFLUXDB=1 ./launch/start.sh
```

Or production mode:
```bash
PRODUCTION=1 ./launch/start.sh
```

### Without InfluxDB (console logging only):
Monitoring runs without InfluxDB and outputs statistics every 5 seconds to logs:
```bash
python3 nodes/monitoring/eeg_latency_monitor.py
```

## Dashboard Metrics

The web dashboard displays latency metrics in the header:

```
EEG Pipeline | Simulator: 150 Hz | Raw>Proc: 12.5 ms | E2E: 45.3 ms
```

- **Raw>Proc**: Exponential moving average (EMA) of latency from raw to processed
- **E2E**: Wallclock end-to-end latency across all components

## Data Storage and Export Format

InfluxDB measurements (tables):

| Measurement | Description | Tags | Fields |
|-------------|------------|------|--------|
| `eeg_latency_raw_to_processed` | Individual latencies (Raw > Processed) | `session_id` | `value` (ms) |
| `eeg_latency_total` | End-to-end latencies (Wallclock) | `session_id` | `value` (ms) |
| `eeg_latency_average_raw_to_processed` | EMA (Raw > Processed) | `session_id` | `value` (ms) |
| `eeg_latency_average_total` | EMA (Total E2E) | `session_id` | `value` (ms) |

### InfluxDB Queries

**Retrieve current average values:**
```flux
from(bucket: "eeg_data")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "eeg_latency_average_raw_to_processed")
  |> last()
```

**Maximum latency in the last minute:**
```flux
from(bucket: "eeg_data")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "eeg_latency_raw_to_processed")
  |> max()
```

**Average over time window (30s):**
```flux
from(bucket: "eeg_data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "eeg_latency_raw_to_processed")
  |> aggregateWindow(every: 30s, fn: mean)
```

## Configuration

### Environment Variables

```bash
# Latency Monitor Node Parameters
LATENCY_WINDOW_SIZE=100          # Window size for moving average (Default: 100)

# InfluxDB Connection
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=<your-token>
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
```

### Starting the Startup Script with Custom Parameters

```bash
# With extended window for smoother average
LATENCY_WINDOW_SIZE=200 USE_INFLUXDB=1 ./launch/start.sh

# With custom InfluxDB URL
INFLUXDB_URL=http://influx.example.com:8086 PRODUCTION=1 ./launch/start.sh
```

## Console Output

When the monitor is running, it outputs a report every 5 seconds:

```
=== EEG Latency Report (last 100 samples) ===
  Raw > Processed: min=8.2ms, max=24.5ms, mean=12.3ms, stddev=3.1ms, EMA=12.1ms
  Total E2E Latency (Wall-clock): 45.2ms
  Messages: Raw=1523, Processed=1523, Matched=1523
```

## Metrics Interpretation

### Typical Latency Ranges

| Component | Typical Range | Explanation |
|-----------|--------------|-------------|
| Raw > Processed | 5-20ms | Bandpass filtering (0.5-45 Hz) + CAR referencing |
| Acquire > Save | 2-5ms | I/O + JSON serialization |
| Total E2E | 30-100ms | Including system latencies, ROS2 middleware, network |

### Optimization Opportunities

If latencies are higher than expected:

1. **High Preprocessing Latency (>30ms)**
   - Optimize filter order (use faster filters)
   - Use IIR instead of FIR filters
   - Enable downsampling

2. **High Storage Latency (>10ms)**
   - Increase batch writes to InfluxDB
   - Replace JSON serialization with Protocol Buffers
   - Write to SSD (if using JSONL files)

3. **High Total Latency (>100ms)**
   - Adjust ROS2 QoS profiles (reduce depth)
   - Check network between nodes
   - Monitor CPU load (could cause jitter)

## Logs

Log files for latency monitoring:

```bash
# Display real-time logs
tail -f logs/eeg_latency_monitor.log

# Show last 50 lines
head -50 logs/eeg_latency_monitor.log

# Filter for errors
grep ERROR logs/eeg_latency_monitor.log
```

## Troubleshooting

### "InfluxDB client not available" Error

**Solution:** Install InfluxDB Python client
```bash
pip install influxdb-client
```

### Latency values not showing in dashboard

1. Check if InfluxDB is running:
   ```bash
   docker-compose ps
   ```

2. Check if monitor node is running:
   ```bash
   ps aux | grep eeg_latency_monitor
   ```

3. Check logs:
   ```bash
   tail -f logs/eeg_latency_monitor.log
   ```

### Constant or very high values

- Check system clock (especially in virtual machines)
- Ensure ROS2 time is not frozen
- Check CPU load and memory

## Best Practices

1. **Always start monitoring with InfluxDB** - This enables historical trend analysis and better insights
2. **Monitor dashboard regularly** - Latencies can indicate system problems
3. **Set up automatic alerts** - InfluxDB has built-in alerting
4. **Export metrics** - For external analysis or reports

## Integration with Other Tools

### Grafana Integration (optional)

Grafana can use InfluxDB data for advanced visualizations:

```bash
# Start with Grafana
docker run -d -p 3000:3000 grafana/grafana
# Add InfluxDB as a data source
```

### Prometheus Export (optional)

Export InfluxDB data to Prometheus:

```bash
# TODO: Add remote write integration
```

## Additional Resources

- [ROS2 QoS Documentation](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service.html)
- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/cloud/)
- [Flux Query Language](https://docs.influxdata.com/flux/v0.x/)

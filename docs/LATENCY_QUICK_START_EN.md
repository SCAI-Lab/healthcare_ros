# Quick Start: EEG Latency Monitoring

## 5-Minute Setup

### 1. Start with Latency Monitoring (Recommended)
```bash
cd ~/ros2_ws/src/healthcare_ros
PRODUCTION=1 ./launch/start.sh
```

### 2. Open Dashboard
```
Browser: http://localhost:8080
```

You will see:
- EEG Data (Raw vs Preprocessed channels)
- Latency Metrics in the top right
  - Raw>Proc: X.X ms (Preprocessing time)
  - E2E: X.X ms (Total latency)

### 3. Monitor Latency Logs
```bash
tail -f logs/eeg_latency_monitor.log
```

Output every 5 seconds:
```
=== EEG Latency Report ===
  Raw > Processed: min=8.2ms, max=24.5ms, mean=12.3ms, EMA=12.1ms
  Total E2E Latency: 45.2ms
```

---

## Understanding the Metrics

### What do these numbers mean?

| Metric | Range | Meaning | If too high |
|--------|-------|---------|-----------|
| **Raw>Proc** | 5-20ms | Time for filtering + CAR | Filter too slow |
| **E2E** | 30-100ms | Start to dashboard | Network/logger latencies |
| **EMA** | — | Moving average | Shows trends |

### Example Scenarios

**Good (low latency):**
```
Raw>Proc: 12.1 ms (EMA)
E2E: 45.3 ms
> System running efficiently
```

**Problematic (high latency):**
```
Raw>Proc: 145.2 ms (EMA)  <- Filter too slow
E2E: 342.1 ms             <- System delay
> Check CPU load and filter parameters
```

---

## Common Commands

```bash
# Dashboard URL
echo "http://localhost:8080"

# Monitor logs in real-time
tail -f logs/eeg_latency_monitor.log

# Show all PIDs
ps aux | grep eeg_

# Stop monitor node
kill $(cat logs/eeg_latency_monitor.pid)

# Check InfluxDB data
docker exec healthcare-influxdb influx query \
  'from(bucket:"eeg_data")
   |> range(start:-5m)
   |> filter(fn:(r)=>r._measurement=="eeg_latency_average_raw_to_processed")'

# Stop all nodes
killall python3

# Show logs (last 50 lines)
tail -50 logs/eeg_latency_monitor.log | grep "Latency Report"
```

---

## Advanced Configuration

### Increased Window Size for Smoother Average
```bash
LATENCY_WINDOW_SIZE=200 PRODUCTION=1 ./launch/start.sh
```
> EMA updates slower but smoother

### With InfluxDB enabled but no Dashboard
```bash
USE_INFLUXDB=1 MANAGE_DOCKER=0 ./launch/start.sh
# Docker must run manually:
docker-compose up -d
```

### Monitoring Only, No EEG Acquisition
```bash
RUN_NODE=0 ./launch/start.sh
python3 nodes/monitoring/eeg_latency_monitor.py
```

---

## Troubleshooting

### Latency values not visible in dashboard?

**1. Is monitor running?**
```bash
ps aux | grep eeg_latency_monitor
# If not: python3 nodes/monitoring/eeg_latency_monitor.py
```

**2. Is InfluxDB running?**
```bash
docker-compose ps
# If not: docker-compose up -d
```

**3. Data in InfluxDB?**
```bash
docker-compose logs influxdb | tail -20
```

**4. Browser cache?**
```
Ctrl+Shift+R (Hard Refresh) in browser
```

### Monitor crashes?

**Error: "InfluxDB client not available"**
```bash
pip install influxdb-client
```

**Error: "Connection refused"**
```bash
# Check InfluxDB URL
echo $INFLUXDB_URL
# Default: http://localhost:8086
```

---

## Performance Optimization

### If E2E latency is too high:

**1. Check system load**
```bash
top
# CPU < 50%, Memory < 80%?
```

**2. Adjust filter parameters**
```bash
# In eeg_preprocessing.py:
# l_freq=1.0  (instead of 0.5)    > faster
# h_freq=30.0 (instead of 45.0)   > faster
```

**3. Change ROS2 QoS Profile** (for older ROS2 versions)
```python
# In eeg_latency_monitor.py, line 130-135
# QoSProfile(depth=1) instead of depth=10  > fewer buffers
```

---

## Additional Resources

Documentation:
- Full Documentation: see LATENCY_MONITORING.md
- Startup Commands: see STARTUP_COMMANDS.md

Dashboard: http://localhost:8080
InfluxDB UI: http://localhost:8086

Data Folders:
- Logs: logs/eeg_latency_monitor.log
- EEG Data: eeg_data/

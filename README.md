# Healthcare EEG System - Docker Application

**ROS2-based EEG data acquisition, preprocessing, and real-time visualization using Docker**

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- ROS2 Jazzy
- Python 3.10+

### 1. Configure Credentials

```bash
# Copy example and edit with your credentials
cp .env.example .env
nano .env
```

**Required credentials:**
```bash
INFLUXDB_ADMIN_USERNAME=admin
INFLUXDB_ADMIN_PASSWORD=YourSecurePassword123!
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
INFLUXDB_ADMIN_TOKEN=your-secure-token-2026!
```

### 2. Generate Dashboard

```bash
python3 nodes/visualization/generate_dashboard.py
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

**Services started:**
- **InfluxDB** on port 8086 (time-series database)
- **Nginx** on port 8080 (web dashboard)

### 4. Access Dashboard

Open: **http://localhost:8080**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ROS2 Native Layer                     │
│                                                          │
│  EEG Simulator (150 Hz)                                 │
│         ↓                                                │
│  Preprocessing (0.5-45 Hz bandpass, CAR)                │
│         ↓                                                │
│  InfluxDB Bridge (writes statistics to DB)              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Docker Container Layer                 │
│                                                          │
│  ┌──────────────┐         ┌─────────────────┐          │
│  │InfluxDB 2.8  │  ←───   │  Nginx (Alpine) │          │
│  │Port 8086     │         │  Port 8080      │          │
│  └──────────────┘         └─────────────────┘          │
│                                   ↓                      │
│                         Web Dashboard (150 Hz)          │
│                    http://localhost:8080                │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **EEG Simulator** generates 4-channel data at 150 Hz
2. **Preprocessor** filters and applies CAR (Common Average Reference)
3. **InfluxDB Bridge** writes statistics (mean, min, max, frame_length) to InfluxDB
4. **Web Dashboard** queries InfluxDB and visualizes in real-time

---

## 📊 System Components

### ROS2 Nodes (Native)

| Node | Topic | Description |
|------|-------|-------------|
| **eeg_simulator** | `/eeg/raw` | 150 Hz 4-channel EEG generation |
| **eeg_preprocessing** | `/eeg/processed` | 0.5-45 Hz bandpass + CAR |
| **eeg_influxdb_bridge** | - | Writes to InfluxDB for web viz |

### Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| **influxdb** | 8086 | Time-series database |
| **nginx** | 8080, 8443 | Web server for dashboard |

---

## 🎮 Usage

### Start Full System

```bash
# Start Docker containers
docker-compose up -d

# In separate terminals, start ROS2 nodes:

# Terminal 1: Simulator
python3 nodes/data_acquisition/eeg_simulator.py

# Terminal 2: Preprocessing
python3 nodes/preprocessing/eeg_preprocessing.py

# Terminal 3: InfluxDB Bridge
python3 nodes/saver/eeg_influxdb_bridge.py
```

### View Dashboard

Open browser: **http://localhost:8080**

**Features:**
- Real-time 4-channel EEG visualization
- 150 Hz refresh rate (6.67ms)
- Statistics: mean, min, max, samples per channel
- Toggle raw/preprocessed data
- Live latency monitoring

### Stop System

```bash
# Stop Docker containers
docker-compose down

# Stop ROS2 nodes with Ctrl+C in each terminal
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```bash
# InfluxDB Configuration
INFLUXDB_ADMIN_USERNAME=admin
INFLUXDB_ADMIN_PASSWORD=YourPassword
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
INFLUXDB_ADMIN_TOKEN=your-token

# InfluxDB Connection (for bridge)
INFLUXDB_URL=http://localhost:8086
```

### Docker Ports

Edit `docker-compose.yml` to change ports:

```yaml
nginx:
  ports:
    - "8080:80"   # HTTP: Change left side
    - "8443:443"  # HTTPS: Change left side
```

---

## 📁 Project Structure

```
.
├── docker-compose.yml              # Docker services configuration
├── .env                             # Credentials (git-ignored)
├── .env.example                     # Credential template
├── nodes/
│   ├── data_acquisition/
│   │   └── eeg_simulator.py        # 150 Hz EEG simulator
│   ├── preprocessing/
│   │   └── eeg_preprocessing.py    # Signal processing
│   ├── saver/
│   │   └── eeg_influxdb_bridge.py  # InfluxDB writer
│   └── visualization/
│       ├── generate_dashboard.py   # Dashboard generator
│       ├── influxdb_realtime_dashboard.template.html
│       └── influxdb_realtime_dashboard.html
├── nginx/                           # Nginx configuration
├── logs/                            # Node logs
└── eeg_data/                        # Recorded data (optional)
```

---

## 🛠️ Development

### Regenerate Dashboard

After changing credentials:

```bash
python3 nodes/visualization/generate_dashboard.py
docker restart healthcare-nginx
```

### View Logs

```bash
# Docker logs
docker logs influxdb -f
docker logs healthcare-nginx -f

# ROS2 node logs
tail -f logs/eeg_simulator.log
tail -f logs/eeg_preprocessing.log
tail -f logs/eeg_influxdb_bridge.log
```

### Check Docker Status

```bash
docker ps
docker-compose ps
```

---

## 🔐 Security

### Best Practices

1. **Change default credentials** in `.env`
2. **Use strong passwords** (min 12 characters, special chars)
3. **Don't commit** `.env` to git (already in .gitignore)
4. **Use HTTPS** in production (configure nginx/ssl/)

### Production Deployment

For production, the dashboard automatically adapts to your server:

```javascript
// Dashboard detects server IP automatically
const INFLUXDB_URL = window.location.protocol + '//' + window.location.host;
```

**Access:** `http://your-server-ip:8080`  
InfluxDB connection: `http://your-server-ip:8086`

---

## 📈 Performance

- **Sampling Rate:** 150 Hz (realistic clinical EEG)
- **Dashboard Refresh:** 6.67ms (150 Hz)
- **Data Window:** 2 seconds (300 samples)
- **Channels:** 4 (FP1, FP2, F3, F4)
- **Latency:** < 10ms typical

---

## 🐛 Troubleshooting

### Dashboard shows no data

```bash
# Check if InfluxDB is running
curl http://localhost:8086/health

# Check bridge logs
tail -f logs/eeg_influxdb_bridge.log

# Restart bridge
pkill -f eeg_influxdb_bridge
python3 nodes/saver/eeg_influxdb_bridge.py
```

### Docker container not starting

```bash
# Check logs
docker logs influxdb
docker logs healthcare-nginx

# Restart containers
docker-compose restart

# Rebuild if needed
docker-compose down
docker-compose up -d
```

### Port already in use

```bash
# Check what's using port 8086 or 8080
sudo netstat -tulpn | grep -E '8080|8086'

# Stop conflicting service or change port in docker-compose.yml
```

---

## 📝 License

This project is part of the healthcare_ros system developed by SCAI-Lab.

---

## 🚀 Summary

**This is a pure Docker application** for EEG data visualization:

1. **Docker Compose** manages InfluxDB + Nginx
2. **ROS2 nodes** run natively and write to InfluxDB
3. **Web dashboard** served by Nginx at http://localhost:8080
4. **No manual installation** of InfluxDB or Nginx required

Just configure `.env`, run `docker-compose up -d`, start ROS2 nodes, and open the dashboard!


# Production Deployment Guide

## Overview

The system uses **Docker Nginx** to serve the dashboard as `index.html` and automatically handles IP address configuration using **relative URLs**.

---

## Current Architecture

### 1. The Dashboard File System

```
docs/
├── influxdb_realtime_dashboard.template.html  # Template (tracked in git)
└── influxdb_realtime_dashboard.html           # Generated dashboard (git-ignored)
```

### 2. Nginx Configuration

In `docker-compose.yml`:

```yaml
nginx:
  image: nginx:alpine
  container_name: healthcare-nginx
  ports:
    - "8080:80"      # HTTP
    - "8443:443"     # HTTPS
  volumes:
    - ./docs/influxdb_realtime_dashboard.html:/usr/share/nginx/html/index.html:ro
```

**The dashboard is served as `index.html`** - Nginx automatically maps it.

---

## How IP Address Configuration Works

### ✅ Already Production-Ready!

The dashboard uses **smart relative URLs** that automatically adapt:

```javascript
// Line 140 in template
const INFLUXDB_URL = window.location.protocol + '//' + window.location.host;
```

This means:
- **Development:** `http://localhost:8080` → connects to `http://localhost:8086`
- **Production:** `http://your-server.com:8080` → connects to `http://your-server.com:8086`
- **HTTPS:** `https://your-server.com:8443` → connects to `https://your-server.com:8086`

### How It Works

1. **Dashboard URL:** Browser accesses `http://your-server-ip:8080`
2. **JavaScript Detection:** `window.location` automatically gets the server IP/domain
3. **API Calls:** Dashboard constructs InfluxDB URL as `http://your-server-ip:8086/api/v2/query`

**No manual IP configuration needed!** 🎉

---

## Production Deployment Steps

### Option 1: Deploy on Remote Server (Recommended)

#### 1. Copy Project to Server

```bash
# On your local machine
rsync -avz --exclude 'eeg_data' --exclude 'logs' --exclude '.venv' \
  ~/ros2_ws/src/healthcare_demo/ \
  user@your-server:/opt/healthcare_demo/
```

#### 2. Configure Credentials on Server

```bash
# On the server
cd /opt/healthcare_demo
cp .env.example .env
nano .env
```

**Update with production credentials:**
```bash
INFLUXDB_ADMIN_USERNAME=admin
INFLUXDB_ADMIN_PASSWORD=YourProductionP@ssw0rd!
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
INFLUXDB_ADMIN_TOKEN=your-production-t0ken!2026@api
```

#### 3. Generate Dashboard

```bash
python3 generate_dashboard.py
```

This injects credentials into the HTML file.

#### 4. Start Docker Services

```bash
docker-compose up -d
```

#### 5. Access Dashboard

Open browser: `http://your-server-ip:8080`

The dashboard will automatically:
- Detect it's running on `your-server-ip`
- Connect to InfluxDB at `http://your-server-ip:8086`

---

### Option 2: Use Domain Name with SSL (Production Best Practice)

#### 1. Configure DNS

Point your domain to the server:
```
eeg-dashboard.your-company.com → 192.168.1.100
```

#### 2. Setup SSL Certificates

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d eeg-dashboard.your-company.com
```

#### 3. Update docker-compose.yml

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"      # HTTP (redirect to HTTPS)
    - "443:443"    # HTTPS
  volumes:
    - ./docs/influxdb_realtime_dashboard.html:/usr/share/nginx/html/index.html:ro
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/nginx/ssl:ro  # SSL certificates
```

#### 4. Access via HTTPS

`https://eeg-dashboard.your-company.com`

The dashboard automatically uses `https://` for InfluxDB connections.

---

## Environment-Specific Configuration

### Development (localhost)
```bash
# Accesses dashboard at:
http://localhost:8080

# Dashboard connects to:
http://localhost:8086  # InfluxDB
```

### Production (IP Address)
```bash
# Accesses dashboard at:
http://192.168.1.100:8080

# Dashboard connects to:
http://192.168.1.100:8086  # InfluxDB
```

### Production (Domain with SSL)
```bash
# Accesses dashboard at:
https://eeg-dashboard.company.com

# Dashboard connects to:
https://eeg-dashboard.company.com:8086  # InfluxDB (requires SSL)
```

---

## InfluxDB Bridge Configuration

The Python bridge that writes data to InfluxDB also uses environment variables:

### For Production Server

Set the `INFLUXDB_URL` environment variable:

```bash
# In .env file
INFLUXDB_URL=http://192.168.1.100:8086

# Or export before running
export INFLUXDB_URL=http://192.168.1.100:8086
python3 nodes/saver/eeg_influxdb_bridge.py
```

### Default Behavior

If `INFLUXDB_URL` is not set, it defaults to `http://localhost:8086` (line 54 in eeg_influxdb_bridge.py):

```python
self.influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
```

---

## Port Configuration for Production

### Default Ports
- **Dashboard (Nginx):** 8080 (HTTP), 8443 (HTTPS)
- **InfluxDB:** 8086

### Change Ports in docker-compose.yml

```yaml
services:
  influxdb:
    ports:
      - "8086:8086"  # Change left side: "EXTERNAL:INTERNAL"

  nginx:
    ports:
      - "80:80"      # Standard HTTP
      - "443:443"    # Standard HTTPS
```

**Example:** Use standard ports (80/443) in production:

```yaml
nginx:
  ports:
    - "80:80"
    - "443:443"
```

Then access: `http://your-server-ip` (no port needed)

---

## Firewall Configuration

### Ubuntu/Debian

```bash
# Allow HTTP/HTTPS (Dashboard)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow InfluxDB (if accessing UI directly)
sudo ufw allow 8086/tcp

# Enable firewall
sudo ufw enable
```

### Check Open Ports

```bash
sudo netstat -tulpn | grep -E '80|443|8086'
```

---

## Security Checklist for Production

### ✅ Required Security Measures

1. **Change Default Credentials**
   ```bash
   # In .env file - use strong passwords
   INFLUXDB_ADMIN_PASSWORD=StrongP@ssw0rd!With$pecial
   INFLUXDB_ADMIN_TOKEN=secure-random-t0ken!2026@production
   ```

2. **Use HTTPS/SSL**
   - Get SSL certificates (Let's Encrypt recommended)
   - Force HTTPS redirects in Nginx

3. **Encrypt .env File**
   ```bash
   python3 scripts/encrypt_credentials.py
   # This creates .env.encrypted and removes .env
   ```

4. **Restrict Network Access**
   ```bash
   # Only allow specific IPs to access InfluxDB directly
   sudo ufw allow from 192.168.1.0/24 to any port 8086
   ```

5. **Enable InfluxDB Authentication**
   - Already configured via `DOCKER_INFLUXDB_INIT_USERNAME/PASSWORD`
   - Dashboard uses token-based auth

6. **Regular Backups**
   ```bash
   # Backup InfluxDB data
   docker exec influxdb influx backup /var/lib/influxdb2/backup
   docker cp influxdb:/var/lib/influxdb2/backup ./backup-$(date +%Y%m%d)
   ```

---

## Monitoring in Production

### Check Container Status

```bash
docker ps
# Should show: influxdb (Up), healthcare-nginx (Up)
```

### Check Dashboard Logs

```bash
docker logs healthcare-nginx -f
```

### Check InfluxDB Logs

```bash
docker logs influxdb -f
```

### Check Bridge Logs

```bash
tail -f logs/eeg_influxdb_bridge.log
```

### Health Checks

```bash
# InfluxDB health
curl http://your-server-ip:8086/health

# Nginx health (returns dashboard HTML)
curl http://your-server-ip:8080
```

---

## Troubleshooting Production Issues

### Dashboard Can't Connect to InfluxDB

**Symptom:** Dashboard shows "Error: HTTP 500" or no data

**Solutions:**

1. Check if InfluxDB container is running:
   ```bash
   docker ps | grep influxdb
   ```

2. Check if firewall allows port 8086:
   ```bash
   sudo ufw status | grep 8086
   ```

3. Check browser console (F12) for CORS errors

4. Verify credentials in dashboard:
   ```bash
   python3 generate_dashboard.py
   ```

### Bridge Can't Write to InfluxDB

**Symptom:** Logs show "Connection refused" or "Unauthorized"

**Solutions:**

1. Set correct INFLUXDB_URL:
   ```bash
   export INFLUXDB_URL=http://your-server-ip:8086
   ```

2. Check .env credentials match InfluxDB:
   ```bash
   cat .env | grep INFLUXDB_ADMIN_TOKEN
   ```

3. Restart bridge with correct environment:
   ```bash
   pkill -f eeg_influxdb_bridge
   source .env
   python3 nodes/saver/eeg_influxdb_bridge.py
   ```

---

## Quick Deployment Commands

### Full Production Setup (One-Liner)

```bash
cd /opt/healthcare_demo && \
cp .env.example .env && \
nano .env && \
python3 generate_dashboard.py && \
docker-compose up -d && \
echo "✅ Dashboard: http://$(hostname -I | awk '{print $1}'):8080"
```

### Update Dashboard on Production

```bash
# After changing credentials
python3 generate_dashboard.py
docker restart healthcare-nginx
```

### Restart All Services

```bash
docker-compose restart
```

### Stop All Services

```bash
docker-compose down
```

---

## Summary

### ✅ No IP Configuration Needed!

The dashboard **automatically detects** the server IP/domain using:
```javascript
window.location.protocol + '//' + window.location.host
```

### Deployment Steps:

1. **Copy project to server**
2. **Configure .env with production credentials**
3. **Run:** `python3 generate_dashboard.py`
4. **Run:** `docker-compose up -d`
5. **Access:** `http://your-server-ip:8080`

The system works seamlessly in:
- Development (localhost)
- Production (IP address)
- Production (Domain with SSL)

**No code changes required!** 🚀

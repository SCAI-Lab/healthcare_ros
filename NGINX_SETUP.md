# Nginx Webserver für EEG Dashboard

## ✅ Installation erfolgreich abgeschlossen!

Der Nginx-Webserver ist nun eingerichtet und läuft zusammen mit InfluxDB in Docker-Containern.

## 🌐 Zugriff

**Dashboard:** http://localhost:8080

**Credentials:** Definiert in Ihrer `.env`-Datei

**⚠️ WICHTIG:** 
- Credentials werden aus `.env` geladen und sind NICHT im Git-Repository!
- Das System startet NICHT ohne `.env`-Datei
- Siehe `CREDENTIALS_SETUP.md` für die Einrichtung

**Standard-Werte aus `.env.example` (NUR als Beispiel):**
- Username: `admin`
- Password: `H3@lthC@re!2026` (NICHT in Produktion verwenden!)
- Token: `hc-eeg-secure-t0ken!2026@api` (NICHT in Produktion verwenden!)

**Eigene Credentials erstellen:**
```bash
cd /home/tjalf/ros2_ws/src/healthcare_demo
cp .env.example .env
nano .env  # Eigene sichere Werte eintragen
```

## 🐳 Docker-Befehle

```bash
# Services starten
cd /home/tjalf/ros2_ws/src/healthcare_demo
docker-compose up -d

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f nginx
docker-compose logs -f influxdb

# Services neustarten
docker-compose restart

# Services stoppen
docker-compose down

# Services stoppen und Daten löschen
docker-compose down -v
```

## 📁 Dateistruktur

```
healthcare_demo/
├── docker-compose.yml          # Docker Compose Konfiguration
├── nginx/
│   ├── nginx.conf             # Haupt-Nginx-Konfiguration
│   ├── conf.d/
│   │   └── default.conf       # Server-Block-Konfiguration
│   ├── ssl/                   # SSL-Zertifikate (für HTTPS)
│   └── README.md              # Detaillierte Dokumentation
└── docs/
    └── influxdb_realtime_dashboard.html  # EEG Dashboard
```

## 🔧 Domain einrichten

### Lokale Test-Domain

1. `/etc/hosts` bearbeiten:
   ```bash
   sudo nano /etc/hosts
   ```

2. Zeile hinzufügen:
   ```
   127.0.0.1 eeg-dashboard.local
   ```

3. In `nginx/conf.d/default.conf` ändern:
   ```nginx
   server_name eeg-dashboard.local;
   ```

4. Nginx neu laden:
   ```bash
   docker-compose restart nginx
   ```

5. Zugriff über: http://eeg-dashboard.local:8080

### Echte Domain (z.B. eeg.example.com)

1. **DNS konfigurieren** (bei Ihrem Domain-Provider):
   - A-Record: `eeg.example.com` → Ihre Server-IP

2. **Nginx-Konfiguration anpassen:**
   
   Datei `nginx/conf.d/default.conf` bearbeiten:
   ```nginx
   server {
       listen 80;
       server_name eeg.example.com;
       # ... rest bleibt gleich
   }
   ```

3. **SSL/HTTPS mit Let's Encrypt (empfohlen):**
   
   ```bash
   # Certbot installieren
   sudo apt-get install certbot
   
   # Zertifikat erstellen (Port 80 muss frei sein)
   docker-compose down
   sudo certbot certonly --standalone -d eeg.example.com
   
   # Zertifikate kopieren
   sudo cp /etc/letsencrypt/live/eeg.example.com/fullchain.pem \
       nginx/ssl/cert.pem
   sudo cp /etc/letsencrypt/live/eeg.example.com/privkey.pem \
       nginx/ssl/key.pem
   sudo chmod 644 nginx/ssl/*.pem
   ```

4. **HTTPS aktivieren** in `nginx/conf.d/default.conf`:
   - Kommentare (`#`) vom HTTPS-Server-Block entfernen
   - `server_name` mit Ihrer Domain ersetzen
   - HTTP→HTTPS Redirect aktivieren (Zeile 9)

5. **Ports für Produktion anpassen** in `docker-compose.yml`:
   ```yaml
   nginx:
     ports:
       - "80:80"      # Statt 8080:80
       - "443:443"    # Statt 8443:443
   ```

6. **Services neu starten:**
   ```bash
   docker-compose up -d
   ```

7. **Firewall konfigurieren:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw reload
   ```

## 🔄 Updates und Wartung

### Dashboard aktualisieren

Das Dashboard wird automatisch aus `docs/influxdb_realtime_dashboard.html` geladen. Nach Änderungen:

```bash
docker-compose restart nginx
```

### SSL-Zertifikate erneuern (alle 90 Tage)

```bash
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem nginx/ssl/
docker-compose restart nginx
```

### Nginx-Konfiguration testen

```bash
docker-compose exec nginx nginx -t
```

## 🛠️ Troubleshooting

### Dashboard lädt nicht

```bash
# Container-Status
docker-compose ps

# Nginx-Logs
docker-compose logs nginx | tail -50

# Browser-Cache leeren und neu laden
```

### InfluxDB-Verbindung fehlgeschlagen

```bash
# InfluxDB-Status
docker-compose exec influxdb influx ping

# Netzwerk prüfen
docker network inspect healthcare_demo_healthcare-network
```

### Port bereits belegt

Falls Port 8080 bereits verwendet wird, in `docker-compose.yml` ändern:
```yaml
nginx:
  ports:
    - "8081:80"  # Anderer Port
```

## 📊 Nächste Schritte

1. ✅ Dashboard läuft auf http://localhost:8080
2. ⚙️ EEG-Simulator starten: `cd /home/tjalf/ros2_ws/src/healthcare_demo && USE_INFLUXDB=1 bash launch/start.sh`
3. 🔄 Daten werden automatisch angezeigt (50ms Refresh)
4. 🌐 Optional: Domain und HTTPS einrichten (siehe oben)

## 📚 Weitere Dokumentation

- Detaillierte Nginx-Konfiguration: `nginx/README.md`
- InfluxDB-Setup: `docs/influxdb_setup.md`
- Quick Start: `docs/influxdb_quick_start.html`

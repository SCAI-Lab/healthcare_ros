# Nginx Webserver Configuration

## Übersicht

Der Nginx-Webserver hostet das EEG Real-Time Dashboard und fungiert als Proxy für InfluxDB API-Anfragen.

## Standard-Konfiguration (localhost)

**Dashboard URL:** http://localhost:8080

Der Webserver läuft auf Port 8080 und zeigt automatisch das EEG Dashboard an.

## Docker-Befehle

```bash
# Alle Services starten (InfluxDB + Nginx)
docker-compose up -d

# Nur Nginx neu starten
docker-compose restart nginx

# Logs ansehen
docker-compose logs -f nginx

# Status prüfen
docker-compose ps

# Services stoppen
docker-compose down
```

## Domain-Konfiguration

### Option 1: Lokale Domain (für Tests)

Füge zu `/etc/hosts` hinzu:
```
127.0.0.1 eeg-dashboard.local
```

Dann in `nginx/conf.d/default.conf` ändern:
```nginx
server_name eeg-dashboard.local;
```

### Option 2: Echte Domain

1. **DNS konfigurieren:**
   - A-Record: `yourdomain.com` → Ihre Server-IP
   - A-Record: `www.yourdomain.com` → Ihre Server-IP

2. **Nginx-Konfiguration anpassen:**
   
   In `nginx/conf.d/default.conf`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       # ... rest der Konfiguration
   }
   ```

3. **SSL/HTTPS aktivieren (empfohlen):**

   **Mit Let's Encrypt (kostenlos):**
   ```bash
   # Certbot installieren
   sudo apt-get install certbot python3-certbot-nginx
   
   # Zertifikat erstellen (außerhalb des Containers)
   sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
   
   # Zertifikate kopieren
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
   ```

   **HTTPS-Block in `nginx/conf.d/default.conf` aktivieren:**
   - Kommentare (`#`) entfernen vom HTTPS-Server-Block
   - `server_name` mit Ihrer Domain ersetzen
   - HTTP-Redirect aktivieren (Zeile 9)

4. **Docker-Compose neu starten:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Firewall-Konfiguration

Für externe Zugriffe Ports öffnen:

```bash
# UFW (Ubuntu)
sudo ufw allow 8080/tcp    # HTTP
sudo ufw allow 8443/tcp    # HTTPS
sudo ufw reload

# iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
```

## Reverse Proxy Konfiguration

Falls der Server hinter einem Reverse Proxy läuft, in `docker-compose.yml` die Ports anpassen:

```yaml
nginx:
  ports:
    - "80:80"      # Statt 8080:80
    - "443:443"    # Statt 8443:443
```

## Troubleshooting

### Dashboard lädt nicht

```bash
# Container-Status prüfen
docker-compose ps

# Nginx-Logs prüfen
docker-compose logs nginx

# Konfiguration testen
docker-compose exec nginx nginx -t

# Neu laden nach Config-Änderung
docker-compose exec nginx nginx -s reload
```

### InfluxDB-Verbindung fehlgeschlagen

```bash
# InfluxDB-Status prüfen
docker-compose exec influxdb influx ping

# Netzwerk prüfen
docker network inspect healthcare_healthcare-network
```

### CORS-Fehler

Falls externe API-Zugriffe nicht funktionieren, CORS-Header in `nginx/conf.d/default.conf` anpassen:

```nginx
add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
```

## Backup & Wartung

```bash
# Nginx-Logs rotieren
docker-compose exec nginx logrotate /etc/logrotate.d/nginx

# SSL-Zertifikate erneuern (alle 90 Tage)
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem nginx/ssl/
docker-compose restart nginx
```

## Sicherheit

- Standard-Ports sind 8080/8443 (nicht 80/443) für Non-Root-Betrieb
- SSL/TLS 1.2+ ist aktiviert
- CORS ist standardmäßig permissive (`*`) - für Produktion einschränken
- Gzip-Kompression ist aktiviert
- Health-Check-Endpoint unter `/health`

## Performance-Optimierung

Für hohe Last in `nginx/nginx.conf` anpassen:

```nginx
worker_processes  auto;
worker_connections  4096;
keepalive_timeout  30;
```

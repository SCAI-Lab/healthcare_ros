# Credentials Setup Guide

## 🔒 Security Policy (Updated Feb 2026)

**IMPORTANT:** The `.env` file is **REQUIRED** for all InfluxDB/web dashboard features. The system will not start without it.

There are no default or fallback credentials for security reasons. You must create your own secure credentials.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cd /home/tjalf/ros2_ws/src/healthcare_demo
   cp .env.example .env
   ```

2. **Edit the file with YOUR secure credentials:**
   ```bash
   nano .env
   ```
   
   **Replace the example values** with your own:
   ```bash
   INFLUXDB_ADMIN_USERNAME=admin
   INFLUXDB_ADMIN_PASSWORD=Your$ecureP@ssw0rd!Here  # Min. 3 special chars
   INFLUXDB_ORG=healthcare
   INFLUXDB_BUCKET=eeg_data
   INFLUXDB_ADMIN_TOKEN=your-custom-t0ken!with@specials  # Min. 3 special chars
   ```

3. **Start the system:**
   ```bash
   USE_INFLUXDB=1 bash launch/start.sh
   ```

## ⚠️ What Happens Without .env

If you try to start with `USE_INFLUXDB=1` without creating `.env` first:

```
❌ ERROR: .env file not found!

The .env file is required for security reasons.
Please create it before starting:

  cd /home/tjalf/ros2_ws/src/healthcare_demo
  cp .env.example .env
  # Edit .env with your secure credentials

See CREDENTIALS_SETUP.md for details.
```

**The system will NOT start.** This is intentional for security.

## Password Requirements

**Your credentials MUST meet these requirements:**

- **Minimum 3 special characters** (e.g., `!`, `@`, `#`, `$`, `%`, `&`, `*`)
- Mix of uppercase, lowercase, numbers
- Recommended: 12+ characters
- **Never use the examples from `.env.example` in production!**

### Example Strong Credentials

```bash
# Good examples (but create your own!)
INFLUXDB_ADMIN_PASSWORD=My$uper!Secur3@Pass
INFLUXDB_ADMIN_TOKEN=eeg-t0k3n!2026@s3cure#api
```

### Weak Credentials (DO NOT USE)

```bash
# ❌ Too simple
INFLUXDB_ADMIN_PASSWORD=password123

# ❌ No special characters
INFLUXDB_ADMIN_PASSWORD=Healthcare2026

# ❌ Using the example values
INFLUXDB_ADMIN_PASSWORD=H3@lthC@re!2026  # From .env.example
```

## Files Not Tracked in Git

✅ **Safe (ignored by git):**
- `.env` - Your actual credentials
- `docs/influxdb_realtime_dashboard.html` - Generated with your credentials

✅ **Tracked (safe to commit):**
- `.env.example` - Template with placeholder/example values
- `docs/influxdb_realtime_dashboard.template.html` - Template with placeholders
- `generate_dashboard.py` - Generator script

## Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Check with: `git status` (should not appear)

2. **Use strong, unique credentials**
   - Different from example values
   - Different for each deployment

3. **Rotate credentials regularly**
   - Edit `.env`
   - Restart: `docker-compose down && USE_INFLUXDB=1 bash launch/start.sh`

4. **For production deployments:**
   - Use environment-specific `.env` files
   - Consider secrets management tools (Vault, AWS Secrets Manager, etc.)
   - Enable HTTPS (see `nginx/README.md`)

## Troubleshooting

### Dashboard shows "unauthorized" errors

**Problem:** Credentials in dashboard don't match InfluxDB

**Solution:**
```bash
# Regenerate dashboard
cd /home/tjalf/ros2_ws/src/healthcare_demo
python3 generate_dashboard.py

# Restart Docker
docker-compose restart nginx
```

### Container fails to start

**Problem:** `.env` file not found or invalid

**Solution:**
```bash
# Check if .env exists
ls -la .env

# Copy from example if missing
cp .env.example .env

# Restart
docker-compose down
USE_INFLUXDB=1 bash launch/start.sh
```

### Want to reset to defaults

```bash
# Remove custom credentials
rm .env

# Copy defaults
cp .env.example .env

# Restart
docker-compose down
docker volume rm healthcare_demo_influxdb-data healthcare_demo_influxdb-config
USE_INFLUXDB=1 bash launch/start.sh
```

## Migration from Old Setup

If you had the old hardcoded credentials (`healthcare2026`), the system will automatically migrate:

1. First run creates `.env` with new secure credentials
2. Dashboard is regenerated with new credentials
3. Docker containers recreated with new credentials
4. Old credentials no longer work

**No manual migration needed!** Just run:
```bash
USE_INFLUXDB=1 bash launch/start.sh
```

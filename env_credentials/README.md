# Credential Management

This directory contains all application credentials in separate `.env` files.

## Files

### `.env.influxdb`
InfluxDB database credentials for time-series storage and dashboard access.

**Required variables:**
```bash
INFLUXDB_ADMIN_USERNAME=admin
INFLUXDB_ADMIN_PASSWORD=YourSecurePassword
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
INFLUXDB_ADMIN_TOKEN=your-secure-token
INFLUXDB_RETENTION_MINUTES=5  # Auto-cleanup (prevents database from filling up)
```

**Production Note:** The bridge automatically deletes data older than `INFLUXDB_RETENTION_MINUTES` (default: 5 minutes) every 60 seconds to prevent the database from running full.

### `neurosity.env`
Neurosity Crown EEG headset authentication credentials.

**Required variables:**
```bash
NEUROSITY_DEVICE_ID=your_device_id
NEUROSITY_EMAIL=your_email@example.com
NEUROSITY_PASSWORD=your_password
```

### `openbci.env`
OpenBCI Cyton/Ganglion device configuration.

**Required variables:**
```bash
OPENBCI_PORT=/dev/ttyUSB0
OPENBCI_BOARD=cyton
OPENBCI_SAMPLE_RATE=250
OPENBCI_DAISY=false
```

## Encryption

### Encrypt credentials (for safe storage/sharing)

```bash
python3 scripts/encrypt_credentials_multi.py --setup
```

This will:
1. Prompt for a master password (min 12 chars)
2. Encrypt all `.env` files → `.env.*.encrypted`
3. Allow you to safely delete plaintext `.env` files

### Decrypt credentials (for use)

```bash
python3 scripts/encrypt_credentials_multi.py --decrypt
```

This will:
1. Prompt for master password
2. Decrypt all `.encrypted` files → `.env` files
3. Set permissions to 600 (owner read/write only)

## Security Best Practices

✅ **DO:**
- Encrypt credentials before committing to git
- Use strong master password (12+ chars, mixed case, numbers, symbols)
- Keep encrypted files (`.encrypted`) in version control
- Delete plaintext `.env` files after encryption

❌ **DON'T:**
- Commit plaintext `.env` files to git
- Share master password via insecure channels
- Use weak/common passwords
- Forget your master password (it's not recoverable!)

## Usage in Code

All credential files are automatically loaded:

```python
# InfluxDB credentials (dashboard generator, bridge)
from dotenv import load_dotenv
load_dotenv('env_credentials/.env.influxdb')

# Neurosity credentials (neurosity_driver)
load_dotenv('env_credentials/neurosity.env')

# OpenBCI credentials (openbci_driver)
load_dotenv('env_credentials/openbci.env')
```

## .gitignore Configuration

The `.gitignore` file is configured to:
- ✅ Ignore plaintext `.env` files
- ✅ Keep encrypted `.encrypted` files
- ✅ Exclude `env_credentials/` from accidental commits

```gitignore
# Plaintext credentials (ignore)
env_credentials/*.env
env_credentials/.env.*

# Encrypted credentials (keep - can be committed safely)
# env_credentials/*.encrypted
```

# Quick Start: Credential Encryption

## 5-Minute Setup

### 1. Create Plain Credentials
```bash
cd ~/ros2_ws/src/healthcare_demo
cp .env.example .env
nano .env  # Set your secure credentials
```

### 2. Encrypt
```bash
python3 scripts/encrypt_credentials.py --setup
# Enter master password (min 12 chars)
# Confirm password
```

### 3. Use Encrypted System
```bash
ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh
# Enter master password when prompted
```

### 4. (Optional) Delete Plain File
```bash
rm .env  # Now only .env.encrypted exists
```

## Daily Usage

```bash
# Start with encryption
ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh

# You'll be prompted:
# 🔐 Using encrypted credentials...
# Decrypting credentials...
# Enter master password: ****

# System starts, credentials auto-deleted on exit
```

## Complete Guide

See `ENCRYPTION_GUIDE.md` for:
- Security architecture
- Troubleshooting
- Master password recovery
- Team sharing
- Compliance details

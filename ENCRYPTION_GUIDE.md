# Credential Encryption Guide

## 🔐 Overview

This system supports **password-based encryption** for all credentials using industry-standard **Fernet encryption** (symmetric encryption with AES-128).

## Why Encryption?

1. **Defense in Depth**: Even if someone gains access to your repository, credentials remain protected
2. **Safe Backups**: Encrypted `.env.encrypted` can be safely committed to git (if desired)
3. **Team Sharing**: Share encrypted credentials securely via secure channels
4. **Compliance**: Meets security requirements for credential storage

## Security Features

- ✅ **PBKDF2** key derivation (480,000 iterations - OWASP 2023 recommendation)
- ✅ **Random salt** per encryption (prevents rainbow table attacks)
- ✅ **Fernet** (AES-128-CBC + HMAC-SHA256)
- ✅ **Master password** protection (minimum 12 characters)
- ✅ **Auto-cleanup** of decrypted credentials on exit

## Setup Guide

### 1. Create Your Plain .env File

```bash
cd /home/tjalf/ros2_ws/src/healthcare_demo
cp .env.example .env
nano .env
```

Set your secure credentials:
```env
INFLUXDB_ADMIN_USERNAME=admin
INFLUXDB_ADMIN_PASSWORD=YourSecureP@ssw0rd!2026
INFLUXDB_ADMIN_TOKEN=your-secure-t0ken!with@special#chars
INFLUXDB_ORG=healthcare
INFLUXDB_BUCKET=eeg_data
```

### 2. Encrypt Your Credentials

```bash
python3 scripts/encrypt_credentials.py --setup
```

You'll be prompted to:
1. Enter a master password (min 12 characters)
2. Confirm the password
3. Encryption creates `.env.encrypted`

**⚠️ IMPORTANT:** 
- Remember your master password - it **cannot be recovered**!
- Store master password in a password manager (1Password, Bitwarden, etc.)
- DO NOT commit master password to git!

### 3. Use Encrypted Credentials

```bash
# Start system with encrypted credentials
ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh
```

The script will:
1. Prompt for your master password
2. Decrypt `.env.encrypted` → `.env` (temporary)
3. Load credentials and start services
4. **Auto-delete** `.env` when script exits

### 4. (Optional) Remove Plain .env

After successful encryption, you can delete the plain .env file:

```bash
rm .env
```

Now only `.env.encrypted` exists. The system will decrypt it when needed.

## Usage Examples

### Use Encrypted Credentials (Recommended)
```bash
ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh
```

### Use Plain .env (Less Secure)
```bash
USE_INFLUXDB=1 bash launch/start.sh
```

### Decrypt Manually (for inspection)
```bash
python3 scripts/encrypt_credentials.py --decrypt
# Creates temporary .env file
cat .env
rm .env  # Clean up when done
```

### Re-encrypt with New Credentials
```bash
# 1. Update plain .env file
nano .env

# 2. Re-encrypt
python3 scripts/encrypt_credentials.py --setup

# 3. Delete plain file (optional)
rm .env
```

## Git Integration

### Option 1: Keep .env.encrypted Private (Default)
```bash
# .gitignore already contains:
.env
*.env
# .env.encrypted  ← Uncommented = also ignored
```

Both `.env` and `.env.encrypted` stay local only.

### Option 2: Commit Encrypted Backups
```bash
# Edit .gitignore and comment out:
# .env.encrypted  ← Commented = will be committed

git add .env.encrypted
git commit -m "Add encrypted credentials backup"
git push
```

**Pros:** Team can pull encrypted credentials
**Cons:** Must share master password via secure channel (Keybase, 1Password shared vault, etc.)

## Security Best Practices

### ✅ DO

- Use strong master passwords (16+ chars, mixed case, numbers, symbols)
- Store master password in password manager
- Rotate credentials regularly
- Use different passwords for dev/staging/production
- Share master password via encrypted channel only
- Run encryption setup in trusted environment

### ❌ DON'T

- Don't use weak master passwords
- Don't commit master password to git
- Don't share master password via email/Slack/Teams
- Don't reuse master password across systems
- Don't store master password in code
- Don't run encryption on compromised systems

## Troubleshooting

### "Decryption failed: Wrong password or corrupted file!"

**Cause:** Incorrect master password

**Solution:** 
1. Try password again (check caps lock!)
2. If lost, decrypt from backup:
   ```bash
   # If you have plain .env backup
   cp .env.backup .env
   python3 scripts/encrypt_credentials.py --setup
   ```

### ".env.encrypted file not found!"

**Cause:** Haven't run encryption setup yet

**Solution:**
```bash
python3 scripts/encrypt_credentials.py --setup
```

### "Missing required credentials in .env file!"

**Cause:** Decryption worked, but .env is missing fields

**Solution:** Check your `.env.encrypted` was created from complete `.env`:
```bash
python3 scripts/encrypt_credentials.py --decrypt
cat .env  # Verify all fields present
rm .env
```

## Credential Rotation

When changing credentials:

```bash
# 1. Decrypt current credentials
python3 scripts/encrypt_credentials.py --decrypt

# 2. Edit with new values
nano .env

# 3. Re-encrypt with SAME or NEW master password
python3 scripts/encrypt_credentials.py --setup

# 4. Test
ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh

# 5. Clean up plain file
rm .env
```

## Performance Impact

- Encryption/Decryption: ~100-200ms (negligible)
- PBKDF2 iterations: ~50-100ms (acceptable for security)
- No runtime performance impact (credentials loaded once at startup)

## Compliance

This encryption implementation meets:

- ✅ **OWASP** recommendations for password-based encryption
- ✅ **NIST SP 800-132** for PBKDF2 parameters
- ✅ **GDPR** requirements for credential protection
- ✅ **SOC 2** controls for encryption at rest

## Technical Details

### Encryption Algorithm

```
Fernet = AES-128-CBC + HMAC-SHA256
Key Derivation = PBKDF2-HMAC-SHA256 (480k iterations)
Salt = Random 16 bytes per encryption
```

### File Format (.env.encrypted)

```
[0:16]    → Salt (16 bytes)
[16:]     → Fernet-encrypted data
```

### Code Reference

See `scripts/encrypt_credentials.py` for implementation details.

## Questions?

- Encryption technical details: See `scripts/encrypt_credentials.py`
- General security: See `CREDENTIALS_SETUP.md`
- System usage: See `README.md`

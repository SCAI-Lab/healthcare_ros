# Security Changes - February 2026

## Breaking Change: .env File Now Required

### What Changed

**Before:** System had fallback default credentials if `.env` was missing.

**After:** System **requires** `.env` file and will not start without it.

### Why This Change

1. **Security:** No default passwords means no predictable credentials
2. **Best Practice:** Forces explicit credential management
3. **Production Ready:** Prevents accidental use of example passwords

### Migration Guide

If you are upgrading from an older version:

1. **Create your .env file:**
   ```bash
   cd /home/tjalf/ros2_ws/src/healthcare_demo
   cp .env.example .env
   ```

2. **Set YOUR credentials (not the examples):**
   ```bash
   nano .env
   # Change all passwords and tokens to your own secure values
   ```

3. **Start the system:**
   ```bash
   USE_INFLUXDB=1 bash launch/start.sh
   ```

### Error Messages

#### If .env is missing:

```
❌ ERROR: .env file not found!

The .env file is required for security reasons.
Please create it before starting:

  cd /home/tjalf/ros2_ws/src/healthcare_demo
  cp .env.example .env
  # Edit .env with your secure credentials
```

**Solution:** Create `.env` file as shown above.

#### If .env has missing fields:

```
❌ ERROR: Missing required credentials in .env file!

Required variables:
  - INFLUXDB_ADMIN_USERNAME
  - INFLUXDB_ADMIN_PASSWORD
  - INFLUXDB_ADMIN_TOKEN
```

**Solution:** Check your `.env` file has all required fields.

### What Still Works Without .env

These features do NOT require `.env`:

- ✅ Simulator mode without InfluxDB: `bash launch/start.sh`
- ✅ ROSBAG recording: `USE_ROSBAG=1 bash launch/start.sh`
- ✅ Hardware acquisition without web dashboard

Only `USE_INFLUXDB=1` requires `.env` file.

### Files Affected

- `launch/start.sh` - Now checks for `.env` and exits if missing
- `README.md` - Updated with .env setup instructions
- `CREDENTIALS_SETUP.md` - Updated with mandatory requirement
- `NGINX_SETUP.md` - Updated credential documentation

### Backward Compatibility

**Breaking:** If you relied on default credentials, you must create `.env` now.

**Non-Breaking:** All other functionality remains unchanged.

### Security Improvements

1. ❌ **Removed:** Hardcoded default credentials
2. ❌ **Removed:** Fallback to example passwords
3. ✅ **Added:** Mandatory `.env` validation
4. ✅ **Added:** Clear error messages for missing credentials
5. ✅ **Added:** Validation of required environment variables

### Questions?

See `CREDENTIALS_SETUP.md` for complete setup guide.

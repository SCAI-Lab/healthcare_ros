#!/usr/bin/env python3
"""
Dashboard Generator - Credential Injection Script

Generates the InfluxDB real-time dashboard HTML file by injecting credentials from a .env file
into the template. This ensures credentials are never hardcoded in version-controlled files.

Process:
1. Reads credentials from env_credentials/.env.influxdb (preferred)
    or falls back to .env (legacy)
2. Loads HTML template from nodes/visualization/dashboard/influxdb_realtime_dashboard.template.html
3. Replaces placeholders with actual credentials
4. Writes generated dashboard to nodes/visualization/dashboard/influxdb_realtime_dashboard.html (git-ignored)

Security:
- Template is tracked in git (no credentials)
- Generated dashboard contains credentials but is git-ignored
- .env file is also git-ignored (or can be encrypted with scripts/encrypt_credentials.py)

Usage:
    python3 generate_dashboard.py
    
    # After updating credentials:
    nano env_credentials/.env.influxdb
    python3 nodes/visualization/dashboard/generate_dashboard.py
    docker restart healthcare-nginx

Output:
    nodes/visualization/dashboard/influxdb_realtime_dashboard.html - Ready to be served by Nginx as index.html

See Also:
    - PRODUCTION_DEPLOYMENT.md - Full deployment guide
    - env_credentials/README.md - Credential setup instructions
"""
import os
import sys
from pathlib import Path

def load_env_file(env_path):
    """Load .env file and return dict of variables."""
    env_vars = {}
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        print("Please decrypt credentials first:")
        print("  python3 scripts/encrypt_credentials_multi.py --decrypt")
        sys.exit(1)
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def generate_dashboard(template_path, output_path, env_vars):
    """Generate dashboard HTML with injected credentials."""
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Replace placeholders
    content = content.replace(
        "const INFLUXDB_TOKEN = 'INFLUXDB_TOKEN_PLACEHOLDER';",
        f"const INFLUXDB_TOKEN = '{env_vars.get('INFLUXDB_ADMIN_TOKEN', 'token-not-set')}';"
    )
    content = content.replace(
        "const INFLUXDB_ORG = 'INFLUXDB_ORG_PLACEHOLDER';",
        f"const INFLUXDB_ORG = '{env_vars.get('INFLUXDB_ORG', 'healthcare')}';"
    )
    content = content.replace(
        "const INFLUXDB_BUCKET = 'INFLUXDB_BUCKET_PLACEHOLDER';",
        f"const INFLUXDB_BUCKET = '{env_vars.get('INFLUXDB_BUCKET', 'eeg_data')}';"
    )
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Dashboard generated: {output_path}")

def main():
    # Navigate to project root from nodes/visualization/
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / 'env_credentials' / '.env.influxdb'
    template_path = Path(__file__).parent / 'influxdb_realtime_dashboard.template.html'
    output_path = Path(__file__).parent / 'influxdb_realtime_dashboard.html'
    
    # Load environment variables
    if env_path.exists():
        env_vars = load_env_file(env_path)
        env_source = 'env_credentials/.env.influxdb'
    else:
        print('ERROR: No credentials file found at env_credentials/.env.influxdb.')
        print('Create it or decrypt encrypted credentials:')
        print('  python3 scripts/encrypt_credentials_multi.py --decrypt')
        sys.exit(1)
    
    # Generate dashboard
    generate_dashboard(template_path, output_path, env_vars)
    
    print(f"✅ Using credentials from {env_source}:")
    print(f"   - Token: {env_vars.get('INFLUXDB_ADMIN_TOKEN', 'N/A')[:20]}...")
    print(f"   - Org: {env_vars.get('INFLUXDB_ORG', 'N/A')}")
    print(f"   - Bucket: {env_vars.get('INFLUXDB_BUCKET', 'N/A')}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generate dashboard HTML with credentials from .env file.
This ensures credentials are never hardcoded in tracked files.
"""
import os
import sys
from pathlib import Path

def load_env_file(env_path):
    """Load .env file and return dict of variables."""
    env_vars = {}
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        print("Please copy .env.example to .env and configure your credentials.")
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
    project_root = Path(__file__).parent
    env_path = project_root / '.env'
    template_path = project_root / 'docs' / 'influxdb_realtime_dashboard.template.html'
    output_path = project_root / 'docs' / 'influxdb_realtime_dashboard.html'
    
    # Load environment variables
    env_vars = load_env_file(env_path)
    
    # Generate dashboard
    generate_dashboard(template_path, output_path, env_vars)
    
    print(f"✅ Using credentials from .env:")
    print(f"   - Token: {env_vars.get('INFLUXDB_ADMIN_TOKEN', 'N/A')[:20]}...")
    print(f"   - Org: {env_vars.get('INFLUXDB_ORG', 'N/A')}")
    print(f"   - Bucket: {env_vars.get('INFLUXDB_BUCKET', 'N/A')}")

if __name__ == '__main__':
    main()

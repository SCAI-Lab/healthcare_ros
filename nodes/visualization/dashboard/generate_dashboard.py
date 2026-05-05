#!/usr/bin/env python3
"""
Dashboard Generator (Clean Data-Layer Version)

No InfluxDB credentials are injected anymore.
Frontend only talks to Python Data Service.
"""

import sys
from pathlib import Path


def generate(template_path, output_path):
    content = template_path.read_text()

    # Inject ONLY data service URL
    content = content.replace(
        "const DATA_SERVICE_URL = 'DATA_SERVICE_URL_PLACEHOLDER';",
        "const DATA_SERVICE_URL = '/api';"
    )

    output_path.write_text(content)
    print("✅ Dashboard generated (data-service mode)")


def main():
    base = Path(__file__).parent

    template = base / "influxdb_realtime_dashboard.template.html"
    output = base / "influxdb_realtime_dashboard.html"

    if not template.exists():
        print("Template not found")
        sys.exit(1)

    generate(template, output)


if __name__ == "__main__":
    main()
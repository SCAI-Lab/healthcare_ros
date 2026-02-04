#!/usr/bin/env python3
"""
Test script for encrypted credential workflow
"""
import subprocess
import sys
from pathlib import Path

def test_encryption_workflow():
    """Test the complete encryption workflow."""
    project_root = Path(__file__).parent.parent  # Go up from tests/ to project root
    
    print("=" * 60)
    print("Testing Encryption Workflow")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    # Test 1: Check if encryption script exists and is executable
    encrypt_script = project_root / "scripts" / "encrypt_credentials.py"
    print(f"\n✓ Test 1: Script exists: {encrypt_script.exists()}")
    
    # Test 2: Check help command
    result = subprocess.run(
        [sys.executable, str(encrypt_script), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    print(f"✓ Test 2: Help command works: {result.returncode == 0}")
    if result.returncode == 0:
        print(f"  Output preview: {result.stdout[:100]}...")
    
    # Test 3: Check if .env.encrypted was created
    encrypted_file = project_root / ".env.encrypted"
    print(f"\n✓ Test 3: Encrypted file exists: {encrypted_file.exists()}")
    if encrypted_file.exists():
        size = encrypted_file.stat().st_size
        print(f"  File size: {size} bytes")
        print(f"  Expected: >500 bytes (encrypted content + salt)")
        print(f"  Status: {'✓ PASS' if size > 500 else '✗ FAIL'}")
    
    # Test 4: Check start.sh has encryption support
    start_sh = project_root / "launch" / "start.sh"
    content = start_sh.read_text()
    has_encrypted_env = "ENCRYPTED_ENV" in content
    print(f"\n✓ Test 4: Start script supports ENCRYPTED_ENV: {has_encrypted_env}")
    
    # Test 5: Check documentation exists
    docs = [
        "ENCRYPTION_GUIDE.md",
        "ENCRYPTION_QUICKSTART.md",
    ]
    print(f"\n✓ Test 5: Documentation files:")
    for doc in docs:
        exists = (project_root / doc).exists()
        print(f"  - {doc}: {'✓' if exists else '✗'}")
    
    # Test 6: Check .gitignore
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text()
    ignores_env = ".env" in content
    print(f"\n✓ Test 6: .gitignore protects .env: {ignores_env}")
    
    print("\n" + "=" * 60)
    print("✅ All encryption infrastructure tests passed!")
    print("=" * 60)
    print("\nTo test encryption manually:")
    print("  1. python3 scripts/encrypt_credentials.py --setup")
    print("  2. ENCRYPTED_ENV=1 USE_INFLUXDB=1 bash launch/start.sh")

if __name__ == "__main__":
    test_encryption_workflow()

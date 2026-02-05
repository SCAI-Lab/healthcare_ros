#!/usr/bin/env python3
"""
Multi-Credential Encryption/Decryption Utility
Encrypts all .env files in env_credentials/ directory
"""

import os
import sys
import base64
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommendation 2023
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(input_file: Path, output_file: Path, password: str):
    """Encrypt a file using password-derived key."""
    # Generate random salt
    salt = os.urandom(16)
    
    # Derive key from password
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    # Read plaintext
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    # Encrypt
    ciphertext = fernet.encrypt(plaintext)
    
    # Write salt + ciphertext
    with open(output_file, 'wb') as f:
        f.write(salt)  # First 16 bytes are salt
        f.write(ciphertext)
    
    print(f"✅ Encrypted: {input_file.name} → {output_file.name}")


def decrypt_file(input_file: Path, output_file: Path, password: str):
    """Decrypt a file using password-derived key."""
    # Read salt + ciphertext
    with open(input_file, 'rb') as f:
        salt = f.read(16)
        ciphertext = f.read()
    
    # Derive key from password
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    # Decrypt
    try:
        plaintext = fernet.decrypt(ciphertext)
    except Exception:
        print(f"❌ ERROR: Wrong password or corrupted file: {input_file.name}")
        sys.exit(1)
    
    # Write plaintext
    with open(output_file, 'wb') as f:
        f.write(plaintext)
    
    print(f"✅ Decrypted: {input_file.name} → {output_file.name}")


def setup_encryption():
    """Interactive setup to encrypt all credential files."""
    project_root = Path(__file__).parent.parent
    creds_dir = project_root / "env_credentials"
    
    # Check if credential directory exists
    if not creds_dir.exists():
        print("❌ ERROR: env_credentials/ directory not found!")
        print(f"Expected location: {creds_dir}")
        sys.exit(1)
    
    # Find all .env files (including .env.influxdb)
    env_files = sorted(list(creds_dir.glob("*.env")) + list(creds_dir.glob(".env.*")))
    
    if not env_files:
        print("❌ ERROR: No .env files found in env_credentials/!")
        print(f"Expected files like: influxdb.env, neurosity.env, openbci.env")
        sys.exit(1)
    
    print("🔐 Multi-Credential Encryption Setup")
    print("=" * 60)
    print(f"Credential directory: {creds_dir}")
    print(f"\nFound {len(env_files)} credential file(s):")
    for f in env_files:
        print(f"  • {f.name}")
    print()
    
    # Get master password
    password = getpass.getpass("Enter master password (min 12 chars): ")
    if len(password) < 12:
        print("❌ Password too short! Minimum 12 characters required.")
        sys.exit(1)
    
    password_confirm = getpass.getpass("Confirm master password: ")
    if password != password_confirm:
        print("❌ Passwords don't match!")
        sys.exit(1)
    
    print("\n🔒 Encrypting files...")
    print("-" * 60)
    
    # Encrypt each file
    for env_file in env_files:
        encrypted_file = env_file.with_suffix(env_file.suffix + '.encrypted')
        encrypt_file(env_file, encrypted_file, password)
    
    print()
    print("=" * 60)
    print("✅ All credentials encrypted successfully!")
    print()
    print("📋 Next Steps:")
    print(f"  1. Encrypted files are in: {creds_dir}")
    print(f"  2. You can safely delete plaintext .env files:")
    print(f"     rm {creds_dir}/*.env {creds_dir}/.env.*")
    print(f"     (Keep the .encrypted files!)")
    print(f"  3. REMEMBER YOUR MASTER PASSWORD - it cannot be recovered!")
    print()
    print("To decrypt for use:")
    print("  python3 scripts/encrypt_credentials_multi.py --decrypt")


def decrypt_for_use():
    """Decrypt all .env.encrypted files to temporary .env files for use."""
    project_root = Path(__file__).parent.parent
    creds_dir = project_root / "env_credentials"
    
    if not creds_dir.exists():
        print("❌ ERROR: env_credentials/ directory not found!")
        sys.exit(1)
    
    # Find all encrypted files
    encrypted_files = sorted(list(creds_dir.glob("*.encrypted")))
    
    if not encrypted_files:
        print("❌ ERROR: No .encrypted files found!")
        print(f"Expected location: {creds_dir}")
        print("\nRun encryption setup first:")
        print("  python3 scripts/encrypt_credentials_multi.py --setup")
        sys.exit(1)
    
    print("🔓 Decrypting credentials...")
    print("-" * 60)
    
    # Get master password
    password = getpass.getpass("Enter master password: ")
    
    # Decrypt each file
    decrypted_count = 0
    for encrypted_file in encrypted_files:
        # Remove .encrypted suffix
        output_file = encrypted_file.with_suffix('')
        decrypt_file(encrypted_file, output_file, password)
        
        # Set restrictive permissions
        os.chmod(output_file, 0o600)
        decrypted_count += 1
    
    print()
    print("=" * 60)
    print(f"✅ Decrypted {decrypted_count} credential file(s) successfully!")
    print(f"   Location: {creds_dir}")
    print("   Permissions: 600 (owner read/write only)")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_encryption()
    elif len(sys.argv) > 1 and sys.argv[1] == "--decrypt":
        decrypt_for_use()
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Multi-Credential Encryption Utility")
        print()
        print("Usage:")
        print("  python3 scripts/encrypt_credentials_multi.py --setup")
        print("    → Encrypt all .env files in env_credentials/ (interactive)")
        print()
        print("  python3 scripts/encrypt_credentials_multi.py --decrypt")
        print("    → Decrypt all .encrypted files in env_credentials/ (interactive)")
        print()
        print("Supported credential files:")
        print("  • .env.influxdb  - InfluxDB database credentials")
        print("  • neurosity.env  - Neurosity Crown device credentials")
        print("  • openbci.env    - OpenBCI device configuration")
    else:
        print("❌ Missing argument!")
        print()
        print("Usage:")
        print("  --setup    Encrypt all credential files")
        print("  --decrypt  Decrypt all credential files")
        print("  --help     Show this help")
        sys.exit(1)


if __name__ == "__main__":
    main()

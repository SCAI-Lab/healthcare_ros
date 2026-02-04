#!/usr/bin/env python3
"""
Credential Encryption/Decryption Utility
Uses Fernet (symmetric encryption) with a master key.
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
    
    print(f"✅ Encrypted: {input_file} → {output_file}")


def decrypt_file(input_file: Path, output_file: Path, password: str):
    """Decrypt a file using password-derived key."""
    # Read salt + ciphertext
    with open(input_file, 'rb') as f:
        salt = f.read(16)  # First 16 bytes are salt
        ciphertext = f.read()
    
    # Derive key from password
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    
    # Decrypt
    try:
        plaintext = fernet.decrypt(ciphertext)
    except Exception as e:
        print(f"❌ Decryption failed: {e}")
        print("Wrong password or corrupted file!")
        sys.exit(1)
    
    # Write plaintext
    with open(output_file, 'wb') as f:
        f.write(plaintext)
    
    print(f"✅ Decrypted: {input_file} → {output_file}")


def setup_encryption():
    """Interactive setup for encrypting .env file."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    encrypted_file = project_root / ".env.encrypted"
    
    if not env_file.exists():
        print("❌ ERROR: .env file not found!")
        print(f"Expected location: {env_file}")
        print("\nCreate .env first:")
        print(f"  cd {project_root}")
        print("  cp .env.example .env")
        print("  nano .env")
        sys.exit(1)
    
    print("🔐 Credential Encryption Setup")
    print("=" * 50)
    print(f"Input:  {env_file}")
    print(f"Output: {encrypted_file}")
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
    
    # Encrypt
    encrypt_file(env_file, encrypted_file, password)
    
    print()
    print("✅ Encryption successful!")
    print()
    print("⚠️  IMPORTANT:")
    print(f"  1. Your credentials are now in: {encrypted_file}")
    print(f"  2. The original .env file is still present!")
    print(f"  3. You can safely delete .env if you want:")
    print(f"     rm {env_file}")
    print(f"  4. REMEMBER YOUR MASTER PASSWORD - it cannot be recovered!")
    print()
    print("To use encrypted credentials:")
    print("  USE_INFLUXDB=1 ENCRYPTED_ENV=1 bash launch/start.sh")


def decrypt_for_use():
    """Decrypt .env.encrypted to temporary .env for use."""
    project_root = Path(__file__).parent.parent
    encrypted_file = project_root / ".env.encrypted"
    env_file = project_root / ".env"
    
    if not encrypted_file.exists():
        print("❌ ERROR: .env.encrypted file not found!")
        print(f"Expected location: {encrypted_file}")
        print("\nRun encryption setup first:")
        print("  python3 scripts/encrypt_credentials.py --setup")
        sys.exit(1)
    
    # Get master password
    password = getpass.getpass("Enter master password: ")
    
    # Decrypt
    decrypt_file(encrypted_file, env_file, password)
    
    # Set restrictive permissions
    os.chmod(env_file, 0o600)
    
    print()
    print("✅ Credentials decrypted successfully!")
    print(f"   Temporary file: {env_file}")
    print("   Permissions: 600 (owner read/write only)")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_encryption()
    elif len(sys.argv) > 1 and sys.argv[1] == "--decrypt":
        decrypt_for_use()
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Credential Encryption Utility")
        print()
        print("Usage:")
        print("  python3 scripts/encrypt_credentials.py --setup")
        print("    → Encrypt .env file (interactive)")
        print()
        print("  python3 scripts/encrypt_credentials.py --decrypt")
        print("    → Decrypt .env.encrypted to .env (interactive)")
        print()
        print("  ENCRYPTED_ENV=1 bash launch/start.sh")
        print("    → Auto-decrypt and start system")
    else:
        print("❌ Missing argument!")
        print()
        print("Usage:")
        print("  --setup    Encrypt .env file")
        print("  --decrypt  Decrypt .env.encrypted")
        print("  --help     Show this help")
        sys.exit(1)


if __name__ == "__main__":
    main()

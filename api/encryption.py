from cryptography.fernet import Fernet
from django.conf import settings
import base64

def get_cipher():
    """Get encryption cipher using key from settings"""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if not key:
        # Generate a fallback key for development
        key = Fernet.generate_key().decode()
    
    # Ensure key is in correct format
    if isinstance(key, str):
        key = key.encode()
    
    # Validate and return cipher
    try:
        return Fernet(key)
    except Exception:
        # If key is invalid, generate a new one
        new_key = Fernet.generate_key()
        print(f"Warning: Invalid encryption key, using generated key: {new_key.decode()}")
        return Fernet(new_key)

def encrypt_sensitive_data(value):
    """Encrypt sensitive data before storing"""
    if not value:
        return None
    try:
        cipher = get_cipher()
        return cipher.encrypt(value.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return value  # Return original if encryption fails

def decrypt_sensitive_data(encrypted_value):
    """Decrypt sensitive data when accessing"""
    if not encrypted_value:
        return None
    try:
        cipher = get_cipher()
        return cipher.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return encrypted_value  # Return original if decryption fails

def get_tax_id_last4(tax_id):
    """Get last 4 digits of tax ID for partial display"""
    if tax_id and len(tax_id) >= 4:
        return tax_id[-4:]
    return ''
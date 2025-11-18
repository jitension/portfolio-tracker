"""
Encryption utilities for securely storing Robinhood credentials.
Uses Fernet (symmetric encryption) with AES-256.
"""
import json
from typing import Dict
from cryptography.fernet import Fernet
from django.conf import settings


class CredentialEncryption:
    """
    Encrypt and decrypt Robinhood credentials using Fernet (AES-256).
    
    The encryption key should be stored securely in environment variables
    and never committed to version control.
    """
    
    def __init__(self):
        """Initialize the encryption cipher with the configured key."""
        if not settings.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY not configured. Please set it in environment variables."
            )
        
        self.key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, credentials: Dict[str, str]) -> str:
        """
        Encrypt credentials dictionary to a string.
        
        Args:
            credentials: Dictionary containing 'username' and 'password'
                        Example: {'username': 'user@example.com', 'password': 'pass123'}
        
        Returns:
            Base64 encoded encrypted string
        
        Raises:
            ValueError: If credentials dict is invalid
            Exception: If encryption fails
        """
        if not isinstance(credentials, dict):
            raise ValueError("Credentials must be a dictionary")
        
        if 'username' not in credentials or 'password' not in credentials:
            raise ValueError("Credentials must contain 'username' and 'password' keys")
        
        try:
            # Convert to JSON string
            json_data = json.dumps(credentials)
            
            # Encrypt
            encrypted = self.cipher.encrypt(json_data.encode())
            
            # Return as string
            return encrypted.decode()
        
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> Dict[str, str]:
        """
        Decrypt credentials string back to dictionary.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
        
        Returns:
            Dictionary containing 'username' and 'password'
        
        Raises:
            Exception: If decryption fails or data is corrupted
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")
        
        try:
            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            
            # Parse JSON
            credentials = json.loads(decrypted.decode())
            
            # Validate structure
            if not isinstance(credentials, dict):
                raise ValueError("Decrypted data is not a valid dictionary")
            
            if 'username' not in credentials or 'password' not in credentials:
                raise ValueError("Decrypted data missing required keys")
            
            return credentials
        
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")


def encrypt_credentials(username: str, password: str) -> str:
    """
    Helper function to encrypt Robinhood credentials.
    
    Args:
        username: Robinhood username/email
        password: Robinhood password
    
    Returns:
        Encrypted credentials string
    """
    encryption = CredentialEncryption()
    return encryption.encrypt({
        'username': username,
        'password': password
    })


def decrypt_credentials(encrypted_data: str) -> Dict[str, str]:
    """
    Helper function to decrypt Robinhood credentials.
    
    Args:
        encrypted_data: Encrypted credentials string
    
    Returns:
        Dictionary with 'username' and 'password'
    """
    encryption = CredentialEncryption()
    return encryption.decrypt(encrypted_data)


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.
    Use this to generate the ENCRYPTION_KEY for your environment.
    
    Returns:
        Base64 encoded encryption key as string
    
    Example:
        >>> key = generate_encryption_key()
        >>> print(f"Add this to your .env file: ENCRYPTION_KEY={key}")
    """
    return Fernet.generate_key().decode()

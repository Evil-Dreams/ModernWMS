"""
Hashing utilities for the application.

This module provides various hashing functions for different purposes,
including password hashing and verification.
"""
import hashlib
import os
import binascii
import base64
from typing import Optional, Tuple

# Constants for password hashing
SALT_LENGTH = 16
HASH_ITERATIONS = 100000
HASH_ALGORITHM = 'sha256'


def md5_hex(text: str) -> str:
    """
    Generate an MD5 hash of the input text.
    
    Note: MD5 should not be used for password hashing in new applications.
    This is maintained for compatibility with legacy systems.
    
    Args:
        text: The text to hash
        
    Returns:
        str: The MD5 hash as a hexadecimal string
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_salt(length: int = SALT_LENGTH) -> str:
    """
    Generate a random salt for password hashing.
    
    Args:
        length: The length of the salt in bytes
        
    Returns:
        str: A URL-safe base64-encoded salt
    """
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password with a salt using PBKDF2.
    
    If no salt is provided, a new one will be generated.
    
    Args:
        password: The password to hash
        salt: Optional salt (if None, a new one will be generated)
        
    Returns:
        tuple: (hashed_password, salt)
    """
    if salt is None:
        salt = generate_salt()
    
    # Ensure the password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Hash the password with the salt
    hashed = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode('utf-8'),
        salt.encode('utf-8'),
        HASH_ITERATIONS
    )
    
    # Encode the hash as base64
    hashed_b64 = base64.b64encode(hashed).decode('utf-8')
    
    return f"pbkdf2:{HASH_ALGORITHM}:{HASH_ITERATIONS}${hashed_b64}", salt


def verify_password(stored_hash: str, provided_password: str, salt: str) -> bool:
    """
    Verify a password against a stored hash and salt.
    
    Args:
        stored_hash: The stored password hash
        provided_password: The password to verify
        salt: The salt used for the stored hash
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    # For backward compatibility with MD5 hashes
    if ':' not in stored_hash:
        return md5_hex(provided_password) == stored_hash
    
    # Parse the stored hash
    try:
        _, algorithm, iterations_hash = stored_hash.split(':')
        iterations, stored_hash_value = iterations_hash.split('$')
        iterations = int(iterations)
    except (ValueError, AttributeError):
        return False
    
    # Hash the provided password with the same parameters
    hashed = hashlib.pbkdf2_hmac(
        algorithm,
        provided_password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    
    # Compare the hashes
    return base64.b64encode(hashed).decode('utf-8') == stored_hash_value


def is_strong_password(password: str) -> Tuple[bool, str]:
    """
    Check if a password meets complexity requirements.
    
    Args:
        password: The password to check
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/`~" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""

"""
Tests for Security utilities.
Covers encryption, decryption, and password hashing.
"""
import pytest
from app.core.security import (
    encrypt_data,
    decrypt_data,
    get_password_hash,
    verify_password
)


def test_encrypt_decrypt():
    """Test encryption and decryption round-trip."""
    original_data = "sensitive_bank_details_12345"
    
    encrypted = encrypt_data(original_data)
    decrypted = decrypt_data(encrypted)
    
    assert decrypted == original_data
    assert encrypted != original_data  # Encrypted should be different


def test_encrypt_different_each_time():
    """Test that encryption produces different output each time."""
    data = "same_data"
    
    encrypted1 = encrypt_data(data)
    encrypted2 = encrypt_data(data)
    
    # Fernet encryption includes timestamp, so outputs should differ
    assert encrypted1 != encrypted2
    
    # But both should decrypt to the same value
    assert decrypt_data(encrypted1) == data
    assert decrypt_data(encrypted2) == data


def test_decrypt_invalid_data():
    """Test that decrypting invalid data raises exception."""
    with pytest.raises(Exception):
        decrypt_data("invalid_encrypted_data")


def test_password_hashing():
    """Test password hashing and verification."""
    password = "secure_password123"
    
    hashed = get_password_hash(password)
    
    # Hashed should be different from original
    assert hashed != password
    
    # Verification should succeed
    assert verify_password(password, hashed) is True


def test_password_verification_failure():
    """Test that wrong password fails verification."""
    password = "correct_password"
    wrong_password = "wrong_password"
    
    hashed = get_password_hash(password)
    
    # Wrong password should fail
    assert verify_password(wrong_password, hashed) is False


def test_hash_different_each_time():
    """Test that hashing produces different output each time (due to salt)."""
    password = "same_password"
    
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Bcrypt includes random salt, so hashes should differ
    assert hash1 != hash2
    
    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True

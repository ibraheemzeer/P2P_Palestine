"""
Rate Limiter Configuration for P2P Palestine
Uses slowapi to implement rate limiting protection
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the limiter using remote address as the key
limiter = Limiter(key_func=get_remote_address)

"""
Pydantic configuration for P2P Palestine.
"""
from pydantic import ConfigDict

# Pydantic v2 configuration
class BaseConfig:
    """Base configuration for all Pydantic models."""
    from_attributes = True
    populate_by_name = True

"""
Exporters Module

Handles exporting recommendations to various music systems:
- Roon integration for automatic playlist creation
- Real-time playlist synchronization
- Zone-specific recommendations
"""

from .roon_client import RoonClient
from .roon_integration import RoonIntegration

__all__ = ['RoonClient', 'RoonIntegration'] 
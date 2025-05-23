"""
Common classes for the Energy Forecast domain of the Edge Mining application.
"""

from typing import NewType
import uuid

ForecastId = NewType("ForecastId", uuid.UUID)

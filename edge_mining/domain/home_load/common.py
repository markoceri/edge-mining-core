"""
Common classes for the Home Load domain of the Edge Mining application.
"""

from typing import NewType
import uuid

HomeLoadId = NewType("HomeLoadId", uuid.UUID)

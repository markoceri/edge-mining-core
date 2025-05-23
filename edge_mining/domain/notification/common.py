"""
Common classes for the Notification domain of the Edge Mining application.
"""

from typing import NewType
import uuid

NotificationId = NewType("NotificationId", uuid.UUID)

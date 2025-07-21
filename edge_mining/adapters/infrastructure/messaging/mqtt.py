import time
import datetime
import threading
import paho.mqtt.client as mqtt
from typing import Optional, Dict, Any, Tuple

class BaseMQTTBus():
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        username: Optional[str],
        password: Optional[str],
        client_id: str,
        topics: Dict[str, Optional[str]], # Map internal name to topic string
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client_id = f"{client_id}-{int(time.time())}" # Add timestamp for more uniqueness
        self.topics_map = {k: v for k, v in topics.items() if v} # Ignore not configured topics

        self._latest_values: Dict[str, Any] = {} # Conserva l'ultimo valore per nome interno sensore
        self._last_update_times: Dict[str, datetime] = {} # Conserva timestamp ultima ricezione
        self._lock = threading.Lock() # Protegge accesso a _latest_values e _last_update_times
        self._connected = threading.Event() # Segnala se connesso
        self._client: Optional[mqtt.Client] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

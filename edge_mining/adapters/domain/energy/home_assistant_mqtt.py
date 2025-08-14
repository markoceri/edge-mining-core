import logging
import math
import ssl  # Per TLS
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import paho.mqtt.client as mqtt

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter
from edge_mining.domain.energy.ports import EnergyMonitorPort
from edge_mining.domain.energy.value_objects import BatteryState, EnergyStateSnapshot
from edge_mining.shared.logging.port import LoggerPort

logger = logging.getLogger(__name__)


class MqttEnergyMonitor(EnergyMonitorPort):
    """
    Fetches energy data by subscribing to topics on an MQTT broker.

    It maintains the latest received values internally and returns a snapshot
    when get_current_energy_state is called.
    """

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        username: Optional[str],
        password: Optional[str],
        client_id: str,
        topics: Dict[str, Optional[str]],  # Map internal name to topic string
        units: Dict[str, str],
        conventions: Dict[str, bool],
        battery_capacity_wh: Optional[float],
        max_data_age_seconds: int,
        logger: LoggerPort = None,
    ):
        super().__init__(energy_monitor_type=EnergyMonitorAdapter.HOME_ASSISTANT_MQTT)

        self.logger = logger

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client_id = (
            f"{client_id}-{int(time.time())}"  # Aggiungi timestamp per maggiore unicità
        )
        self.topics_map = {
            k: v for k, v in topics.items() if v
        }  # Ignora topic non configurati
        self.units_map = units
        self.conventions = conventions
        self.battery_capacity = (
            WattHours(battery_capacity_wh) if battery_capacity_wh else None
        )
        self.max_data_age = timedelta(seconds=max_data_age_seconds)

        self._latest_values: Dict[str, Any] = (
            {}
        )  # Conserva l'ultimo valore per nome interno sensore
        self._last_update_times: Dict[str, datetime] = (
            {}
        )  # Conserva timestamp ultima ricezione
        self._lock = (
            threading.Lock()
        )  # Protegge accesso a _latest_values e _last_update_times
        self._connected = threading.Event()  # Segnala se connesso
        self._client: Optional[mqtt.Client] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        logger.info(f"Initializing MqttEnergyMonitor for {broker_host}:{broker_port}")
        logger.debug(f"Client ID: {self.client_id}")
        logger.debug(f"Topics configured: {self.topics_map}")
        logger.debug(f"Units: {self.units_map}")
        logger.debug(f"Conventions: {self.conventions}")
        if self.battery_capacity:
            logger.debug(f"Static Battery Capacity: {self.battery_capacity} Wh")
        logger.debug(f"Max data age: {self.max_data_age_seconds} seconds")

        if not self.topics_map:
            logger.warning(
                "MQTT Energy Monitor initialized, but no topics were configured."
            )
            # L'adapter funzionerà ma non riceverà dati

        self._setup_client()

    def _setup_client(self):
        """Configura il client MQTT e avvia il loop in un thread separato."""
        try:
            # Usare MQTTv5 se possibile, altrimenti fallback
            try:
                self._client = mqtt.Client(
                    client_id=self.client_id, protocol=mqtt.MQTTv5
                )
                logger.debug("Using MQTTv5 protocol.")
            except ValueError:
                logger.warning(
                    "MQTTv5 not supported by paho-mqtt version or broker? Falling back to v3.1.1."
                )
                self._client = mqtt.Client(client_id=self.client_id)  # Default (v3.1.1)

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            self._client.on_log = self._on_log  # Opzionale, per debug paho

            if self.username:
                self._client.username_pw_set(self.username, self.password)

            # Gestione TLS (basica, aggiungere più opzioni se necessario)
            if self.broker_port == 8883:  # Porta standard per MQTTS
                logger.info("Configuring TLS for MQTT connection (port 8883 detected).")
                # Usare certs di default del sistema operativo
                self._client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
                # Per certs custom: self._client.tls_set(ca_certs="ca.crt", certfile="client.crt", keyfile="client.key")

            logger.info(
                f"Connecting MQTT client to {self.broker_host}:{self.broker_port}..."
            )
            self._client.connect_async(self.broker_host, self.broker_port, 60)

            # Avvia il loop di rete in un thread separato
            self._thread = threading.Thread(target=self._mqtt_loop, daemon=True)
            self._thread.start()

        except Exception as e:
            logger.error(f"Failed to setup MQTT client: {e}")
            self._client = None  # Assicurati che sia None se fallisce

    def _mqtt_loop(self):
        """Funzione eseguita nel thread per mantenere il loop MQTT."""
        if not self._client:
            return
        logger.info("MQTT client loop started.")
        while not self._stop_event.is_set():
            try:
                # loop() gestisce la rete e i timeout per noi
                rc = self._client.loop(timeout=1.0)
                if rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.warning(
                        f"MQTT loop returned error code: {rc}. Attempting to handle."
                    )
                    # Paho tenta di riconnettersi automaticamente, ma potremmo aggiungere logica qui
                    time.sleep(5)  # Aspetta prima di riprovare il loop
            except Exception as e:
                logger.error(f"Exception in MQTT loop: {e}")
                # In caso di errore grave, prova a riconnettere dopo una pausa
                if not self._stop_event.is_set():
                    time.sleep(10)
                    try:
                        if not self._client.is_connected():
                            logger.info("Attempting to reconnect MQTT client...")
                            self._client.reconnect()
                    except Exception as reconn_e:
                        logger.error(f"Failed to manually reconnect MQTT: {reconn_e}")

        logger.info("MQTT client loop stopped.")
        if self._client.is_connected():
            logger.debug("Disconnecting MQTT client cleanly.")
            self._client.disconnect()

    def stop(self):
        """Ferma il loop MQTT e disconnette il client."""
        logger.info("Stopping MQTT Energy Monitor...")
        self._stop_event.set()
        if self._client:
            # Non chiamare disconnect qui, loop_stop lo fa se necessario
            # Chiamare loop_stop aspetta che il thread finisca il ciclo corrente
            self._client.loop_stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)  # Aspetta che il thread termini
            if self._thread.is_alive():
                logger.warning("MQTT loop thread did not stop gracefully.")
        logger.info("MQTT Energy Monitor stopped.")

    def _on_log(self, client, userdata, level, buf):
        """Callback per i log interni di paho-mqtt."""
        # Mappa i livelli di paho a quelli di logging di Python se necessario
        if level == mqtt.MQTT_LOG_ERR:
            logger.error(f"PAHO-MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            logger.warning(f"PAHO-MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_INFO:
            logger.info(f"PAHO-MQTT: {buf}")
        else:  # MQTT_LOG_DEBUG, MQTT_LOG_NOTICE
            logger.debug(f"PAHO-MQTT: {buf}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback quando la connessione al broker è stabilita."""
        if rc == 0:
            logger.info(
                f"Successfully connected to MQTT broker: {self.broker_host}:{self.broker_port}"
            )
            self._connected.set()  # Segnala connessione avvenuta
            # Iscriviti ai topic configurati
            for internal_name, topic in self.topics_map.items():
                if topic:
                    logger.info(f"Subscribing to topic '{topic}' for '{internal_name}'")
                    # Usare QoS 1 per maggiore affidabilità se il broker lo supporta bene
                    result, mid = client.subscribe(topic, qos=1)
                    if result != mqtt.MQTT_ERR_SUCCESS:
                        logger.error(
                            f"Failed to subscribe to topic '{topic}': {mqtt.error_string(result)}"
                        )
                    else:
                        logger.debug(
                            f"Subscription request sent for '{topic}' (MID: {mid})"
                        )

        else:
            logger.error(f"Failed to connect to MQTT broker: {mqtt.connack_string(rc)}")
            self._connected.clear()

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Callback quando la connessione viene persa."""
        self._connected.clear()
        logger.warning(
            f"Disconnected from MQTT broker (rc: {rc}). Reconnection should be attempted automatically by Paho."
        )

    def _on_message(self, client, userdata, msg):
        """Callback quando un messaggio viene ricevuto da un topic sottoscritto."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.debug(f"MQTT message received: Topic='{topic}', Payload='{payload}'")

            # Trova a quale sensore interno corrisponde questo topic
            internal_name = None
            for name, configured_topic in self.topics_map.items():
                # Usare `mqtt.topic_matches_sub` per gestire wildcard se necessario in futuro
                if configured_topic == topic:
                    internal_name = name
                    break

            if internal_name:
                # Processa il payload in base al tipo di sensore
                parsed_value = None
                unit = self.units_map.get(internal_name, "W").lower()  # Default a Watts

                if internal_name in [
                    "solar_production",
                    "house_consumption",
                    "grid_power",
                    "battery_power",
                ]:
                    parsed_value = self._parse_power(payload, unit, topic)
                    # Applica convenzioni per grid e battery
                    if internal_name == "grid_power" and parsed_value is not None:
                        if self.conventions.get("grid_positive_export", False):
                            parsed_value = -parsed_value  # Vogliamo positivo per import
                    elif internal_name == "battery_power" and parsed_value is not None:
                        if not self.conventions.get("battery_positive_charge", True):
                            parsed_value = -parsed_value  # Vogliamo positivo per carica

                elif internal_name == "battery_soc":
                    parsed_value = self._parse_percentage(payload, topic)

                else:
                    logger.warning(
                        f"Received message for unhandled internal sensor name: '{internal_name}'"
                    )

                # Aggiorna lo stato interno in modo thread-safe
                if parsed_value is not None:
                    with self._lock:
                        self._latest_values[internal_name] = parsed_value
                        self._last_update_times[internal_name] = datetime.now(
                            timezone.utc
                        )  # Usa UTC
                        logger.debug(
                            f"Stored '{internal_name}' = {parsed_value} (Timestamp: {self._last_update_times[internal_name]})"
                        )
                else:
                    logger.warning(
                        f"Could not parse value for topic '{topic}', payload '{payload}'"
                    )

            else:
                logger.warning(f"Received message on unexpected topic: '{topic}'")

        except Exception as e:
            logger.error(f"Error processing MQTT message (Topic: {msg.topic}): {e}")

    def _parse_power(
        self,
        state: Optional[str],
        configured_unit: str,
        entity_id_for_log: str,
    ) -> Optional[Watts]:
        """Helper per parsare valori di potenza."""
        if state is None:
            return None
        try:
            value = float(state)
            if math.isnan(value):
                return None
            if configured_unit == "kw":
                value *= 1000
            elif configured_unit != "w":
                logger.warning(
                    f"Unsupported unit '{configured_unit}' for topic '{entity_id_for_log}'. Assuming Watts."
                )
            return Watts(value)
        except (ValueError, TypeError):
            return None

    def _parse_percentage(
        self, state: Optional[str], entity_id_for_log: str
    ) -> Optional[Percentage]:
        """Helper per parsare valori percentuali."""
        if state is None:
            return None
        try:
            value = float(state)
            if math.isnan(value):
                return None
            return Percentage(max(0.0, min(100.0, value)))  # Clamp 0-100
        except (ValueError, TypeError):
            return None

    def get_current_energy_state(self) -> Optional[EnergyStateSnapshot]:
        """
        Restituisce l'ultimo stato energetico conosciuto basato sui messaggi MQTT ricevuti.
        Controlla anche se i dati sono troppo vecchi.
        """
        if not self._connected.is_set():
            logger.warning("MQTT client not connected. Cannot provide energy state.")
            # Potremmo provare a leggere valori vecchi, ma è rischioso. Meglio None.
            return None

        # Accedi ai valori più recenti in modo sicuro
        with self._lock:
            latest_values = self._latest_values.copy()
            last_update_times = self._last_update_times.copy()

        now = datetime.now(timezone.utc)
        snapshot_time = Timestamp(
            now.astimezone()
        )  # Converti a timezone locale per snapshot
        has_critical_error = False
        is_stale = False

        # Helper per ottenere valore e controllare età
        def get_value(name: str) -> Tuple[Optional[Any], bool]:
            nonlocal is_stale
            value = latest_values.get(name)
            last_update = last_update_times.get(name)
            stale = False
            if self.topics_map.get(name):  # Solo se il topic è configurato
                if value is None:
                    logger.warning(
                        f"No value received yet for sensor '{name}' (Topic: {self.topics_map.get(name)})"
                    )
                    # Consideralo errore solo se è un sensore fondamentale?
                    # Per ora, non lo consideriamo errore critico se non è MAI arrivato
                elif last_update is None or (now - last_update) > self.max_data_age:
                    logger.warning(
                        f"Data for sensor '{name}' is stale (Last update: {last_update}, Age: {now - last_update if last_update else 'N/A'})"
                    )
                    is_stale = True
                    stale = True
                    # Consideriamo i dati stantii come non disponibili per il calcolo?
                    # Dipende dalla criticità. Per ora li usiamo ma logghiamo.
                    # Potremmo scegliere di restituire None per il valore qui.

            return value, stale

        # Recupera i valori e controlla la loro età
        production, stale_prod = get_value("solar_production")
        consumption, stale_cons = get_value("house_consumption")
        grid_power, stale_grid = get_value("grid_power")
        battery_soc, stale_soc = get_value("battery_soc")
        battery_power, stale_power = get_value("battery_power")

        # Verifica se i dati *richiesti* (configurati) sono mancanti (mai arrivati)
        if self.topics_map.get("solar_production") and production is None:
            logger.error(
                f"Missing critical value: Solar Production (Topic: {self.topics_map['solar_production']})"
            )
            has_critical_error = True
        if self.topics_map.get("house_consumption") and consumption is None:
            logger.error(
                f"Missing critical value: House Consumption (Topic: {self.topics_map['house_consumption']})"
            )
            has_critical_error = True
        if self.topics_map.get("grid_power") and grid_power is None:
            logger.error(
                f"Missing critical value: Grid Power (Topic: {self.topics_map['grid_power']})"
            )
            has_critical_error = True
        # Batteria è critica solo se SOC e Power sono entrambi richiesti e mancanti
        if self.topics_map.get("battery_soc") and self.topics_map.get("battery_power"):
            if battery_soc is None:
                logger.error(
                    f"Missing critical value: Battery SOC (Topic: {self.topics_map['battery_soc']})"
                )
                has_critical_error = True
            if battery_power is None:
                logger.error(
                    f"Missing critical value: Battery Power (Topic: {self.topics_map['battery_power']})"
                )
                has_critical_error = True

        if has_critical_error:
            logger.error(
                "One or more critical energy values were never received via MQTT. Cannot create snapshot."
            )
            return None

        if is_stale:
            logger.warning(
                "One or more sensor values are stale. Using last known values, but they might be inaccurate."
            )
            # Decisione: Continuare con dati stantii o restituire None? Per ora continuiamo.
            # if is_stale: return None # Opzione più sicura

        # Riempi defaults se non configurati o mancanti (ma non critici)
        production = production if production is not None else Watts(0.0)
        consumption = consumption if consumption is not None else Watts(0.0)
        grid_power = grid_power if grid_power is not None else Watts(0.0)

        # Costruisci BatteryState se possibile
        battery_state: Optional[BatteryState] = None
        if (
            battery_soc is not None
            and battery_power is not None
            and self.battery_capacity is not None
        ):
            battery_state = BatteryState(
                state_of_charge=battery_soc,
                nominal_capacity=self.battery_capacity,
                current_power=battery_power,
                timestamp=snapshot_time,  # Usiamo il tempo dello snapshot
            )
        elif self.topics_map.get("battery_soc"):
            logger.debug(
                "Battery SOC topic configured, but full BatteryState cannot be created (missing power topic/value or static capacity setting?)."
            )

        snapshot = EnergyStateSnapshot(
            production=production,
            consumption=consumption,
            battery=battery_state,
            grid_power=grid_power,
            timestamp=snapshot_time,
        )

        logger.info(
            f"MQTT Monitor: State Snapshot: Prod={snapshot.production:.0f}W, "
            f"Cons={snapshot.consumption:.0f}W, Grid={snapshot.grid_power:.0f}W, "
            f"SOC={snapshot.battery.state_of_charge if snapshot.battery else 'N/A'}%, "
            f"BattPwr={snapshot.battery.current_power if snapshot.battery else 'N/A'}W "
            f"(Stale: {is_stale})"
        )

        return snapshot

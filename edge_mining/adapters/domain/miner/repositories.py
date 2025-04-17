import copy
import sqlite3
from typing import List, Optional, Dict

from edge_mining.domain.common import Watts
from edge_mining.domain.exceptions import MinerError

from edge_mining.domain.miner.common import MinerId, MinerStatus
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.ports import MinerRepository

from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository

# Simple In-Memory implementation for testing and basic use

class InMemoryMinerRepository(MinerRepository):
    def __init__(self, initial_miners: Optional[Dict[MinerId, Miner]] = None):
        self._miners: Dict[MinerId, Miner] = copy.deepcopy(initial_miners) if initial_miners else {}

    def add(self, miner: Miner) -> None:
        if miner.id in self._miners:
             # Handle update or raise error depending on desired behavior
             print(f"Warning: Miner {miner.id} already exists, overwriting.")
        self._miners[miner.id] = copy.deepcopy(miner)

    def get_by_id(self, miner_id: MinerId) -> Optional[Miner]:
        return copy.deepcopy(self._miners.get(miner_id))

    def get_all(self) -> List[Miner]:
        return [copy.deepcopy(m) for m in self._miners.values()]

    def update(self, miner: Miner) -> None:
        if miner.id not in self._miners:
            raise ValueError(f"Miner {miner.id} not found for update.")
        self._miners[miner.id] = copy.deepcopy(miner)

    def remove(self, miner_id: MinerId) -> None:
        if miner_id in self._miners:
            del self._miners[miner_id]

class SqliteMinerRepository(BaseSqliteRepository, MinerRepository):

    def _row_to_miner(self, row: sqlite3.Row) -> Optional[Miner]:
        if not row:
            return None
        try:
            return Miner(
                id=MinerId(row["id"]),
                name=row["name"],
                ip_address=row["ip_address"],
                status=MinerStatus(row["status"]),
                power_consumption=Watts(row["power_consumption"]) if row["power_consumption"] is not None else None
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Errore nel deserializzare Miner dalla riga DB: {row}. Errore: {e}")
            return None

    def add(self, miner: Miner) -> None:
        self.logger.debug(f"Adding miner {miner.id} to SQLite.")
        
        sql = """
            INSERT INTO miners (id, name, ip_address, status, power_consumption)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(sql, (
                    miner.id,
                    miner.name,
                    miner.ip_address,
                    miner.status.value,
                    float(miner.power_consumption) if miner.power_consumption is not None else None
                ))
        except sqlite3.IntegrityError as e:
             self.logger.error(f"Errore di integrità aggiungendo miner {miner.id}: {e}")
             # Potrebbe significare che l'ID esiste già
             raise MinerError(f"Miner con ID {miner.id} esiste già o violazione constraint: {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite aggiungendo miner {miner.id}: {e}")
            raise MinerError(f"Errore DB aggiungendo miner: {e}") from e
        finally:
            if conn: conn.close()

    def get_by_id(self, miner_id: MinerId) -> Optional[Miner]:
        self.logger.debug(f"Getting miner {miner_id} from SQLite.")
        
        sql = "SELECT * FROM miners WHERE id = ?"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (miner_id,))
            row = cursor.fetchone()
            return self._row_to_miner(row)
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite ottenendo miner {miner_id}: {e}")
            return None # O sollevare eccezione? Restituire None è più tollerante
        finally:
             if conn: conn.close()

    def get_all(self) -> List[Miner]:
        self.logger.debug("Getting all miners from SQLite.")
        
        sql = "SELECT * FROM miners"
        conn = self._get_connection()
        miners = []
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                 miner = self._row_to_miner(row)
                 if miner:
                     miners.append(miner)
            return miners
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite ottenendo tutti i miner: {e}")
            return []
        finally:
            if conn: conn.close()

    def update(self, miner: Miner) -> None:
        self.logger.debug(f"Updating miner {miner.id} in SQLite.")
        
        sql = """
            UPDATE miners
            SET name = ?, ip_address = ?, status = ?, power_consumption = ?
            WHERE id = ?
        """
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    miner.name,
                    miner.ip_address,
                    miner.status.value,
                    float(miner.power_consumption) if miner.power_consumption is not None else None,
                    miner.id
                ))
                if cursor.rowcount == 0:
                     raise MinerError(f"Nessun miner trovato con ID {miner.id} per aggiornare.")
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite aggiornando miner {miner.id}: {e}")
            raise MinerError(f"Errore DB aggiornando miner: {e}") from e
        finally:
            if conn: conn.close()

    def remove(self, miner_id: MinerId) -> None:
        self.logger.debug(f"Removing miner {miner_id} from SQLite.")
        
        sql = "DELETE FROM miners WHERE id = ?"
        conn = self._get_connection()
        try:
            with conn:
                 cursor = conn.cursor()
                 cursor.execute(sql, (miner_id,))
                 if cursor.rowcount == 0:
                      self.logger.warning(f"Tentativo di rimuovere miner inesistente con ID {miner_id}.")
                      # Non c'è bisogno di sollevare eccezione qui, la rimozione di un non esistente è idempotente
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite rimuovendo miner {miner_id}: {e}")
            raise MinerError(f"Errore DB rimuovendo miner: {e}") from e
        finally:
            if conn: conn.close()
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
            self.logger.error(f"Error deserializing Miner from DB row: {row}. Errorr: {e}")
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
             self.logger.error(f"Integrity error adding miner {miner.id}: {e}")
             # Potrebbe significare che l'ID esiste già
             raise MinerError(f"Miner with ID {miner.id} already exists or constraint violation: {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding miner {miner.id}: {e}")
            raise MinerError(f"DB error adding miner: {e}") from e
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
            self.logger.error(f"SQLite error getting miner {miner_id}: {e}")
            return None # Or raise exception? Returning None is more forgiving
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
            self.logger.error(f"SQLite error getting all miners: {e}")
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
                     raise MinerError(f"No miner found with ID {miner.id} for update.")
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating miner {miner.id}: {e}")
            raise MinerError(f"DB error updating miner: {e}") from e
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
                      self.logger.warning(f"Attempt to remove non-existent miner with ID {miner_id}.")
                      # There is no need to raise an exception here, removing a non-existent is idempotent.
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing miner {miner_id}: {e}")
            raise MinerError(f"DB error removing miner: {e}") from e
        finally:
            if conn: conn.close()
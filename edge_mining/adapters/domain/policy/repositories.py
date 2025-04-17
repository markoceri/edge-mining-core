import copy
import uuid
import json
import sqlite3
from typing import List, Optional, Dict, Any

from edge_mining.domain.common import EntityId
from edge_mining.domain.exceptions import PolicyError
from edge_mining.domain.miner.common import MinerId
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy, AutomationRule
from edge_mining.domain.policy.common import MiningDecision
from edge_mining.domain.policy.ports import OptimizationPolicyRepository

from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository

# Simple In-Memory implementation for testing and basic use

class InMemoryOptimizationPolicyRepository(OptimizationPolicyRepository):
    def __init__(self, initial_policies: Optional[Dict[EntityId, OptimizationPolicy]] = None):
        self._policies: Dict[EntityId, OptimizationPolicy] = copy.deepcopy(initial_policies) if initial_policies else {}

    def add(self, policy: OptimizationPolicy) -> None:
        if policy.id in self._policies:
             print(f"Warning: Policy {policy.id} already exists, overwriting.")
        self._policies[policy.id] = copy.deepcopy(policy)

    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        return copy.deepcopy(self._policies.get(policy_id))

    def get_active_policy(self) -> Optional[OptimizationPolicy]:
        for policy in self._policies.values():
            if policy.is_active:
                return copy.deepcopy(policy)
        return None

    def get_all(self) -> List[OptimizationPolicy]:
        return [copy.deepcopy(p) for p in self._policies.values()]

    def update(self, policy: OptimizationPolicy) -> None:
        if policy.id not in self._policies:
            raise ValueError(f"Policy {policy.id} not found for update.")
        # Ensure only one policy is active if is_active is being set to True
        if policy.is_active:
            for p_id, p in self._policies.items():
                if p_id != policy.id and p.is_active:
                    p.is_active = False # Deactivate others
        self._policies[policy.id] = copy.deepcopy(policy)

class SqliteOptimizationPolicyRepository(BaseSqliteRepository, OptimizationPolicyRepository):

    def _dict_to_rule(self, data: Dict[str, Any]) -> AutomationRule:
        # Deserializza un dizionario (da JSON) in un oggetto AutomationRule
        return AutomationRule(
            id=uuid.UUID(data['id']), # Converte stringa UUID
            name=data['name'],
            conditions=data['conditions'],
            action=MiningDecision(data['action']) # Converte valore Enum
        )

    def _rule_to_dict(self, rule: AutomationRule) -> Dict[str, Any]:
         # Serializza un oggetto AutomationRule in un dizionario per JSON
         return {
             'id': str(rule.id),
             'name': rule.name,
             'conditions': rule.conditions,
             'action': rule.action.value
         }

    def _row_to_policy(self, row: sqlite3.Row) -> Optional[OptimizationPolicy]:
        if not row:
            return None
        try:
            # Deserializza le liste JSON di regole e target IDs
            start_rules_data = json.loads(row["start_rules"] or '[]')
            stop_rules_data = json.loads(row["stop_rules"] or '[]')
            target_ids_data = json.loads(row["target_miner_ids"] or '[]')

            start_rules = [self._dict_to_rule(r) for r in start_rules_data]
            stop_rules = [self._dict_to_rule(r) for r in stop_rules_data]
            target_ids = [MinerId(tid) for tid in target_ids_data]

            return OptimizationPolicy(
                id=row["id"], # UUID è già convertito da detect_types
                name=row["name"],
                description=row["description"],
                is_active=bool(row["is_active"]),
                start_rules=start_rules,
                stop_rules=stop_rules,
                target_miner_ids=target_ids
            )
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Errore nel deserializzare Policy dalla riga DB: {dict(row)}. Errore: {e}", exc_info=True)
            return None

    def add(self, policy: OptimizationPolicy) -> None:
        self.logger.debug(f"Adding policy '{policy.name}' ({policy.id}) to SQLite.")
        sql = """
            INSERT INTO policies (id, name, description, is_active, start_rules, stop_rules, target_miner_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        conn = self._get_connection()
        try:
            # Serializza le regole e i target IDs in JSON
            start_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.start_rules])
            stop_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.stop_rules])
            target_ids_json = json.dumps([str(tid) for tid in policy.target_miner_ids])

            with conn:
                conn.execute(sql, (
                    policy.id, # UUID
                    policy.name,
                    policy.description,
                    1 if policy.is_active else 0,
                    start_rules_json,
                    stop_rules_json,
                    target_ids_json
                ))
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Errore di integrità aggiungendo policy '{policy.name}': {e}")
            raise PolicyError(f"Policy con ID {policy.id} o nome '{policy.name}' esiste già: {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite aggiungendo policy '{policy.name}': {e}")
            raise PolicyError(f"Errore DB aggiungendo policy: {e}") from e
        finally:
            if conn: conn.close()

    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        self.logger.debug(f"Getting policy {policy_id} from SQLite.")
        sql = "SELECT * FROM policies WHERE id = ?"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (policy_id,)) # Passa UUID direttamente
            row = cursor.fetchone()
            return self._row_to_policy(row)
        except sqlite3.Error as e:
            self.logger.exception(f"Errore SQLite ottenendo policy {policy_id}: {e}")
            return None
        finally:
            if conn: conn.close()

    def get_active_policy(self) -> Optional[OptimizationPolicy]:
        self.logger.debug("Getting active policy from SQLite.")
        sql = "SELECT * FROM policies WHERE is_active = 1 LIMIT 1"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            return self._row_to_policy(row)
        except sqlite3.Error as e:
            self.logger.exception(f"Errore SQLite ottenendo policy attiva: {e}")
            return None
        finally:
            if conn: conn.close()

    def get_all(self) -> List[OptimizationPolicy]:
        self.logger.debug("Getting all policies from SQLite.")
        sql = "SELECT * FROM policies ORDER BY name"
        conn = self._get_connection()
        policies = []
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                policy = self._row_to_policy(row)
                if policy:
                     policies.append(policy)
            return policies
        except sqlite3.Error as e:
            self.logger.exception(f"Errore SQLite ottenendo tutte le policy: {e}")
            return []
        finally:
            if conn: conn.close()

    def update(self, policy: OptimizationPolicy) -> None:
        self.logger.debug(f"Updating policy '{policy.name}' ({policy.id}) in SQLite.")
        # Gestione attivazione: se questa policy diventa attiva, disattiva le altre
        conn = self._get_connection()
        try:
            with conn: # Transazione
                cursor = conn.cursor()
                if policy.is_active:
                    self.logger.debug(f"Deactivating other policies as '{policy.name}' becomes active.")
                    cursor.execute("UPDATE policies SET is_active = 0 WHERE id != ?", (policy.id,))

                # Ora aggiorna la policy corrente
                sql_update = """
                    UPDATE policies
                    SET name = ?, description = ?, is_active = ?, start_rules = ?, stop_rules = ?, target_miner_ids = ?
                    WHERE id = ?
                """
                start_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.start_rules])
                stop_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.stop_rules])
                target_ids_json = json.dumps([str(tid) for tid in policy.target_miner_ids])

                cursor.execute(sql_update, (
                    policy.name,
                    policy.description,
                    1 if policy.is_active else 0,
                    start_rules_json,
                    stop_rules_json,
                    target_ids_json,
                    policy.id # UUID
                ))

                if cursor.rowcount == 0:
                    raise PolicyError(f"Nessuna policy trovata con ID {policy.id} per aggiornare.")

        except sqlite3.IntegrityError as e:
            self.logger.error(f"Errore di integrità aggiornando policy '{policy.name}': {e}")
            # Potrebbe essere un conflitto sul nome UNIQUE
            raise PolicyError(f"Errore di constraint aggiornando policy (nome duplicato?): {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"Errore SQLite aggiornando policy '{policy.name}': {e}")
            raise PolicyError(f"Errore DB aggiornando policy: {e}") from e
        finally:
            if conn: conn.close()
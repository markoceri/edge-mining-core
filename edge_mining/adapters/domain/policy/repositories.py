"""
This module contains the adapter classes implementing the OptimizationPolicyRepository interface.
"""

import copy
import uuid
import json
import sqlite3
from typing import List, Optional, Dict, Any

from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.exceptions import (
    PolicyError, PolicyConfigurationError
)
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy, AutomationRule
from edge_mining.domain.policy.common import MiningDecision
from edge_mining.domain.policy.ports import OptimizationPolicyRepository

from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository

# Simple In-Memory implementation for testing and basic use

class InMemoryOptimizationPolicyRepository(OptimizationPolicyRepository):
    """In-Memory implementation of the OptimizationPolicyRepository."""
    def __init__(self, initial_policies: Optional[Dict[EntityId, OptimizationPolicy]] = None):
        self._policies: Dict[EntityId, OptimizationPolicy] = copy.deepcopy(initial_policies) if initial_policies else {}

    def add(self, policy: OptimizationPolicy) -> None:
        if policy.id in self._policies:
            print(f"Warning: Policy {policy.id} already exists, overwriting.")
        self._policies[policy.id] = copy.deepcopy(policy)

    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        return copy.deepcopy(self._policies.get(policy_id))

    def get_all(self) -> List[OptimizationPolicy]:
        return [copy.deepcopy(p) for p in self._policies.values()]

    def update(self, policy: OptimizationPolicy) -> None:
        if policy.id not in self._policies:
            raise ValueError(f"Policy {policy.id} not found for update.")
        self._policies[policy.id] = copy.deepcopy(policy)

    def remove(self, policy_id: EntityId) -> None:
        if policy_id not in self._policies:
            raise ValueError(f"Policy {policy_id} not found for removal.")
        del self._policies[policy_id]

class SqliteOptimizationPolicyRepository(OptimizationPolicyRepository):
    """SQLite implementation of the OptimizationPolicyRepository."""

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._create_tables()

    def _create_tables(self):
        """Create the necessary tables for the Optimization Policy domain if they do not exist."""
        self.logger.debug(f"Ensuring SQLite tables exist "
                        f"for Optimization Policy Repository in {self._db.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                start_rules TEXT, -- JSON list of AutomationRule dicts
                stop_rules TEXT  -- JSON list of AutomationRule dicts
            );
            """
        ]

        conn = self._db.get_connection()

        try:
            with conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)

                self.logger.debug("Optimization Policies tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise PolicyConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def _dict_to_rule(self, data: Dict[str, Any]) -> AutomationRule:
        # Deserialize a dictionary (from JSON) into an AutomationRule object
        return AutomationRule(
            id=uuid.UUID(data['id']), # Convert UUID string
            name=data['name'],
            conditions=data['conditions'],
            action=MiningDecision(data['action']) # Convert Enum value
        )

    def _rule_to_dict(self, rule: AutomationRule) -> Dict[str, Any]:
        # Serializes an AutomationRule object into a dictionary for JSON
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
            # Deserialize JSON lists of rules and target IDs
            start_rules_data = json.loads(row["start_rules"] or '[]')
            stop_rules_data = json.loads(row["stop_rules"] or '[]')

            start_rules = [self._dict_to_rule(r) for r in start_rules_data]
            stop_rules = [self._dict_to_rule(r) for r in stop_rules_data]

            return OptimizationPolicy(
                id=row["id"], # UUID is already converted by detect_types
                name=row["name"],
                description=row["description"],
                start_rules=start_rules,
                stop_rules=stop_rules
            )
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error deserializing Policy from DB line: {dict(row)}. Error: {e}")
            return None

    def add(self, policy: OptimizationPolicy) -> None:
        self.logger.debug(f"Adding policy '{policy.name}' ({policy.id}) to SQLite.")
        sql = """
            INSERT INTO policies (id, name, description, start_rules, stop_rules)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = self._db.get_connection()
        try:
            # Serialize rules and target IDs to JSON
            start_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.start_rules])
            stop_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.stop_rules])

            with conn:
                conn.execute(sql, (
                    policy.id, # UUID
                    policy.name,
                    policy.description,
                    start_rules_json,
                    stop_rules_json
                ))
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error adding policy '{policy.name}': {e}")
            raise PolicyError(f"Policy with ID {policy.id} or name '{policy.name}' already exists: {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding policy '{policy.name}': {e}")
            raise PolicyError(f"DB error adding policy: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        self.logger.debug(f"Getting policy {policy_id} from SQLite.")
        sql = "SELECT * FROM policies WHERE id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (policy_id,)) # Pass UUID directly
            row = cursor.fetchone()
            return self._row_to_policy(row)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting policy {policy_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[OptimizationPolicy]:
        self.logger.debug("Getting all policies from SQLite.")
        sql = "SELECT * FROM policies ORDER BY name"
        conn = self._db.get_connection()
        policies = []
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                policy = self._row_to_policy(row)
                if policy:
                    policies.append(policy)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting all policies: {e}")
            return []
        finally:
            if conn:
                conn.close()
        return policies

    def update(self, policy: OptimizationPolicy) -> None:
        self.logger.debug(f"Updating policy '{policy.name}' ({policy.id}) in SQLite.")
        # Activation Management: If this policy becomes active, deactivates the others
        conn = self._db.get_connection()
        try:
            with conn: # Transaction
                cursor = conn.cursor()

                # Update the current policy
                sql_update = """
                    UPDATE policies
                    SET name = ?, description = ?, start_rules = ?, stop_rules = ?
                    WHERE id = ?
                """
                start_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.start_rules])
                stop_rules_json = json.dumps([self._rule_to_dict(r) for r in policy.stop_rules])

                cursor.execute(sql_update, (
                    policy.name,
                    policy.description,
                    start_rules_json,
                    stop_rules_json,
                    policy.id # UUID
                ))

                if cursor.rowcount == 0:
                    raise PolicyError(f"No policies found with ID {policy.id}.")

        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error updating policy '{policy.name}': {e}")
            # There might be a conflict over the name UNIQUE
            raise PolicyError(f"Constraint error updating policy (duplicate name?): {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating policy '{policy.name}': {e}")
            raise PolicyError(f"EDB error updating policy: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, policy_id: EntityId) -> None:
        self.logger.debug(f"Removing policy {policy_id} from SQLite.")
        sql = "DELETE FROM policies WHERE id = ?"
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, (policy_id,))
                if cursor.rowcount == 0:
                    raise PolicyError(f"No policies found with ID {policy_id}.")
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing policy {policy_id}: {e}")
            raise PolicyError(f"DB error removing policy: {e}") from e
        finally:
            if conn:
                conn.close()

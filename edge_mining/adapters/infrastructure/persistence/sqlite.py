import sqlite3
import json

from edge_mining.shared.logging.port import LoggerPort
from edge_mining.domain.exceptions import ConfigurationError

class BaseSqliteRepository:
    def __init__(self, db_path: str, logger: LoggerPort):
        self.db_path = db_path
        self.logger = logger
        
        self._create_tables()

    def _get_connection(self):
        """Obtain a database connection."""
        try:
            # We set a timeout for blocking operations
            conn = sqlite3.connect(self.db_path, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row # Accessing columns by name
            conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign keys if used
            
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"SQLite DB connection error ({self.db_path}): {e}")
            raise ConnectionError(f"SQLite Connection Error: {e}") from e


    def _create_tables(self):
        """Create the necessary tables if they do not exist."""

        self.logger.debug(f"Ensuring SQLite tables exist in {self.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS miners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ip_address TEXT,
                status TEXT NOT NULL,
                power_consumption REAL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS policies (
                id UUID PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0,1)),
                start_rules TEXT, -- JSON list of AutomationRule dicts
                stop_rules TEXT,  -- JSON list of AutomationRule dicts
                target_miner_ids TEXT -- JSON list of MinerId strings
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY, -- e.g., 'global'
                settings_json TEXT NOT NULL -- JSON blob
            );
            """,
             """
            CREATE TABLE IF NOT EXISTS home_profiles (
                id UUID PRIMARY KEY, -- e.g., fixed UUID for default profile
                name TEXT NOT NULL,
                devices_json TEXT -- JSON Dict[EntityId_str, LoadDevice_dict]
            );
            """
            
            # Add Users table if needed
        ]
        
        conn = self._get_connection()
        
        try:
            with conn: # Context manager gestisce commit/rollback
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)
                    
                self.logger.debug("Tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()
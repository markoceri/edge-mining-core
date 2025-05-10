"""Action service for miners, energy, and optimizations."""
from typing import Optional

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.common import MinerId
from edge_mining.shared.logging.port import LoggerPort
from edge_mining.domain.exceptions import MinerError, MinerNotFoundError
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.domain.miner.ports import MinerControlPort, MinerRepository

class ActionService:
    """Handles actions on miners"""

    def __init__(
        self,
        miner_controller: MinerControlPort,
        miner_repo: MinerRepository,
        notifier: Optional[NotificationPort] = None,
        logger: LoggerPort = None
    ):
        # Domains
        self.miner_controller = miner_controller
        self.miner_repo = miner_repo
        
        # Infrastructure
        self.notifier = notifier
        self.logger = logger
    
    def _notify(self, title: str, message: str):
        """Sends a notification using the configured notifier."""
        if self.notifier:
            try:
                self.notifier.send_notification(title, message)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to send notification: {e}")

    # --- Miner Actions ---
    def start_miner(self, miner_id: MinerId) -> bool:
        """Starts the specified miner."""
        if self.logger:
            self.logger.info(f"Starting miner {miner_id}")
        
        miner: Miner = self.miner_repo.get_by_id(miner_id)
        
        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")
        
        # Update miner status from controller
        current_status = self.miner_controller.get_miner_status(miner_id)
        current_power = self.miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_power)
        
        # Persist the observed state
        self.miner_repo.update(miner)
        
        success = self.miner_controller.start_miner(miner.id)
        
        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) started successfully.")
            
            # Update domain state
            miner.turn_on()
            self.miner_repo.update(miner)
            self._notify("Edge Mining Info", f"Miner {miner.id} ({miner.name}) started.")
        else:
            self.logger.error(f"Failed to start miner {miner.id} ({miner.name}).")
        
        return success
    
    def stop_miner(self, miner_id: MinerId) -> bool:
        """Stops the specified miner."""
        if self.logger:
            self.logger.info(f"Stopping miner {miner_id}")
        
        miner: Miner = self.miner_repo.get_by_id(miner_id)
        
        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")
        
        # Update miner status from controller
        current_status = self.miner_controller.get_miner_status(miner_id)
        current_power = self.miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_power)
        
        # Persist the observed state
        self.miner_repo.update(miner)
        
        success = self.miner_controller.stop_miner(miner.id)
        
        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) stopped successfully.")
            
            # Update domain state
            miner.turn_off()
            self.miner_repo.update(miner)
            self._notify("Edge Mining Info", f"Miner {miner.id} ({miner.name}) stopped.")
        else:
            self.logger.error(f"Failed to stop miner {miner.id} ({miner.name}).")
        
        return success
    
    def get_miner_consumption(self, miner_id: MinerId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting power consumption for miner {miner_id}")
        
        miner: Miner = self.miner_repo.get_by_id(miner_id)
        
        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")
        
        # Update miner status from controller
        current_status = self.miner_controller.get_miner_status(miner_id)
        current_power = self.miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_power)
        
        # Persist the observed state
        self.miner_repo.update(miner)
        
        return current_power
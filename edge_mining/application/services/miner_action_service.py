"""Action service for miners, energy, and optimizations."""

from typing import List, Optional

from edge_mining.application.interfaces import ActionServiceInterface, AdapterServiceInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.exceptions import MinerNotFoundError
from edge_mining.domain.miner.ports import MinerControlPort, MinerRepository
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.shared.logging.port import LoggerPort


class MinerActionService(ActionServiceInterface):
    """Handles actions on miners"""

    def __init__(
        self,
        adapter_service: AdapterServiceInterface,
        miner_repo: MinerRepository,
        logger: LoggerPort = None,
    ):
        # Services
        self.adapter_service = adapter_service

        # Domains
        self.miner_repo = miner_repo

        # Infrastructure
        self.logger = logger

    def _notify(self, notifiers: List[NotificationPort], title: str, message: str):
        """Sends a notification using the configured notifiers."""

        for notifier in notifiers:
            if notifier:
                try:
                    notifier.send_notification(title, message)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to send notification: {e}")

    # --- Miner Actions ---
    async def start_miner(self, miner_id: EntityId, notifiers: List[NotificationPort]) -> bool:
        """Starts the specified miner."""
        if self.logger:
            self.logger.info(f"Starting miner {miner_id}")

        miner: Miner = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller: MinerControlPort = self.adapter_service.get_miner_controller(miner)

        # Update miner status using controller
        current_status = miner_controller.get_miner_status(miner_id)
        current_hashrate = miner_controller.get_miner_hashrate(miner_id)
        current_power = miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_hashrate, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        success = miner_controller.start_miner(miner.id)

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) started successfully.")

            # Update domain state
            miner.turn_on()
            self.miner_repo.update(miner)
            self._notify(
                notifiers,
                "Edge Mining Info",
                f"Miner {miner.id} ({miner.name}) started.",
            )
        else:
            self.logger.error(f"Failed to start miner {miner.id} ({miner.name}).")

        return success

    async def stop_miner(self, miner_id: EntityId, notifiers: List[NotificationPort]) -> bool:
        """Stops the specified miner."""
        if self.logger:
            self.logger.info(f"Stopping miner {miner_id}")

        miner: Miner = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller: MinerControlPort = self.adapter_service.get_miner_controller(miner)

        # Update miner status using controller
        current_status = miner_controller.get_miner_status(miner_id)
        current_hashrate = miner_controller.get_miner_hashrate(miner_id)
        current_power = miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_hashrate, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        success = miner_controller.stop_miner(miner.id)

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) stopped successfully.")

            # Update domain state
            miner.turn_off()
            self.miner_repo.update(miner)
            self._notify(
                notifiers,
                "Edge Mining Info",
                f"Miner {miner.id} ({miner.name}) stopped.",
            )
        else:
            self.logger.error(f"Failed to stop miner {miner.id} ({miner.name}).")

        return success

    def get_miner_consumption(self, miner_id: EntityId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting power consumption for miner {miner_id}")

        miner: Miner = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller: MinerControlPort = self.adapter_service.get_miner_controller(miner)

        # Update miner status using controller
        current_status = miner_controller.get_miner_status(miner_id)
        current_power = miner_controller.get_miner_power(miner_id)
        miner.update_status(current_status, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        return current_power

    def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting hash rate for miner {miner_id}")

        miner: Miner = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller: MinerControlPort = self.adapter_service.get_miner_controller(miner)

        # Update miner status using controller
        current_status = miner_controller.get_miner_status(miner_id)
        current_hashrate = miner_controller.get_miner_hashrate(miner_id)
        miner.update_status(current_status, current_hashrate)

        # Persist the observed state
        self.miner_repo.update(miner)

        return current_hashrate

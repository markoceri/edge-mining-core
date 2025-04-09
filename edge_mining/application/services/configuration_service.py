import logging
from typing import List, Optional, Dict, Any

from edge_mining.domain.common import EntityId
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.common import MinerId
from edge_mining.domain.exceptions import PolicyError
from edge_mining.domain.miner.ports import MinerRepository
from edge_mining.domain.user.entities import SystemSettings
from edge_mining.domain.user.ports import SettingsRepository
from edge_mining.domain.policy.ports import OptimizationPolicyRepository
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy, AutomationRule, MiningDecision

logger = logging.getLogger(__name__)

class ConfigurationService:
    """Handles configuration of miners, policies, and system settings."""

    def __init__(
        self,
        miner_repo: MinerRepository,
        policy_repo: OptimizationPolicyRepository,
        settings_repo: SettingsRepository
    ):
        self.miner_repo = miner_repo
        self.policy_repo = policy_repo
        self.settings_repo = settings_repo

    # --- Miner Management ---
    def add_miner(self, miner_id: MinerId, name: str, ip_address: Optional[str] = None) -> Miner:
        logger.info(f"Adding miner {miner_id} ({name})")
        miner = Miner(id=miner_id, name=name, ip_address=ip_address)
        # TODO: Add validation (e.g., check if ID already exists)
        self.miner_repo.add(miner)
        return miner

    def get_miner(self, miner_id: MinerId) -> Optional[Miner]:
        return self.miner_repo.get_by_id(miner_id)

    def list_miners(self) -> List[Miner]:
        return self.miner_repo.get_all()

    def remove_miner(self, miner_id: MinerId) -> None:
        logger.info(f"Removing miner {miner_id}")
        # TODO: Check if miner exists before removing
        self.miner_repo.remove(miner_id)

    # --- Policy Management ---
    def create_policy(self, name: str, description: str = "", target_miner_ids: List[MinerId] = None) -> OptimizationPolicy:
        logger.info(f"Creating policy '{name}'")
        if target_miner_ids is None:
            target_miner_ids = []
        # Validate miner IDs exist?
        policy = OptimizationPolicy(name=name, description=description, target_miner_ids=target_miner_ids)
        self.policy_repo.add(policy)
        return policy

    def get_policy(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        return self.policy_repo.get_by_id(policy_id)

    def list_policies(self) -> List[OptimizationPolicy]:
        return self.policy_repo.get_all()

    def add_rule_to_policy(self, policy_id: EntityId, rule_type: str, name: str, conditions: Dict[str, Any], action: MiningDecision) -> AutomationRule:
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            raise PolicyError(f"Policy with ID {policy_id} not found.")

        rule = AutomationRule(name=name, conditions=conditions, action=action)
        if rule_type == "start": # I will make it enum, promise! 🤝
            policy.start_rules.append(rule)
        elif rule_type == "stop":
            policy.stop_rules.append(rule)
        else:
            raise ValueError("Invalid rule_type. Must be 'start' or 'stop'.")

        self.policy_repo.update(policy)
        logger.info(f"Added {rule_type} rule '{name}' to policy '{policy.name}'")
        return rule
    
        # TODO: Add method to remove/update rules

    def set_active_policy(self, policy_id: EntityId) -> None:
        logger.info(f"Setting policy {policy_id} as active.")
        policies = self.policy_repo.get_all()
        found = False
        for p in policies:
            if p.id == policy_id:
                p.is_active = True
                found = True
            else:
                p.is_active = False
            self.policy_repo.update(p) # Persist change for each policy

        if not found:
            raise PolicyError(f"Policy with ID {policy_id} not found.")

    def get_active_policy(self) -> Optional[OptimizationPolicy]:
        return self.policy_repo.get_active_policy()

    # --- Settings Management ---
    def get_all_settings(self) -> Dict[str, Any]:
        settings = self.settings_repo.get_settings()
        return settings.settings if settings else {}

    def update_setting(self, key: str, value: Any) -> None:
        settings = self.settings_repo.get_settings()
        if not settings:
            settings = SystemSettings() # Create if doesn't exist

        logger.info(f"Updating setting '{key}' to '{value}'")
        settings.set_setting(key, value)
        self.settings_repo.save_settings(settings)
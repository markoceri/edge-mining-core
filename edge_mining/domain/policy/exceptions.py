"""Collection of Exceptions."""

from edge_mining.domain.exceptions import DomainError


class PolicyError(DomainError):
    """Errors related to optimization policies."""

    pass


class PolicyNotFoundError(PolicyError):
    """Optimization policy not found."""

    pass


class PolicyAlreadyExistsError(PolicyError):
    """Optimization policy already exists."""

    pass


class InvalidRuleError(PolicyError):
    """Invalid automation rule."""

    pass


class RuleNotFoundError(PolicyError):
    """Automation rule not found."""

    pass


class PolicyConfigurationError(PolicyError):
    """Error in policy configuration."""

    pass


class RuleEngineError(Exception):
    """Base exception for rule engine errors."""

    pass


class RuleLoadError(RuleEngineError):
    """Exception raised when rules fail to load."""

    pass


class RuleEvaluationError(RuleEngineError):
    """Exception raised during rule evaluation."""

    pass

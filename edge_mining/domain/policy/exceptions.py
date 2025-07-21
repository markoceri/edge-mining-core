"""Collection of Exceptions."""

from edge_mining.domain.exceptions import DomainError

class PolicyError(DomainError):
    """Errors related to optimization policies."""
    pass

class PolicyNotFoundError(PolicyError):
    """Optimization policy not found."""
    pass

class InvalidRuleError(PolicyError):
    """Invalid automation rule."""
    pass

class PolicyConfigurationError(PolicyError):
    """Error in policy configuration."""
    pass

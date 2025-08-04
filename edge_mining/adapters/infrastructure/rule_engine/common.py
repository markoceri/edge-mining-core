"""Common objects for rule engine."""

from enum import Enum

class OperatorType(Enum):
    """Supported operators for rule conditions."""
    EQ = "eq"           # equal
    NE = "ne"           # not equal
    GT = "gt"           # greater than
    GTE = "gte"         # greater than or equal
    LT = "lt"           # less than
    LTE = "lte"         # less than or equal
    IN = "in"           # in list/array
    NOT_IN = "not_in"   # not in list/array
    CONTAINS = "contains"  # string contains
    STARTS_WITH = "starts_with"  # string starts with
    ENDS_WITH = "ends_with"    # string ends with
    REGEX = "regex"     # regex match

class RuleEngineType(Enum):
    """Types of rule engines."""
    CUSTOM = "custom"  # Custom rule engine


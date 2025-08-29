"""Utility functions for rule engine Fast API operations."""

from typing import List, Tuple

from edge_mining.adapters.infrastructure.rule_engine.common import OperatorType
from edge_mining.adapters.infrastructure.rule_engine.schemas import LogicalGroupSchema, RuleConditionSchema


def validate_condition_recursively(cond_dict, path="") -> Tuple[bool, List[str], List[str]]:
    """
    Recursively validate condition structure and return validation results.

    Returns:
        tuple: (is_valid, syntax_errors, field_errors)
    """
    syntax_errors = []
    field_errors = []
    is_valid = True

    if isinstance(cond_dict, dict):
        # Check if it's a rule condition
        if all(k in cond_dict for k in RuleConditionSchema.model_fields.keys()):
            # Validate field path
            field_path = cond_dict.get("field", "")
            if not field_path or not isinstance(field_path, str):
                field_errors.append(f"Invalid field path at {path}: '{field_path}'")
                is_valid = False

            # Validate operator
            operator = cond_dict.get("operator")
            try:
                if isinstance(operator, str):
                    if operator.lower() not in [op.value for op in OperatorType]:
                        raise ValueError(f"Invalid operator: {operator}")
                elif not isinstance(operator, OperatorType):
                    raise ValueError(f"Invalid operator type: {type(operator)}")
            except ValueError:
                syntax_errors.append(f"Invalid operator at {path}: '{operator}'")
                is_valid = False

            # Basic value validation
            # TODO: expand with all decisional context values check
            value = cond_dict.get("value")
            if value is None:
                syntax_errors.append(f"Missing value at {path}")
                is_valid = False

        # Check logical groups
        elif any(k in cond_dict for k in LogicalGroupSchema.model_fields.keys()):
            for key, sub_conditions in cond_dict.items():
                if key in ["all_of", "any_of"] and isinstance(sub_conditions, list):
                    for i, sub_cond in enumerate(sub_conditions):
                        sub_valid, sub_syntax_errors, sub_field_errors = validate_condition_recursively(
                            sub_cond, f"{path}.{key}[{i}]"
                        )
                        if not sub_valid:
                            is_valid = False
                        syntax_errors.extend(sub_syntax_errors)
                        field_errors.extend(sub_field_errors)
                elif key == "not_" and sub_conditions:
                    sub_valid, sub_syntax_errors, sub_field_errors = validate_condition_recursively(
                        sub_conditions, f"{path}.{key}"
                    )
                    if not sub_valid:
                        is_valid = False
                    syntax_errors.extend(sub_syntax_errors)
                    field_errors.extend(sub_field_errors)

        else:
            syntax_errors.append(f"Invalid condition structure at {path}: {cond_dict}")
            is_valid = False

    return is_valid, syntax_errors, field_errors
    return is_valid, syntax_errors, field_errors

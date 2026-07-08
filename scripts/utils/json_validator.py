"""
Lightweight JSON validation framework.

Usage:
    from .json_validator import validate, load_and_validate, Schema

    SCHEMA = {
        'name': {'type': str, 'required': True},
        'age':  {'type': int, 'default': 0},
        'role': {'type': str, 'enum': ['warrior', 'mage']},
        'stats': {
            'type': dict,
            'schema': {
                'hp':  {'type': (int, float), 'required': True},
                'mp':  {'type': (int, float), 'default': 0},
            }
        },
        'items': {
            'type': list,
            'item_schema': {
                'id':   {'type': str, 'required': True},
                'qty':  {'type': int, 'default': 1},
            }
        }
    }

    data = load_and_validate('path.json', SCHEMA)  # raises ValueError on failure
"""

import json
import os


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(data, schema, path="root", allow_extra=True):
    """Validate *data* against *schema*.

    *schema* is a dict mapping field names to rule dicts.
    Returns a list of error message strings (empty = valid).
    """
    errors = []

    if not isinstance(data, dict):
        errors.append(f"{path}: expected dict, got {type(data).__name__}")
        return errors

    # Check for unknown fields
    if not allow_extra:
        for key in data:
            if key not in schema:
                errors.append(f"{path}.{key}: unknown field")

    for key, rules in schema.items():
        full_path = f"{path}.{key}"
        value = data.get(key, _MISSING)

        # --- Required / default ---
        if value is _MISSING:
            if rules.get('required', True):
                errors.append(f"{full_path}: missing required field")
            elif 'default' in rules:
                data[key] = rules['default']
            continue

        # --- Type check ---
        type_ok = _check_type(value, rules)
        if not type_ok:
            expected = _type_str(rules.get('type'))
            got = type(value).__name__
            errors.append(f"{full_path}: expected {expected}, got {got}")
            continue  # skip further checks that might crash

        # --- Enum check ---
        enum_values = rules.get('enum')
        if enum_values is not None and value not in enum_values:
            errors.append(f"{full_path}: invalid value '{value}', expected one of {enum_values}")

        # --- Nested dict ---
        nested = rules.get('schema')
        if nested and isinstance(value, dict):
            errors.extend(validate(value, nested, full_path,
                                   allow_extra=rules.get('allow_extra', True)))

        # --- List items ---
        item_schema = rules.get('item_schema')
        if item_schema and isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item_schema, dict):
                    if isinstance(item, dict):
                        errors.extend(validate(item, item_schema, f"{full_path}[{i}]",
                                               allow_extra=rules.get('allow_extra', True)))
                    else:
                        errors.append(f"{full_path}[{i}]: expected dict, got {type(item).__name__}")
                else:
                    # item_schema is a type tuple for simple lists
                    if not isinstance(item, item_schema):
                        errors.append(f"{full_path}[{i}]: expected {_type_str(item_schema)}, got {type(item).__name__}")

        # --- Number range ---
        min_val = rules.get('min')
        max_val = rules.get('max')
        if min_val is not None and isinstance(value, (int, float)) and value < min_val:
            errors.append(f"{full_path}: value {value} < minimum {min_val}")
        if max_val is not None and isinstance(value, (int, float)) and value > max_val:
            errors.append(f"{full_path}: value {value} > maximum {max_val}")

    return errors


# ---------------------------------------------------------------------------
# Load + Validate helper
# ---------------------------------------------------------------------------

def load_and_validate(filepath, schema, allow_extra=True):
    """Load a JSON file and validate it against *schema*.

    Returns the parsed dict on success.
    Raises ValueError with all validation errors on failure.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    errors = validate(data, schema, path=os.path.basename(filepath), allow_extra=allow_extra)
    if errors:
        raise ValueError(
            f"Validation failed for {filepath}:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    return data


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MISSING = object()


def _check_type(value, rules):
    type_spec = rules.get('type')
    if type_spec is None:
        return True  # no type constraint
    if isinstance(type_spec, tuple):
        return isinstance(value, type_spec)
    return isinstance(value, type_spec)


def _type_str(type_spec):
    if type_spec is None:
        return "any"
    if isinstance(type_spec, tuple):
        return " | ".join(t.__name__ for t in type_spec)
    return type_spec.__name__


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

class Schema:
    """Minimal namespace for schema definitions."""

    @staticmethod
    def field(type=None, required=True, default=None, enum=None,
              schema=None, item_schema=None, min=None, max=None,
              allow_extra=True, description=""):
        return {
            'type': type,
            'required': required,
            'default': default,
            'enum': enum,
            'schema': schema,
            'item_schema': item_schema,
            'min': min,
            'max': max,
            'allow_extra': allow_extra,
            'description': description,
        }

    @staticmethod
    def optional(type=None, default=None, **kw):
        return Schema.field(type=type, required=False, default=default, **kw)

    @staticmethod
    def string(required=True, **kw):
        return Schema.field(type=str, required=required, **kw)

    @staticmethod
    def number(required=True, **kw):
        return Schema.field(type=(int, float), required=required, **kw)

    @staticmethod
    def integer(required=True, **kw):
        return Schema.field(type=int, required=required, **kw)

    @staticmethod
    def boolean(required=True, **kw):
        return Schema.field(type=bool, required=required, **kw)

    @staticmethod
    def enum(values, required=True, **kw):
        return Schema.field(type=str, required=required, enum=values, **kw)

    @staticmethod
    def array(item_schema, **kw):
        return Schema.field(type=list, item_schema=item_schema, **kw)

    @staticmethod
    def dict(schema, **kw):
        return Schema.field(type=dict, schema=schema, **kw)

    @staticmethod
    def any(**kw):
        return Schema.field(type=None, **kw)

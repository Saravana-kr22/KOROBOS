"""
KOROBOS — Database Service Type Validation

Validates record values against property types and options.
Provides type-safe value handling and casting.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PropertyType(str, Enum):
    """Supported property types."""

    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RELATION = "relation"


class ValidationError(ValueError):
    """Custom validation error with type-specific messages."""

    def __init__(self, property_name: str, property_type: str, message: str):
        self.property_name = property_name
        self.property_type = property_type
        self.message = message
        super().__init__(f"Property '{property_name}' ({property_type}): {message}")


class TypeValidator:
    """Validates and casts record values by property type."""

    @staticmethod
    def validate(
        value: Optional[str],
        property_name: str,
        property_type: str,
        options: Optional[dict] = None,
    ) -> str:
        """Validate a value against its property type.

        Args:
            value: The value to validate (stored as TEXT)
            property_name: Property name (for error messages)
            property_type: One of: text, number, boolean, date, select,
                multi_select, relation
            options: Type-specific configuration (e.g., select choices)

        Returns:
            The validated value (as string, or None serialized)

        Raises:
            ValidationError: If validation fails
        """
        # Allow empty/null values
        if value is None or value == "":
            return value or ""

        # Dispatch to type-specific validator
        try:
            ptype = PropertyType(property_type)
        except ValueError:
            raise ValidationError(
                property_name, property_type, f"Unknown property type: {property_type}"
            )

        if ptype == PropertyType.TEXT:
            return TypeValidator._validate_text(value, property_name)
        elif ptype == PropertyType.NUMBER:
            return TypeValidator._validate_number(value, property_name)
        elif ptype == PropertyType.BOOLEAN:
            return TypeValidator._validate_boolean(value, property_name)
        elif ptype == PropertyType.DATE:
            return TypeValidator._validate_date(value, property_name)
        elif ptype == PropertyType.SELECT:
            return TypeValidator._validate_select(value, property_name, options)
        elif ptype == PropertyType.MULTI_SELECT:
            return TypeValidator._validate_multi_select(value, property_name, options)
        elif ptype == PropertyType.RELATION:
            return TypeValidator._validate_relation(value, property_name, options)

        raise ValidationError(property_name, property_type, "Unhandled property type")

    @staticmethod
    def _validate_text(value: str, property_name: str) -> str:
        """Validate text property (any non-empty string is valid)."""
        if not isinstance(value, str):
            raise ValidationError(
                property_name, "text", f"Expected string, got {type(value).__name__}"
            )
        return value

    @staticmethod
    def _validate_number(value: str, property_name: str) -> str:
        """Validate number property (must be convertible to float)."""
        try:
            float(value)
            return value
        except (ValueError, TypeError):
            raise ValidationError(
                property_name,
                "number",
                f"Expected numeric value, got '{value}'",
            )

    @staticmethod
    def _validate_boolean(value: str, property_name: str) -> str:
        """Validate boolean property (true/false, 1/0, yes/no)."""
        lower_val = value.lower()
        if lower_val in ("true", "false", "1", "0", "yes", "no", "on", "off"):
            # Normalize to lowercase true/false
            if lower_val in ("true", "1", "yes", "on"):
                return "true"
            else:
                return "false"

        raise ValidationError(
            property_name,
            "boolean",
            f"Expected boolean value (true/false), got '{value}'",
        )

    @staticmethod
    def _validate_date(value: str, property_name: str) -> str:
        """Validate date property (ISO 8601 format)."""
        # Supported formats
        formats = [
            "%Y-%m-%d",  # 2026-03-15
            "%Y-%m-%dT%H:%M:%S",  # 2026-03-15T14:30:00
            "%Y-%m-%dT%H:%M:%SZ",  # 2026-03-15T14:30:00Z
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime("%Y-%m-%d")  # Normalize to date only
            except ValueError:
                continue

        raise ValidationError(
            property_name,
            "date",
            f"Expected ISO 8601 date (YYYY-MM-DD), got '{value}'",
        )

    @staticmethod
    def _validate_select(
        value: str,
        property_name: str,
        options: Optional[dict] = None,
    ) -> str:
        """Validate select property (value must be in options list)."""
        if not options or "choices" not in options:
            # No choices configured, allow any value
            return value

        choices = options.get("choices", [])
        if not isinstance(choices, list):
            choices = []

        if value not in choices:
            raise ValidationError(
                property_name,
                "select",
                f"Value '{value}' not in allowed choices: {choices}",
            )

        return value

    @staticmethod
    def _validate_multi_select(
        value: str,
        property_name: str,
        options: Optional[dict] = None,
    ) -> str:
        """Validate multi_select property (comma-separated values in choices).

        Stored as comma-separated string: "choice1,choice2,choice3"
        """
        if not options or "choices" not in options:
            return value

        choices = options.get("choices", [])
        if not isinstance(choices, list):
            choices = []

        # Parse comma-separated values
        selected = [v.strip() for v in value.split(",")]

        # Validate each selection
        for sel in selected:
            if sel not in choices:
                raise ValidationError(
                    property_name,
                    "multi_select",
                    f"Value '{sel}' not in allowed choices: {choices}",
                )

        return value

    @staticmethod
    def _validate_relation(
        value: str,
        property_name: str,
        options: Optional[dict] = None,
    ) -> str:
        """Validate relation property (must be valid UUID of target record).

        For Sprint 7, we validate format but not existence (deferred).
        """
        # Validate UUID format
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(uuid_pattern, value, re.IGNORECASE):
            raise ValidationError(
                property_name,
                "relation",
                f"Expected UUID format, got '{value}'",
            )

        return value.lower()  # Normalize to lowercase

    @staticmethod
    def cast_to_type(value: Optional[str], property_type: str) -> Any:
        """Cast a value to its Python type for application logic.

        Args:
            value: The value (stored as TEXT)
            property_type: The property type

        Returns:
            Python typed value (str, float, bool, datetime.date, list, etc.)
        """
        if value is None or value == "":
            return None

        try:
            ptype = PropertyType(property_type)
        except ValueError:
            return value

        if ptype == PropertyType.NUMBER:
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        elif ptype == PropertyType.BOOLEAN:
            return value.lower() == "true"

        elif ptype == PropertyType.DATE:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return value

        elif ptype == PropertyType.MULTI_SELECT:
            return [v.strip() for v in value.split(",")]

        else:
            return value

    @staticmethod
    def serialize_value(value: Any, property_type: str) -> str:
        """Serialize a Python value back to TEXT storage.

        Args:
            value: Python typed value
            property_type: The property type

        Returns:
            String representation for storage
        """
        if value is None:
            return ""

        try:
            ptype = PropertyType(property_type)
        except ValueError:
            return str(value)

        if ptype == PropertyType.NUMBER:
            return str(value)

        elif ptype == PropertyType.BOOLEAN:
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value).lower()

        elif ptype == PropertyType.DATE:
            if hasattr(value, "strftime"):
                return value.strftime("%Y-%m-%d")
            return str(value)

        elif ptype == PropertyType.MULTI_SELECT:
            if isinstance(value, list):
                return ",".join(str(v) for v in value)
            return str(value)

        else:
            return str(value)

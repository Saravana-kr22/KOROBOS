"""
KOROBOS — Database Service Type Validation Tests

Tests for the TypeValidator to ensure proper property type validation.
"""

import pytest
from app.services.type_validator import TypeValidator, ValidationError


class TestTextValidation:
    """Text property type validation tests."""

    def test_valid_text(self):
        """Text accepts any string value."""
        result = TypeValidator.validate("Hello World", "title", "text")
        assert result == "Hello World"

    def test_empty_text(self):
        """Empty text is allowed."""
        result = TypeValidator.validate("", "title", "text")
        assert result == ""

    def test_null_text(self):
        """Null text is allowed."""
        result = TypeValidator.validate(None, "title", "text")
        assert result is None


class TestNumberValidation:
    """Number property type validation tests."""

    def test_valid_integer(self):
        """Valid integer passes."""
        result = TypeValidator.validate("42", "count", "number")
        assert result == "42"

    def test_valid_float(self):
        """Valid float passes."""
        result = TypeValidator.validate("3.14", "price", "number")
        assert result == "3.14"

    def test_negative_number(self):
        """Negative numbers are valid."""
        result = TypeValidator.validate("-10", "balance", "number")
        assert result == "-10"

    def test_invalid_number(self):
        """Non-numeric value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("abc", "count", "number")
        assert "numeric" in str(exc_info.value).lower()

    def test_empty_number(self):
        """Empty number is allowed (null/unset)."""
        result = TypeValidator.validate("", "count", "number")
        assert result == ""


class TestBooleanValidation:
    """Boolean property type validation tests."""

    def test_true_values(self):
        """Various representations of true."""
        for value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            result = TypeValidator.validate(value, "active", "boolean")
            assert result == "true"

    def test_false_values(self):
        """Various representations of false."""
        for value in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]:
            result = TypeValidator.validate(value, "active", "boolean")
            assert result == "false"

    def test_invalid_boolean(self):
        """Invalid boolean raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("maybe", "active", "boolean")
        assert "boolean" in str(exc_info.value).lower()


class TestDateValidation:
    """Date property type validation tests."""

    def test_valid_iso_date(self):
        """ISO 8601 date format (YYYY-MM-DD)."""
        result = TypeValidator.validate("2026-03-15", "created", "date")
        assert result == "2026-03-15"

    def test_iso_datetime_strips_time(self):
        """ISO datetime is normalized to date only."""
        result = TypeValidator.validate("2026-03-15T14:30:00", "created", "date")
        assert result == "2026-03-15"

    def test_iso_datetime_with_z(self):
        """ISO datetime with Z suffix."""
        result = TypeValidator.validate("2026-03-15T14:30:00Z", "created", "date")
        assert result == "2026-03-15"

    def test_invalid_date_format(self):
        """Invalid date format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("03/15/2026", "created", "date")
        assert (
            "ISO 8601" in str(exc_info.value) or "date" in str(exc_info.value).lower()
        )

    def test_invalid_date_value(self):
        """Invalid date values raise ValidationError."""
        with pytest.raises(ValidationError):
            TypeValidator.validate("2026-13-45", "created", "date")


class TestSelectValidation:
    """Select property type validation tests."""

    def test_valid_select(self):
        """Valid select option."""
        options = {"choices": ["Low", "Medium", "High"]}
        result = TypeValidator.validate("High", "priority", "select", options)
        assert result == "High"

    def test_invalid_select(self):
        """Invalid select option raises ValidationError."""
        options = {"choices": ["Low", "Medium", "High"]}
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("Critical", "priority", "select", options)
        assert "not in allowed choices" in str(exc_info.value).lower()

    def test_select_no_options(self):
        """Select without options defined allows any value."""
        result = TypeValidator.validate("Any Value", "status", "select")
        assert result == "Any Value"

    def test_select_case_sensitive(self):
        """Select options are case-sensitive."""
        options = {"choices": ["Low", "Medium", "High"]}
        with pytest.raises(ValidationError):
            TypeValidator.validate("high", "priority", "select", options)


class TestMultiSelectValidation:
    """Multi-select property type validation tests."""

    def test_valid_multi_select(self):
        """Valid comma-separated selections."""
        options = {"choices": ["Python", "JavaScript", "Go", "Rust"]}
        result = TypeValidator.validate(
            "Python,Go", "languages", "multi_select", options
        )
        assert result == "Python,Go"

    def test_multi_select_single_value(self):
        """Multi-select with single value."""
        options = {"choices": ["A", "B", "C"]}
        result = TypeValidator.validate("A", "tags", "multi_select", options)
        assert result == "A"

    def test_invalid_multi_select(self):
        """Invalid selection in multi_select raises ValidationError."""
        options = {"choices": ["Python", "JavaScript", "Go"]}
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("Python,Ruby", "languages", "multi_select", options)
        assert "not in allowed choices" in str(exc_info.value).lower()

    def test_multi_select_with_spaces(self):
        """Spaces are trimmed in multi-select values."""
        options = {"choices": ["A", "B", "C"]}
        result = TypeValidator.validate("A , B", "tags", "multi_select", options)
        assert result == "A , B"  # Spaces preserved in storage, trimmed on parse


class TestRelationValidation:
    """Relation property type validation tests."""

    def test_valid_relation_uuid(self):
        """Valid UUID format for relation."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = TypeValidator.validate(uuid_str, "related_task", "relation")
        assert result == uuid_str.lower()

    def test_valid_relation_uuid_uppercase(self):
        """UUID with uppercase is normalized to lowercase."""
        uuid_str = "550E8400-E29B-41D4-A716-446655440000"
        result = TypeValidator.validate(uuid_str, "related_task", "relation")
        assert result == uuid_str.lower()

    def test_invalid_relation_format(self):
        """Invalid UUID format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("not-a-uuid", "related_task", "relation")
        assert "UUID" in str(exc_info.value)

    def test_invalid_relation_partial_uuid(self):
        """Partial UUID is invalid."""
        with pytest.raises(ValidationError):
            TypeValidator.validate("550e8400-e29b-41d4", "related_task", "relation")


class TestTypeCasting:
    """Type casting/deserialization tests."""

    def test_cast_number_to_float(self):
        """Cast number to float."""
        result = TypeValidator.cast_to_type("3.14", "number")
        assert result == 3.14
        assert isinstance(result, float)

    def test_cast_number_to_int(self):
        """Cast integer number."""
        result = TypeValidator.cast_to_type("42", "number")
        assert result == 42
        assert isinstance(result, int)

    def test_cast_boolean_to_bool(self):
        """Cast boolean value."""
        assert TypeValidator.cast_to_type("true", "boolean") is True
        assert TypeValidator.cast_to_type("false", "boolean") is False

    def test_cast_date_to_date_object(self):
        """Cast date to date object."""
        result = TypeValidator.cast_to_type("2026-03-15", "date")
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 15

    def test_cast_multi_select_to_list(self):
        """Cast multi-select to list."""
        result = TypeValidator.cast_to_type("A,B,C", "multi_select")
        assert result == ["A", "B", "C"]

    def test_cast_text_remains_string(self):
        """Text casting keeps string type."""
        result = TypeValidator.cast_to_type("hello", "text")
        assert result == "hello"
        assert isinstance(result, str)


class TestSerialization:
    """Value serialization tests."""

    def test_serialize_number(self):
        """Serialize number types."""
        assert TypeValidator.serialize_value(42, "number") == "42"
        assert TypeValidator.serialize_value(3.14, "number") == "3.14"

    def test_serialize_boolean(self):
        """Serialize boolean values."""
        assert TypeValidator.serialize_value(True, "boolean") == "true"
        assert TypeValidator.serialize_value(False, "boolean") == "false"

    def test_serialize_date(self):
        """Serialize date objects."""
        from datetime import date

        d = date(2026, 3, 15)
        assert TypeValidator.serialize_value(d, "date") == "2026-03-15"

    def test_serialize_multi_select_list(self):
        """Serialize list to comma-separated."""
        assert TypeValidator.serialize_value(["A", "B", "C"], "multi_select") == "A,B,C"


class TestValidationError:
    """ValidationError exception tests."""

    def test_error_message_format(self):
        """Error message includes property name and type."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("invalid", "age", "number")

        error = exc_info.value
        assert error.property_name == "age"
        assert error.property_type == "number"
        assert "age" in str(error)
        assert "number" in str(error)


class TestUnknownType:
    """Unknown property type handling."""

    def test_unknown_property_type(self):
        """Unknown property type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TypeValidator.validate("value", "field", "unknown_type")
        assert "unknown" in str(exc_info.value).lower()

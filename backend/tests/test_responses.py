"""
Unit tests for the standardized API response helpers.
"""

from backend.shared.utils.responses import (
    APIResponse,
    ErrorDetail,
    error_response,
    success_response,
)


class TestSuccessResponse:
    """Tests for success_response."""

    def test_with_data(self):
        result = success_response(data={"id": "123", "name": "test"})
        assert result["status"] == "success"
        assert result["data"] == {"id": "123", "name": "test"}

    def test_without_data(self):
        result = success_response()
        assert result["status"] == "success"
        assert result["data"] is None

    def test_with_list_data(self):
        result = success_response(data=[1, 2, 3])
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]


class TestErrorResponse:
    """Tests for error_response."""

    def test_standard_error(self):
        result = error_response(code="RESOURCE_NOT_FOUND", message="Note not found")
        assert result["status"] == "error"
        assert result["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert result["error"]["message"] == "Note not found"

    def test_validation_error(self):
        result = error_response(code="VALIDATION_ERROR", message="Invalid email format")
        assert result["status"] == "error"
        assert result["error"]["code"] == "VALIDATION_ERROR"


class TestPydanticModels:
    """Tests for Pydantic response schemas."""

    def test_api_response_success(self):
        resp = APIResponse(status="success", data={"key": "value"})
        assert resp.status == "success"
        assert resp.data == {"key": "value"}
        assert resp.error is None

    def test_api_response_error(self):
        detail = ErrorDetail(code="ERR_CODE", message="Something went wrong")
        resp = APIResponse(status="error", error=detail)
        assert resp.status == "error"
        assert resp.error is not None
        assert resp.error.code == "ERR_CODE"
        assert resp.error.message == "Something went wrong"
        assert resp.data is None

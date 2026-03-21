"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for Health Service HTTP routes.
"""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
class TestHealthRoutes:
    """Integration tests for Health Service routes."""

    def _get_headers(self, user_id: str):
        """Helper to create auth headers."""
        return {
            "Authorization": "Bearer fake-token",
            "X-User-ID": user_id,
        }

    def test_log_meal_success(self, client, test_user_id, test_meal_data):
        """Test successful meal logging."""
        response = client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["log_type"] == "meal"
        assert data["calories"] == test_meal_data["calories"]
        assert data["food_name"] == test_meal_data["food_name"]

    def test_log_workout_success(self, client, test_user_id, test_workout_data):
        """Test successful workout logging."""
        response = client.post(
            "/workouts",
            json=test_workout_data,
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["log_type"] == "workout"
        assert data["duration"] == test_workout_data["duration"]
        assert data["workout_type"] == test_workout_data["workout_type"]

    def test_list_logs(self, client, test_user_id, test_meal_data, test_workout_data):
        """Test listing health logs."""
        # Log meal and workout
        client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )
        client.post(
            "/workouts",
            json=test_workout_data,
            headers=self._get_headers(test_user_id),
        )

        # List logs
        response = client.get(
            "/logs",
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["logs"]) == 2

    def test_get_stats(self, client, test_user_id, test_meal_data, test_workout_data):
        """Test getting lifetime health statistics."""
        # Log meal and workout
        client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )
        client.post(
            "/workouts",
            json=test_workout_data,
            headers=self._get_headers(test_user_id),
        )

        response = client.get(
            "/stats",
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_meals"] == 1
        assert data["total_workouts"] == 1
        assert data["total_calories"] == test_meal_data["calories"]
        assert data["total_workout_minutes"] == test_workout_data["duration"]

    def test_get_daily_stats(
        self, client, test_user_id, test_meal_data, test_workout_data
    ):
        """Test getting daily calorie statistics."""
        # Log meal and workout
        client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )
        client.post(
            "/workouts",
            json=test_workout_data,
            headers=self._get_headers(test_user_id),
        )

        response = client.get(
            "/daily",
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["calories_consumed"] == test_meal_data["calories"]
        assert data["calories_burned"] == test_workout_data["calories"]
        assert data["net_calories"] == (
            test_meal_data["calories"] - test_workout_data["calories"]
        )

    def test_delete_log_success(self, client, test_user_id, test_meal_data):
        """Test deleting a log successfully."""
        # Log a meal
        response = client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )
        log_id = response.json()["id"]

        # Delete it
        delete_response = client.delete(
            f"/logs/{log_id}",
            headers=self._get_headers(test_user_id),
        )

        assert delete_response.status_code == 204

        # Verify it's gone
        list_response = client.get(
            "/logs",
            headers=self._get_headers(test_user_id),
        )
        assert list_response.json()["total"] == 0

    def test_delete_log_not_found(self, client, test_user_id):
        """Test deleting a non-existent log."""
        fake_log_id = str(uuid4())

        response = client.delete(
            f"/logs/{fake_log_id}",
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 404

    def test_meal_missing_calories(self, client, test_user_id):
        """Test meal logging with missing required field."""
        response = client.post(
            "/meals",
            json={"food_name": "Pizza"},  # calories is missing
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 422  # Validation error

    def test_workout_missing_duration(self, client, test_user_id):
        """Test workout logging with missing required field."""
        response = client.post(
            "/workouts",
            json={"workout_type": "running"},  # duration is missing
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 422  # Validation error

    def test_filter_logs_by_type(
        self, client, test_user_id, test_meal_data, test_workout_data
    ):
        """Test filtering logs by type."""
        # Log meal and workout
        client.post(
            "/meals",
            json=test_meal_data,
            headers=self._get_headers(test_user_id),
        )
        client.post(
            "/workouts",
            json=test_workout_data,
            headers=self._get_headers(test_user_id),
        )

        # Filter by meals
        response = client.get(
            "/logs?log_type=meal",
            headers=self._get_headers(test_user_id),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["logs"][0]["log_type"] == "meal"

    def test_pagination(self, client, test_user_id, test_meal_data):
        """Test log pagination."""
        # Create 5 meals
        for i in range(5):
            meal_data = {**test_meal_data, "calories": 100 + i}
            client.post(
                "/meals",
                json=meal_data,
                headers=self._get_headers(test_user_id),
            )

        # Get first page (limit=2)
        response = client.get(
            "/logs?limit=2&offset=0",
            headers=self._get_headers(test_user_id),
        )

        data = response.json()
        assert data["total"] == 5
        assert len(data["logs"]) == 2

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Should return Prometheus format text
        assert b"meals_logged_total" in response.content or b"#" in response.content

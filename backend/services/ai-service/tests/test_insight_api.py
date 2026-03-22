"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Tests for AI Service insights and recommendations APIs.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.main import app
from app.services.feature_engineering import FeatureVector
from fastapi.testclient import TestClient

# Test client
client = TestClient(app)


@pytest.fixture
def user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def valid_headers(user_id):
    """Generate valid request headers with user ID."""
    return {"X-User-ID": str(user_id)}


class TestInsightAPI:
    """Tests for the /insights endpoint."""

    @pytest.mark.asyncio
    async def test_get_insights_success(self, user_id, valid_headers):
        """Test successful GET /insights."""
        with patch("app.api.routes.FeatureEngineeringService") as mock_feature_svc:
            with patch("app.api.routes.InsightService") as mock_insight_svc:
                # Mock feature vector
                mock_feature_instance = AsyncMock()
                mock_feature_instance.get_feature_vector.return_value = FeatureVector(
                    habit_consistency_score=75.0,
                    learning_velocity=60.0,
                    health_balance_index=80.0,
                    productivity_score=70.0,
                    graph_connectivity_score=65.0,
                )
                mock_feature_svc.return_value = mock_feature_instance

                # Mock insights
                mock_insight_instance = AsyncMock()
                mock_insight_instance.generate_insights.return_value = []
                mock_insight_instance.list_insights.return_value = ([], 0)
                mock_insight_svc.return_value = mock_insight_instance

                # Make request
                response = client.get(
                    "/insights",
                    headers=valid_headers,
                )

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert "insights" in data
                assert "total" in data
                assert isinstance(data["insights"], list)

    @pytest.mark.asyncio
    async def test_get_insights_with_filter(self, user_id, valid_headers):
        """Test GET /insights with insight_type filter."""
        with patch("app.api.routes.FeatureEngineeringService") as mock_feature_svc:
            with patch("app.api.routes.InsightService") as mock_insight_svc:
                mock_feature_instance = AsyncMock()
                mock_feature_instance.get_feature_vector.return_value = FeatureVector(
                    habit_consistency_score=75.0,
                    learning_velocity=60.0,
                    health_balance_index=80.0,
                    productivity_score=70.0,
                    graph_connectivity_score=65.0,
                )
                mock_feature_svc.return_value = mock_feature_instance

                mock_insight_instance = AsyncMock()
                mock_insight_instance.generate_insights.return_value = []
                mock_insight_instance.list_insights.return_value = ([], 0)
                mock_insight_svc.return_value = mock_insight_instance

                response = client.get(
                    "/insights?insight_type=behavioral",
                    headers=valid_headers,
                )

                assert response.status_code == 200
                mock_insight_instance.list_insights.assert_called_once()


class TestRecommendationAPI:
    """Tests for the /recommendations endpoint."""

    @pytest.mark.asyncio
    async def test_get_recommendations_success(self, user_id, valid_headers):
        """Test successful GET /recommendations."""
        with patch("app.api.routes.FeatureEngineeringService") as mock_feature_svc:
            with patch("app.api.routes.RecommendationService") as mock_rec_svc:
                # Mock feature vector
                mock_feature_instance = AsyncMock()
                mock_feature_instance.get_feature_vector.return_value = FeatureVector(
                    habit_consistency_score=75.0,
                    learning_velocity=60.0,
                    health_balance_index=80.0,
                    productivity_score=70.0,
                    graph_connectivity_score=65.0,
                )
                mock_feature_svc.return_value = mock_feature_instance

                # Mock recommendations
                mock_rec_instance = AsyncMock()
                mock_rec_instance.generate_recommendations.return_value = []
                mock_rec_instance.list_recommendations.return_value = ([], 0)
                mock_rec_svc.return_value = mock_rec_instance

                # Make request
                response = client.get(
                    "/recommendations",
                    headers=valid_headers,
                )

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert "recommendations" in data
                assert "total" in data
                assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_get_recommendations_with_category(self, user_id, valid_headers):
        """Test GET /recommendations with category filter."""
        with patch("app.api.routes.FeatureEngineeringService") as mock_feature_svc:
            with patch("app.api.routes.RecommendationService") as mock_rec_svc:
                mock_feature_instance = AsyncMock()
                mock_feature_instance.get_feature_vector.return_value = FeatureVector(
                    habit_consistency_score=75.0,
                    learning_velocity=60.0,
                    health_balance_index=80.0,
                    productivity_score=70.0,
                    graph_connectivity_score=65.0,
                )
                mock_feature_svc.return_value = mock_feature_instance

                mock_rec_instance = AsyncMock()
                mock_rec_instance.generate_recommendations.return_value = []
                mock_rec_instance.list_recommendations.return_value = ([], 0)
                mock_rec_svc.return_value = mock_rec_instance

                response = client.get(
                    "/recommendations?category=habit",
                    headers=valid_headers,
                )

                assert response.status_code == 200
                mock_rec_instance.list_recommendations.assert_called_once()


class TestSummaryAPI:
    """Tests for the /summary endpoint."""

    @pytest.mark.asyncio
    async def test_get_summary_success(self, user_id, valid_headers):
        """Test successful GET /summary."""
        with patch("app.api.routes.FeatureEngineeringService") as mock_feature_svc:
            with patch("app.api.routes.InsightService") as mock_insight_svc:
                with patch("app.api.routes.RecommendationService") as mock_rec_svc:
                    with patch("app.api.routes.AIService") as mock_ai_svc:
                        # Mock all services
                        mock_feature_instance = AsyncMock()
                        mock_feature_instance.get_feature_vector.return_value = (
                            FeatureVector(
                                habit_consistency_score=75.0,
                                learning_velocity=60.0,
                                health_balance_index=80.0,
                                productivity_score=70.0,
                                graph_connectivity_score=65.0,
                            )
                        )
                        mock_feature_svc.return_value = mock_feature_instance

                        mock_insight_instance = AsyncMock()
                        mock_insight_instance.generate_insights.return_value = []
                        mock_insight_instance.list_insights.return_value = ([], 0)
                        mock_insight_svc.return_value = mock_insight_instance

                        mock_rec_instance = AsyncMock()
                        mock_rec_instance.generate_recommendations.return_value = []
                        mock_rec_instance.list_recommendations.return_value = ([], 0)
                        mock_rec_svc.return_value = mock_rec_instance

                        mock_ai_instance = AsyncMock()
                        mock_ai_instance.process_prompt.return_value = MagicMock(
                            response="Good progress!"
                        )
                        mock_ai_instance.list_interactions.return_value = ([], 0)
                        mock_ai_svc.return_value = mock_ai_instance

                        # Make request
                        response = client.get(
                            "/summary",
                            headers=valid_headers,
                        )

                        # Assert response
                        assert response.status_code == 200
                        data = response.json()
                        assert "user_id" in data
                        assert "summary" in data
                        assert "generated_at" in data
                        assert "insights" in data
                        assert "recommendations" in data


class TestPromptAPI:
    """Tests for the /prompt endpoint."""

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, user_id, valid_headers):
        """Test successful POST /prompt."""
        with patch("app.api.routes.AIService") as mock_ai_svc:
            # Mock AI service
            mock_ai_instance = AsyncMock()
            mock_interaction = MagicMock()
            mock_interaction.id = uuid4()
            mock_interaction.user_id = user_id
            mock_interaction.interaction_type = "recommendation"
            mock_interaction.prompt = "Test prompt"
            mock_interaction.response = "Test response"
            mock_interaction.metadata_json = {}
            mock_interaction.created_at = "2026-03-22T00:00:00Z"
            mock_ai_instance.process_prompt.return_value = mock_interaction
            mock_ai_svc.return_value = mock_ai_instance

            # Make request
            response = client.post(
                "/prompt",
                json={
                    "prompt": "What should I do next?",
                    "interaction_type": "recommendation",
                },
                headers=valid_headers,
            )

            # Assert response
            assert response.status_code == 201
            data = response.json()
            assert data["interaction_type"] == "recommendation"
            assert "id" in data
            assert "response" in data


class TestInteractionsAPI:
    """Tests for the /interactions endpoints."""

    @pytest.mark.asyncio
    async def test_list_interactions_success(self, user_id, valid_headers):
        """Test successful GET /interactions."""
        with patch("app.api.routes.AIService") as mock_ai_svc:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.list_interactions.return_value = ([], 0)
            mock_ai_svc.return_value = mock_ai_instance

            response = client.get(
                "/interactions",
                headers=valid_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "interactions" in data
            assert "total" in data

    @pytest.mark.asyncio
    async def test_get_interaction_by_id_success(self, user_id, valid_headers):
        """Test successful GET /interactions/{id}."""
        interaction_id = uuid4()

        with patch("app.api.routes.AIService") as mock_ai_svc:
            mock_ai_instance = AsyncMock()
            mock_interaction = MagicMock()
            mock_interaction.id = interaction_id
            mock_interaction.user_id = user_id
            mock_interaction.interaction_type = "recommendation"
            mock_interaction.prompt = "Test"
            mock_interaction.response = "Response"
            mock_interaction.metadata_json = {}
            mock_interaction.created_at = "2026-03-22T00:00:00Z"
            mock_ai_instance.get_interaction.return_value = mock_interaction
            mock_ai_svc.return_value = mock_ai_instance

            response = client.get(
                f"/interactions/{interaction_id}",
                headers=valid_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(interaction_id)

    @pytest.mark.asyncio
    async def test_get_interaction_not_found(self, user_id, valid_headers):
        """Test GET /interactions/{id} when interaction doesn't exist."""
        interaction_id = uuid4()

        with patch("app.api.routes.AIService") as mock_ai_svc:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.get_interaction.return_value = None
            mock_ai_svc.return_value = mock_ai_instance

            response = client.get(
                f"/interactions/{interaction_id}",
                headers=valid_headers,
            )

            assert response.status_code == 404


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_endpoint(self):
        """Test GET / endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

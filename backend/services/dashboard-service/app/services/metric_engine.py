"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Metric Engine — productivity score calculation and domain scoring.
"""


class MetricEngine:
    """Computes derived metrics from domain-specific data."""

    @staticmethod
    def compute_productivity_score(
        habit_score: float,
        learning_score: float,
        health_score: float,
    ) -> int:
        """
        Compute overall productivity score from component scores.

        Formula (Sprint 11 §9):
        score = (habit_score * 0.4) + (learning_score * 0.3) + (health_score * 0.3)

        Returns:
            Integer 0-100 representing productivity.
        """
        score = (habit_score * 0.4) + (learning_score * 0.3) + (health_score * 0.3)
        # Clamp to 0-100 range
        return max(0, min(100, int(round(score))))

    @staticmethod
    def habit_score(completed: int, total: int) -> float:
        """
        Calculate habit completion score.

        Returns:
            Float 0-100. Percentage of habits completed today.
        """
        if total == 0:
            return 0.0
        return (completed / total) * 100.0

    @staticmethod
    def learning_score(minutes: int, target_minutes: int = 60) -> float:
        """
        Calculate learning score based on time spent.

        Args:
            minutes: Total learning minutes today
            target_minutes: Target daily learning (default 60 min)

        Returns:
            Float 0-100. Capped at 100 (can't over-score).
        """
        if target_minutes == 0:
            return 0.0
        score = (minutes / target_minutes) * 100.0
        return min(score, 100.0)

    @staticmethod
    def health_score(net_calories: int, tolerance: int = 500) -> float:
        """
        Calculate health/caloric balance score.

        Penalizes surplus (positive net) or deficit (negative net) calories.
        Perfect score (100) when net calories within [-tolerance, +tolerance].

        Args:
            net_calories: calories_consumed - calories_burned
            tolerance: acceptable deviation (default 500 kcal)

        Returns:
            Float 0-100.
        """
        if tolerance == 0:
            return 0.0

        # Penalty is proportional to distance from 0
        penalty = (abs(net_calories) / tolerance) * 100.0
        return max(0.0, 100.0 - penalty)

    @staticmethod
    def consistency_score(daily_scores: list[int]) -> float:
        """
        Calculate consistency score based on variance of daily productivity.

        Perfect consistency (100) when all days have equal productivity scores.
        Lower variance = higher consistency score.

        Args:
            daily_scores: List of daily productivity scores (0-100)

        Returns:
            Float 0-100 representing consistency.
        """
        if not daily_scores or len(daily_scores) < 2:
            # Single day or no data = perfect consistency by definition
            return 100.0

        # Calculate mean
        mean = sum(daily_scores) / len(daily_scores)

        # Calculate variance
        variance = sum((x - mean) ** 2 for x in daily_scores) / len(daily_scores)

        # Convert variance to a score: lower variance = higher score
        # Max variance for 0-100 range would be around 2500 (when values range 0-100)
        # Use 2500 as scaling factor to cap score at 100
        max_variance = 2500.0
        consistency = 100.0 - (variance / max_variance) * 100.0
        return max(0.0, min(100.0, consistency))

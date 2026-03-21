"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ClickHouse repository for long-term behavior pattern analysis.

ClickHouse is an OLAP database optimized for analytical queries on large
datasets. This repository handles archival and analysis of aggregated metrics
for trend detection, anomaly detection, and long-term behavioral insights.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

import httpx


class ClickHouseRepository:
    """
    Repository for storing and querying aggregated metrics in ClickHouse.

    Handles:
    - Archival of daily aggregated metrics from analytics_metrics table
    - Long-term trend analysis (30/90/365 day periods)
    - Behavior pattern detection (consistency, anomalies)
    - Moving averages and percentile calculations
    - Cross-metric correlations
    """

    def __init__(
        self,
        clickhouse_url: str = "http://localhost:8123",
        user: str = "default",
        password: str = "clickhouse",
        database: str = "korobos",
    ):
        self.clickhouse_url = clickhouse_url
        self.user = user
        self.password = password
        self.database = database
        self.timeout = 30.0  # seconds

    async def _query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Execute ClickHouse query and return results."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                query_params = {
                    "query": sql,
                    "user": self.user,
                    "password": self.password,
                    "database": self.database,
                    "format": "JSONEachRow",
                }
                response = await client.get(
                    f"{self.clickhouse_url}/",
                    params=query_params,
                )
                response.raise_for_status()

                # Parse JSON lines response
                lines = response.text.strip().split("\n")
                results = []
                for line in lines:
                    if line:
                        import json

                        results.append(json.loads(line))
                return results
        except Exception as exc:
            print(f"ClickHouse query failed: {exc}")
            return []

    async def init_tables(self) -> bool:
        """Initialize ClickHouse tables for metrics archival."""
        try:
            # Create metrics_archive table (denormalized for analytics)
            create_archive_sql = """
            CREATE TABLE IF NOT EXISTS korobos.metrics_archive (
                user_id UUID,
                date Date,
                metric_type String,
                value Float64,
                count UInt32,
                min_value Float64,
                max_value Float64,
                avg_value Float64,
                recorded_at DateTime
            ) ENGINE = MergeTree()
            ORDER BY (user_id, date, metric_type)
            PARTITION BY toYYYYMM(date);
            """
            await self._query(create_archive_sql)

            # Create behavior_patterns table (computed insights)
            create_patterns_sql = """
            CREATE TABLE IF NOT EXISTS korobos.behavior_patterns (
                user_id UUID,
                period_start Date,
                period_end Date,
                metric_type String,
                avg_value Float64,
                std_dev Float64,
                min_value Float64,
                max_value Float64,
                consistency_score Float64,
                trend_direction String,  -- 'increasing', 'decreasing', 'stable'
                anomaly_count UInt32,
                computed_at DateTime
            ) ENGINE = MergeTree()
            ORDER BY (user_id, period_start, metric_type)
            PARTITION BY toYYYYMM(period_start);
            """
            await self._query(create_patterns_sql)

            print("ClickHouse tables initialized successfully")
            return True
        except Exception as exc:
            print(f"Failed to initialize ClickHouse tables: {exc}")
            return False

    async def archive_daily_metrics(
        self,
        user_id: UUID,
        date: datetime,
        metrics: Dict[str, Dict[str, Any]],
    ) -> bool:
        """
        Archive daily aggregated metrics to ClickHouse.

        Args:
            user_id: User identifier
            date: Date of metrics
            metrics: Dict of {metric_type: {value, count, min, max, avg}}
        """
        try:
            rows = []
            for metric_type, data in metrics.items():
                rows.append(
                    {
                        "user_id": str(user_id),
                        "date": date.date(),
                        "metric_type": metric_type,
                        "value": data.get("value", 0.0),
                        "count": data.get("count", 1),
                        "min_value": data.get("min", 0.0),
                        "max_value": data.get("max", 0.0),
                        "avg_value": data.get("avg", 0.0),
                        "recorded_at": datetime.utcnow(),
                    }
                )

            # Insert into ClickHouse
            if rows:
                import json

                json_rows = [f"'{json.dumps(r)}'" for r in rows]
                json_array = ",".join(json_rows)
                insert_sql = f"""
                INSERT INTO korobos.metrics_archive
                SELECT
                    parseUUID(JSONExtractString(json, 'user_id')) as user_id,
                    JSONExtractString(json, 'date') as date,
                    JSONExtractString(json, 'metric_type') as metric_type,
                    JSONExtractFloat(json, 'value') as value,
                    JSONExtractUInt(json, 'count') as count,
                    JSONExtractFloat(json, 'min_value') as min_value,
                    JSONExtractFloat(json, 'max_value') as max_value,
                    JSONExtractFloat(json, 'avg_value') as avg_value,
                    JSONExtractString(json, 'recorded_at') as recorded_at
                FROM (SELECT arrayJoin([{json_array}]) as json);
                """
                await self._query(insert_sql)
            return True
        except Exception as exc:
            print(f"Failed to archive daily metrics: {exc}")
            return False

    async def get_trend(
        self,
        user_id: UUID,
        metric_type: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get long-term trend data (30/90/365 days)."""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()
            query = f"""
            SELECT
                date,
                avg_value as value,
                count as count
            FROM korobos.metrics_archive
            WHERE user_id = parseUUID('{user_id}')
                AND metric_type = '{metric_type}'
                AND date >= '{start_date}'
            ORDER BY date ASC;
            """
            results = await self._query(query)

            return {
                "metric_type": metric_type,
                "period_days": days,
                "values": [r.get("value", 0) for r in results],
                "labels": [r.get("date", "") for r in results],
                "count": len(results),
            }
        except Exception as exc:
            print(f"Failed to get trend: {exc}")
            return {"metric_type": metric_type, "values": [], "labels": []}

    async def compute_behavior_pattern(
        self,
        user_id: UUID,
        metric_type: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Compute behavior pattern metrics:
        - Average and standard deviation
        - Min/max values
        - Consistency score (inverse of CV)
        - Trend direction
        - Anomaly count
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()
            query = f"""
            SELECT
                avg(avg_value) as mean_value,
                sqrt(sum((avg_value - mean_value) * (avg_value - mean_value))
                    / count()) as std_dev,
                min(min_value) as min_value,
                max(max_value) as max_value,
                count(*) as data_points
            FROM korobos.metrics_archive
            WHERE user_id = parseUUID('{user_id}')
                AND metric_type = '{metric_type}'
                AND date >= '{start_date}';
            """
            results = await self._query(query)

            if not results:
                return {
                    "metric_type": metric_type,
                    "status": "no_data",
                }

            data = results[0]
            mean = float(data.get("mean_value", 0))
            std_dev = float(data.get("std_dev", 0))
            min_val = float(data.get("min_value", 0))
            max_val = float(data.get("max_value", 0))

            # Consistency score: 1 / (1 + CV) where CV = std_dev / mean
            cv = std_dev / mean if mean > 0 else 0
            consistency_score = 1.0 / (1.0 + cv) if cv >= 0 else 0

            # Trend direction: compare first and last values
            trend_query = f"""
            SELECT
                avg_value,
                date
            FROM korobos.metrics_archive
            WHERE user_id = parseUUID('{user_id}')
                AND metric_type = '{metric_type}'
                AND date >= '{start_date}'
            ORDER BY date ASC
            LIMIT 1;
            """
            first_results = await self._query(trend_query)
            first_value = (
                float(first_results[0].get("avg_value", 0)) if first_results else 0
            )

            trend_query_last = f"""
            SELECT
                avg_value,
                date
            FROM korobos.metrics_archive
            WHERE user_id = parseUUID('{user_id}')
                AND metric_type = '{metric_type}'
                AND date >= '{start_date}'
            ORDER BY date DESC
            LIMIT 1;
            """
            last_results = await self._query(trend_query_last)
            last_value = (
                float(last_results[0].get("avg_value", 0)) if last_results else 0
            )

            if last_value > first_value * 1.1:
                trend_direction = "increasing"
            elif last_value < first_value * 0.9:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"

            return {
                "metric_type": metric_type,
                "period_days": days,
                "mean_value": round(mean, 2),
                "std_dev": round(std_dev, 2),
                "min_value": round(min_val, 2),
                "max_value": round(max_val, 2),
                "consistency_score": round(consistency_score, 2),
                "trend_direction": trend_direction,
                "data_points": int(data.get("data_points", 0)),
            }
        except Exception as exc:
            print(f"Failed to compute behavior pattern: {exc}")
            return {
                "metric_type": metric_type,
                "status": "error",
                "error": str(exc),
            }

    async def detect_anomalies(
        self,
        user_id: UUID,
        metric_type: str,
        threshold_std_devs: float = 2.0,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Detect anomalies using statistical methods.
        Points beyond threshold_std_devs from mean are flagged as anomalies.
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()

            # Get mean and std dev
            pattern = await self.compute_behavior_pattern(user_id, metric_type, days)
            if "mean_value" not in pattern:
                return {"anomalies": []}

            mean = pattern["mean_value"]
            std_dev = pattern["std_dev"]

            # Find values beyond threshold
            threshold = threshold_std_devs * std_dev
            lower_bound = mean - threshold
            upper_bound = mean + threshold

            query = f"""
            SELECT
                date,
                avg_value,
                abs(avg_value - {mean}) as deviation
            FROM korobos.metrics_archive
            WHERE user_id = parseUUID('{user_id}')
                AND metric_type = '{metric_type}'
                AND date >= '{start_date}'
                AND (avg_value < {lower_bound} OR avg_value > {upper_bound})
            ORDER BY deviation DESC;
            """
            results = await self._query(query)

            anomalies = [
                {
                    "date": r.get("date"),
                    "value": r.get("avg_value"),
                    "deviation": r.get("deviation"),
                }
                for r in results
            ]

            return {
                "metric_type": metric_type,
                "threshold_std_devs": threshold_std_devs,
                "mean": mean,
                "std_dev": std_dev,
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "anomaly_count": len(anomalies),
                "anomalies": anomalies[:10],  # Top 10 anomalies
            }
        except Exception as exc:
            print(f"Failed to detect anomalies: {exc}")
            return {"anomalies": []}

    async def get_cross_metric_correlation(
        self,
        user_id: UUID,
        metric_type_1: str,
        metric_type_2: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Compute correlation between two metrics over a time period.
        Returns Pearson correlation coefficient.
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()

            query = f"""
            WITH metric1 AS (
                SELECT date, avg_value as val1
                FROM korobos.metrics_archive
                WHERE user_id = parseUUID('{user_id}')
                    AND metric_type = '{metric_type_1}'
                    AND date >= '{start_date}'
            ),
            metric2 AS (
                SELECT date, avg_value as val2
                FROM korobos.metrics_archive
                WHERE user_id = parseUUID('{user_id}')
                    AND metric_type = '{metric_type_2}'
                    AND date >= '{start_date}'
            )
            SELECT
                count(*) as n,
                avg(m1.val1) as mean1,
                avg(m2.val2) as mean2,
                sqrt(sum((m1.val1 - mean1) * (m1.val1 - mean1)) / n) as std1,
                sqrt(sum((m2.val2 - mean2) * (m2.val2 - mean2)) / n) as std2,
                sum((m1.val1 - mean1) * (m2.val2 - mean2)) / (n * std1 * std2)
                  as correlation
            FROM metric1 m1
            JOIN metric2 m2 ON m1.date = m2.date;
            """
            results = await self._query(query)

            if not results:
                return {"correlation": 0.0}

            return {
                "metric_type_1": metric_type_1,
                "metric_type_2": metric_type_2,
                "period_days": days,
                "data_points": int(results[0].get("n", 0)),
                "correlation": round(float(results[0].get("correlation", 0)), 3),
            }
        except Exception as exc:
            print(f"Failed to compute correlation: {exc}")
            return {"correlation": 0.0}

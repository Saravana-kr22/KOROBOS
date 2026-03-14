"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Metrics collection for the Auth Service.
Tracks authentication events for monitoring and observability.
"""

from datetime import datetime
from typing import Dict, List

# Global metrics counters
_metrics: Dict[str, int] = {
    "login_success": 0,
    "login_failure": 0,
    "login_invalid_credentials": 0,
    "login_account_locked": 0,
    "login_email_not_verified": 0,
    "login_account_inactive": 0,
    "signup_success": 0,
    "signup_failure": 0,
    "signup_duplicate_email": 0,
    "signup_weak_password": 0,
    "signup_invalid_email": 0,
    "email_verification_success": 0,
    "email_verification_failure": 0,
    "email_verification_invalid_token": 0,
    "email_verification_resend_requested": 0,
    "password_reset_requested": 0,
    "password_reset_success": 0,
    "password_reset_failure": 0,
    "password_reset_invalid_token": 0,
    "token_refresh_success": 0,
    "token_refresh_failure": 0,
    "token_refresh_invalid_token": 0,
    "logout_success": 0,
    "logout_all_success": 0,
    "account_lockout": 0,
    "account_unlock": 0,
}

# Track last event timestamps for observability
_last_events: Dict[str, datetime] = {}

# Rate tracking (for anomaly detection)
_event_window: Dict[str, List[datetime]] = {
    "login_failure": [],
    "account_lockout": [],
}


def increment_metric(metric_name: str) -> None:
    """Increment a metric counter."""
    if metric_name in _metrics:
        _metrics[metric_name] += 1
        _last_events[metric_name] = datetime.now()


def get_metric(metric_name: str) -> int:
    """Get current value of a metric."""
    return _metrics.get(metric_name, 0)


def get_all_metrics() -> Dict[str, int]:
    """Get all metrics as a dictionary."""
    return _metrics.copy()


def get_metrics_summary() -> Dict[str, any]:
    """Get a summary of key metrics."""
    return {
        "authentication": {
            "login_success": get_metric("login_success"),
            "login_failure": get_metric("login_failure"),
            "login_invalid_credentials": get_metric("login_invalid_credentials"),
            "login_account_locked": get_metric("login_account_locked"),
            "login_email_not_verified": get_metric("login_email_not_verified"),
            "login_account_inactive": get_metric("login_account_inactive"),
        },
        "registration": {
            "signup_success": get_metric("signup_success"),
            "signup_failure": get_metric("signup_failure"),
            "signup_duplicate_email": get_metric("signup_duplicate_email"),
            "signup_weak_password": get_metric("signup_weak_password"),
            "signup_invalid_email": get_metric("signup_invalid_email"),
        },
        "email_verification": {
            "success": get_metric("email_verification_success"),
            "failure": get_metric("email_verification_failure"),
            "invalid_token": get_metric("email_verification_invalid_token"),
            "resend_requested": get_metric("email_verification_resend_requested"),
        },
        "password_reset": {
            "requested": get_metric("password_reset_requested"),
            "success": get_metric("password_reset_success"),
            "failure": get_metric("password_reset_failure"),
            "invalid_token": get_metric("password_reset_invalid_token"),
        },
        "token_management": {
            "refresh_success": get_metric("token_refresh_success"),
            "refresh_failure": get_metric("token_refresh_failure"),
            "refresh_invalid_token": get_metric("token_refresh_invalid_token"),
        },
        "session_management": {
            "logout_success": get_metric("logout_success"),
            "logout_all_success": get_metric("logout_all_success"),
        },
        "security": {
            "account_lockout": get_metric("account_lockout"),
            "account_unlock": get_metric("account_unlock"),
        },
    }


def get_prometheus_metrics() -> str:
    """
    Export metrics in Prometheus text exposition format.

    Returns:
        Prometheus-compatible metrics string.
    """
    lines = [
        "# HELP auth_login_success_total Total successful logins",
        "# TYPE auth_login_success_total counter",
        f"auth_login_success_total {get_metric('login_success')}",
        "",
        "# HELP auth_login_failure_total Total failed login attempts",
        "# TYPE auth_login_failure_total counter",
        f"auth_login_failure_total {get_metric('login_failure')}",
        "",
        "# HELP auth_signup_success_total Total successful signups",
        "# TYPE auth_signup_success_total counter",
        f"auth_signup_success_total {get_metric('signup_success')}",
        "",
        "# HELP auth_signup_failure_total Total failed signups",
        "# TYPE auth_signup_failure_total counter",
        f"auth_signup_failure_total {get_metric('signup_failure')}",
        "",
        "# HELP auth_email_verification_success_total Successful email verifications",
        "# TYPE auth_email_verification_success_total counter",
        (
            f"auth_email_verification_success_total "
            f"{get_metric('email_verification_success')}"
        ),
        "",
        "# HELP auth_email_verification_resend_total Email resend requests",
        "# TYPE auth_email_verification_resend_total counter",
        (
            f"auth_email_verification_resend_total "
            f"{get_metric('email_verification_resend_requested')}"
        ),
        "",
        "# HELP auth_password_reset_requested_total Password reset requests",
        "# TYPE auth_password_reset_requested_total counter",
        f"auth_password_reset_requested_total {get_metric('password_reset_requested')}",
        "",
        "# HELP auth_password_reset_success_total Total successful password resets",
        "# TYPE auth_password_reset_success_total counter",
        f"auth_password_reset_success_total {get_metric('password_reset_success')}",
        "",
        "# HELP auth_token_refresh_success_total Total successful token refreshes",
        "# TYPE auth_token_refresh_success_total counter",
        f"auth_token_refresh_success_total {get_metric('token_refresh_success')}",
        "",
        "# HELP auth_token_refresh_failure_total Total failed token refreshes",
        "# TYPE auth_token_refresh_failure_total counter",
        f"auth_token_refresh_failure_total {get_metric('token_refresh_failure')}",
        "",
        "# HELP auth_account_lockout_total Account lockouts due to failed attempts",
        "# TYPE auth_account_lockout_total counter",
        f"auth_account_lockout_total {get_metric('account_lockout')}",
        "",
        "# HELP auth_account_unlock_total Total account unlocks",
        "# TYPE auth_account_unlock_total counter",
        f"auth_account_unlock_total {get_metric('account_unlock')}",
    ]

    return "\n".join(lines) + "\n"


def reset_metrics() -> None:
    """Reset all metrics to zero (for testing only)."""
    global _metrics, _last_events
    _metrics = {k: 0 for k in _metrics}
    _last_events.clear()

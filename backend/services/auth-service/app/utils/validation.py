"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Validation utilities — password strength, email format, etc.
"""

import re


class PasswordValidator:
    """Validate password strength against security requirements."""

    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Plain-text password to validate.

        Returns:
            Tuple of (is_valid: bool, message: str).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"

        return True, "Password meets all requirements"


class EmailValidator:
    """Validate email format."""

    @staticmethod
    def validate(email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate.

        Returns:
            True if email is valid, False otherwise.
        """
        # RFC 5322 simplified pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

"""Output sanitizer: Removes sensitive information from logs and outputs."""

import re
from typing import Any, Dict, List


class OutputSanitizer:
    """Sanitizes output to remove sensitive information."""

    def __init__(self):
        # Patterns for sensitive data
        self.patterns = [
            # API Keys
            (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API_KEY_REDACTED'),
            (r'["\']?apikey["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API_KEY_REDACTED'),

            # Passwords
            (r'["\']?password["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', 'PASSWORD_REDACTED'),
            (r'["\']?passwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', 'PASSWORD_REDACTED'),
            (r'["\']?pwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', 'PASSWORD_REDACTED'),

            # Tokens
            (r'["\']?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'TOKEN_REDACTED'),
            (r'["\']?access_token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'TOKEN_REDACTED'),
            (r'["\']?bearer["\']?\s+([a-zA-Z0-9_\-\.]{20,})', 'TOKEN_REDACTED'),

            # AWS Keys
            (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY_REDACTED'),
            (r'aws_secret_access_key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?', 'AWS_SECRET_REDACTED'),

            # Private keys
            (r'-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', 'PRIVATE_KEY_REDACTED'),

            # Database URLs
            (r'(postgres|mysql|mongodb)://[^:]+:([^@]+)@', r'\1://USER:PASSWORD_REDACTED@'),

            # Generic secrets
            (r'["\']?secret["\']?\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?', 'SECRET_REDACTED'),
        ]

    def sanitize(self, text: str) -> str:
        """Remove sensitive information from text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)

        sanitized = text

        for pattern, replacement in self.patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE | re.DOTALL)

        return sanitized

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for key, value in data.items():
            # Check if key itself is sensitive
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in ['password', 'secret', 'token', 'key', 'api']):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item) if isinstance(item, dict) else self.sanitize(str(item))
                    for item in value
                ]
            elif isinstance(value, str):
                sanitized[key] = self.sanitize(value)
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Recursively sanitize a list.

        Args:
            data: List to sanitize

        Returns:
            Sanitized list
        """
        return [
            self.sanitize_dict(item) if isinstance(item, dict)
            else self.sanitize(str(item)) if isinstance(item, str)
            else item
            for item in data
        ]


# Global instance
_sanitizer = None


def get_sanitizer() -> OutputSanitizer:
    """Get or create global sanitizer instance."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = OutputSanitizer()
    return _sanitizer

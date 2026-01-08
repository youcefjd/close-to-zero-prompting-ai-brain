"""Output sanitizer: Removes sensitive information from logs and outputs."""

import re
from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass
class SanitizationResult:
    """Result of sanitization operation."""
    sanitized_content: str
    redactions: List[str]
    context: str = ""


class OutputSanitizer:
    """Sanitizes output to remove sensitive information."""

    def __init__(self):
        # Patterns for sensitive data: (pattern, redaction_label)
        self.patterns = [
            # PII Patterns
            (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN_REDACTED'),  # SSN
            (r'\b\d{3}\.\d{2}\.\d{4}\b', 'SSN_REDACTED'),  # SSN with dots
            (r'\b\d{9}\b', 'SSN_REDACTED'),  # SSN without separators (9 digits)
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL_REDACTED'),  # Email
            (r'\b\d{3}-\d{3}-\d{4}\b', 'PHONE_REDACTED'),  # US phone (XXX-XXX-XXXX)
            (r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', 'PHONE_REDACTED'),  # US phone ((XXX) XXX-XXXX)
            (r'\b\d{3}\.\d{3}\.\d{4}\b', 'PHONE_REDACTED'),  # US phone (XXX.XXX.XXXX)
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'CREDIT_CARD_REDACTED'),  # Credit card
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_ADDRESS_REDACTED'),  # IP address
            
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

    def has_secrets(self, text: str) -> bool:
        """Check if text contains secrets without sanitizing.
        
        Args:
            text: Text to check
            
        Returns:
            True if secrets detected, False otherwise
        """
        if not isinstance(text, str):
            text = str(text)
        
        for pattern, _ in self.patterns:
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                return True
        return False

    def sanitize(self, text: str, context: str = "") -> SanitizationResult:
        """Remove sensitive information from text.

        Args:
            text: Text to sanitize
            context: Optional context for logging (e.g., tool name)

        Returns:
            SanitizationResult with sanitized content and list of redactions
        """
        if not isinstance(text, str):
            text = str(text)

        sanitized = text
        redactions = []

        for pattern, redaction_label in self.patterns:
            matches = re.findall(pattern, sanitized, flags=re.IGNORECASE | re.DOTALL)
            if matches:
                # Track what was redacted
                if redaction_label not in redactions:
                    redactions.append(redaction_label)
                # Apply redaction
                sanitized = re.sub(pattern, redaction_label, sanitized, flags=re.IGNORECASE | re.DOTALL)

        return SanitizationResult(
            sanitized_content=sanitized,
            redactions=redactions,
            context=context
        )

    def sanitize_dict(self, data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Recursively sanitize a dictionary.

        Args:
            data: Dictionary to sanitize
            context: Optional context for logging

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
                sanitized[key] = self.sanitize_dict(value, context)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item, context) if isinstance(item, dict) 
                    else self.sanitize(str(item), context).sanitized_content
                    for item in value
                ]
            elif isinstance(value, str):
                result = self.sanitize(value, context)
                sanitized[key] = result.sanitized_content
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

"""Auth Broker: Identity Management for Self-Evolving Agents.

The Golden Rule: Context is Public, Environment is Private
- Chat Context: Treat as public. Never put keys here.
- Host Environment (.env / ~/.aws / Keychain): Treat as private. Keys live here.

Three Authentication Patterns:
1. Host Inheritance (AWS, K8s) - Agent inherits from host CLI credentials
2. Secret Vault (.env) - For API keys, username/password
3. OAuth 2.0 - For user data (Gmail, Calendar)
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
import subprocess
import json


class NeedAuthError(Exception):
    """Raised when authentication is required."""
    def __init__(self, message: str, auth_type: str, service_name: str, action: Optional[str] = None):
        self.message = message
        self.auth_type = auth_type  # "host", "env", "oauth"
        self.service_name = service_name
        self.action = action
        super().__init__(self.message)


class AuthBroker:
    """The Gatekeeper for all Agents - handles authentication patterns."""
    
    def __init__(self):
        self.env_file = Path(".env")
        self.secrets_dir = Path(".secrets")
        self.secrets_dir.mkdir(exist_ok=True)
    
    def require_auth(self, service_name: str, auth_pattern: Optional[str] = None) -> bool:
        """
        The Gatekeeper function for all Agents.
        
        Args:
            service_name: Name of the service (e.g., "aws", "cookidoo", "gmail")
            auth_pattern: Optional override for auth pattern ("host", "env", "oauth")
        
        Returns:
            True if authenticated, raises NeedAuthError if not
        
        Raises:
            NeedAuthError: When authentication is required
        """
        # Auto-detect auth pattern if not provided
        if not auth_pattern:
            auth_pattern = self._detect_auth_pattern(service_name)
        
        # Check if already authenticated
        if self._has_credentials(service_name, auth_pattern):
            return True
        
        # Not authenticated - raise appropriate error
        self._raise_auth_error(service_name, auth_pattern)
    
    def _detect_auth_pattern(self, service_name: str) -> str:
        """Detect which authentication pattern to use for a service."""
        service_lower = service_name.lower()
        
        # Pattern 1: Host Inheritance (CLI tools)
        host_inheritance_services = ["aws", "eks", "kubernetes", "k8s", "kubectl", "terraform", "gcloud", "azure"]
        if any(svc in service_lower for svc in host_inheritance_services):
            return "host"
        
        # Pattern 3: OAuth 2.0 (User data)
        oauth_services = ["gmail", "google", "calendar", "spotify", "github", "oauth"]
        if any(svc in service_lower for svc in oauth_services):
            return "oauth"
        
        # Pattern 2: Secret Vault (Default for API keys)
        return "env"
    
    def _has_credentials(self, service_name: str, auth_pattern: str) -> bool:
        """Check if credentials are available for a service."""
        if auth_pattern == "host":
            return self._check_host_credentials(service_name)
        elif auth_pattern == "env":
            return self._check_env_credentials(service_name)
        elif auth_pattern == "oauth":
            return self._check_oauth_credentials(service_name)
        return False
    
    def _check_host_credentials(self, service_name: str) -> bool:
        """Check if host CLI credentials are available."""
        service_lower = service_name.lower()
        
        if "aws" in service_lower:
            # Check AWS credentials
            aws_creds = Path.home() / ".aws" / "credentials"
            aws_config = Path.home() / ".aws" / "config"
            if aws_creds.exists() or aws_config.exists():
                # Try to verify with AWS CLI
                try:
                    result = subprocess.run(
                        ["aws", "sts", "get-caller-identity"],
                        capture_output=True,
                        timeout=5
                    )
                    return result.returncode == 0
                except:
                    return False
            return False
        
        elif "kubernetes" in service_lower or "k8s" in service_lower or "kubectl" in service_lower:
            # Check kubeconfig
            kubeconfig = Path.home() / ".kube" / "config"
            if kubeconfig.exists():
                # Try to verify with kubectl
                try:
                    result = subprocess.run(
                        ["kubectl", "cluster-info"],
                        capture_output=True,
                        timeout=5
                    )
                    return result.returncode == 0
                except:
                    return False
            return False
        
        elif "terraform" in service_lower:
            # Terraform uses provider-specific credentials (AWS, GCP, etc.)
            # Check if any provider credentials exist
            return self._check_host_credentials("aws") or self._check_host_credentials("gcp")
        
        return False
    
    def _check_env_credentials(self, service_name: str) -> bool:
        """Check if environment variable credentials are available."""
        service_upper = service_name.upper().replace("-", "_")
        
        # Check common credential patterns
        patterns = [
            f"{service_upper}_API_KEY",
            f"{service_upper}_TOKEN",
            f"{service_upper}_PASSWORD",
            f"{service_upper}_USER",
            f"{service_upper}_USERNAME",
        ]
        
        # Check .env file
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                env_content = f.read()
                for pattern in patterns:
                    if pattern in env_content:
                        # Check if it's actually set (not empty)
                        if os.getenv(pattern):
                            return True
        
        # Check environment variables directly
        for pattern in patterns:
            if os.getenv(pattern):
                return True
        
        return False
    
    def _check_oauth_credentials(self, service_name: str) -> bool:
        """Check if OAuth token is available."""
        token_file = self.secrets_dir / f"{service_name}_token.json"
        return token_file.exists()
    
    def _raise_auth_error(self, service_name: str, auth_pattern: str):
        """Raise appropriate authentication error based on pattern."""
        if auth_pattern == "host":
            self._raise_host_auth_error(service_name)
        elif auth_pattern == "env":
            self._raise_env_auth_error(service_name)
        elif auth_pattern == "oauth":
            self._raise_oauth_auth_error(service_name)
    
    def _raise_host_auth_error(self, service_name: str):
        """Raise error for host inheritance pattern."""
        service_lower = service_name.lower()
        
        if "aws" in service_lower:
            action = "aws configure"
            if "sso" in service_lower:
                action = "aws sso login"
            raise NeedAuthError(
                f"I need AWS access. Please run '{action}' in your terminal, then tell me 'Ready'.",
                auth_type="host",
                service_name="aws",
                action=action
            )
        
        elif "kubernetes" in service_lower or "k8s" in service_lower or "kubectl" in service_lower:
            raise NeedAuthError(
                "I need Kubernetes access. Please configure kubectl (e.g., 'aws eks update-kubeconfig --name <cluster>'), then tell me 'Ready'.",
                auth_type="host",
                service_name="kubernetes",
                action="kubectl config"
            )
        
        elif "terraform" in service_lower:
            raise NeedAuthError(
                "I need Terraform access. Please configure your cloud provider credentials (AWS, GCP, etc.), then tell me 'Ready'.",
                auth_type="host",
                service_name="terraform",
                action="terraform init"
            )
        
        else:
            raise NeedAuthError(
                f"I need {service_name} access. Please configure your CLI credentials, then tell me 'Ready'.",
                auth_type="host",
                service_name=service_name,
                action="configure"
            )
    
    def _raise_env_auth_error(self, service_name: str):
        """Raise error for secret vault pattern."""
        service_upper = service_name.upper().replace("-", "_")
        
        # Suggest common env var names
        env_vars = [
            f"{service_upper}_API_KEY",
            f"{service_upper}_TOKEN",
            f"{service_upper}_USER",
            f"{service_upper}_PASSWORD",
        ]
        
        raise NeedAuthError(
            f"I need {service_name} credentials. Please run this command to securely add them:\n"
            f"  ./scripts/add_secret.sh {service_upper}_API_KEY\n"
            f"Or add them to .env file:\n"
            f"  {service_upper}_API_KEY=your_key_here",
            auth_type="env",
            service_name=service_name,
            action=f"./scripts/add_secret.sh {service_upper}_API_KEY"
        )
    
    def _raise_oauth_auth_error(self, service_name: str):
        """Raise error for OAuth pattern."""
        # Generate OAuth URL (would be service-specific in production)
        oauth_url = self._generate_oauth_url(service_name)
        
        raise NeedAuthError(
            f"I need {service_name} access. Please click this authorization link to grant read-only access:\n"
            f"  {oauth_url}\n"
            f"After authorization, tell me 'Ready'.",
            auth_type="oauth",
            service_name=service_name,
            action=oauth_url
        )
    
    def _generate_oauth_url(self, service_name: str) -> str:
        """Generate OAuth authorization URL (placeholder - would be service-specific)."""
        service_lower = service_name.lower()
        
        if "gmail" in service_lower or "google" in service_lower:
            # Google OAuth URL (would use actual client_id, redirect_uri, etc.)
            return "https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=readonly&response_type=code"
        
        elif "spotify" in service_lower:
            return "https://accounts.spotify.com/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=readonly&response_type=code"
        
        else:
            return f"https://oauth.{service_name}.com/authorize"
    
    def check_and_prompt(self, service_name: str) -> bool:
        """
        Wrapper function that checks auth and prompts if needed.
        Returns True if authenticated, raises NeedAuthError if not.
        """
        return self.require_auth(service_name)


def get_auth_broker() -> AuthBroker:
    """Get singleton AuthBroker instance."""
    if not hasattr(get_auth_broker, '_instance'):
        get_auth_broker._instance = AuthBroker()
    return get_auth_broker._instance


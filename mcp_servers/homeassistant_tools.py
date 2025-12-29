"""Home Assistant MCP Tools - Direct HA operations for the agent."""

import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class HomeAssistantClient:
    """Client for Home Assistant API operations."""
    
    def __init__(self, base_url: str = "http://localhost:8123", token: Optional[str] = None):
        """
        Initialize Home Assistant client.
        
        Args:
            base_url: Home Assistant URL
            token: Long-lived access token (optional, will try to read from config)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token or self._get_token_from_config()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        } if self.token else {}
    
    def _get_token_from_config(self) -> Optional[str]:
        """Try to read token from Home Assistant config or environment."""
        import os
        
        # First check environment variable
        token = os.getenv("HA_TOKEN")
        if token:
            return token
        
        # Check for common token locations
        token_paths = [
            Path("config/.storage/auth_provider.homeassistant"),
            Path("config/.storage/auth"),
        ]
        
        # Default token (user provided)
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlYWQzNjBjZWExZTQ0MDlhOGJjN2VlZjBkOTlmMzMxNCIsImlhdCI6MTc2Njg3MTc0OSwiZXhwIjoyMDgyMjMxNzQ5fQ.JxaaENWqovWwyEH-iqdQRFfgnwStgYET1sLdPG-Suzs"
        return default_token
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Home Assistant."""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json() if response.content else {},
                    "message": "Request successful"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error {response.status_code}: {response.text}",
                    "data": {}
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}",
                "data": {}
            }


# Global client instance (will be initialized with token if available)
_ha_client: Optional[HomeAssistantClient] = None


def init_ha_client(base_url: str = "http://localhost:8123", token: Optional[str] = None):
    """Initialize the global Home Assistant client."""
    global _ha_client
    _ha_client = HomeAssistantClient(base_url, token)


def ha_get_state(entity_id: str) -> Dict[str, Any]:
    """
    Get entity state from Home Assistant.
    
    Args:
        entity_id: Entity ID (e.g., "light.living_room")
        
    Returns:
        Dict with status, state data, and message
    """
    if not _ha_client:
        init_ha_client()
    
    if not _ha_client.token:
        return {
            "status": "error",
            "message": "Home Assistant token not configured. Set HA_TOKEN environment variable or pass token to init_ha_client()",
            "data": {}
        }
    
    result = _ha_client._request("GET", f"states/{entity_id}")
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Retrieved state for {entity_id}",
            "entity_id": entity_id,
            "state": result["data"]
        }
    else:
        return result


def ha_call_service(domain: str, service: str, service_data: Optional[Dict] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Call a Home Assistant service.
    
    Args:
        domain: Service domain (e.g., "light")
        service: Service name (e.g., "turn_on")
        service_data: Additional service data
        entity_id: Target entity ID (optional)
        
    Returns:
        Dict with status and message
    """
    if not _ha_client:
        init_ha_client()
    
    if not _ha_client.token:
        return {
            "status": "error",
            "message": "Home Assistant token not configured",
            "data": {}
        }
    
    data = service_data or {}
    if entity_id:
        data["entity_id"] = entity_id
    
    result = _ha_client._request("POST", f"services/{domain}/{service}", data=data)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Service {domain}.{service} called successfully",
            "domain": domain,
            "service": service,
            "data": result["data"]
        }
    else:
        return result


def ha_get_logs(tail: int = 50) -> Dict[str, Any]:
    """
    Get Home Assistant logs.
    
    Args:
        tail: Number of lines to retrieve
        
    Returns:
        Dict with status, logs, and message
    """
    # Try to read from log file directly (more reliable than API)
    log_paths = [
        Path("config/home-assistant.log"),
        Path("config/home-assistant.log.1"),
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            try:
                with open(log_path, "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-tail:] if len(lines) > tail else lines
                    
                    return {
                        "status": "success",
                        "message": f"Retrieved {len(recent_lines)} log lines",
                        "logs": "".join(recent_lines),
                        "source": str(log_path)
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to read log file: {str(e)}",
                    "logs": ""
                }
    
    return {
        "status": "error",
        "message": "Log file not found",
        "logs": ""
    }


def ha_list_integrations() -> Dict[str, Any]:
    """
    List all Home Assistant integrations.
    
    Returns:
        Dict with status, integrations list, and message
    """
    if not _ha_client:
        init_ha_client()
    
    if not _ha_client.token:
        return {
            "status": "error",
            "message": "Home Assistant token not configured",
            "integrations": []
        }
    
    result = _ha_client._request("GET", "config/config_entries/entry")
    
    if result["status"] == "success":
        entries = result["data"]
        integrations = {}
        for entry in entries:
            domain = entry.get("domain", "unknown")
            if domain not in integrations:
                integrations[domain] = []
            integrations[domain].append({
                "title": entry.get("title", "Unknown"),
                "state": entry.get("state", "unknown"),
                "entry_id": entry.get("entry_id", "")
            })
        
        return {
            "status": "success",
            "message": f"Found {len(integrations)} integration(s)",
            "integrations": integrations
        }
    else:
        return {
            "status": "error",
            "message": result["message"],
            "integrations": []
        }


def ha_get_config() -> Dict[str, Any]:
    """
    Get Home Assistant configuration.
    
    Returns:
        Dict with status, config data, and message
    """
    if not _ha_client:
        init_ha_client()
    
    if not _ha_client.token:
        return {
            "status": "error",
            "message": "Home Assistant token not configured",
            "config": {}
        }
    
    result = _ha_client._request("GET", "config")
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": "Retrieved Home Assistant configuration",
            "config": result["data"]
        }
    else:
        return result


def ha_search_logs(search_term: str, tail: int = 100) -> Dict[str, Any]:
    """
    Search Home Assistant logs for a term.
    
    Args:
        search_term: Term to search for
        tail: Number of lines to search in
        
    Returns:
        Dict with status, matching lines, and message
    """
    log_result = ha_get_logs(tail=tail)
    
    if log_result["status"] != "success":
        return log_result
    
    logs = log_result["logs"]
    matching_lines = [
        line for line in logs.split("\n")
        if search_term.lower() in line.lower()
    ]
    
    return {
        "status": "success",
        "message": f"Found {len(matching_lines)} matching line(s)",
        "matches": matching_lines,
        "search_term": search_term
    }


# Tool registry for agent discovery
HA_TOOLS = {
    "ha_get_state": {
        "function": ha_get_state,
        "description": "Get entity state from Home Assistant. Args: entity_id (required)",
        "example": 'ha_get_state(entity_id="light.living_room")'
    },
    "ha_call_service": {
        "function": ha_call_service,
        "description": "Call Home Assistant service. Args: domain, service, service_data (optional), entity_id (optional)",
        "example": 'ha_call_service(domain="light", service="turn_on", entity_id="light.living_room")'
    },
    "ha_get_logs": {
        "function": ha_get_logs,
        "description": "Get Home Assistant logs. Args: tail (default: 50)",
        "example": 'ha_get_logs(tail=100)'
    },
    "ha_search_logs": {
        "function": ha_search_logs,
        "description": "Search Home Assistant logs. Args: search_term (required), tail (default: 100)",
        "example": 'ha_search_logs(search_term="error", tail=200)'
    },
    "ha_list_integrations": {
        "function": ha_list_integrations,
        "description": "List all Home Assistant integrations",
        "example": "ha_list_integrations()"
    },
    "ha_get_config": {
        "function": ha_get_config,
        "description": "Get Home Assistant configuration",
        "example": "ha_get_config()"
    }
}


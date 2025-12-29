"""Docker MCP Tools - Direct Docker operations for the agent."""

import subprocess
import json
from typing import Dict, Any, List, Optional


def docker_ps(filter_name: Optional[str] = None) -> Dict[str, Any]:
    """
    List Docker containers.
    
    Args:
        filter_name: Optional container name filter
        
    Returns:
        Dict with status, containers list, and message
    """
    try:
        cmd = ["docker", "ps", "--format", "json"]
        if filter_name:
            cmd.extend(["--filter", f"name={filter_name}"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to list containers: {result.stderr}",
                "containers": []
            }
        
        # Parse JSON lines
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return {
            "status": "success",
            "message": f"Found {len(containers)} container(s)",
            "containers": containers
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "containers": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "containers": []
        }


def docker_logs(container: str, tail: int = 50, follow: bool = False) -> Dict[str, Any]:
    """
    Get container logs.
    
    Args:
        container: Container name or ID
        tail: Number of lines to retrieve
        follow: Whether to follow logs (not implemented for agent use)
        
    Returns:
        Dict with status, logs, and message
    """
    try:
        cmd = ["docker", "logs", "--tail", str(tail), container]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to get logs: {result.stderr}",
                "logs": ""
            }
        
        return {
            "status": "success",
            "message": f"Retrieved {len(result.stdout.splitlines())} log lines",
            "logs": result.stdout,
            "container": container
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "logs": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "logs": ""
        }


def docker_exec(container: str, command: str) -> Dict[str, Any]:
    """
    Execute command in container.
    
    Args:
        container: Container name or ID
        command: Command to execute
        
    Returns:
        Dict with status, stdout, stderr, and exit_code
    """
    try:
        cmd = ["docker", "exec", container, "sh", "-c", command]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "message": f"Command executed with exit code {result.returncode}",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "container": container,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "stdout": "",
            "stderr": "Command execution exceeded 60 second timeout",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }


def docker_restart(container: str) -> Dict[str, Any]:
    """
    Restart a container.
    
    Args:
        container: Container name or ID
        
    Returns:
        Dict with status and message
    """
    try:
        result = subprocess.run(
            ["docker", "restart", container],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to restart container: {result.stderr}",
                "container": container
            }
        
        return {
            "status": "success",
            "message": f"Container {container} restarted successfully",
            "container": container
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "container": container
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "container": container
        }


def docker_inspect(container: str) -> Dict[str, Any]:
    """
    Inspect container details.
    
    Args:
        container: Container name or ID
        
    Returns:
        Dict with status, inspection data, and message
    """
    try:
        result = subprocess.run(
            ["docker", "inspect", container],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to inspect container: {result.stderr}",
                "data": {}
            }
        
        try:
            data = json.loads(result.stdout)
            return {
                "status": "success",
                "message": f"Inspected container {container}",
                "data": data[0] if data else {},
                "container": container
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Failed to parse inspection data",
                "data": {}
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "data": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "data": {}
        }


def docker_compose_up(compose_file: Optional[str] = None, service: Optional[str] = None) -> Dict[str, Any]:
    """
    Start docker-compose services.
    
    Args:
        compose_file: Path to docker-compose.yml (optional)
        service: Specific service to start (optional)
        
    Returns:
        Dict with status and message
    """
    try:
        cmd = ["docker", "compose"]
        if compose_file:
            cmd.extend(["-f", compose_file])
        cmd.append("up")
        if service:
            cmd.append(service)
        cmd.append("-d")  # Detached mode
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Failed to start services: {result.stderr}",
                "stdout": result.stdout
            }
        
        return {
            "status": "success",
            "message": f"Services started successfully",
            "stdout": result.stdout
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out",
            "stdout": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "stdout": ""
        }


# Tool registry for agent discovery
DOCKER_TOOLS = {
    "docker_ps": {
        "function": docker_ps,
        "description": "List Docker containers. Args: filter_name (optional)",
        "example": 'docker_ps(filter_name="homeassistant")'
    },
    "docker_logs": {
        "function": docker_logs,
        "description": "Get container logs. Args: container (required), tail (default: 50)",
        "example": 'docker_logs(container="homeassistant", tail=100)'
    },
    "docker_exec": {
        "function": docker_exec,
        "description": "Execute command in container. Args: container (required), command (required)",
        "example": 'docker_exec(container="homeassistant", command="ls -la /config")'
    },
    "docker_restart": {
        "function": docker_restart,
        "description": "Restart a container. Args: container (required)",
        "example": 'docker_restart(container="homeassistant")'
    },
    "docker_inspect": {
        "function": docker_inspect,
        "description": "Inspect container details. Args: container (required)",
        "example": 'docker_inspect(container="homeassistant")'
    },
    "docker_compose_up": {
        "function": docker_compose_up,
        "description": "Start docker-compose services. Args: compose_file (optional), service (optional)",
        "example": 'docker_compose_up(compose_file="docker-compose.yml")'
    }
}


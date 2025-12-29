"""Tools for the Builder Agent: file operations and shell execution."""

import subprocess
import shlex
from typing import Dict, Any
from pathlib import Path


# High-risk commands that should be blocked
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf ~",
    "format",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    "chmod 777",
    "chown",
]


def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file, creating directories if needed.
    
    Args:
        file_path: Path to the file (relative or absolute)
        content: Content to write to the file
        
    Returns:
        Dict with status and message
    """
    try:
        path = Path(file_path)
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        path.write_text(content, encoding='utf-8')
        
        return {
            "status": "success",
            "message": f"Successfully wrote {len(content)} characters to {file_path}",
            "file_path": str(path.absolute())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to write file: {str(e)}",
            "file_path": file_path
        }


def run_shell(command: str, cwd: str = None) -> Dict[str, Any]:
    """
    Execute a shell command with safety checks.
    
    Args:
        command: Shell command to execute
        cwd: Working directory for the command (optional)
        
    Returns:
        Dict with status, exit_code, stdout, stderr, and message
    """
    # Safety check: block dangerous commands
    command_lower = command.lower().strip()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return {
                "status": "error",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Blocked dangerous command: {dangerous}",
                "message": f"Command blocked for safety: {command}"
            }
    
    try:
        # Use shlex to properly parse the command
        cmd_parts = shlex.split(command)
        
        # Execute the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False  # Don't raise exception on non-zero exit
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": f"Command executed with exit code {result.returncode}"
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "message": "Command execution timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "message": f"Failed to execute command: {str(e)}"
        }



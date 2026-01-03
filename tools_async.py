"""Async Tools for the Builder Agent: file operations and shell execution.

This module provides async versions of tools for non-blocking execution.
"""

import asyncio
import subprocess
import shlex
from typing import Dict, Any, Optional
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


async def write_file_async(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write content to a file asynchronously, creating directories if needed.
    
    Args:
        file_path: Path to the file (relative or absolute)
        content: Content to write to the file
        
    Returns:
        Dict with status and message
    """
    try:
        # File I/O is relatively fast, but we can still make it async
        path = Path(file_path)
        
        # Create parent directories if they don't exist (run in executor)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, path.parent.mkdir, parents=True, exist_ok=True)
        
        # Write the file (run in executor)
        await loop.run_in_executor(
            None,
            lambda: path.write_text(content, encoding='utf-8')
        )
        
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


async def run_shell_async(
    command: str, 
    cwd: Optional[str] = None,
    timeout: Optional[float] = 300.0
) -> Dict[str, Any]:
    """
    Execute a shell command asynchronously with safety checks.
    
    Args:
        command: Shell command to execute
        cwd: Working directory for the command (optional)
        timeout: Maximum execution time in seconds (default: 300 = 5 minutes)
        
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
        
        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "exit_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "message": f"Command executed with exit code {process.returncode}"
            }
        except asyncio.TimeoutError:
            # Kill the process if it times out
            try:
                process.kill()
                await process.wait()
            except:
                pass
            
            return {
                "status": "error",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "message": f"Command execution timed out after {timeout} seconds"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "message": f"Failed to execute command: {str(e)}"
        }


# Keep synchronous versions for backward compatibility
from tools import write_file, run_shell


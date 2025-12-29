"""Fact-checking and validation system for agent actions."""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib


class FactChecker:
    """Validates agent actions and prevents hallucinations."""
    
    def __init__(self, memory_file: str = ".agent_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory of past successes/failures."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {"successes": [], "failures": [], "patterns": {}}
        return {"successes": [], "failures": [], "patterns": {}}
    
    def _save_memory(self):
        """Save memory to disk."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")
    
    def verify_file_exists(self, file_path: str) -> Dict[str, Any]:
        """Verify a file exists before operations."""
        # Handle both absolute and relative paths
        if file_path.startswith('/'):
            path = Path(file_path)
        else:
            path = Path(file_path)
            # Also try with config/ prefix for HA paths
            if not path.exists() and '/.storage/' in file_path:
                alt_path = Path(f"config/{file_path.lstrip('/')}")
                if alt_path.exists():
                    return {"exists": True, "path": str(alt_path), "verified": True}
        
        exists = path.exists()
        return {
            "exists": exists,
            "path": str(path),
            "verified": True,
            "message": f"File {'exists' if exists else 'does not exist'}: {path}"
        }
    
    def verify_file_content(self, file_path: str, expected_content: Optional[str] = None) -> Dict[str, Any]:
        """Verify file content matches expectations."""
        check = self.verify_file_exists(file_path)
        if not check["exists"]:
            return {**check, "content_verified": False, "message": "File does not exist, cannot verify content"}
        
        try:
            with open(check["path"], 'r') as f:
                actual_content = f.read()
            
            result = {
                "exists": True,
                "path": check["path"],
                "content_verified": True,
                "file_size": len(actual_content),
                "has_content": len(actual_content.strip()) > 0
            }
            
            if expected_content:
                # Check if expected content is in file
                if expected_content in actual_content:
                    result["matches_expected"] = True
                else:
                    result["matches_expected"] = False
                    result["message"] = "File exists but content does not match expected"
            
            return result
        except Exception as e:
            return {
                "exists": True,
                "content_verified": False,
                "error": str(e),
                "message": f"Could not read file: {e}"
            }
    
    def verify_command_output(self, command: str, expected_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Verify command output matches expectations."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "verified": True
            }
            
            if expected_pattern:
                if expected_pattern in result.stdout or expected_pattern in result.stderr:
                    output["matches_expected"] = True
                else:
                    output["matches_expected"] = False
                    output["message"] = f"Output does not contain expected pattern: {expected_pattern}"
            
            return output
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "verified": False,
                "error": "Command timed out",
                "message": "Command execution exceeded 10 second timeout"
            }
        except Exception as e:
            return {
                "command": command,
                "verified": False,
                "error": str(e),
                "message": f"Command execution failed: {e}"
            }
    
    def verify_docker_container(self, container_name: str) -> Dict[str, Any]:
        """Verify Docker container exists and is running."""
        result = self.verify_command_output(f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'")
        
        if result["success"]:
            containers = [line.strip() for line in result["stdout"].split('\n') if line.strip()]
            if container_name in containers or any(container_name in c for c in containers):
                # Check if running
                status_result = self.verify_command_output(f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'")
                is_running = "Up" in status_result.get("stdout", "")
                
                return {
                    "container_exists": True,
                    "container_name": container_name,
                    "is_running": is_running,
                    "verified": True,
                    "message": f"Container {container_name} exists and is {'running' if is_running else 'stopped'}"
                }
            else:
                return {
                    "container_exists": False,
                    "container_name": container_name,
                    "verified": True,
                    "message": f"Container {container_name} not found"
                }
        
        return {
            "container_exists": False,
            "verified": False,
            "error": result.get("error", "Unknown error"),
            "message": f"Could not verify container: {result.get('message', 'Unknown error')}"
        }
    
    def check_similar_failures(self, action_type: str, error_signature: str) -> Dict[str, Any]:
        """Check if similar actions have failed before."""
        failures = self.memory.get("failures", [])
        
        # Create a hash of the error signature for comparison
        error_hash = hashlib.md5(error_signature.encode()).hexdigest()[:8]
        
        similar_failures = [
            f for f in failures 
            if f.get("action_type") == action_type and 
            (error_hash in f.get("error_hash", "") or 
             error_signature[:50] in f.get("error", ""))
        ]
        
        if similar_failures:
            # Count how many times this pattern failed
            failure_count = len(similar_failures)
            last_failure = similar_failures[-1]
            
            return {
                "has_similar_failures": True,
                "failure_count": failure_count,
                "last_failure": last_failure.get("timestamp", "unknown"),
                "suggestion": self._generate_suggestion(action_type, failure_count, last_failure),
                "should_avoid": failure_count >= 3  # Avoid if failed 3+ times
            }
        
        return {
            "has_similar_failures": False,
            "failure_count": 0
        }
    
    def check_similar_successes(self, action_type: str) -> Dict[str, Any]:
        """Check if similar actions have succeeded before."""
        successes = self.memory.get("successes", [])
        
        similar_successes = [
            s for s in successes 
            if s.get("action_type") == action_type
        ]
        
        if similar_successes:
            return {
                "has_similar_successes": True,
                "success_count": len(similar_successes),
                "last_success": similar_successes[-1].get("timestamp", "unknown"),
                "pattern": similar_successes[-1].get("pattern", "")
            }
        
        return {
            "has_similar_successes": False,
            "success_count": 0
        }
    
    def record_success(self, action_type: str, action_details: Dict[str, Any], pattern: Optional[str] = None):
        """Record a successful action for learning."""
        success_record = {
            "action_type": action_type,
            "timestamp": str(Path(self.memory_file).stat().st_mtime) if os.path.exists(self.memory_file) else "unknown",
            "details": action_details,
            "pattern": pattern or action_type
        }
        
        self.memory.setdefault("successes", []).append(success_record)
        
        # Keep only last 100 successes
        if len(self.memory["successes"]) > 100:
            self.memory["successes"] = self.memory["successes"][-100:]
        
        self._save_memory()
    
    def record_failure(self, action_type: str, error: str, action_details: Dict[str, Any]):
        """Record a failed action for learning."""
        error_hash = hashlib.md5(error.encode()).hexdigest()[:8]
        
        failure_record = {
            "action_type": action_type,
            "timestamp": str(Path(self.memory_file).stat().st_mtime) if os.path.exists(self.memory_file) else "unknown",
            "error": error,
            "error_hash": error_hash,
            "details": action_details
        }
        
        self.memory.setdefault("failures", []).append(failure_record)
        
        # Keep only last 100 failures
        if len(self.memory["failures"]) > 100:
            self.memory["failures"] = self.memory["failures"][-100:]
        
        self._save_memory()
    
    def _generate_suggestion(self, action_type: str, failure_count: int, last_failure: Dict[str, Any]) -> str:
        """Generate suggestions based on failure patterns."""
        if failure_count >= 3:
            if action_type == "file_write":
                return "This file write pattern has failed 3+ times. Try: 1) Verify file path exists, 2) Check permissions, 3) Use simpler approach"
            elif action_type == "command_exec":
                return "This command has failed 3+ times. Try: 1) Verify command syntax, 2) Check prerequisites, 3) Use alternative method"
            elif action_type == "docker_operation":
                return "Docker operation has failed 3+ times. Try: 1) Verify container name, 2) Check Docker is running, 3) Use docker ps to list containers"
        
        return f"This action has failed {failure_count} time(s) before. Consider a different approach."
    
    def validate_action_before_execution(self, action_type: str, action_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an action before execution to prevent obvious mistakes."""
        validation = {
            "should_proceed": True,
            "warnings": [],
            "suggestions": []
        }
        
        if action_type == "file_write":
            file_path = action_details.get("file_path", "")
            if file_path:
                # Check if file exists and we're overwriting
                file_check = self.verify_file_exists(file_path)
                if file_check["exists"]:
                    validation["warnings"].append(f"File {file_path} already exists - will be overwritten")
                
                # Check if directory exists
                dir_path = Path(file_path).parent
                if not dir_path.exists() and str(dir_path) != ".":
                    validation["should_proceed"] = False
                    validation["warnings"].append(f"Directory {dir_path} does not exist - cannot write file")
        
        elif action_type == "file_delete":
            file_path = action_details.get("file_path", "")
            if file_path:
                file_check = self.verify_file_exists(file_path)
                if not file_check["exists"]:
                    validation["warnings"].append(f"File {file_path} does not exist - deletion will fail")
                    validation["should_proceed"] = False
        
        elif action_type == "command_exec":
            command = action_details.get("command", "")
            # Check for dangerous commands
            dangerous_patterns = ["rm -rf /", "format", "dd if="]
            for pattern in dangerous_patterns:
                if pattern in command:
                    validation["should_proceed"] = False
                    validation["warnings"].append(f"Dangerous command detected: {pattern}")
            
            # Check for Docker commands
            if "docker" in command:
                if "exec" in command or "run" in command:
                    container_match = None
                    # Try to extract container name
                    import re
                    match = re.search(r"docker\s+(?:exec|run)\s+(\w+)", command)
                    if match:
                        container_name = match.group(1)
                        container_check = self.verify_docker_container(container_name)
                        if not container_check.get("container_exists"):
                            validation["warnings"].append(f"Container {container_name} does not exist")
                            validation["should_proceed"] = False
        
        # Check for similar failures
        error_sig = f"{action_type}:{str(action_details)}"
        similar_failures = self.check_similar_failures(action_type, error_sig)
        if similar_failures.get("should_avoid"):
            validation["should_proceed"] = False
            validation["warnings"].append(similar_failures.get("suggestion", "This action has failed multiple times"))
        
        return validation
    
    def retrieve_solution(self, task: str) -> Optional[Dict[str, Any]]:
        """Retrieve similar solution from memory."""
        if not Path(self.memory_file).exists():
            return None
        
        try:
            with open(self.memory_file) as f:
                memory = json.load(f)
            
            solutions = memory.get("solutions", [])
            
            # Simple similarity check (can be enhanced with embeddings)
            task_lower = task.lower()
            for solution in solutions:
                solution_task = solution.get("task", "").lower()
                # Check for keyword overlap
                task_words = set(task_lower.split())
                solution_words = set(solution_task.split())
                overlap = len(task_words & solution_words) / max(len(task_words), 1)
                
                if overlap > 0.5:  # 50% keyword overlap
                    return solution
            
            return None
        except:
            return None
    
    def store_solution(self, task: str, result: Dict[str, Any]) -> None:
        """Store successful solution in memory."""
        if not Path(self.memory_file).exists():
            memory = {"solutions": [], "failures": self.memory.get("failures", []), "successes": self.memory.get("successes", [])}
        else:
            try:
                with open(self.memory_file) as f:
                    memory = json.load(f)
            except:
                memory = {"solutions": [], "failures": [], "successes": []}
        
        solution = {
            "task": task,
            "result": result,
            "timestamp": str(__import__("datetime").datetime.now()),
            "summary": result.get("message", "")[:200] if isinstance(result.get("message"), str) else ""
        }
        
        if "solutions" not in memory:
            memory["solutions"] = []
        memory["solutions"].append(solution)
        
        # Keep only last 100 solutions
        if len(memory["solutions"]) > 100:
            memory["solutions"] = memory["solutions"][-100:]
        
        with open(self.memory_file, "w") as f:
            json.dump(memory, f, indent=2)
    
    def pre_execution_check(self, task: str, context: Dict) -> Dict[str, Any]:
        """Pre-execution validation to prevent known issues."""
        # Check for similar failures
        similar_failures = self.check_similar_failures("execution", task)
        if similar_failures.get("should_avoid"):
            return {
                "should_abort": True,
                "reason": f"Similar task failed {similar_failures['failure_count']} time(s) before",
                "suggestion": "Try a different approach or break task into smaller steps"
            }
        
        return {"should_abort": False}
    
    def post_execution_validation(self, task: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-execution validation."""
        if result.get("status") != "success":
            return {"is_valid": False, "warning": "Execution did not succeed"}
        
        return {"is_valid": True}
    
    def validate_action_after_execution(self, action_type: str, action_details: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an action after execution to verify it worked."""
        validation = {
            "verified": False,
            "warnings": [],
            "success": result.get("status") == "success"
        }
        
        if action_type == "file_write":
            file_path = action_details.get("file_path", "")
            if file_path:
                file_check = self.verify_file_content(file_path)
                if file_check.get("exists") and file_check.get("has_content"):
                    validation["verified"] = True
                else:
                    validation["warnings"].append("File was written but appears empty or does not exist")
        
        elif action_type == "command_exec":
            command = action_details.get("command", "")
            exit_code = result.get("exit_code", -1)
            if exit_code == 0:
                validation["verified"] = True
            else:
                validation["warnings"].append(f"Command exited with code {exit_code}")
        
        return validation


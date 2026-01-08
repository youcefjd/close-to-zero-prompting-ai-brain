"""Self-Healing System: Detects, analyzes, and fixes issues in the codebase itself.

This module enables the AI Brain to:
1. Detect when errors are related to its own codebase
2. Analyze root causes (scalability, reliability, auditability, governance)
3. Propose and validate fixes
4. Apply fixes safely with rollback capability
5. Learn from successes and failures
"""

import os
import ast
import importlib
import subprocess
import traceback
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import hashlib

from governance import get_governance, RiskLevel
from fact_checker import FactChecker
from output_sanitizer import get_sanitizer
from llm_provider import LLMProvider, create_llm_provider
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


@dataclass
class CodebaseIssue:
    """Represents an issue detected in the codebase."""
    file_path: str
    line_number: Optional[int]
    issue_type: str  # "scalability", "reliability", "auditability", "governance", "bug", "performance"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    fix_validated: bool = False
    fix_applied: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SelfHealingResult:
    """Result of self-healing operation."""
    success: bool
    issue_detected: bool
    issue: Optional[CodebaseIssue] = None
    fix_proposed: bool = False
    fix_validated: bool = False
    fix_applied: bool = False
    rollback_performed: bool = False
    message: str = ""
    changes: List[Dict[str, Any]] = field(default_factory=list)


class CodebaseAnalyzer:
    """Analyzes codebase to detect issues and understand limitations."""
    
    def __init__(self, codebase_root: str = "."):
        self.codebase_root = Path(codebase_root)
        self.sanitizer = get_sanitizer()
    
    def is_codebase_error(self, error: Exception, stack_trace: str) -> bool:
        """Determine if error is related to the codebase itself.
        
        Args:
            error: The exception that occurred
            stack_trace: Full stack trace
            
        Returns:
            True if error is in codebase, False if external
        """
        # Check if stack trace references codebase files
        codebase_files = [
            "autonomous_orchestrator.py",
            "sub_agents/",
            "tools.py",
            "governance.py",
            "fact_checker.py",
            "context_manager.py",
            "output_sanitizer.py",
            "self_healing.py",
            "agent_enhanced.py",
        ]
        
        stack_lower = stack_trace.lower()
        for file_pattern in codebase_files:
            if file_pattern.lower() in stack_lower:
                return True
        
        # Check error type - some errors are clearly codebase issues
        codebase_error_types = [
            "AttributeError",  # Missing method/attribute
            "NameError",  # Undefined variable
            "TypeError",  # Type mismatch
            "ImportError",  # Import issue
            "SyntaxError",  # Syntax error
        ]
        
        if type(error).__name__ in codebase_error_types:
            return True
        
        return False
    
    def analyze_issue(
        self,
        error: Exception,
        stack_trace: str,
        context: Dict[str, Any]
    ) -> Optional[CodebaseIssue]:
        """Analyze error to identify root cause and issue type.
        
        Args:
            error: The exception
            stack_trace: Full stack trace
            context: Execution context (task, agent, etc.)
            
        Returns:
            CodebaseIssue if issue detected, None otherwise
        """
        if not self.is_codebase_error(error, stack_trace):
            return None
        
        # Extract file and line from stack trace
        file_path, line_number = self._extract_location(stack_trace)
        
        # Determine issue type based on error
        issue_type = self._classify_issue(error, stack_trace, context)
        
        # Determine severity
        severity = self._determine_severity(error, issue_type, context)
        
        # Analyze root cause
        root_cause = self._analyze_root_cause(error, stack_trace, file_path, context)
        
        return CodebaseIssue(
            file_path=file_path or "unknown",
            line_number=line_number,
            issue_type=issue_type,
            severity=severity,
            description=str(error),
            error_message=str(error),
            stack_trace=stack_trace,
            root_cause=root_cause
        )
    
    def _extract_location(self, stack_trace: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from stack trace."""
        lines = stack_trace.split('\n')
        for line in lines:
            if 'File "' in line:
                # Extract file path
                start = line.find('File "') + 6
                end = line.find('"', start)
                if end > start:
                    file_path = line[start:end]
                    # Extract line number
                    if ', line ' in line:
                        line_start = line.find(', line ') + 7
                        line_end = line.find(',', line_start)
                        if line_end == -1:
                            line_end = line.find(')', line_start)
                        if line_end > line_start:
                            try:
                                line_num = int(line[line_start:line_end])
                                return file_path, line_num
                            except:
                                pass
                    return file_path, None
        return None, None
    
    def _classify_issue(
        self,
        error: Exception,
        stack_trace: str,
        context: Dict[str, Any]
    ) -> str:
        """Classify the type of issue."""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        stack_lower = stack_trace.lower()
        
        # Scalability issues
        if "timeout" in error_msg or "timeout" in stack_lower:
            return "scalability"
        if "blocking" in error_msg or "deadlock" in error_msg:
            return "scalability"
        
        # Reliability issues
        if error_type == "AttributeError":
            if "has_secrets" in error_msg or "hasattr" in stack_lower:
                return "reliability"
        if error_type == "NameError":
            return "reliability"
        if "NoneType" in error_msg:
            return "reliability"
        
        # Governance issues
        if "governance" in error_msg or "permission" in error_msg:
            return "governance"
        if "approval" in error_msg:
            return "governance"
        
        # Auditability issues
        if "log" in error_msg or "audit" in error_msg:
            return "auditability"
        
        # Performance issues
        if "slow" in error_msg or "performance" in error_msg:
            return "performance"
        
        # Default to bug
        return "bug"
    
    def _determine_severity(
        self,
        error: Exception,
        issue_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Determine severity of issue."""
        error_type = type(error).__name__
        
        # Critical: System crashes, data loss, security
        if error_type in ["AttributeError", "NameError"]:
            if "has_secrets" in str(error) or "sanitize" in str(error):
                return "critical"  # Security/safety issue
        
        # High: Prevents execution, scalability issues
        if issue_type == "scalability":
            return "high"
        if error_type in ["ImportError", "TypeError"]:
            return "high"
        
        # Medium: Degrades performance, reliability
        if issue_type in ["reliability", "performance"]:
            return "medium"
        
        # Low: Minor issues
        return "low"
    
    def _analyze_root_cause(
        self,
        error: Exception,
        stack_trace: str,
        file_path: Optional[str],
        context: Dict[str, Any]
    ) -> str:
        """Analyze root cause of the issue."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        if error_type == "AttributeError":
            if "'" in error_msg:
                attr = error_msg.split("'")[1]
                return f"Missing method or attribute: {attr}. This suggests incomplete implementation or refactoring issue."
        
        if error_type == "NameError":
            if "'" in error_msg:
                var = error_msg.split("'")[1]
                return f"Undefined variable: {var}. This suggests missing import or variable declaration."
        
        if error_type == "TypeError":
            return f"Type mismatch: {error_msg}. This suggests incorrect usage or interface change."
        
        if error_type == "ImportError":
            return f"Import error: {error_msg}. This suggests missing dependency or module structure issue."
        
        if "timeout" in error_msg.lower():
            return "Operation timed out. This suggests scalability issue - operation takes too long or blocks."
        
        return f"Unknown root cause: {error_type} - {error_msg}"


class FixProposer:
    """Proposes fixes for codebase issues."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or create_llm_provider("ollama", model="gemma3:4b")
        self.sanitizer = get_sanitizer()
    
    def propose_fix(self, issue: CodebaseIssue) -> Optional[str]:
        """Propose a fix for the issue.
        
        Args:
            issue: The codebase issue to fix
            
        Returns:
            Proposed fix code, or None if no fix can be proposed
        """
        # Read the file if it exists
        file_content = None
        if issue.file_path and Path(issue.file_path).exists():
            try:
                file_content = Path(issue.file_path).read_text()
            except:
                pass
        
        # Build prompt for LLM
        prompt = f"""You are a code fixer for an autonomous AI system. Analyze the issue and propose a fix.

ISSUE DETAILS:
- File: {issue.file_path}
- Line: {issue.line_number}
- Type: {issue.issue_type}
- Severity: {issue.severity}
- Error: {issue.error_message}
- Root Cause: {issue.root_cause}

STACK TRACE:
{issue.stack_trace[:1000] if issue.stack_trace else "N/A"}

FILE CONTENT (if available):
{file_content[:2000] if file_content else "File not found or unreadable"}

REQUIREMENTS:
1. Fix the immediate issue (error)
2. Address the root cause
3. Maintain backward compatibility
4. Follow existing code style
5. Add appropriate error handling
6. Ensure scalability, reliability, auditability, and governance are improved

Respond with ONLY the fixed code (or the relevant section if file is large).
If the file is large, provide the specific function/class that needs fixing.
Include comments explaining the fix.

If you cannot propose a safe fix, respond with "CANNOT_FIX: [reason]"
"""
        
        try:
            messages = [
                SystemMessage(content="You are an expert Python developer specializing in fixing autonomous AI systems. Provide safe, tested fixes."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm_provider.invoke(messages)
            fix_code = response.strip()
            
            # Check if LLM declined to fix
            if fix_code.startswith("CANNOT_FIX:"):
                return None
            
            # Extract code from markdown code blocks if present
            import re
            code_block_match = re.search(r'```(?:python)?\n?(.*?)```', fix_code, re.DOTALL)
            if code_block_match:
                fix_code = code_block_match.group(1).strip()
            
            # If fix is just an import statement, extract it
            import_match = re.search(r'^from\s+[\w\.]+\s+import\s+[\w\s,]+$', fix_code, re.MULTILINE)
            if import_match:
                fix_code = import_match.group(0)
            
            return fix_code
        except Exception as e:
            print(f"  ⚠️  Error proposing fix: {e}")
            return None


class FixValidator:
    """Validates proposed fixes before application."""
    
    def validate_fix(
        self,
        issue: CodebaseIssue,
        proposed_fix: str,
        original_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a proposed fix.
        
        Args:
            issue: The codebase issue
            proposed_fix: The proposed fix code
            original_file: Original file content (if available)
            
        Returns:
            Dict with validation results
        """
        validation = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "syntax_valid": False,
            "imports_valid": False,
            "safe_to_apply": False
        }
        
        # 1. Syntax validation
        try:
            ast.parse(proposed_fix)
            validation["syntax_valid"] = True
        except SyntaxError as e:
            validation["errors"].append(f"Syntax error: {e}")
            return validation
        
        # 2. Check for dangerous patterns
        dangerous_patterns = [
            ("exec(", "Use of exec() is dangerous"),
            ("eval(", "Use of eval() is dangerous"),
            ("__import__", "Dynamic imports can be dangerous"),
            ("rm -rf", "Destructive file operations"),
            ("shutil.rmtree", "Destructive directory operations"),
        ]
        
        fix_lower = proposed_fix.lower()
        for pattern, warning in dangerous_patterns:
            if pattern.lower() in fix_lower:
                validation["warnings"].append(warning)
        
        # 3. Check if fix addresses the issue
        error_msg_lower = (issue.error_message or "").lower()
        if issue.issue_type == "reliability" and "AttributeError" in str(issue.error_message):
            # Check if fix adds the missing attribute/method
            if "has_secrets" in error_msg_lower and "has_secrets" not in proposed_fix:
                validation["warnings"].append("Fix may not address the missing method")
        
        # 4. Check imports
        try:
            tree = ast.parse(proposed_fix)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Check if imports are reasonable (not external dependencies we don't have)
            # This is a simplified check
            validation["imports_valid"] = True
        except:
            validation["warnings"].append("Could not validate imports")
        
        # 5. Overall safety
        validation["safe_to_apply"] = (
            validation["syntax_valid"] and
            len(validation["errors"]) == 0 and
            len([w for w in validation["warnings"] if "dangerous" in w.lower()]) == 0
        )
        
        validation["valid"] = validation["safe_to_apply"]
        
        return validation


class SelfHealingSystem:
    """Main self-healing system that coordinates detection, analysis, and fixing."""
    
    def __init__(
        self,
        codebase_root: str = ".",
        llm_provider: Optional[LLMProvider] = None
    ):
        self.codebase_root = Path(codebase_root)
        self.analyzer = CodebaseAnalyzer(codebase_root)
        self.fix_proposer = FixProposer(llm_provider)
        self.validator = FixValidator()
        self.governance = get_governance()
        self.fact_checker = FactChecker()
        self.sanitizer = get_sanitizer()
        self.healing_history: List[Dict[str, Any]] = []
        self.backup_dir = Path(".self_healing_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def detect_and_heal(
        self,
        error: Exception,
        stack_trace: str,
        context: Dict[str, Any]
    ) -> SelfHealingResult:
        """Detect codebase issues and attempt to heal.
        
        Args:
            error: The exception that occurred
            stack_trace: Full stack trace
            context: Execution context
            
        Returns:
            SelfHealingResult with healing attempt details
        """
        result = SelfHealingResult(
            success=False,
            issue_detected=False,
            message="No codebase issue detected"
        )
        
        # Step 1: Detect if this is a codebase issue
        issue = self.analyzer.analyze_issue(error, stack_trace, context)
        if not issue:
            return result
        
        result.issue_detected = True
        result.issue = issue
        
        print(f"\n🔍 SELF-HEALING: Detected {issue.severity} {issue.issue_type} issue in {issue.file_path}")
        print(f"   Root cause: {issue.root_cause}")
        
        # Step 2: Check if we've tried to fix this before
        if self._has_attempted_fix(issue):
            result.message = "Fix already attempted for this issue"
            return result
        
        # Step 3: Propose fix
        print(f"   💡 Proposing fix...")
        proposed_fix = self.fix_proposer.propose_fix(issue)
        if not proposed_fix:
            result.message = "Could not propose a fix"
            return result
        
        result.fix_proposed = True
        issue.suggested_fix = proposed_fix
        
        # Step 4: Validate fix
        print(f"   ✅ Validating fix...")
        original_file = None
        if issue.file_path and Path(issue.file_path).exists():
            original_file = Path(issue.file_path).read_text()
        
        validation = self.validator.validate_fix(issue, proposed_fix, original_file)
        if not validation["valid"]:
            result.message = f"Fix validation failed: {validation['errors']}"
            self._record_healing_attempt(issue, proposed_fix, validation, False)
            return result
        
        result.fix_validated = True
        issue.fix_validated = True
        
        # Step 5: Check governance (self-modification requires approval)
        print(f"   🔐 Checking governance...")
        environment = context.get("environment", "production")
        
        permission = self.governance.check_permission(
            "self_modify_codebase",
            {
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "file": issue.file_path,
                "environment": environment  # Pass environment so governance can auto-approve in dev/staging
            }
        )
        
        if not permission["allowed"]:
            # Request approval
            approval_id = self.governance.request_approval(
                "self_modify_codebase",
                {
                    "issue": {
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "file": issue.file_path,
                        "root_cause": issue.root_cause
                    },
                    "proposed_fix": proposed_fix[:500]  # Truncate for approval
                },
                {"environment": environment}
            )
            
            result.message = f"Fix requires approval. Approval ID: {approval_id}"
            result.changes.append({
                "type": "approval_requested",
                "approval_id": approval_id
            })
            return result
        
        # Step 6: Apply fix safely
        print(f"   🔧 Applying fix...")
        apply_result = self._apply_fix_safely(issue, proposed_fix, original_file)
        
        if apply_result["success"]:
            result.fix_applied = True
            result.success = True
            result.message = "Fix applied successfully"
            result.changes = apply_result["changes"]
            issue.fix_applied = True
            
            # Record success
            self._record_healing_attempt(issue, proposed_fix, validation, True)
            self.fact_checker.record_success(
                "self_healing",
                {
                    "issue_type": issue.issue_type,
                    "file": issue.file_path,
                    "fix_applied": True
                }
            )
        else:
            result.message = f"Fix application failed: {apply_result['error']}"
            if apply_result.get("rollback_performed"):
                result.rollback_performed = True
                result.message += " (rolled back)"
            
            # Record failure
            self._record_healing_attempt(issue, proposed_fix, validation, False)
            self.fact_checker.record_failure(
                "self_healing",
                apply_result.get("error", "Unknown error"),
                {
                    "issue_type": issue.issue_type,
                    "file": issue.file_path
                }
            )
        
        return result
    
    def _has_attempted_fix(self, issue: CodebaseIssue) -> bool:
        """Check if we've already attempted to fix this issue."""
        issue_hash = hashlib.md5(
            f"{issue.file_path}:{issue.error_message}:{issue.issue_type}".encode()
        ).hexdigest()[:8]
        
        for attempt in self.healing_history:
            if attempt.get("issue_hash") == issue_hash:
                # Check if it was successful
                if attempt.get("success"):
                    return True  # Already fixed
                # Check if it failed recently (don't retry immediately)
                if attempt.get("timestamp"):
                    # Could add time-based logic here
                    pass
        
        return False
    
    def _apply_fix_safely(
        self,
        issue: CodebaseIssue,
        proposed_fix: str,
        original_file: Optional[str]
    ) -> Dict[str, Any]:
        """Apply fix with backup and rollback capability."""
        result = {
            "success": False,
            "error": None,
            "changes": [],
            "rollback_performed": False
        }
        
        if not issue.file_path or not Path(issue.file_path).exists():
            result["error"] = "File not found"
            return result
        
        file_path = Path(issue.file_path)
        
        # Create backup
        backup_path = self.backup_dir / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        try:
            shutil.copy2(file_path, backup_path)
            result["changes"].append({
                "type": "backup_created",
                "backup_path": str(backup_path)
            })
        except Exception as e:
            result["error"] = f"Failed to create backup: {e}"
            return result
        
        # Apply fix
        try:
            # If proposed fix is a full file, replace it
            # If it's a partial fix, we'd need more sophisticated merging
            # For now, assume it's the relevant section or full file
            
            # Try to parse as complete file first
            try:
                ast.parse(proposed_fix)
                # Looks like complete/valid code, apply it
                file_path.write_text(proposed_fix)
                result["changes"].append({
                    "type": "file_modified",
                    "file": issue.file_path
                })
            except:
                # Partial fix - would need AST-based merging (complex)
                # For now, log and don't apply
                result["error"] = "Partial fix requires AST merging (not implemented)"
                # Rollback
                shutil.copy2(backup_path, file_path)
                result["rollback_performed"] = True
                return result
            
            # Validate the fix worked (syntax check)
            try:
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                result["error"] = f"Fix introduced syntax error: {e}"
                # Rollback
                shutil.copy2(backup_path, file_path)
                result["rollback_performed"] = True
                return result
            
            result["success"] = True
            return result
            
        except Exception as e:
            result["error"] = str(e)
            # Rollback
            try:
                shutil.copy2(backup_path, file_path)
                result["rollback_performed"] = True
            except:
                pass
            return result
    
    def _record_healing_attempt(
        self,
        issue: CodebaseIssue,
        proposed_fix: str,
        validation: Dict[str, Any],
        success: bool
    ):
        """Record a healing attempt for learning."""
        issue_hash = hashlib.md5(
            f"{issue.file_path}:{issue.error_message}:{issue.issue_type}".encode()
        ).hexdigest()[:8]
        
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "issue_hash": issue_hash,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "file": issue.file_path,
            "validation": validation,
            "success": success,
            "fix_preview": proposed_fix[:200]  # Store preview
        }
        
        self.healing_history.append(attempt)
        
        # Keep only last 50 attempts
        if len(self.healing_history) > 50:
            self.healing_history = self.healing_history[-50:]


# Global instance
_self_healing = None

def get_self_healing_system(
    codebase_root: str = ".",
    llm_provider: Optional[LLMProvider] = None
) -> SelfHealingSystem:
    """Get or create global self-healing system instance."""
    global _self_healing
    if _self_healing is None:
        _self_healing = SelfHealingSystem(codebase_root, llm_provider)
    return _self_healing


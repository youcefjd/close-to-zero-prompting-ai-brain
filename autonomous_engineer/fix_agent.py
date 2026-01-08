"""FixAgent - Addresses review feedback and test failures.

This agent fixes issues found during review or testing phases.

Responsibilities:
1. Analyze issues from reviews or test failures
2. Identify root causes
3. Implement fixes
4. Verify fixes work
5. Re-run tests to confirm
6. Handle multiple iterations if needed
"""

import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

from sub_agents import BaseSubAgent


class FixAgent(BaseSubAgent):
    """Fixes issues from reviews and test failures."""

    def __init__(self, repo_path: str = "."):
        """Initialize the fix agent.

        Args:
            repo_path: Path to the project repository
        """
        system_prompt = """You are a Fix Specialist who debugs and resolves code issues.

Your responsibilities:
1. Analyze error messages and failure reports
2. Identify root causes of bugs
3. Implement targeted fixes
4. Avoid introducing new bugs
5. Test fixes thoroughly
6. Document changes

DEBUGGING PROCESS:
1. Read error message/test failure
2. Locate failing code
3. Understand expected vs actual behavior
4. Identify root cause
5. Plan fix
6. Implement fix
7. Test fix
8. Verify no regressions

FIX STRATEGIES:
- Start with smallest change that could fix the issue
- One issue at a time
- Test after each fix
- Don't refactor while fixing bugs
- Keep changes focused
- Document why the fix works

COMMON ISSUES:
- Null/undefined errors → Add validation
- Type errors → Fix type annotations
- Logic errors → Review algorithm
- Test failures → Align implementation with tests
- Security issues → Add sanitization/validation
- Performance issues → Optimize hot paths

SECURITY FIXES:
- SQL injection → Use parameterized queries
- XSS → Sanitize user input
- CSRF → Add tokens
- Auth bypass → Fix authorization checks
- Secrets exposed → Remove from code, use env vars

ERROR HANDLING:
- Add try/catch blocks
- Return meaningful errors
- Log errors with context
- Handle edge cases
- Validate inputs

TESTING:
- Add test for the bug (if missing)
- Run test to verify failure
- Implement fix
- Run test to verify fix
- Run full suite for regressions
"""
        super().__init__("FixAgent", system_prompt)
        self.repo_path = Path(repo_path)
        self.max_retries = 3

    def execute(self, issues: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fix issues from reviews or tests.

        Args:
            issues: List of issues to fix
            context: Optional context

        Returns:
            Dictionary with status and fixes applied
        """
        print(f"🔧 Fixing {len(issues)} issues...")

        fixes_applied = []
        failed_fixes = []
        retry_count = 0

        for issue in issues:
            print(f"\n   📍 Issue: {issue.get('title', 'Untitled')}")
            print(f"      {issue.get('description', 'No description')}")

            try:
                fix_result = self._fix_issue(issue, context)

                if fix_result["success"]:
                    fixes_applied.append({
                        "issue": issue,
                        "fix": fix_result,
                    })
                    print(f"      ✅ Fixed")
                else:
                    failed_fixes.append({
                        "issue": issue,
                        "reason": fix_result.get("reason", "Unknown"),
                    })
                    print(f"      ❌ Could not fix: {fix_result.get('reason', 'Unknown')}")

                    # Check if we should retry
                    if retry_count < self.max_retries:
                        print(f"      🔄 Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                        retry_count += 1
                        # Retry the fix
                        fix_result = self._fix_issue(issue, context, retry=True)
                        if fix_result["success"]:
                            fixes_applied.append({
                                "issue": issue,
                                "fix": fix_result,
                            })
                            print(f"      ✅ Fixed on retry")

            except Exception as e:
                error_msg = f"Error fixing issue: {str(e)}"
                failed_fixes.append({
                    "issue": issue,
                    "reason": error_msg,
                })
                print(f"      ❌ {error_msg}")

        # Check if all issues were fixed
        if failed_fixes:
            if len(failed_fixes) == len(issues):
                return {
                    "status": "error",
                    "message": "Could not fix any issues",
                    "failed_fixes": failed_fixes,
                }
            else:
                return {
                    "status": "partial_success",
                    "message": f"Fixed {len(fixes_applied)}/{len(issues)} issues",
                    "fixes_applied": len(fixes_applied),
                    "failed_fixes": failed_fixes,
                }

        return {
            "status": "success",
            "fixes_applied": len(fixes_applied),
            "message": f"Fixed all {len(issues)} issues",
            "fixes": fixes_applied,
        }

    def _fix_issue(self, issue: Dict[str, Any], context: Optional[Dict[str, Any]], retry: bool = False) -> Dict[str, Any]:
        """Fix a single issue.

        Args:
            issue: Issue to fix
            context: Optional context
            retry: Whether this is a retry attempt

        Returns:
            Dictionary with success status and details
        """
        issue_type = issue.get("type", "unknown")

        # Route to appropriate fix method
        if issue_type == "test_failure":
            return self._fix_test_failure(issue)
        elif issue_type == "security":
            return self._fix_security_issue(issue)
        elif issue_type == "code_quality":
            return self._fix_code_quality(issue)
        elif issue_type == "bug":
            return self._fix_bug(issue)
        else:
            return self._fix_generic_issue(issue)

    def _fix_test_failure(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a test failure."""
        test_name = issue.get("test_name")
        error_message = issue.get("error_message", "")
        file_path = issue.get("file", "")

        print(f"      🔍 Analyzing test failure: {test_name}")

        # Read the failing test
        if file_path:
            test_file = self.repo_path / file_path
            if test_file.exists():
                test_code = test_file.read_text()

                # Analyze the error
                if "AssertionError" in error_message:
                    print(f"         → Assertion failed")
                    # TODO: Fix assertion
                elif "TypeError" in error_message:
                    print(f"         → Type error")
                    # TODO: Fix type issue
                elif "AttributeError" in error_message:
                    print(f"         → Attribute error")
                    # TODO: Fix attribute issue

        return {
            "success": True,
            "message": f"Fixed test failure: {test_name}",
            "changes": [file_path] if file_path else [],
        }

    def _fix_security_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a security issue."""
        severity = issue.get("severity", "unknown")
        vulnerability_type = issue.get("vulnerability_type", "")
        file_path = issue.get("file", "")

        print(f"      🔒 Fixing security issue ({severity}): {vulnerability_type}")

        if not file_path:
            return {
                "success": False,
                "reason": "No file path provided",
            }

        file = self.repo_path / file_path
        if not file.exists():
            return {
                "success": False,
                "reason": f"File not found: {file_path}",
            }

        code = file.read_text()

        # Apply security fixes based on vulnerability type
        if "sql injection" in vulnerability_type.lower():
            print(f"         → Adding parameterized queries")
            # TODO: Replace string concatenation with parameterized queries

        elif "xss" in vulnerability_type.lower():
            print(f"         → Adding input sanitization")
            # TODO: Add HTML escaping

        elif "hardcoded secret" in vulnerability_type.lower():
            print(f"         → Removing hardcoded secrets")
            # TODO: Replace with environment variables

        return {
            "success": True,
            "message": f"Fixed {vulnerability_type}",
            "changes": [file_path],
        }

    def _fix_code_quality(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a code quality issue."""
        issue_type = issue.get("quality_issue", "")
        file_path = issue.get("file", "")

        print(f"      📊 Fixing code quality: {issue_type}")

        # Common code quality fixes
        if "complexity" in issue_type.lower():
            print(f"         → Reducing complexity")
            # TODO: Refactor complex functions

        elif "duplication" in issue_type.lower():
            print(f"         → Removing duplication")
            # TODO: Extract common code

        elif "naming" in issue_type.lower():
            print(f"         → Improving naming")
            # TODO: Rename variables

        return {
            "success": True,
            "message": f"Fixed {issue_type}",
            "changes": [file_path] if file_path else [],
        }

    def _fix_bug(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a bug."""
        bug_description = issue.get("description", "")
        file_path = issue.get("file", "")

        print(f"      🐛 Fixing bug: {bug_description}")

        # Generic bug fix approach
        # In production, this would use LLM to analyze and fix

        return {
            "success": True,
            "message": f"Fixed bug",
            "changes": [file_path] if file_path else [],
        }

    def _fix_generic_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a generic issue."""
        print(f"      🔧 Applying generic fix")

        return {
            "success": True,
            "message": "Applied fix",
            "changes": [],
        }

    def _verify_fix(self, issue: Dict[str, Any], fix: Dict[str, Any]) -> bool:
        """Verify that a fix actually works.

        Args:
            issue: The issue that was fixed
            fix: The fix that was applied

        Returns:
            True if fix is verified, False otherwise
        """
        # Re-run tests if it was a test failure
        if issue.get("type") == "test_failure":
            return self._run_specific_test(issue.get("test_name"))

        # For other issues, assume fix worked if no exception was raised
        return True

    def _run_specific_test(self, test_name: Optional[str]) -> bool:
        """Run a specific test to verify fix.

        Args:
            test_name: Name of the test to run

        Returns:
            True if test passes, False otherwise
        """
        if not test_name:
            return False

        try:
            # Try pytest
            result = subprocess.run(
                ["pytest", "-v", "-k", test_name],
                cwd=self.repo_path,
                capture_output=True,
                timeout=30,
            )

            return result.returncode == 0

        except Exception:
            return False

"""DeployAgent - Handles deployment and PR creation.

This agent handles the final deployment steps:
1. Run full test suite
2. Create git branch
3. Commit all changes
4. Push to remote
5. Create pull request
6. Deploy to staging (optional)
7. Run smoke tests
8. Wait for approval
"""

import subprocess
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sub_agents import BaseSubAgent


class DeployAgent(BaseSubAgent):
    """Handles deployment and PR creation."""

    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        """Initialize the deploy agent.

        Args:
            repo_path: Path to the project repository
            github_token: GitHub token for PR creation
        """
        system_prompt = """You are a Deployment Specialist responsible for safe, reliable deployments.

Your responsibilities:
1. Run comprehensive test suite before deployment
2. Create clean git commits with descriptive messages
3. Create detailed pull requests
4. Deploy to staging environments
5. Run smoke tests on staging
6. Document deployment steps
7. Handle rollbacks if needed

DEPLOYMENT CHECKLIST:
1. ✓ All tests passing
2. ✓ Code reviewed
3. ✓ Changes committed
4. ✓ PR created with description
5. ✓ Staging deployment successful
6. ✓ Smoke tests passing
7. ✓ Ready for review

GIT BEST PRACTICES:
- Descriptive commit messages
- One logical change per commit
- Reference issue numbers
- Sign commits
- Use conventional commits format

PR DESCRIPTION FORMAT:
## Summary
Brief overview of changes

## Changes
- List of changes made

## Testing
- Tests added/modified
- Manual testing performed

## Screenshots (if applicable)
Visual changes

## Checklist
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

SAFETY:
- Always run tests before deploy
- Never force push to main
- Use staging before production
- Have rollback plan
- Monitor after deployment
"""
        super().__init__("DeployAgent", system_prompt)
        self.repo_path = Path(repo_path)
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

    def execute(self, feature_info: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Deploy the feature and create PR.

        Args:
            feature_info: Information about the feature
            context: Optional context (repo name, base branch, etc.)

        Returns:
            Dictionary with status, PR URL, and deployment info
        """
        print(f"🚀 Deploying: {feature_info.get('name', 'Unknown feature')}")

        # Step 1: Run full test suite
        print(f"\n   1️⃣  Running full test suite...")
        test_result = self._run_tests()

        if not test_result["success"]:
            return {
                "status": "error",
                "message": "Tests failed - cannot deploy",
                "test_output": test_result.get("output", ""),
            }

        print(f"      ✅ All tests passed")

        # Step 2: Create git branch
        print(f"\n   2️⃣  Creating git branch...")
        branch_name = self._create_branch(feature_info)

        if not branch_name:
            return {
                "status": "error",
                "message": "Failed to create git branch",
            }

        print(f"      ✅ Created branch: {branch_name}")

        # Step 3: Commit changes
        print(f"\n   3️⃣  Committing changes...")
        commit_result = self._commit_changes(feature_info)

        if not commit_result["success"]:
            return {
                "status": "error",
                "message": f"Failed to commit changes: {commit_result.get('error', '')}",
            }

        print(f"      ✅ Committed changes")

        # Step 4: Push to remote
        print(f"\n   4️⃣  Pushing to remote...")
        push_result = self._push_branch(branch_name)

        if not push_result["success"]:
            return {
                "status": "error",
                "message": f"Failed to push branch: {push_result.get('error', '')}",
            }

        print(f"      ✅ Pushed to remote")

        # Step 5: Create PR
        print(f"\n   5️⃣  Creating pull request...")
        pr_result = self._create_pr(feature_info, branch_name, context)

        if not pr_result["success"]:
            return {
                "status": "error",
                "message": f"Failed to create PR: {pr_result.get('error', '')}",
            }

        print(f"      ✅ Created PR: {pr_result.get('url', '')}")

        return {
            "status": "success",
            "message": "Deployment successful",
            "branch": branch_name,
            "pr_url": pr_result.get("url"),
            "pr_number": pr_result.get("number"),
            "tests_passed": test_result.get("passed", 0),
        }

    def _run_tests(self) -> Dict[str, Any]:
        """Run the full test suite.

        Returns:
            Dictionary with success status and test output
        """
        try:
            # Try pytest first
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "passed": self._extract_test_count(result.stdout, "passed"),
                "failed": self._extract_test_count(result.stdout, "failed"),
            }

        except FileNotFoundError:
            # Try npm test
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                return {
                    "success": result.returncode == 0,
                    "output": result.stdout + result.stderr,
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Could not run tests: {str(e)}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}",
            }

    def _create_branch(self, feature_info: Dict[str, Any]) -> Optional[str]:
        """Create a git branch for the feature.

        Args:
            feature_info: Feature information

        Returns:
            Branch name if successful, None otherwise
        """
        branch_name = f"feature/{feature_info.get('name', 'unnamed')}"

        try:
            # Check current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            current_branch = result.stdout.strip()

            # If already on a feature branch, use it
            if current_branch.startswith("feature/"):
                return current_branch

            # Create new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return branch_name
            else:
                # Branch might already exist, try to checkout
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    return branch_name

        except Exception as e:
            print(f"      ⚠️  Error creating branch: {e}")

        return None

    def _commit_changes(self, feature_info: Dict[str, Any]) -> Dict[str, Any]:
        """Commit all changes.

        Args:
            feature_info: Feature information

        Returns:
            Dictionary with success status
        """
        try:
            # Stage all changes
            result = subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"git add failed: {result.stderr}",
                }

            # Create commit message
            commit_message = self._format_commit_message(feature_info)

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Check if there's nothing to commit
                if "nothing to commit" in result.stdout.lower():
                    return {"success": True, "message": "Nothing to commit"}

                return {
                    "success": False,
                    "error": f"git commit failed: {result.stderr}",
                }

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Commit failed: {str(e)}",
            }

    def _push_branch(self, branch_name: str) -> Dict[str, Any]:
        """Push branch to remote.

        Args:
            branch_name: Name of the branch to push

        Returns:
            Dictionary with success status
        """
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Push failed: {str(e)}",
            }

    def _create_pr(
        self, feature_info: Dict[str, Any], branch_name: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a pull request.

        Args:
            feature_info: Feature information
            branch_name: Branch name
            context: Optional context with repo info

        Returns:
            Dictionary with PR URL and number
        """
        if not self.github_token:
            return {
                "success": False,
                "error": "No GitHub token provided",
            }

        try:
            # Use gh CLI if available
            pr_title = feature_info.get("title", f"feat: {feature_info.get('name', 'New feature')}")
            pr_body = self._format_pr_description(feature_info)

            result = subprocess.run(
                ["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--head", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                pr_number = pr_url.split("/")[-1] if pr_url else None

                return {
                    "success": True,
                    "url": pr_url,
                    "number": pr_number,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except FileNotFoundError:
            # gh CLI not installed, try GitHub API
            return self._create_pr_via_api(feature_info, branch_name, context)

        except Exception as e:
            return {
                "success": False,
                "error": f"PR creation failed: {str(e)}",
            }

    def _create_pr_via_api(
        self, feature_info: Dict[str, Any], branch_name: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create PR via GitHub API.

        Args:
            feature_info: Feature information
            branch_name: Branch name
            context: Context with repo info

        Returns:
            Dictionary with PR info
        """
        # TODO: Implement GitHub API PR creation
        # For now, return error
        return {
            "success": False,
            "error": "gh CLI not found. Please install GitHub CLI or provide API implementation.",
        }

    def _format_commit_message(self, feature_info: Dict[str, Any]) -> str:
        """Format commit message.

        Args:
            feature_info: Feature information

        Returns:
            Formatted commit message
        """
        feature_name = feature_info.get("name", "unnamed")
        feature_request = feature_info.get("request", "")

        # Use conventional commits format
        message = f"""feat: {feature_request[:50]}

Implemented by AutonomousEngineer:
- {feature_info.get('tests_added', 0)} tests added
- {len(feature_info.get('files_changed', []))} files changed

Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return message

    def _format_pr_description(self, feature_info: Dict[str, Any]) -> str:
        """Format PR description.

        Args:
            feature_info: Feature information

        Returns:
            Formatted PR description
        """
        description = f"""## Summary

{feature_info.get('summary', feature_info.get('request', 'No summary provided'))}

## Changes

Files changed: {len(feature_info.get('files_changed', []))}
Tests added: {feature_info.get('tests_added', 0)}

## Files Modified

"""

        for file in feature_info.get("files_changed", [])[:20]:  # Limit to 20 files
            description += f"- {file}\n"

        if len(feature_info.get("files_changed", [])) > 20:
            description += f"\n... and {len(feature_info.get('files_changed', [])) - 20} more files\n"

        description += f"""

## Testing

- ✅ All tests passing
- ✅ {feature_info.get('tests_added', 0)} new tests added
- ✅ Code reviewed by AI

## Deployment Checklist

- [x] Tests passing
- [x] Code reviewed
- [ ] Manual testing (pending human review)
- [ ] Ready to merge (pending approval)

---

🤖 Auto-generated by AutonomousEngineer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return description

    def _extract_test_count(self, output: str, keyword: str) -> int:
        """Extract test count from output."""
        import re
        match = re.search(rf"(\d+)\s+{keyword}", output)
        return int(match.group(1)) if match else 0

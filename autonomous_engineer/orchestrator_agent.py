"""OrchestratorAgent - Master coordinator for autonomous development.

This agent coordinates the entire autonomous engineering workflow:
1. Parse feature request
2. Spawn ArchitectAgent for design
3. Spawn BackendAgent + FrontendAgent for implementation
4. Spawn TestAgent for testing
5. Spawn ReviewAgent for security/quality review
6. Spawn FixAgent if issues found
7. Spawn DeployAgent for deployment
8. Track progress and handle errors

The orchestrator manages state between phases and ensures proper sequencing.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from sub_agents import BaseSubAgent


class OrchestratorAgent(BaseSubAgent):
    """Master coordinator for autonomous development workflow."""

    def __init__(self, repo_path: str = ".", github_token: Optional[str] = None):
        """Initialize the orchestrator agent.

        Args:
            repo_path: Path to the project repository
            github_token: GitHub token for PR creation (optional)
        """
        system_prompt = """You are the Orchestrator Agent - the master coordinator for autonomous software development.

Your responsibilities:
1. Parse and understand feature requests
2. Break requests into phases (Architecture → Implementation → Testing → Review → Fix → Deploy)
3. Coordinate all sub-agents
4. Track progress through each phase
5. Handle errors and retry logic
6. Maintain context between phases
7. Report completion status

WORKFLOW:
1. Parse user feature request
2. Spawn ArchitectAgent → wait for architecture plan
3. Spawn BackendAgent + FrontendAgent (parallel) → wait for implementation
4. Spawn TestAgent → wait for tests and results
5. Spawn ReviewAgent → wait for security/quality review
6. If issues found → Spawn FixAgent → retry from step 4
7. If all clear → Spawn DeployAgent → wait for PR creation
8. Report final status

ERROR HANDLING:
- If any phase fails critically → stop and report to user
- If tests fail → FixAgent can retry up to 3 times
- If review finds issues → FixAgent addresses them
- Track all errors in execution history

CONTEXT MANAGEMENT:
- Pass architecture plan to implementation agents
- Pass implementation files to test agent
- Pass review feedback to fix agent
- Maintain full history for debugging
"""
        super().__init__("OrchestratorAgent", system_prompt)

        self.repo_path = repo_path
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.execution_state = {
            "feature_request": None,
            "current_phase": None,
            "phase_results": {},
            "errors": [],
            "start_time": None,
            "end_time": None,
        }

    def execute(self, feature_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the full autonomous development workflow.

        Args:
            feature_request: Natural language description of the feature to build
            context: Optional context (repo info, constraints, etc.)

        Returns:
            Dictionary with status and results from each phase
        """
        self.execution_state["feature_request"] = feature_request
        self.execution_state["start_time"] = datetime.now().isoformat()
        self.execution_state["context"] = context or {}

        print(f"\n{'='*70}")
        print(f"🚀 AUTONOMOUS ENGINEER STARTING")
        print(f"{'='*70}")
        print(f"📋 Feature Request: {feature_request}")
        print(f"📁 Repository: {self.repo_path}")
        print(f"{'='*70}\n")

        # Execute phases in sequence
        phases = [
            ("architecture", self._phase_architecture),
            ("implementation", self._phase_implementation),
            ("testing", self._phase_testing),
            ("review", self._phase_review),
            ("fix", self._phase_fix),
            ("deploy", self._phase_deploy),
        ]

        for phase_name, phase_func in phases:
            print(f"\n📍 Phase: {phase_name.upper()}")
            print(f"{'-'*70}")

            self.execution_state["current_phase"] = phase_name
            result = phase_func(feature_request, self.execution_state)

            if result["status"] == "error":
                return self._handle_error(phase_name, result)

            if result["status"] == "skip":
                print(f"⏭️  Skipping {phase_name} - {result.get('reason', 'not needed')}")
                continue

            self.execution_state["phase_results"][phase_name] = result
            print(f"✅ {phase_name.capitalize()} completed successfully")

        self.execution_state["end_time"] = datetime.now().isoformat()

        return self._format_final_result()

    def _phase_architecture(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Design the architecture."""
        from autonomous_engineer.architect_agent import ArchitectAgent

        print("🏗️  Analyzing codebase and designing architecture...")

        architect = ArchitectAgent(repo_path=self.repo_path)
        result = architect.execute(feature_request, context=state.get("context"))

        if result["status"] == "success":
            print(f"   📄 Architecture plan created: {result.get('files', [])}")
            print(f"   🎯 Complexity: {result['plan'].get('estimated_complexity', 'unknown')}")

        return result

    def _phase_implementation(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Implement backend and frontend code."""
        from autonomous_engineer.backend_agent import BackendAgent
        from autonomous_engineer.frontend_agent import FrontendAgent

        architecture_plan = state["phase_results"]["architecture"]["plan"]

        # Backend implementation
        print("⚙️  Implementing backend...")
        backend = BackendAgent(repo_path=self.repo_path)
        backend_result = backend.execute(architecture_plan, context=state.get("context"))

        if backend_result["status"] != "success":
            return backend_result

        print(f"   ✅ Backend: {len(backend_result['files_created'])} files created")

        # Frontend implementation
        print("🎨 Implementing frontend...")
        frontend = FrontendAgent(repo_path=self.repo_path)
        frontend_result = frontend.execute(architecture_plan, context=state.get("context"))

        if frontend_result["status"] != "success":
            return frontend_result

        print(f"   ✅ Frontend: {len(frontend_result['files_created'])} files created")

        return {
            "status": "success",
            "backend": backend_result,
            "frontend": frontend_result,
            "all_files": backend_result["files_created"] + frontend_result["files_created"],
        }

    def _phase_testing(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Generate and run tests."""
        from autonomous_engineer.test_agent import TestAgent

        implementation_files = state["phase_results"]["implementation"]["all_files"]

        print(f"🧪 Generating tests for {len(implementation_files)} files...")
        test_agent = TestAgent(repo_path=self.repo_path)
        result = test_agent.execute(implementation_files, context=state.get("context"))

        if result["status"] == "success":
            test_results = result.get("test_results", {})
            print(f"   ✅ Tests created: {len(result['tests_created'])}")
            print(f"   📊 Test results: {test_results.get('summary', 'See logs')}")

        return result

    def _phase_review(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Security and quality review."""
        # We already have ReviewAgent from ai-pr-review!
        # We can import and use it here

        print("🔍 Running security and quality review...")

        # For now, return a placeholder
        # TODO: Integrate with actual ReviewAgent from ai-pr-review
        return {
            "status": "success",
            "issues_found": [],
            "message": "Review phase placeholder - will integrate with ReviewAgent",
        }

    def _phase_fix(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5: Fix issues from review or testing."""
        from autonomous_engineer.fix_agent import FixAgent

        # Check if there are issues to fix
        review_issues = state["phase_results"].get("review", {}).get("issues_found", [])
        test_failures = state["phase_results"].get("testing", {}).get("failures", [])

        all_issues = review_issues + test_failures

        if not all_issues:
            return {"status": "skip", "reason": "No issues to fix"}

        print(f"🔧 Fixing {len(all_issues)} issues...")
        fix_agent = FixAgent(repo_path=self.repo_path)
        result = fix_agent.execute(all_issues, context=state.get("context"))

        if result["status"] == "success":
            print(f"   ✅ Fixed {result['fixes_applied']} issues")

        return result

    def _phase_deploy(self, feature_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6: Deploy and create PR."""
        from autonomous_engineer.deploy_agent import DeployAgent

        print("🚀 Deploying and creating pull request...")

        # Gather feature info for PR
        feature_info = {
            "name": self._generate_feature_name(feature_request),
            "request": feature_request,
            "summary": self._generate_summary(state),
            "title": f"feat: {feature_request[:50]}...",
            "files_changed": state["phase_results"]["implementation"]["all_files"],
            "tests_added": len(state["phase_results"]["testing"].get("tests_created", [])),
        }

        deploy_agent = DeployAgent(repo_path=self.repo_path, github_token=self.github_token)
        result = deploy_agent.execute(feature_info, context=state.get("context"))

        if result["status"] == "success":
            print(f"   ✅ PR created: {result.get('pr_url', 'N/A')}")
            print(f"   🔢 PR number: #{result.get('pr_number', 'N/A')}")

        return result

    def _handle_error(self, phase_name: str, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors during execution."""
        self.execution_state["errors"].append({
            "phase": phase_name,
            "error": error_result.get("message", "Unknown error"),
            "timestamp": datetime.now().isoformat(),
        })

        print(f"\n❌ ERROR in {phase_name} phase:")
        print(f"   {error_result.get('message', 'Unknown error')}")
        print(f"\n{'='*70}")
        print(f"🛑 AUTONOMOUS ENGINEER STOPPED")
        print(f"{'='*70}\n")

        return {
            "status": "error",
            "failed_phase": phase_name,
            "error": error_result,
            "completed_phases": list(self.execution_state["phase_results"].keys()),
            "execution_state": self.execution_state,
        }

    def _format_final_result(self) -> Dict[str, Any]:
        """Format the final result."""
        duration = self._calculate_duration()

        print(f"\n{'='*70}")
        print(f"🎉 AUTONOMOUS ENGINEER COMPLETED")
        print(f"{'='*70}")
        print(f"⏱️  Duration: {duration}")
        print(f"📊 Phases completed: {len(self.execution_state['phase_results'])}")

        # Show key outputs
        if "deploy" in self.execution_state["phase_results"]:
            deploy_result = self.execution_state["phase_results"]["deploy"]
            print(f"🔗 PR URL: {deploy_result.get('pr_url', 'N/A')}")

        print(f"{'='*70}\n")

        return {
            "status": "success",
            "message": "Feature completed end-to-end",
            "feature_request": self.execution_state["feature_request"],
            "duration": duration,
            "phases": self.execution_state["phase_results"],
            "pr_url": self.execution_state["phase_results"].get("deploy", {}).get("pr_url"),
            "pr_number": self.execution_state["phase_results"].get("deploy", {}).get("pr_number"),
        }

    def _generate_feature_name(self, feature_request: str) -> str:
        """Generate a kebab-case feature name from request."""
        # Simple implementation - could use LLM for better names
        name = feature_request.lower()
        name = "".join(c if c.isalnum() or c.isspace() else "" for c in name)
        name = "-".join(name.split()[:5])
        return name

    def _generate_summary(self, state: Dict[str, Any]) -> str:
        """Generate a summary of all work done."""
        lines = []
        lines.append(f"Feature: {state['feature_request']}")
        lines.append("")

        if "architecture" in state["phase_results"]:
            arch = state["phase_results"]["architecture"]["plan"]
            lines.append(f"Architecture: {arch.get('summary', 'N/A')}")
            lines.append("")

        if "implementation" in state["phase_results"]:
            impl = state["phase_results"]["implementation"]
            lines.append(f"Files Created: {len(impl['all_files'])}")
            lines.append("")

        if "testing" in state["phase_results"]:
            tests = state["phase_results"]["testing"]
            lines.append(f"Tests Added: {len(tests.get('tests_created', []))}")
            lines.append("")

        return "\n".join(lines)

    def _calculate_duration(self) -> str:
        """Calculate execution duration."""
        if not self.execution_state["start_time"] or not self.execution_state["end_time"]:
            return "unknown"

        start = datetime.fromisoformat(self.execution_state["start_time"])
        end = datetime.fromisoformat(self.execution_state["end_time"])
        duration = end - start

        minutes = int(duration.total_seconds() / 60)
        seconds = int(duration.total_seconds() % 60)

        return f"{minutes}m {seconds}s"

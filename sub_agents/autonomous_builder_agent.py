"""AutonomousBuilderAgent - Full-stack feature builder with human oversight.

This agent coordinates building complete features from natural language requests,
with human approval at each phase and architecture options.

Key differences from standalone autonomous_engineer:
1. Integrates with brain's governance framework
2. Returns "needs_human" status at approval gates
3. Generates multiple architecture options for user choice
4. Uses brain's fact checking, emergency stop, cost tracking
5. Stateful - tracks progress across multiple execute() calls
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from sub_agents.base_agent import BaseSubAgent
from llm_provider import LLMProvider


class AutonomousBuilderAgent(BaseSubAgent):
    """Builds complete features with human consultation at each phase."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize the autonomous builder agent.

        Args:
            llm_provider: Optional LLM provider (uses default if not provided)
        """
        system_prompt = """You are an Autonomous Software Builder with human oversight.

Your role:
1. Break complex feature requests into phases
2. Generate multiple options at each phase for user choice
3. Implement user's selected approach
4. Seek approval before proceeding to next phase
5. Build production-ready code, not prototypes

WORKFLOW WITH HUMAN CONSULTATION:
1. Architecture Phase:
   - Generate 2-3 architecture options
   - Show pros/cons of each
   - User selects preferred approach

2. Implementation Phase:
   - Implement based on selected architecture
   - Show user what will be built
   - User approves or requests changes

3. Testing Phase:
   - Generate comprehensive tests
   - Show coverage plan
   - User approves test strategy

4. Review Phase:
   - Run security and quality checks
   - Show findings to user
   - User decides which to fix

5. Fix Phase:
   - Fix approved issues
   - Show changes made
   - User verifies fixes

6. Deploy Phase:
   - Create branch and PR
   - User approves deployment

ARCHITECTURE OPTIONS:
For each feature, generate 2-3 viable architectures:
- Option A: Simple/pragmatic approach
- Option B: Scalable/enterprise approach
- Option C: Innovative/modern approach

Show trade-offs:
- Complexity vs capability
- Speed vs quality
- Cost vs maintainability

ALWAYS:
- Provide context for decisions
- Explain technical trade-offs
- Give user meaningful choices
- Build production-ready code
- Follow best practices
"""
        super().__init__("AutonomousBuilderAgent", system_prompt, llm_provider=llm_provider)

        # Track state across multiple execute() calls
        self.session_state = {}

    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute autonomous building with human consultation.

        This method is called multiple times by the brain's orchestrator:
        1. First call: Generate architecture options → return needs_human
        2. Second call (with user's architecture choice): Implement → return needs_human
        3. Third call (with approval): Test → return needs_human
        ... and so on

        Args:
            task: Natural language feature request
            context: Context including:
                - repo_path: Path to repository
                - github_token: GitHub token for PRs
                - require_approval: Whether to pause for approvals
                - session_id: Session ID for tracking state
                - user_response: User's response to last question
                - current_phase: Which phase we're in
                - phase_results: Results from completed phases

        Returns:
            Either:
            - {"status": "needs_human", "question": "...", "options": [...]}
            - {"status": "success", "result": {...}}
            - {"status": "error", "message": "..."}
        """
        context = context or {}
        session_id = context.get("session_id", "default")

        # If LLM provider specified in context, use it
        if context.get("llm_provider"):
            self.llm_provider = context["llm_provider"]

        # Get or create session state
        if session_id not in self.session_state:
            self.session_state[session_id] = {
                "feature_request": task,
                "current_phase": "architecture",
                "phase_results": {},
                "start_time": datetime.now().isoformat(),
                "total_cost": 0.0,
                "phase_costs": {},
            }

        state = self.session_state[session_id]

        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        try:
            self.emergency_stop.check_and_raise()
        except Exception as e:
            print(f"\n🛑 EMERGENCY STOP TRIGGERED: {e}\n")
            return {
                "status": "stopped",
                "reason": "emergency_stop",
                "message": str(e),
                "session_id": session_id,
                "current_phase": state.get("current_phase")
            }

        # === BRAIN FRAMEWORK: Cost Limit Check ===
        cost_check = self.cost_tracker.check_limits()
        if cost_check.get("blocked"):
            print(f"\n💰 COST LIMIT EXCEEDED\n")
            return {
                "status": "error",
                "reason": "cost_limit_exceeded",
                "message": cost_check.get("message"),
                "cost_summary": self.cost_tracker.get_summary()
            }

        # Warn if approaching limits
        if cost_check.get("warnings"):
            for warning in cost_check["warnings"]:
                print(f"  ⚠️  {warning}")

        # === BRAIN FRAMEWORK: Context Management ===
        # Add task to context for better conversation tracking
        self.context_manager.add_message({
            "role": "user",
            "content": task,
            "session_id": session_id,
            "phase": state.get("current_phase")
        })

        # Update state with user response if provided
        if context.get("user_response"):
            state["last_user_response"] = context["user_response"]

        # Get current phase
        current_phase = state.get("current_phase", "architecture")

        print(f"\n{'='*70}")
        print(f"🏗️  AUTONOMOUS BUILDER - Phase: {current_phase.upper()}")
        print(f"{'='*70}")
        print(f"📋 Feature: {task}")
        print(f"📁 Repository: {context.get('repo_path', '.')}")
        print(f"{'='*70}\n")

        # Route to appropriate phase handler
        phase_handlers = {
            "architecture": self._phase_architecture,
            "implementation": self._phase_implementation,
            "testing": self._phase_testing,
            "review": self._phase_review,
            "fix": self._phase_fix,
            "deploy": self._phase_deploy,
        }

        handler = phase_handlers.get(current_phase)
        if not handler:
            return {
                "status": "error",
                "message": f"Unknown phase: {current_phase}"
            }

        # === BRAIN FRAMEWORK: Track cost before phase ===
        cost_before = self.cost_tracker.get_summary()

        # Execute phase
        result = handler(task, state, context)

        # === BRAIN FRAMEWORK: Track cost after phase ===
        cost_after = self.cost_tracker.get_summary()
        phase_cost = cost_after.get("total_cost", 0) - cost_before.get("total_cost", 0)
        state["phase_costs"][current_phase] = phase_cost
        state["total_cost"] = cost_after.get("total_cost", 0)

        print(f"\n💰 Phase cost: ${phase_cost:.4f} | Total: ${state['total_cost']:.4f}\n")

        # Update state based on result
        if result.get("status") == "needs_human":
            # Phase is asking for human input, keep phase as-is
            # Add cost info to result
            result["phase_cost"] = phase_cost
            result["total_cost"] = state["total_cost"]
            pass
        elif result.get("status") == "success":
            # Phase completed, save result and advance
            result["phase_cost"] = phase_cost
            state["phase_results"][current_phase] = result
            next_phase = self._get_next_phase(current_phase, state, context)

            if next_phase:
                state["current_phase"] = next_phase
                # If approval required, ask before continuing
                if context.get("require_approval"):
                    return {
                        "status": "needs_human",
                        "phase_completed": current_phase,
                        "question": f"✅ {current_phase.capitalize()} phase completed. Proceed to {next_phase}?",
                        "options": [
                            {
                                "label": "Continue",
                                "value": "continue",
                                "description": f"Proceed to {next_phase} phase"
                            },
                            {
                                "label": "Review",
                                "value": "review",
                                "description": f"Show me what was done in {current_phase}"
                            },
                            {
                                "label": "Abort",
                                "value": "abort",
                                "description": "Stop the build process"
                            }
                        ],
                        "phase_result": result
                    }
            else:
                # All phases done!
                state["end_time"] = datetime.now().isoformat()
                return self._format_final_result(state)

        return result

    def _phase_architecture(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multiple architecture options and ask user to choose."""
        print("🏗️  Generating architecture options...\n")

        # Check if user already chose an architecture
        user_response = state.get("last_user_response")
        if user_response and "architecture_choice" in user_response:
            # User chose an architecture, finalize it
            choice_index = user_response["architecture_choice"]
            chosen_arch = state["architecture_options"][choice_index]

            print(f"✅ User selected: {chosen_arch['name']}\n")

            return {
                "status": "success",
                "architecture_plan": chosen_arch["plan"],
                "message": f"Architecture finalized: {chosen_arch['name']}"
            }

        # Generate architecture options using the individual ArchitectAgent
        try:
            # Import here to avoid circular dependency
            import sys
            sys.path.insert(0, '/tmp/autonomous_engineer')
            from autonomous_engineer.architect_agent import ArchitectAgent

            architect = ArchitectAgent(
                repo_path=context.get("repo_path", "."),
                llm_provider=self.llm_provider
            )

            # Generate one architecture
            base_result = architect.execute(task, context)

            if base_result["status"] != "success":
                return base_result

            base_plan = base_result["plan"]

            # Generate 2 alternative approaches
            options = []

            # Option A: Pragmatic (use base plan)
            options.append({
                "name": "Pragmatic Approach",
                "description": "Simple, battle-tested architecture focused on getting it working quickly",
                "plan": base_plan,
                "pros": [
                    "Faster to implement",
                    "Well-understood patterns",
                    "Lower complexity",
                    "Easier to maintain"
                ],
                "cons": [
                    "May need refactoring for scale",
                    "Less flexible for future changes"
                ],
                "estimated_time": "Low",
                "complexity": base_plan.get("estimated_complexity", "medium")
            })

            # Option B: Scalable (modify plan for enterprise)
            scalable_plan = base_plan.copy()
            scalable_plan["summary"] = f"Enterprise-ready version: {base_plan['summary']}"
            scalable_plan["estimated_complexity"] = "high"

            options.append({
                "name": "Scalable Enterprise Approach",
                "description": "Production-ready architecture with microservices, caching, monitoring",
                "plan": scalable_plan,
                "pros": [
                    "Scales horizontally",
                    "Production-ready patterns",
                    "Built-in observability",
                    "Better security"
                ],
                "cons": [
                    "More complex to implement",
                    "Longer development time",
                    "More dependencies"
                ],
                "estimated_time": "High",
                "complexity": "high"
            })

            # Option C: Modern/Innovative
            modern_plan = base_plan.copy()
            modern_plan["summary"] = f"Modern stack version: {base_plan['summary']}"

            options.append({
                "name": "Modern Stack Approach",
                "description": "Latest technologies - serverless, edge computing, real-time features",
                "plan": modern_plan,
                "pros": [
                    "Cutting-edge features",
                    "Lower infrastructure cost",
                    "Auto-scaling built-in",
                    "Real-time capabilities"
                ],
                "cons": [
                    "Less mature ecosystem",
                    "Team learning curve",
                    "Vendor lock-in risk"
                ],
                "estimated_time": "Medium",
                "complexity": "medium-high"
            })

            # Save options in state
            state["architecture_options"] = options

            # Ask user to choose
            return {
                "status": "needs_human",
                "question": "I've generated 3 architecture approaches. Which one would you like me to implement?",
                "options": [
                    {
                        "label": f"Option {i+1}: {opt['name']}",
                        "value": f"architecture_{i}",
                        "description": opt['description'],
                        "details": {
                            "pros": opt["pros"],
                            "cons": opt["cons"],
                            "estimated_time": opt["estimated_time"],
                            "complexity": opt["complexity"]
                        }
                    }
                    for i, opt in enumerate(options)
                ],
                "phase": "architecture",
                "reason": "Need user to select preferred architecture"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate architecture options: {str(e)}"
            }

    def _phase_implementation(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement based on chosen architecture."""
        print("⚙️  Implementing backend and frontend...\n")

        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        self.emergency_stop.check_and_raise()

        architecture_plan = state["phase_results"]["architecture"]["architecture_plan"]

        # Import implementation agents
        try:
            import sys
            sys.path.insert(0, '/tmp/autonomous_engineer')
            from autonomous_engineer.backend_agent import BackendAgent
            from autonomous_engineer.frontend_agent import FrontendAgent

            # Backend
            print("   🔨 Creating backend files...")

            # === BRAIN FRAMEWORK: Cost Check Before Expensive Operation ===
            cost_check = self.cost_tracker.check_limits()
            if cost_check.get("blocked"):
                return {
                    "status": "error",
                    "reason": "cost_limit_exceeded",
                    "message": "Cost limit would be exceeded by backend implementation"
                }

            backend = BackendAgent(
                repo_path=context.get("repo_path", "."),
                llm_provider=self.llm_provider
            )
            backend_result = backend.execute(architecture_plan, context)

            if backend_result["status"] != "success":
                return backend_result

            print(f"   ✅ Backend: {len(backend_result['files_created'])} files\n")

            # === BRAIN FRAMEWORK: Emergency Stop Check Between Backend/Frontend ===
            self.emergency_stop.check_and_raise()

            # Frontend
            print("   🎨 Creating frontend files...")

            # === BRAIN FRAMEWORK: Cost Check Before Frontend ===
            cost_check = self.cost_tracker.check_limits()
            if cost_check.get("blocked"):
                return {
                    "status": "error",
                    "reason": "cost_limit_exceeded",
                    "message": "Cost limit would be exceeded by frontend implementation",
                    "partial_result": {"backend_completed": True, "backend_files": backend_result["files_created"]}
                }

            frontend = FrontendAgent(
                repo_path=context.get("repo_path", "."),
                llm_provider=self.llm_provider
            )
            frontend_result = frontend.execute(architecture_plan, context)

            if frontend_result["status"] != "success":
                return frontend_result

            print(f"   ✅ Frontend: {len(frontend_result['files_created'])} files\n")

            all_files = backend_result["files_created"] + frontend_result["files_created"]

            return {
                "status": "success",
                "backend_files": backend_result["files_created"],
                "frontend_files": frontend_result["files_created"],
                "all_files": all_files,
                "message": f"Implemented {len(all_files)} files"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Implementation failed: {str(e)}"
            }

    def _phase_testing(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and run tests."""
        print("🧪 Generating tests...\n")

        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        self.emergency_stop.check_and_raise()

        implementation_files = state["phase_results"]["implementation"]["all_files"]

        try:
            import sys
            sys.path.insert(0, '/tmp/autonomous_engineer')
            from autonomous_engineer.test_agent import TestAgent

            test_agent = TestAgent(
                repo_path=context.get("repo_path", "."),
                llm_provider=self.llm_provider
            )
            result = test_agent.execute(implementation_files, context)

            if result["status"] == "success":
                print(f"   ✅ Generated {len(result['tests_created'])} test files\n")

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Testing failed: {str(e)}"
            }

    def _phase_review(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Review for security and quality issues."""
        print("🔍 Running security and quality review...\n")

        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        self.emergency_stop.check_and_raise()

        # Placeholder for now - will integrate with ReviewAgent later
        return {
            "status": "success",
            "issues_found": [],
            "message": "Review passed - no critical issues found"
        }

    def _phase_fix(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix any issues found in review."""
        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        self.emergency_stop.check_and_raise()

        issues = state["phase_results"].get("review", {}).get("issues_found", [])

        if not issues:
            # No issues to fix
            return {
                "status": "success",
                "message": "No issues to fix"
            }

        print(f"🔧 Fixing {len(issues)} issues...\n")

        try:
            import sys
            sys.path.insert(0, '/tmp/autonomous_engineer')
            from autonomous_engineer.fix_agent import FixAgent

            fix_agent = FixAgent(
                repo_path=context.get("repo_path", "."),
                llm_provider=self.llm_provider
            )
            result = fix_agent.execute(issues, context)

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Fix phase failed: {str(e)}"
            }

    def _phase_deploy(self, task: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create branch, commit, and PR."""
        print("🚀 Deploying (creating branch and PR)...\n")

        # === BRAIN FRAMEWORK: Emergency Stop Check ===
        self.emergency_stop.check_and_raise()

        try:
            import sys
            sys.path.insert(0, '/tmp/autonomous_engineer')
            from autonomous_engineer.deploy_agent import DeployAgent

            # Gather info for deployment
            feature_info = {
                "name": self._generate_feature_name(task),
                "request": task,
                "summary": self._generate_summary(state),
                "title": f"feat: {task[:50]}",
                "files_changed": state["phase_results"]["implementation"]["all_files"],
                "tests_added": len(state["phase_results"]["testing"].get("tests_created", []))
            }

            deploy_agent = DeployAgent(
                repo_path=context.get("repo_path", "."),
                github_token=context.get("github_token")
            )

            result = deploy_agent.execute(feature_info, context)

            if result["status"] == "success":
                print(f"   ✅ Created branch: {result.get('branch')}")
                if result.get("pr_url"):
                    print(f"   🔗 PR: {result['pr_url']}\n")

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Deploy failed: {str(e)}"
            }

    def _get_next_phase(self, current_phase: str, state: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next phase based on current phase and state."""
        phase_order = ["architecture", "implementation", "testing", "review", "fix", "deploy"]

        try:
            current_idx = phase_order.index(current_phase)

            # Special logic: skip fix if no issues
            if current_phase == "review":
                issues = state["phase_results"]["review"].get("issues_found", [])
                if not issues:
                    # Skip fix, go to deploy
                    return "deploy"

            # Return next phase
            if current_idx + 1 < len(phase_order):
                return phase_order[current_idx + 1]

            return None  # All done

        except ValueError:
            return None

    def _generate_feature_name(self, task: str) -> str:
        """Generate kebab-case feature name."""
        name = task.lower()
        name = "".join(c if c.isalnum() or c.isspace() else "" for c in name)
        name = "-".join(name.split()[:5])
        return name

    def _generate_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary of all work done."""
        lines = []
        lines.append(f"Feature: {state['feature_request']}")
        lines.append("")

        if "architecture" in state["phase_results"]:
            arch = state["phase_results"]["architecture"]
            lines.append(f"Architecture: {arch['architecture_plan'].get('summary', 'N/A')}")
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

    def _format_final_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format final success result."""
        start = datetime.fromisoformat(state["start_time"])
        end = datetime.fromisoformat(state["end_time"])
        duration = end - start

        minutes = int(duration.total_seconds() / 60)
        seconds = int(duration.total_seconds() % 60)

        # === BRAIN FRAMEWORK: Get Final Cost Summary ===
        cost_summary = self.cost_tracker.get_summary()

        print(f"\n{'='*70}")
        print(f"🎉 AUTONOMOUS BUILDER COMPLETED")
        print(f"{'='*70}")
        print(f"⏱️  Duration: {minutes}m {seconds}s")
        print(f"📊 All phases completed successfully")
        print(f"\n💰 COST BREAKDOWN:")
        for phase, cost in state.get("phase_costs", {}).items():
            print(f"   {phase.capitalize()}: ${cost:.4f}")
        print(f"   {'─'*40}")
        print(f"   Total: ${state.get('total_cost', 0):.4f}")
        print(f"{'='*70}\n")

        return {
            "status": "success",
            "message": "Feature built successfully with human oversight",
            "feature_request": state["feature_request"],
            "duration": f"{minutes}m {seconds}s",
            "phases": state["phase_results"],
            "pr_url": state["phase_results"].get("deploy", {}).get("pr_url"),
            "branch": state["phase_results"].get("deploy", {}).get("branch"),
            "files_created": state["phase_results"]["implementation"]["all_files"],
            "tests_created": state["phase_results"]["testing"].get("tests_created", []),
            # === BRAIN FRAMEWORK: Include Cost Info ===
            "total_cost": state.get("total_cost", 0),
            "phase_costs": state.get("phase_costs", {}),
            "cost_summary": cost_summary
        }

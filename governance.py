"""Governance Framework: Traffic Light Protocol for Autonomous Agents.

The Agent is an Intern - treat every agent as a talented but reckless Junior Engineer with sudo access.

🟢 Green: Tasks you'd let an intern do while you're at lunch (read-only, safe)
🟡 Yellow: Tasks you'd let an intern do if you reviewed their PR first (drafts, reversible)
🔴 Red: Tasks you'd never let an intern do without you typing the password (destructive, production)
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path


class RiskLevel(Enum):
    """Traffic Light Protocol Risk Levels."""
    GREEN = "green"   # Read-only, safe, idempotent
    YELLOW = "yellow" # Drafts, reversible mutations
    RED = "red"       # Destructive, production state


@dataclass
class ToolGovernance:
    """Governance rules for a tool/operation."""
    tool_name: str
    risk_level: RiskLevel
    description: str
    requires_approval: bool
    approval_message: Optional[str] = None
    max_auto_retries: int = 3
    allowed_contexts: List[str] = None  # e.g., ["dev", "staging"] but not ["production"]
    
    def __post_init__(self):
        if self.allowed_contexts is None:
            self.allowed_contexts = []


class GovernanceFramework:
    """Governance framework for autonomous agents."""
    
    def __init__(self, approval_store: str = ".agent_approvals.json"):
        self.approval_store = Path(approval_store)
        self.tool_registry: Dict[str, ToolGovernance] = {}
        self.pending_approvals: Dict[str, Dict] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools with risk levels."""
        
        # 🟢 GREEN: Read-only, safe operations
        green_tools = [
            ToolGovernance("docker_ps", RiskLevel.GREEN, "List containers", False),
            ToolGovernance("docker_logs", RiskLevel.GREEN, "Read container logs", False),
            ToolGovernance("docker_inspect", RiskLevel.GREEN, "Inspect container", False),
            ToolGovernance("ha_get_state", RiskLevel.GREEN, "Get entity state", False),
            ToolGovernance("ha_get_logs", RiskLevel.GREEN, "Read HA logs", False),
            ToolGovernance("ha_search_logs", RiskLevel.GREEN, "Search HA logs", False),
            ToolGovernance("ha_list_integrations", RiskLevel.GREEN, "List integrations", False),
            ToolGovernance("ha_get_config", RiskLevel.GREEN, "Read HA config", False),
            ToolGovernance("web_search", RiskLevel.GREEN, "Search the web for current information", False),
        ]
        
        # 🟡 YELLOW: Drafts, reversible mutations
        yellow_tools = [
            ToolGovernance(
                "write_file",
                RiskLevel.YELLOW,
                "Write/create file",
                True,
                "I want to create/modify a file. Review the change plan?",
                allowed_contexts=["dev", "staging", "local"]
            ),
            ToolGovernance(
                "docker_exec",
                RiskLevel.YELLOW,
                "Execute command in container",
                True,
                "I want to run a command in a container. Review?",
                allowed_contexts=["dev", "staging"]
            ),
            ToolGovernance(
                "ha_call_service",
                RiskLevel.YELLOW,
                "Call HA service",
                True,
                "I want to call a Home Assistant service. Review?",
                allowed_contexts=["dev", "staging"]
            ),
        ]
        
        # 🔴 RED: Destructive, production state
        red_tools = [
            ToolGovernance(
                "docker_restart",
                RiskLevel.RED,
                "Restart container",
                True,
                "⚠️ CRITICAL: I want to restart a container. This may cause downtime. Approve?",
                allowed_contexts=[]  # Never auto-approve
            ),
            ToolGovernance(
                "docker_compose_up",
                RiskLevel.RED,
                "Start/update services",
                True,
                "⚠️ CRITICAL: I want to start/update Docker services. This affects infrastructure. Approve?",
                allowed_contexts=[]  # Never auto-approve
            ),
            ToolGovernance(
                "run_shell",
                RiskLevel.RED,
                "Execute shell command",
                True,
                "⚠️ CRITICAL: I want to execute a shell command. Review carefully?",
                allowed_contexts=[]  # Never auto-approve
            ),
            ToolGovernance(
                "deploy_mcp_server",
                RiskLevel.RED,
                "Deploy new MCP server",
                True,
                "⚠️ CRITICAL: I want to deploy a new MCP server. This gives the agent new capabilities. Approve?",
                allowed_contexts=[]  # Never auto-approve - most dangerous operation
            ),
            ToolGovernance(
                "self_modify_codebase",
                RiskLevel.RED,
                "Self-modify codebase (self-healing)",
                True,
                "⚠️ CRITICAL: I want to modify my own codebase to fix an issue. This is self-healing. Approve?",
                allowed_contexts=["dev", "staging"]  # Allow in dev/staging, require approval in production
            ),
        ]
        
        # Register all tools
        for tool in green_tools + yellow_tools + red_tools:
            self.tool_registry[tool.tool_name] = tool
    
    def register_tool(self, tool: ToolGovernance):
        """Register a custom tool with governance rules."""
        self.tool_registry[tool.tool_name] = tool
    
    def check_permission(self, tool_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if tool can be executed autonomously."""
        if tool_name not in self.tool_registry:
            # Special handling for self_modify_codebase
            if tool_name == "self_modify_codebase":
                context = context or {}
                environment = context.get("environment", "production")
                issue_type = context.get("issue_type", "unknown")
                severity = context.get("severity", "medium")
                
                # Allow in dev/staging for critical issues, require approval in production
                if environment in ["dev", "development", "staging", "local"]:
                    if severity == "critical" and issue_type in ["reliability", "bug"]:
                        return {
                            "allowed": True,
                            "risk_level": RiskLevel.RED.value,
                            "requires_approval": False,
                            "message": "Self-healing allowed in non-production for critical reliability issues"
                        }
                
                # Default: require approval
                return {
                    "allowed": False,
                    "risk_level": RiskLevel.RED.value,
                    "requires_approval": True,
                    "approval_message": f"Self-modification of codebase requires approval (severity: {severity}, type: {issue_type})",
                    "tool": ToolGovernance(
                        tool_name,
                        RiskLevel.RED,
                        "Self-modify codebase",
                        True,
                        f"⚠️ CRITICAL: Self-healing wants to modify codebase. Approve?",
                        allowed_contexts=["dev", "staging"]
                    )
                }
            
            # Unknown tool - default to RED (most restrictive)
            return {
                "allowed": False,
                "risk_level": RiskLevel.RED.value,
                "requires_approval": True,
                "message": f"Unknown tool '{tool_name}' - requires approval"
            }
        
        tool = self.tool_registry[tool_name]
        context = context or {}
        environment = context.get("environment", "production")  # Default to production (safest)
        
        # Check context restrictions
        if tool.allowed_contexts and environment not in tool.allowed_contexts:
            return {
                "allowed": False,
                "risk_level": tool.risk_level.value,
                "requires_approval": True,
                "message": f"Tool '{tool_name}' not allowed in '{environment}' environment"
            }
        
        # GREEN tools: Always allowed (fully autonomous)
        if tool.risk_level == RiskLevel.GREEN:
            return {
                "allowed": True,
                "risk_level": RiskLevel.GREEN.value,
                "requires_approval": False,
                "message": "Read-only operation - safe to execute autonomously"
            }
        
        # YELLOW tools: Check if can auto-approve
        if tool.risk_level == RiskLevel.YELLOW:
            # Check environment - auto-approve in dev/staging
            if environment in ["dev", "development", "staging", "local"]:
                return {
                    "allowed": True,
                    "risk_level": RiskLevel.YELLOW.value,
                    "requires_approval": False,
                    "message": "Yellow operation - auto-approved in non-production environment"
                }
            
            # In production, require approval for yellow
            return {
                "allowed": False,
                "risk_level": RiskLevel.YELLOW.value,
                "requires_approval": True,
                "approval_message": tool.approval_message or f"Tool '{tool_name}' requires approval (YELLOW risk)",
                "tool": tool
            }
        
        # RED tools: Always require approval (never auto-approve)
        return {
            "allowed": False,
            "risk_level": RiskLevel.RED.value,
            "requires_approval": True,
            "approval_message": tool.approval_message or f"Tool '{tool_name}' requires approval (RED risk - critical operation)",
            "tool": tool
        }
    
    def request_approval(self, tool_name: str, change_plan: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Request approval for a tool execution. Returns approval_id."""
        import uuid
        approval_id = str(uuid.uuid4())[:8]
        
        tool = self.tool_registry.get(tool_name)
        if not tool:
            tool = ToolGovernance(tool_name, RiskLevel.RED, "Unknown tool", True)
        
        approval_request = {
            "approval_id": approval_id,
            "tool_name": tool_name,
            "risk_level": tool.risk_level.value,
            "change_plan": change_plan,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "approval_message": tool.approval_message or f"Approval required for {tool_name}"
        }
        
        self.pending_approvals[approval_id] = approval_request
        self._save_approvals()
        
        return approval_id
    
    def get_approval_request(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval request details."""
        return self.pending_approvals.get(approval_id)
    
    def approve(self, approval_id: str, approver: str = "human") -> Dict[str, Any]:
        """Approve a pending request."""
        if approval_id not in self.pending_approvals:
            return {"status": "error", "message": f"Approval {approval_id} not found"}
        
        request = self.pending_approvals[approval_id]
        request["status"] = "approved"
        request["approver"] = approver
        request["approved_at"] = datetime.now().isoformat()
        
        self._save_approvals()
        
        return {
            "status": "approved",
            "approval_id": approval_id,
            "tool_name": request["tool_name"],
            "change_plan": request["change_plan"]
        }
    
    def reject(self, approval_id: str, reason: str = "") -> Dict[str, Any]:
        """Reject a pending request."""
        if approval_id not in self.pending_approvals:
            return {"status": "error", "message": f"Approval {approval_id} not found"}
        
        request = self.pending_approvals[approval_id]
        request["status"] = "rejected"
        request["rejection_reason"] = reason
        request["rejected_at"] = datetime.now().isoformat()
        
        self._save_approvals()
        
        return {"status": "rejected", "approval_id": approval_id}
    
    def is_approved(self, approval_id: str) -> bool:
        """Check if approval is granted."""
        request = self.pending_approvals.get(approval_id)
        return request and request.get("status") == "approved"
    
    def _save_approvals(self):
        """Save approval requests to disk."""
        try:
            with open(self.approval_store, "w") as f:
                json.dump(self.pending_approvals, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save approvals: {e}")
    
    def _load_approvals(self):
        """Load approval requests from disk."""
        if self.approval_store.exists():
            try:
                with open(self.approval_store) as f:
                    self.pending_approvals = json.load(f)
            except:
                self.pending_approvals = {}


class PlanAndApply:
    """Plan & Apply pattern (like Terraform workflow)."""
    
    def __init__(self, governance: GovernanceFramework):
        self.governance = governance
        self.current_plan: Optional[Dict[str, Any]] = None
    
    def create_plan(self, task: str, proposed_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a change plan (Phase 1: Plan)."""
        plan = {
            "task": task,
            "actions": [],
            "risk_summary": {
                "green": 0,
                "yellow": 0,
                "red": 0
            },
            "requires_approval": False,
            "timestamp": datetime.now().isoformat()
        }
        
        for action in proposed_actions:
            tool_name = action.get("tool")
            permission = self.governance.check_permission(tool_name, action.get("context", {}))
            
            action_plan = {
                "tool": tool_name,
                "args": action.get("args", {}),
                "risk_level": permission["risk_level"],
                "requires_approval": permission["requires_approval"],
                "approval_message": permission.get("approval_message")
            }
            
            plan["actions"].append(action_plan)
            plan["risk_summary"][permission["risk_level"]] += 1
            
            if permission["requires_approval"]:
                plan["requires_approval"] = True
        
        self.current_plan = plan
        return plan
    
    def format_plan(self, plan: Dict[str, Any] = None) -> str:
        """Format plan as human-readable markdown."""
        plan = plan or self.current_plan
        if not plan:
            return "No plan available"
        
        md = f"# Change Plan: {plan['task']}\n\n"
        md += f"**Timestamp:** {plan['timestamp']}\n\n"
        
        # Risk summary
        risk = plan["risk_summary"]
        md += "## Risk Summary\n\n"
        md += f"- 🟢 Green (Safe): {risk['green']}\n"
        md += f"- 🟡 Yellow (Review): {risk['yellow']}\n"
        md += f"- 🔴 Red (Critical): {risk['red']}\n\n"
        
        # Actions
        md += "## Proposed Actions\n\n"
        for i, action in enumerate(plan["actions"], 1):
            risk_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(action["risk_level"], "⚪")
            md += f"### {i}. {risk_emoji} {action['tool']}\n\n"
            md += f"**Risk Level:** {action['risk_level'].upper()}\n\n"
            if action.get("args"):
                md += f"**Arguments:**\n```json\n{json.dumps(action['args'], indent=2)}\n```\n\n"
            if action["requires_approval"]:
                md += f"**⚠️ Requires Approval:** {action.get('approval_message', '')}\n\n"
        
        if plan["requires_approval"]:
            md += "\n---\n\n"
            md += "## ⚠️ Approval Required\n\n"
            md += "This plan contains operations that require human approval.\n"
            md += "Review the actions above and approve/reject when ready.\n"
        
        return md
    
    def apply(self, plan: Dict[str, Any] = None, approval_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the plan (Phase 2: Apply)."""
        plan = plan or self.current_plan
        if not plan:
            return {"status": "error", "message": "No plan to apply"}
        
        # Check if approval is needed and granted
        if plan["requires_approval"]:
            if not approval_id:
                return {
                    "status": "error",
                    "message": "Approval required but not provided",
                    "plan": plan
                }
            
            if not self.governance.is_approved(approval_id):
                return {
                    "status": "error",
                    "message": f"Approval {approval_id} not granted",
                    "plan": plan
                }
        
        # Execute actions
        results = []
        for action in plan["actions"]:
            # Check permission again (safety check)
            permission = self.governance.check_permission(
                action["tool"],
                action.get("context", {})
            )
            
            if not permission["allowed"] and not self.governance.is_approved(approval_id):
                results.append({
                    "tool": action["tool"],
                    "status": "skipped",
                    "reason": "Not approved"
                })
                continue
            
            # Execute action (this would call the actual tool)
            results.append({
                "tool": action["tool"],
                "status": "executed",
                "args": action.get("args", {})
            })
        
        return {
            "status": "success",
            "plan": plan,
            "results": results
        }


# Global governance instance
_governance = None

def get_governance() -> GovernanceFramework:
    """Get or create global governance instance."""
    global _governance
    if _governance is None:
        _governance = GovernanceFramework()
    return _governance


"""Meta-Agent: Self-Evolving Agent Architecture.

The agent can:
1. Classify requests by risk (Green/Yellow/Red)
2. Write code for new MCP servers (Yellow - drafting)
3. Deploy new MCP servers (Red - requires approval)

This is the "Holy Grail" - an agent that extends its own capabilities safely.
"""

from typing import Dict, Any, List, Optional
from autonomous_router import AutonomousRouter
from governance import get_governance, RiskLevel, ToolGovernance
from fact_checker import FactChecker
from auth_broker import AuthBroker, NeedAuthError, get_auth_broker
import json
import os
from pathlib import Path
import subprocess


class ToolsmithAgent:
    """Agent that can write new MCP server code to extend capabilities."""
    
    def __init__(self):
        self.governance = get_governance()
        self.mcp_servers_dir = Path("mcp_servers")
        self.mcp_servers_dir.mkdir(exist_ok=True)
    
    def detect_missing_tool(self, task: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
        """Detect if a required tool is missing for the task."""
        task_lower = task.lower()
        
        # Common tool patterns
        missing_tools = []
        
        if "aws" in task_lower or "cost" in task_lower or "billing" in task_lower or "s3" in task_lower:
            if "cost_explorer" not in str(available_tools).lower() and "s3" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "cost_explorer",
                    "description": "AWS Cost Explorer API access",
                    "reason": "Task requires AWS cost/billing information",
                    "auth_required": "aws"  # Requires AWS authentication
                })
        
        if "s3" in task_lower or "bucket" in task_lower:
            if "s3" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "s3",
                    "description": "AWS S3 access",
                    "reason": "Task requires S3 bucket access",
                    "auth_required": "aws"  # Requires AWS authentication
                })
        
        if "kubernetes" in task_lower or "k8s" in task_lower or "kubectl" in task_lower:
            if "kubectl" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "kubectl",
                    "description": "Kubernetes cluster management",
                    "reason": "Task requires Kubernetes operations",
                    "auth_required": "kubernetes"  # Requires kubeconfig
                })
        
        if "terraform" in task_lower or "infrastructure" in task_lower:
            if "terraform" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "terraform",
                    "description": "Terraform state management",
                    "reason": "Task requires infrastructure as code",
                    "auth_required": "terraform"  # Requires cloud provider credentials
                })
        
        if "git" in task_lower or "repository" in task_lower:
            if "git" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "git",
                    "description": "Git repository operations",
                    "reason": "Task requires Git operations",
                    "auth_required": None  # Git may or may not need auth
                })
        
        if "email" in task_lower or "gmail" in task_lower or "spam" in task_lower:
            if "gmail" not in str(available_tools).lower() and "email" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "gmail",
                    "description": "Gmail API access",
                    "reason": "Task requires email access",
                    "auth_required": "gmail"  # Requires OAuth
                })
        
        if "cookidoo" in task_lower:
            if "cookidoo" not in str(available_tools).lower():
                missing_tools.append({
                    "tool_name": "cookidoo",
                    "description": "Cookidoo recipe API",
                    "reason": "Task requires Cookidoo access",
                    "auth_required": "cookidoo"  # Requires API key
                })
        
        return missing_tools[0] if missing_tools else None
    
    def generate_mcp_server(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MCP server code for a missing tool."""
        tool_name = tool_spec["tool_name"]
        description = tool_spec["description"]
        
        print(f"\n🔧 Toolsmith Agent: Generating MCP server for {tool_name}")
        print(f"   Reason: {tool_spec['reason']}")
        
        # This would use LLM to generate the MCP server code
        # For now, we'll create a template structure
        
        server_file = self.mcp_servers_dir / f"{tool_name}_tools.py"
        
        # Check if already exists
        if server_file.exists():
            return {
                "status": "exists",
                "message": f"MCP server for {tool_name} already exists",
                "file_path": str(server_file)
            }
        
        # Generate code template (in real implementation, LLM would generate this)
        code_template = self._generate_mcp_template(tool_name, description)
        
        # Write code (Yellow risk - drafting)
        permission = self.governance.check_permission("write_file", {"environment": "production"})
        
        if not permission["allowed"]:
            # Request approval for writing code
            approval_id = self.governance.request_approval(
                "write_file",
                {
                    "file_path": str(server_file),
                    "description": f"Generate MCP server code for {tool_name}",
                    "code_preview": code_template[:500]
                },
                {"environment": "production"}
            )
            
            return {
                "status": "pending_approval",
                "approval_id": approval_id,
                "file_path": str(server_file),
                "code": code_template
            }
        
        # Write file (if allowed in dev/staging)
        try:
            with open(server_file, "w") as f:
                f.write(code_template)
            
            return {
                "status": "success",
                "message": f"MCP server code generated for {tool_name}",
                "file_path": str(server_file),
                "code": code_template
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to write code: {str(e)}"
            }
    
    def _generate_mcp_template(self, tool_name: str, description: str) -> str:
        """Generate MCP server code using LLM."""
        from langchain_ollama import ChatOllama
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOllama(model="llama3.1:latest", temperature=0.3)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert MCP (Model Context Protocol) server developer.
Generate a complete, production-ready MCP server Python module.

Requirements:
1. Follow the pattern of existing MCP servers (docker_tools.py, homeassistant_tools.py)
2. Use proper type hints (Dict[str, Any], Optional, etc.)
3. Include error handling
4. Return standardized response format: {"status": "success/error", "message": "...", ...}
5. Include tool registry at the bottom
6. Include initialization function

The tool should be for: {description}

Generate complete, working code. Do not include TODO comments - implement fully."""),
            HumanMessage(content=f"""Create an MCP server for: {tool_name}
Description: {description}

Generate a complete Python module with:
- Functions for common operations
- Proper error handling
- Tool registry
- Client initialization

Make it production-ready.""")
        ])
        
        chain = prompt | llm
        response = chain.invoke({})
        
        code = response.content if hasattr(response, 'content') else str(response)
        
        # Extract code block if wrapped in markdown
        import re
        code_match = re.search(r'```(?:python)?\n(.*?)```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
        
        return code


class MetaAgent:
    """Meta-Agent: Self-evolving agent that can extend its capabilities."""
    
    def __init__(self, environment: str = "production"):
        self.router = AutonomousRouter()
        self.governance = get_governance()
        self.fact_checker = FactChecker()
        self.toolsmith = ToolsmithAgent()
        self.auth_broker = get_auth_broker()  # Identity Broker
        self.environment = environment
        self.available_tools = self._discover_tools()
    
    def _discover_tools(self) -> List[str]:
        """Discover all available MCP tools."""
        tools = []
        
        # Check MCP servers directory
        mcp_dir = Path("mcp_servers")
        if mcp_dir.exists():
            for file in mcp_dir.glob("*_tools.py"):
                tool_name = file.stem.replace("_tools", "")
                tools.append(tool_name)
        
        # Add base tools
        tools.extend(["write_file", "run_shell"])
        
        return tools
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Process request with self-evolution capability."""
        print("\n" + "="*70)
        print("🧠 META-AGENT: Self-Evolving Request Processing")
        print("="*70)
        print(f"\n📥 Request: {request}\n")
        
        # Step 1: Classify (The "Sorting Hat")
        print("="*70)
        print("STEP 1: CLASSIFICATION (The Sorting Hat)")
        print("="*70)
        
        classification = self._classify_request(request)
        print(f"\n   Intent: {classification['intent']}")
        print(f"   Risk Level: {classification['risk_level']}")
        print(f"   Routing: {classification['routing']}")
        
        # Step 2: Check for missing tools
        print("\n" + "="*70)
        print("STEP 2: TOOL DISCOVERY")
        print("="*70)
        
        missing_tool = self.toolsmith.detect_missing_tool(request, self.available_tools)
        
        if missing_tool:
            print(f"\n   ⚠️  Missing Tool Detected:")
            print(f"      Tool: {missing_tool['tool_name']}")
            print(f"      Description: {missing_tool['description']}")
            print(f"      Reason: {missing_tool['reason']}")
            
            # Step 3: Self-Evolution (Toolsmith)
            print("\n" + "="*70)
            print("STEP 3: SELF-EVOLUTION (Toolsmith Agent)")
            print("="*70)
            
            print(f"\n   🔧 Agent realizes it needs: {missing_tool['tool_name']}")
            print(f"   💡 Switching to 'Developer' mode...")
            
            # Generate MCP server code (Yellow risk - drafting)
            generation_result = self.toolsmith.generate_mcp_server(missing_tool)
            
            if generation_result.get("status") == "pending_approval":
                print(f"\n   ⏸️  Code generation requires approval")
                print(f"      Approval ID: {generation_result['approval_id']}")
                print(f"      File: {generation_result['file_path']}")
                print(f"\n   📋 Code Preview:")
                print(f"      {generation_result['code'][:300]}...")
                print(f"\n   💡 Review and approve: python approve.py approve {generation_result['approval_id']}")
                
                return {
                    "status": "pending_approval",
                    "stage": "code_generation",
                    "approval_id": generation_result["approval_id"],
                    "missing_tool": missing_tool,
                    "generated_code": generation_result["code"]
                }
            
            elif generation_result.get("status") == "success":
                print(f"\n   ✅ Code generated: {generation_result['file_path']}")
                
                # Step 3.5: Check Authentication (if required)
                auth_required = missing_tool.get("auth_required")
                if auth_required:
                    print("\n" + "="*70)
                    print("STEP 3.5: AUTHENTICATION CHECK")
                    print("="*70)
                    
                    try:
                        self.auth_broker.require_auth(auth_required)
                        print(f"\n   ✅ Authentication verified for {auth_required}")
                    except NeedAuthError as e:
                        print(f"\n   ⚠️  Authentication required for {auth_required}")
                        print(f"   📋 {e.message}")
                        print(f"\n   💡 Action: {e.action}")
                        
                        return {
                            "status": "auth_required",
                            "auth_type": e.auth_type,
                            "service_name": e.service_name,
                            "message": e.message,
                            "action": e.action,
                            "missing_tool": missing_tool,
                            "generated_code": generation_result.get("code")
                        }
                
                # Step 4: MVP Deployment (Red risk - requires approval)
                print("\n" + "="*70)
                print("STEP 4: MVP DEPLOYMENT (Red Risk)")
                print("="*70)
                
                deploy_result = self._deploy_mcp_server(
                    generation_result["file_path"],
                    missing_tool["tool_name"]
                )
                
                if deploy_result.get("status") == "pending_approval":
                    return {
                        "status": "pending_approval",
                        "stage": "deployment",
                        "approval_id": deploy_result["approval_id"],
                        "missing_tool": missing_tool,
                        "generated_code": generation_result["code"]
                    }
                elif deploy_result.get("status") == "success":
                    # Hot-reload tools (refresh discovery)
                    self.available_tools = self._discover_tools()
                    print(f"\n   ✅ Tool deployed and hot-reloaded (MVP: process reload)")
                    print(f"   🔄 Re-running original request with new tool...")
                    
                    # Re-process original request with new tool
                    return self._process_with_tools(request)
        
        # No missing tools - process normally
        return self._process_with_tools(request)
    
    def _classify_request(self, request: str) -> Dict[str, Any]:
        """Classify request by intent and risk (The Sorting Hat)."""
        request_lower = request.lower()
        
        # Intent detection
        analysis_keywords = ["assess", "analyze", "diagnose", "check", "why", "what", "how"]
        drafting_keywords = ["create", "write", "generate", "draft", "build"]
        execution_keywords = ["deploy", "run", "execute", "apply", "install", "restart"]
        
        if any(kw in request_lower for kw in analysis_keywords):
            intent = "ANALYSIS"
            risk_level = "🟢 Green"
            routing = "Diagnosis/Consulting Agent"
        elif any(kw in request_lower for kw in drafting_keywords):
            intent = "DRAFTING"
            risk_level = "🟡 Yellow"
            routing = "Coder Agent (with approval gate)"
        elif any(kw in request_lower for kw in execution_keywords):
            intent = "EXECUTION"
            risk_level = "🔴 Red"
            routing = "Execution Agent (with approval gate)"
        else:
            intent = "ANALYSIS"
            risk_level = "🟢 Green"
            routing = "General Agent"
        
        return {
            "intent": intent,
            "risk_level": risk_level,
            "routing": routing
        }
    
    def _deploy_mcp_server(self, file_path: str, tool_name: str) -> Dict[str, Any]:
        """Deploy MCP server (Red risk - requires approval).
        
        MVP Approach: Write to mcp_servers/ and restart Python MCP process.
        Future: Can upgrade to Docker container deployment for full isolation.
        """
        print(f"\n   🚀 Deploying MCP server: {tool_name}")
        print(f"   ⚠️  CRITICAL: This gives the agent new capabilities")
        print(f"   ⚠️  This is RED risk - requires explicit approval")
        print(f"\n   📝 MVP Approach: Restarting MCP process (not Docker container)")
        print(f"   💡 Future: Can upgrade to Docker-in-Docker for full isolation")
        
        # Request approval for deployment
        approval_id = self.governance.request_approval(
            "deploy_mcp_server",
            {
                "tool_name": tool_name,
                "file_path": file_path,
                "description": f"Deploy new MCP server for {tool_name} - this gives the agent new capabilities",
                "risk": "RED - Agent will gain new powers",
                "deployment_method": "MVP: Restart MCP process (not Docker container)"
            },
            {"environment": self.environment}
        )
        
        if not self.governance.is_approved(approval_id):
            return {
                "status": "pending_approval",
                "approval_id": approval_id,
                "message": "Deployment requires human approval"
            }
        
        # MVP Deployment: Validate and reload
        print(f"\n   ✅ Deployment approved - deploying (MVP method)...")
        
        # Step 1: Validate code syntax
        print(f"   🔍 Step 1: Validating code syntax...")
        validation_result = self._validate_python_code(file_path)
        if not validation_result["valid"]:
            return {
                "status": "error",
                "message": f"Code validation failed: {validation_result['error']}",
                "file_path": file_path
            }
        print(f"   ✅ Code syntax valid")
        
        # Step 2: Reload Python modules (hot-reload)
        print(f"   🔄 Step 2: Reloading MCP tool registry...")
        reload_result = self._reload_mcp_tools()
        if not reload_result["success"]:
            return {
                "status": "error",
                "message": f"Failed to reload tools: {reload_result['error']}",
                "file_path": file_path
            }
        print(f"   ✅ Tool registry reloaded")
        
        # Step 3: Verify tool is available
        print(f"   ✅ Step 3: Verifying tool availability...")
        if tool_name not in self._discover_tools():
            return {
                "status": "error",
                "message": f"Tool {tool_name} not found after deployment",
                "file_path": file_path
            }
        print(f"   ✅ Tool {tool_name} is now available")
        
        return {
            "status": "success",
            "message": f"MCP server for {tool_name} deployed and reloaded",
            "tool_name": tool_name,
            "deployment_method": "MVP: Process reload (not Docker container)"
        }
    
    def _validate_python_code(self, file_path: str) -> Dict[str, Any]:
        """Validate Python code syntax."""
        try:
            import ast
            with open(file_path, 'r') as f:
                code = f.read()
            ast.parse(code)
            return {"valid": True}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def _reload_mcp_tools(self) -> Dict[str, Any]:
        """Reload MCP tools by refreshing Python imports.
        
        MVP: Uses importlib.reload() to hot-reload modules.
        Note: This works for new modules. Existing modules need explicit reload.
        """
        try:
            import importlib
            import sys
            
            # Clear any cached imports for mcp_servers
            modules_to_remove = [
                name for name in sys.modules.keys()
                if name.startswith('mcp_servers.')
            ]
            for module_name in modules_to_remove:
                del sys.modules[module_name]
            
            # Force re-discovery on next import
            return {"success": True, "message": "MCP tool registry cleared for reload"}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_with_tools(self, request: str) -> Dict[str, Any]:
        """Process request using available tools."""
        # Use existing orchestrator
        from autonomous_orchestrator import AutonomousOrchestrator
        
        orchestrator = AutonomousOrchestrator()
        return orchestrator.execute(request)


def main():
    """Main entry point for Meta-Agent."""
    import sys
    
    meta_agent = MetaAgent(environment="production")
    
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        print("Enter request (or 'exit' to quit):")
        request = input("> ").strip()
        if not request or request.lower() == "exit":
            return
    
    result = meta_agent.process_request(request)
    
    print("\n" + "="*70)
    print("📊 META-AGENT RESULT")
    print("="*70)
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("status") == "pending_approval":
        print(f"\n⏸️  Approval required at stage: {result.get('stage')}")
        print(f"   Approval ID: {result.get('approval_id')}")
        print(f"   Run: python approve.py approve {result.get('approval_id')}")


if __name__ == "__main__":
    main()


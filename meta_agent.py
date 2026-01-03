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
from llm_provider import LLMProvider, create_llm_provider
# from observability_generator import get_observability_generator
from architecture_agent import get_architecture_agent
import json
import os
import re
from pathlib import Path
import subprocess


class ToolsmithAgent:
    """Agent that can write new MCP server code to extend capabilities."""
    
    def __init__(self):
        self.governance = get_governance()
        self.mcp_servers_dir = Path("mcp_servers")
        self.mcp_servers_dir.mkdir(exist_ok=True)
    
    def detect_missing_tool_llm(self, task: str, available_tools: List[str]) -> List[Dict[str, Any]]:
        """Use LLM to detect ALL missing tools for a task.
        
        Args:
            task: Task description
            available_tools: List of currently available tools
            
        Returns:
            List of missing tool specifications
        """
        from langchain_ollama import ChatOllama
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOllama(model="gemma3:4b", temperature=0.3)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a tool requirement analyzer. Analyze a task and determine ALL tools/capabilities needed to complete it.

Available tools: {available_tools}

For each MISSING tool needed, provide:
1. Tool name (e.g., "kubernetes", "monitoring", "logging", "error_tracker")
2. Description of what it does
3. Why it's needed for this task
4. Whether authentication is required (e.g., "aws", "kubernetes", "gmail", or null)

Return ONLY valid JSON array (no markdown, no explanation):
[
    {{
        "tool_name": "tool_name",
        "description": "What the tool does",
        "reason": "Why it's needed for this task",
        "auth_required": "aws" or null
    }}
]

If no tools are missing, return empty array: []"""),
            HumanMessage(content=f"Task: {task}\n\nAnalyze and list ALL missing tools needed to complete this task.")
        ])
        
        try:
            chain = prompt | llm
            response = chain.invoke({"available_tools": ", ".join(available_tools)})
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                tools = json.loads(json_match.group())
                return tools if isinstance(tools, list) else []
        except Exception as e:
            print(f"⚠️  LLM tool detection failed: {e}, falling back to pattern matching")
        
        return []
    
    def detect_missing_tool(self, task: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
        """Detect if a required tool is missing for the task (uses LLM if available)."""
        # Try LLM-based detection first
        llm_tools = self.detect_missing_tool_llm(task, available_tools)
        if llm_tools:
            return llm_tools[0]  # Return first missing tool
        
        # Fallback to pattern matching
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
        
        llm = ChatOllama(model="gemma3:4b", temperature=0.3)
        
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
    
    def __init__(self, environment: str = "production", enable_full_autonomy: bool = True):
        self.router = AutonomousRouter()
        self.governance = get_governance()
        self.fact_checker = FactChecker()
        self.toolsmith = ToolsmithAgent()
        self.auth_broker = get_auth_broker()  # Identity Broker
        self.environment = environment
        self.enable_full_autonomy = enable_full_autonomy
        from observability_generator import get_observability_generator
        self.llm_provider = create_llm_provider("ollama")
        self.observability_gen = get_observability_generator()
        self.architect = get_architecture_agent()
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
        
        # Step 0: Check if this is a system-building request
        is_system_building = self._is_system_building_request(request)
        
        if is_system_building and self.enable_full_autonomy:
            return self._process_system_building_request(request)
        
        # Step 1: Classify (The "Sorting Hat")
        print("="*70)
        print("STEP 1: CLASSIFICATION (The Sorting Hat)")
        print("="*70)
        
        classification = self._classify_request(request)
        print(f"\n   Intent: {classification['intent']}")
        print(f"   Risk Level: {classification['risk_level']}")
        print(f"   Routing: {classification['routing']}")
        
        # Step 2: Check for missing tools (enhanced with LLM analysis)
        print("\n" + "="*70)
        print("STEP 2: TOOL DISCOVERY")
        print("="*70)
        
        # Use LLM to detect ALL missing tools
        if self.enable_full_autonomy:
            missing_tools = self.toolsmith.detect_missing_tool_llm(request, self.available_tools)
            if not missing_tools:
                # Fallback to pattern matching
                missing_tool = self.toolsmith.detect_missing_tool(request, self.available_tools)
                missing_tools = [missing_tool] if missing_tool else []
        else:
            missing_tool = self.toolsmith.detect_missing_tool(request, self.available_tools)
            missing_tools = [missing_tool] if missing_tool else []
        
        if missing_tools:
            # Process all missing tools
            for missing_tool in missing_tools:
                if not missing_tool:
                    continue
                print(f"\n   ⚠️  Missing Tool Detected:")
                print(f"      Tool: {missing_tool['tool_name']}")
                print(f"      Description: {missing_tool['description']}")
                print(f"      Reason: {missing_tool['reason']}")
            
            # Step 3: Self-Evolution (Toolsmith) - Batch generation
            print("\n" + "="*70)
            print("STEP 3: SELF-EVOLUTION (Toolsmith Agent)")
            print("="*70)
            
            if len(missing_tools) > 1:
                print(f"\n   🔧 Agent realizes it needs {len(missing_tools)} tools")
                print(f"   💡 Generating tools in batch for efficiency...")
            else:
                print(f"\n   🔧 Agent realizes it needs: {missing_tools[0]['tool_name']}")
                print(f"   💡 Switching to 'Developer' mode...")
            
            # Generate all tools (batch if multiple)
            generation_results = []
            valid_missing_tools = [t for t in missing_tools if t]  # Filter out None values
            
            for missing_tool in valid_missing_tools:
                # Check risk level - green tools can be auto-approved
                risk_level = self._assess_tool_risk(missing_tool)
                
                if risk_level == "green" and self.enable_full_autonomy:
                    print(f"\n   🟢 Green tool: {missing_tool['tool_name']} - Auto-approving")
                    # Auto-approve green tools
                    generation_result = self.toolsmith.generate_mcp_server(missing_tool)
                    if generation_result.get("status") == "pending_approval":
                        # Auto-approve for green tools
                        approval_id = generation_result.get("approval_id")
                        if approval_id:
                            self.governance.approve(approval_id, approver="auto_green")
                            generation_result = self.toolsmith.generate_mcp_server(missing_tool)
                    generation_results.append((missing_tool, generation_result))
                else:
                    # Yellow/Red tools - check if can auto-approve
                    generation_result = self.toolsmith.generate_mcp_server(missing_tool)
                    generation_results.append((missing_tool, generation_result))
            
            # Process generation results
            pending_approvals = []
            successful_generations = []
            
            for missing_tool, generation_result in generation_results:
                
                if generation_result.get("status") == "pending_approval":
                    risk_level = self._assess_tool_risk(missing_tool)
                    
                    if risk_level == "yellow" and self.enable_full_autonomy:
                        # For yellow tasks, check if we can auto-approve based on context
                        if self._can_auto_approve_yellow(missing_tool, request):
                            print(f"\n   🟡 Yellow tool: {missing_tool['tool_name']} - Auto-approving (safe context)")
                            approval_id = generation_result.get("approval_id")
                            if approval_id:
                                self.governance.approve(approval_id, approver="auto_yellow")
                                # Regenerate after approval
                                generation_result = self.toolsmith.generate_mcp_server(missing_tool)
                                if generation_result.get("status") == "success":
                                    successful_generations.append((missing_tool, generation_result))
                                    continue
                    
                    # Still needs approval
                    print(f"\n   ⏸️  Code generation requires approval ({risk_level.upper()} risk)")
                    print(f"      Tool: {missing_tool['tool_name']}")
                    print(f"      Approval ID: {generation_result['approval_id']}")
                    print(f"      File: {generation_result['file_path']}")
                    if generation_result.get('code'):
                        print(f"\n   📋 Code Preview:")
                        print(f"      {generation_result.get('code', '')[:300]}...")
                    print(f"\n   💡 Review and approve: python approve.py approve {generation_result['approval_id']}")
                    
                    pending_approvals.append({
                        "tool": missing_tool,
                        "approval_id": generation_result["approval_id"],
                        "code": generation_result.get("code", "")
                    })
                
                elif generation_result.get("status") == "success":
                    successful_generations.append((missing_tool, generation_result))
            
            # If we have pending approvals, return them
            if pending_approvals:
                if len(pending_approvals) == 1:
                    return {
                        "status": "pending_approval",
                        "stage": "code_generation",
                        "approval_id": pending_approvals[0]["approval_id"],
                        "missing_tool": pending_approvals[0]["tool"],
                        "generated_code": pending_approvals[0]["code"]
                    }
                else:
                    return {
                        "status": "pending_approval",
                        "stage": "code_generation",
                        "pending_approvals": pending_approvals,
                        "message": f"{len(pending_approvals)} tools require approval"
                    }
            
            # Process successful generations
            for missing_tool, generation_result in successful_generations:
                print(f"\n   ✅ Code generated: {generation_result['file_path']}")
                
                # Step 3.5: Check Authentication (if required)
                auth_required = missing_tool.get("auth_required")
                if auth_required:
                    print("\n" + "="*70)
                    print(f"STEP 3.5: AUTHENTICATION CHECK ({missing_tool['tool_name']})")
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
                
                # Step 4: MVP Deployment
                print("\n" + "="*70)
                print(f"STEP 4: DEPLOYMENT ({missing_tool['tool_name']})")
                print("="*70)
                
                deploy_result = self._deploy_mcp_server(
                    generation_result["file_path"],
                    missing_tool["tool_name"],
                    risk_level=self._assess_tool_risk(missing_tool)
                )
                
                if deploy_result.get("status") == "pending_approval":
                    return {
                        "status": "pending_approval",
                        "stage": "deployment",
                        "approval_id": deploy_result["approval_id"],
                        "missing_tool": missing_tool,
                        "generated_code": generation_result.get("code")
                    }
                elif deploy_result.get("status") == "success":
                    # Hot-reload tools (refresh discovery)
                    self.available_tools = self._discover_tools()
                    print(f"\n   ✅ Tool {missing_tool['tool_name']} deployed and hot-reloaded")
            
            # After all tools are deployed, re-process original request
            if successful_generations:
                print(f"\n   🔄 Re-running original request with {len(successful_generations)} new tool(s)...")
                return self._process_with_tools(request)
        
        # No missing tools - process normally
        return self._process_with_tools(request)
    
    def _is_system_building_request(self, request: str) -> bool:
        """Check if request is for building a system from scratch.
        
        Args:
            request: Task request
            
        Returns:
            True if system building request
        """
        system_keywords = [
            "build", "create", "set up", "deploy", "architect",
            "design", "implement", "system", "application",
            "microservices", "infrastructure", "from scratch"
        ]
        
        request_lower = request.lower()
        return any(keyword in request_lower for keyword in system_keywords)
    
    def _process_system_building_request(self, request: str) -> Dict[str, Any]:
        """Process system-building request with full autonomy.
        
        Args:
            request: System building request
            
        Returns:
            Execution result
        """
        print("\n" + "="*70)
        print("🏗️  SYSTEM BUILDING MODE: Full Autonomy")
        print("="*70)
        
        # Step 1: Design architecture
        print("\n" + "="*70)
        print("STEP 1: ARCHITECTURE DESIGN")
        print("="*70)
        
        architecture = self.architect.design_system(request)
        print(f"\n   📐 Architecture designed:")
        print(f"      Components: {len(architecture.get('components', []))}")
        print(f"      Deployment: {architecture.get('deployment', {}).get('strategy', 'unknown')}")
        
        # Step 2: Extract all required tools
        print("\n" + "="*70)
        print("STEP 2: TOOL REQUIREMENT ANALYSIS")
        print("="*70)
        
        required_tools = self.architect.extract_tools_from_architecture(architecture)
        print(f"\n   🔧 Required tools from architecture: {', '.join(required_tools)}")
        
        # Step 3: Discover observability needs automatically
        print("\n" + "="*70)
        print("STEP 3: AUTOMATIC OBSERVABILITY GENERATION")
        print("="*70)
        
        observability_tools = self.observability_gen.auto_discover_observability_needs(request)
        print(f"\n   📊 Discovered {len(observability_tools)} observability tools")
        
        # Step 4: Combine all tool requirements
        all_tool_specs = []
        
        # Add architecture tools
        for tool_name in required_tools:
            all_tool_specs.append({
                "tool_name": tool_name,
                "description": f"Tool for {tool_name} operations",
                "reason": f"Required by architecture for {tool_name}",
                "auth_required": None
            })
        
        # Add observability tools
        all_tool_specs.extend(observability_tools)
        
        # Step 5: Use LLM to detect any additional missing tools
        llm_tools = self.toolsmith.detect_missing_tool_llm(request, self.available_tools)
        existing_tool_names = {spec["tool_name"] for spec in all_tool_specs}
        for tool in llm_tools:
            if tool["tool_name"] not in existing_tool_names:
                all_tool_specs.append(tool)
        
        if all_tool_specs:
            print(f"\n   📦 Total tools needed: {len(all_tool_specs)}")
            for spec in all_tool_specs:
                print(f"      - {spec['tool_name']}: {spec['description']}")
            
            # Step 6: Generate all tools in batch
            print("\n" + "="*70)
            print("STEP 4: BATCH TOOL GENERATION")
            print("="*70)
            
            generation_results = []
            for tool_spec in all_tool_specs:
                risk_level = self._assess_tool_risk(tool_spec)
                
                print(f"\n   🔧 Generating: {tool_spec['tool_name']} ({risk_level.upper()})")
                
                # Generate tool
                result = self.toolsmith.generate_mcp_server(tool_spec)
                
                # Auto-approve green tools
                if risk_level == "green" and result.get("status") == "pending_approval":
                    approval_id = result.get("approval_id")
                    if approval_id:
                        self.governance.approve(approval_id, approver="auto_green")
                        result = self.toolsmith.generate_mcp_server(tool_spec)
                
                # Auto-approve yellow in safe contexts
                elif risk_level == "yellow" and result.get("status") == "pending_approval":
                    if self._can_auto_approve_yellow(tool_spec, request):
                        approval_id = result.get("approval_id")
                        if approval_id:
                            self.governance.approve(approval_id, approver="auto_yellow")
                            result = self.toolsmith.generate_mcp_server(tool_spec)
                
                generation_results.append((tool_spec, result))
            
            # Step 7: Deploy all successfully generated tools
            print("\n" + "="*70)
            print("STEP 5: BATCH DEPLOYMENT")
            print("="*70)
            
            deployed_tools = []
            pending_deployments = []
            
            for tool_spec, gen_result in generation_results:
                if gen_result.get("status") == "success":
                    risk_level = self._assess_tool_risk(tool_spec)
                    deploy_result = self._deploy_mcp_server(
                        gen_result["file_path"],
                        tool_spec["tool_name"],
                        risk_level=risk_level
                    )
                    
                    if deploy_result.get("status") == "success":
                        deployed_tools.append(tool_spec["tool_name"])
                    elif deploy_result.get("status") == "pending_approval":
                        pending_deployments.append({
                            "tool": tool_spec,
                            "approval_id": deploy_result.get("approval_id")
                        })
            
            # Refresh available tools
            if deployed_tools:
                self.available_tools = self._discover_tools()
                print(f"\n   ✅ Deployed {len(deployed_tools)} tools: {', '.join(deployed_tools)}")
            
            if pending_deployments:
                print(f"\n   ⏸️  {len(pending_deployments)} tools require approval for deployment")
                return {
                    "status": "pending_approval",
                    "stage": "deployment",
                    "pending_deployments": pending_deployments,
                    "architecture": architecture
                }
        
        # Step 8: Execute the original request with all tools available
        print("\n" + "="*70)
        print("STEP 6: EXECUTING SYSTEM BUILD")
        print("="*70)
        
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
    
    def _assess_tool_risk(self, tool_spec: Dict[str, Any]) -> str:
        """Assess risk level of a tool.
        
        Args:
            tool_spec: Tool specification
            
        Returns:
            Risk level: "green", "yellow", or "red"
        """
        tool_name = tool_spec.get("tool_name", "").lower()
        description = tool_spec.get("description", "").lower()
        
        # Green: Read-only, safe tools
        green_patterns = ["read", "list", "get", "check", "status", "info", "search", "query", "monitor", "log"]
        if any(pattern in tool_name or pattern in description for pattern in green_patterns):
            return "green"
        
        # Red: Destructive, system-changing tools
        red_patterns = ["delete", "remove", "destroy", "format", "wipe", "reset", "deploy", "install", "execute"]
        if any(pattern in tool_name or pattern in description for pattern in red_patterns):
            return "red"
        
        # Yellow: Everything else (reversible changes)
        return "yellow"
    
    def _can_auto_approve_yellow(self, tool_spec: Dict[str, Any], task: str) -> bool:
        """Determine if a yellow tool can be auto-approved.
        
        Args:
            tool_spec: Tool specification
            task: Original task
            
        Returns:
            True if can auto-approve
        """
        if not self.enable_full_autonomy:
            return False
        
        # Auto-approve yellow tools in safe contexts:
        # - Development/staging environment
        # - Reversible operations
        # - Non-production systems
        
        tool_name = tool_spec.get("tool_name", "").lower()
        task_lower = task.lower()
        
        # Safe contexts for auto-approval
        safe_contexts = [
            "test", "dev", "development", "staging", "local",
            "create", "generate", "write", "add", "configure"
        ]
        
        # Unsafe contexts (never auto-approve)
        unsafe_contexts = [
            "production", "prod", "live", "critical", "delete", "remove"
        ]
        
        # Check for unsafe contexts
        if any(context in task_lower for context in unsafe_contexts):
            return False
        
        # Check for safe contexts
        if any(context in task_lower for context in safe_contexts):
            return True
        
        # Default: require approval for yellow in production
        return self.environment != "production"
    
    def _deploy_mcp_server(self, file_path: str, tool_name: str, risk_level: str = "yellow") -> Dict[str, Any]:
        """Deploy MCP server with risk-based approval.
        
        Args:
            file_path: Path to MCP server file
            tool_name: Name of tool
            risk_level: Risk level ("green", "yellow", "red")
        
        MVP Approach: Write to mcp_servers/ and restart Python MCP process.
        Future: Can upgrade to Docker container deployment for full isolation.
        """
        print(f"\n   🚀 Deploying MCP server: {tool_name}")
        print(f"   Risk Level: {risk_level.upper()}")
        
        # Green tools: Auto-approve
        if risk_level == "green":
            print(f"   🟢 Green tool - Auto-approving deployment")
            # Skip approval for green tools
            approval_id = None
        # Yellow tools: Check if can auto-approve
        elif risk_level == "yellow":
            if self._can_auto_approve_yellow({"tool_name": tool_name}, ""):
                print(f"   🟡 Yellow tool - Auto-approving (safe context)")
                approval_id = None
            else:
                print(f"   🟡 Yellow tool - Requires approval")
                approval_id = self.governance.request_approval(
                    "deploy_mcp_server",
                    {
                        "tool_name": tool_name,
                        "file_path": file_path,
                        "description": f"Deploy new MCP server for {tool_name}",
                        "risk": "YELLOW - Reversible operation",
                        "deployment_method": "MVP: Restart MCP process"
                    },
                    {"environment": self.environment}
                )
        # Red tools: Always require approval
        else:
            print(f"   🔴 Red tool - CRITICAL: Requires explicit approval")
            print(f"   ⚠️  This gives the agent new capabilities")
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
        
        if approval_id and not self.governance.is_approved(approval_id):
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
    from config import get_llm_provider_from_user, get_config

    # Prompt for LLM provider selection at startup
    print("\n" + "="*70)
    print("🧠 CLOSE-TO-ZERO PROMPTING AI BRAIN")
    print("="*70)

    # Get LLM provider (will prompt user if not configured)
    llm_provider = get_llm_provider_from_user()

    # Get environment from config
    config = get_config()
    environment = config["environment"]

    meta_agent = MetaAgent(environment=environment)

    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        print("\nEnter request (or 'exit' to quit):")
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


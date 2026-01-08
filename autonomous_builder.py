"""Autonomous Builder: End-to-end system building with design consultation.

This module orchestrates the complete workflow:
1. Gather context through targeted questions
2. Generate design options with pros/cons
3. Get user selection
4. Build the system
5. Handle authentication
6. Configure resource quotas
7. Create troubleshooting MCP servers
"""

from typing import Dict, Any, List, Optional
from design_consultant import get_design_consultant, DesignOption
from architecture_agent import get_architecture_agent
from observability_generator import get_observability_generator
from meta_agent import MetaAgent
from auth_broker import get_auth_broker, NeedAuthError
from governance import get_governance
import json


class AutonomousBuilder:
    """Orchestrates complete system building workflow."""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.design_consultant = get_design_consultant()
        self.architect = get_architecture_agent()
        self.observability_gen = get_observability_generator()
        self.meta_agent = MetaAgent(environment=environment, enable_full_autonomy=True)
        self.auth_broker = get_auth_broker()
        self.governance = get_governance()
    
    def build_system(self, initial_prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Complete system building workflow.
        
        Args:
            initial_prompt: Initial user request
            context: Optional context with existing clarifications
            
        Returns:
            Build result
        """
        existing_context = context or {}
        
        print("\n" + "="*70)
        print("🏗️  AUTONOMOUS SYSTEM BUILDER")
        print("="*70)
        print(f"\n📥 Initial Request: {initial_prompt}\n")
        
        # Check if we already have clarifications from routing phase
        all_clarifications = existing_context.get("all_clarifications", [])
        
        # Step 1: Gather context through targeted questions
        # Pass existing clarifications so LLM only asks NEW questions
        print("\n" + "="*70)
        print("STEP 1: CONTEXT GATHERING")
        print("="*70)
        
        if all_clarifications:
            print(f"\n   📋 Passing {len(all_clarifications)} previous clarification(s) to context gathering...")
        
        # Pass existing context - the design consultant will only ask NEW questions
        gathered_context = self.design_consultant.gather_context(
            initial_prompt, 
            existing_context=existing_context
        )
        
        # Step 2: Generate design options
        print("\n" + "="*70)
        print("STEP 2: DESIGN OPTION GENERATION")
        print("="*70)
        
        options = self.design_consultant.generate_design_options(initial_prompt, gathered_context)
        
        if not options:
            return {
                "status": "error",
                "message": "Failed to generate design options"
            }
        
        # Step 3: Present options and get user selection
        selected_index = self.design_consultant.present_options(options)
        selected_option = options[selected_index]
        
        print(f"\n   ✅ Selected: Option {selected_index + 1} - {selected_option.name}")
        
        # Step 4: Gather resource quotas
        print("\n" + "="*70)
        print("STEP 3: RESOURCE QUOTAS")
        print("="*70)
        
        quotas = self.design_consultant.gather_resource_quotas(selected_option)
        gathered_context["resource_quotas"] = quotas
        
        # Step 5: Design architecture based on selected option
        print("\n" + "="*70)
        print("STEP 4: ARCHITECTURE DESIGN")
        print("="*70)
        
        # Combine requirements with context
        full_requirements = f"""{initial_prompt}

Selected Design: {selected_option.name}
{selected_option.description}

Context:
{json.dumps(context, indent=2)}

Resource Quotas:
{json.dumps(quotas, indent=2)}"""
        
        architecture = self.architect.design_system(full_requirements)
        
        print(f"\n   📐 Architecture designed:")
        print(f"      Components: {len(architecture.get('components', []))}")
        print(f"      Deployment: {architecture.get('deployment', {}).get('strategy', 'unknown')}")
        
        # Step 6: Check authentication requirements
        print("\n" + "="*70)
        print("STEP 5: AUTHENTICATION")
        print("="*70)
        
        auth_requirements = self._identify_auth_requirements(architecture, gathered_context)
        
        for auth_type, service_name in auth_requirements:
            print(f"\n   🔐 Authentication required for: {service_name}")
            try:
                self.auth_broker.require_auth(service_name)
                print(f"   ✅ Authentication verified")
            except NeedAuthError as e:
                print(f"   ⚠️  {e.message}")
                print(f"   💡 Action: {e.action}")
                print(f"\n   Please complete authentication, then type 'ready' to continue")
                input("   > ")
        
        # Step 7: Generate observability tools automatically
        print("\n" + "="*70)
        print("STEP 6: AUTOMATIC OBSERVABILITY GENERATION")
        print("="*70)
        
        observability_result = self.observability_gen.generate_observability_stack(
            full_requirements
        )
        
        if observability_result.get("status") == "success":
            print(f"\n   ✅ Generated {observability_result.get('tools_generated', 0)} observability tools")
        
        # Step 8: Create troubleshooting MCP servers
        print("\n" + "="*70)
        print("STEP 7: TROUBLESHOOTING TOOLS")
        print("="*70)
        
        troubleshooting_tools = self._generate_troubleshooting_tools(architecture, gathered_context)
        
        if troubleshooting_tools:
            print(f"\n   🔧 Generating {len(troubleshooting_tools)} troubleshooting tools...")
            for tool_spec in troubleshooting_tools:
                result = self.meta_agent.toolsmith.generate_mcp_server(tool_spec)
                if result.get("status") == "success":
                    print(f"   ✅ Generated: {tool_spec['tool_name']}")
        
        # Step 9: Build the system - execute directly with ConsultingAgent
        # DO NOT use meta_agent.process_request as it would route back to design (infinite loop)
        print("\n" + "="*70)
        print("STEP 8: SYSTEM BUILDING")
        print("="*70)
        
        # Use ConsultingAgent directly for execution to avoid recursive routing
        from sub_agents.consulting_agent import ConsultingAgent
        
        execution_agent = ConsultingAgent()
        
        # Build execution context with all gathered information
        execution_context = {
            "design_complete": True,
            "selected_option": selected_option.name,
            "architecture": architecture,
            "context": gathered_context,
            "resource_quotas": quotas,
            "skip_design_routing": True  # Prevent re-routing to design
        }
        
        # AUTONOMOUS EXECUTION - Execute build steps one by one
        # The agent has FULL AUTONOMY - it executes commands directly
        # Governance framework handles safety (green=auto, yellow=warn, red=approve)
        # NO HARDCODING - steps come from the LLM-generated architecture
        
        print(f"\n   🚀 BUILDING: {selected_option.name}")
        print(f"   📋 Resources: {quotas.get('cpu_cores', 'default')} CPU, {quotas.get('memory', 'default')} RAM")
        
        # Extract implementation steps from LLM-generated architecture
        # This is DYNAMIC - steps are generated by the LLM based on the task
        implementation_steps = architecture.get("implementation_steps", [])
        tools_required = architecture.get("tools_required", [])
        
        if not implementation_steps:
            # If architecture doesn't have steps, use LLM to generate them
            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage
            
            step_llm = ChatOllama(model="gemma3:4b", temperature=0.2)
            
            step_prompt = f"""Generate executable shell commands for this system setup.

SYSTEM: {selected_option.name}
DESCRIPTION: {selected_option.description}
TOOLS NEEDED: {json.dumps(tools_required)}
RESOURCE CONSTRAINTS: CPU={quotas.get('cpu_cores', '2')}, Memory={quotas.get('memory', '4GB')}, Storage={quotas.get('storage', '20GB')}

Generate a JSON array of steps. Each step has:
- "name": short description
- "command": the exact shell command to run
- "check_first": optional command to check if already done

Example format:
[
  {{"name": "Check prerequisites", "command": "which docker", "check_first": null}},
  {{"name": "Install tool", "command": "brew install sometool", "check_first": "which sometool"}},
  {{"name": "Start service", "command": "sometool start --flag=value", "check_first": null}},
  {{"name": "Verify running", "command": "sometool status", "check_first": null}}
]

Return ONLY valid JSON array, no explanation."""

            response = step_llm.invoke([
                SystemMessage(content="You are a DevOps expert. Generate executable shell commands."),
                HumanMessage(content=step_prompt)
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    build_steps = json.loads(json_match.group())
                except json.JSONDecodeError:
                    build_steps = []
            else:
                build_steps = []
        else:
            # Convert implementation_steps (strings) to executable steps
            # Use LLM to extract actual commands from the step descriptions
            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage
            
            step_llm = ChatOllama(model="gemma3:4b", temperature=0.1)
            
            convert_prompt = f"""Convert these implementation steps into EXECUTABLE shell commands for macOS.

STEPS:
{json.dumps(implementation_steps, indent=2)}

RESOURCE CONSTRAINTS: CPU={quotas.get('cpu_cores', '2')}, Memory={quotas.get('memory', '4GB')}, Storage={quotas.get('storage', '20GB')}

RULES:
1. Each command must be a REAL shell command that can be executed
2. Use 'brew install' for installing tools on macOS
3. For minikube, use: minikube start --driver=docker --memory=2048 --cpus=2
4. Do NOT include manual steps or descriptions
5. Skip steps that require visiting websites or manual downloads

Return as JSON array:
[
  {{"name": "Install Minikube", "command": "brew install minikube"}},
  {{"name": "Start Cluster", "command": "minikube start --driver=docker --memory=2048 --cpus=2"}},
  {{"name": "Verify", "command": "kubectl get nodes"}}
]

Return ONLY valid JSON array with REAL EXECUTABLE commands."""

            response = step_llm.invoke([
                SystemMessage(content="Extract shell commands from step descriptions."),
                HumanMessage(content=convert_prompt)
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    build_steps = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Fallback: create basic steps from implementation_steps
                    build_steps = [{"name": step, "command": step} for step in implementation_steps if isinstance(step, str)]
            else:
                build_steps = [{"name": step, "command": step} for step in implementation_steps if isinstance(step, str)]
        
        build_results = []
        needs_install = []
        
        # STEP 1: Check prerequisites FIRST (read-only, auto-approved)
        # Identify what tools are needed and check if already installed
        tools_required = architecture.get("tools_required", [])
        
        print(f"\n   🔍 CHECKING PREREQUISITES...")
        print(f"   {'─'*50}")
        
        already_installed = []
        missing_tools = []
        
        for tool in tools_required:
            # Normalize tool name for checking
            tool_lower = tool.lower().replace(" ", "-").replace("_", "-")
            
            # Use LLM to determine if this is an installable tool or not
            # NO HARDCODING - semantic understanding decides
            from langchain_ollama import ChatOllama
            from langchain_core.messages import SystemMessage, HumanMessage
            
            classify_llm = ChatOllama(model="gemma3:4b", temperature=0.1)
            classify_result = classify_llm.invoke([
                SystemMessage(content="""Classify if this is an INSTALLABLE TOOL or NOT.

INSTALLABLE TOOLS: Software that can be installed via package manager or installer
Examples: docker, minikube, kubectl, git, node, python, brew, helm

NOT INSTALLABLE: Operating systems, vague categories, or non-software items
Examples: macOS, Linux, Windows, "text editor", "IDE", "virtualization software"

Respond with ONLY one word: INSTALLABLE or SKIP"""),
                HumanMessage(content=f"Is '{tool}' an installable tool?")
            ])
            
            classification = classify_result.content.strip().upper() if hasattr(classify_result, 'content') else "INSTALLABLE"
            
            if "SKIP" in classification:
                print(f"\n   ⏭️  Skipping: {tool} (not an installable tool)")
                continue
            
            # Define check commands - prefer --version for cleaner output
            if "docker" in tool_lower:
                check_cmd = "docker --version"
            elif "minikube" in tool_lower:
                check_cmd = "minikube version 2>/dev/null || echo 'NOT_INSTALLED'"
            elif "kubectl" in tool_lower:
                check_cmd = "kubectl version --client 2>/dev/null || echo 'NOT_INSTALLED'"
            elif "brew" in tool_lower or "homebrew" in tool_lower:
                check_cmd = "brew --version 2>/dev/null || echo 'NOT_INSTALLED'"
            elif "helm" in tool_lower:
                check_cmd = "helm version 2>/dev/null || echo 'NOT_INSTALLED'"
            elif "git" in tool_lower:
                check_cmd = "git --version 2>/dev/null || echo 'NOT_INSTALLED'"
            else:
                # Generic check - use which with fallback
                check_cmd = f"which {tool_lower} 2>/dev/null || echo 'NOT_INSTALLED'"
            
            print(f"\n   🔍 Checking: {tool}")
            
            # Execute check directly using run_shell (not through ConsultingAgent to avoid retries)
            from tools import run_shell
            try:
                result = run_shell(check_cmd)
                output = result.get("stdout", "") or result.get("output", "")
                exit_code = result.get("exit_code", 0)
                
                # Check if tool is installed
                if "NOT_INSTALLED" in output or exit_code != 0:
                    print(f"   ❌ {tool} is NOT installed")
                    missing_tools.append(tool)
                elif output.strip():
                    # Tool is installed - show version info
                    version_info = output.strip().split('\n')[0][:60]
                    print(f"   ✅ {tool} is installed: {version_info}")
                    already_installed.append(tool)
                else:
                    print(f"   ❌ {tool} is NOT installed")
                    missing_tools.append(tool)
                    
            except Exception as e:
                print(f"   ⚠️  Could not check {tool}: {str(e)[:50]}")
                missing_tools.append(tool)  # Assume missing if can't check
        
        print(f"\n   {'─'*50}")
        print(f"   📊 PREREQUISITE SUMMARY:")
        print(f"   ✅ Already installed: {len(already_installed)} ({', '.join(already_installed) if already_installed else 'none'})")
        print(f"   ❌ Missing: {len(missing_tools)} ({', '.join(missing_tools) if missing_tools else 'none'})")
        print(f"   {'─'*50}")
        
        # Filter build_steps to skip installation of already-installed tools
        filtered_steps = []
        for step in build_steps:
            step_name = step.get("name", "").lower()
            command = step.get("command", "").lower()
            
            # Check if this is an install step for something already installed
            skip_step = False
            for installed_tool in already_installed:
                tool_lower = installed_tool.lower()
                if ("install" in step_name or "install" in command) and tool_lower in (step_name + " " + command):
                    print(f"   ⏭️  Skipping: {step.get('name', '')} (already installed)")
                    skip_step = True
                    build_results.append({"step": step.get("name", ""), "status": "skipped", "reason": "Already installed"})
                    break
            
            if not skip_step:
                filtered_steps.append(step)
        
        build_steps = filtered_steps
        
        # STEP 2: Execute remaining build steps
        print(f"\n   ⚙️  Executing {len(build_steps)} build steps...")
        print(f"   {'─'*50}")
        
        for i, step in enumerate(build_steps, 1):
            step_name = step.get("name", f"Step {i}")
            command = step.get("command", "")
            
            if not command:
                print(f"\n   [{i}/{len(build_steps)}] {step_name}")
                print(f"   ⚠️  No command found, skipping")
                build_results.append({"step": step_name, "status": "skipped", "reason": "No command"})
                continue
            
            # Skip steps that are descriptions, not actual commands
            skip_phrases = [
                "manual installation", "requires manual", "no shell command",
                "this step requires", "download and install from", "visit the website"
            ]
            if any(phrase in command.lower() for phrase in skip_phrases):
                print(f"\n   [{i}/{len(build_steps)}] {step_name}")
                print(f"   ⏭️  Manual step - skipping (requires user action)")
                print(f"   💡 Hint: {command[:100]}...")
                build_results.append({"step": step_name, "status": "manual", "hint": command})
                continue
            
            # Skip if command looks like a description, not a command
            # Real commands are short and don't start with "This" or contain "http"
            if (command.startswith("This ") or 
                len(command) > 200 or 
                "http" in command and "curl" not in command and "wget" not in command):
                print(f"\n   [{i}/{len(build_steps)}] {step_name}")
                print(f"   ⏭️  Description, not a command - skipping")
                build_results.append({"step": step_name, "status": "skipped", "reason": "Not a command"})
                continue
            
            print(f"\n   [{i}/{len(build_steps)}] {step_name}")
            print(f"   📝 Command: {command}")
            
            # Execute the command through the agent (with governance)
            result = execution_agent.execute(
                f"Execute this command and report the result: run_shell(\"{command}\")",
                execution_context
            )
            
            status = result.get("status", "unknown")
            message = result.get("message", "")
            
            if status == "success":
                print(f"   ✅ Success: {message[:100]}..." if len(message) > 100 else f"   ✅ Success: {message}")
                build_results.append({"step": step_name, "status": "success", "output": message})
            elif status == "needs_approval":
                # INTERACTIVE APPROVAL - Ask user inline
                approval_id = result.get("approval_id")
                print(f"\n   🔴 APPROVAL REQUIRED")
                print(f"   {'─'*50}")
                print(f"   📋 Step: {step_name}")
                print(f"   📝 Command: {command}")
                print(f"   ⚠️  This is a write operation that modifies your system.")
                print(f"   {'─'*50}")
                print(f"   Approve this command? (yes/no/skip/abort): ", end="", flush=True)
                
                try:
                    user_input = input().strip().lower()
                    
                    if user_input in ["yes", "y"]:
                        # Approve and execute DIRECTLY (bypass ConsultingAgent to avoid re-approval)
                        print(f"   ✅ Approved! Executing...")
                        
                        # Execute command directly using run_shell
                        from tools import run_shell
                        try:
                            direct_result = run_shell(command)
                            
                            stdout = direct_result.get("stdout", "") or direct_result.get("output", "")
                            stderr = direct_result.get("stderr", "")
                            exit_code = direct_result.get("exit_code", 0)
                            
                            if exit_code == 0:
                                output_preview = stdout[:100] + "..." if len(stdout) > 100 else stdout
                                print(f"   ✅ Success: {output_preview}")
                                build_results.append({"step": step_name, "status": "success", "output": stdout})
                            else:
                                error_msg = stderr or stdout or f"Exit code {exit_code}"
                                print(f"   ❌ Failed (exit {exit_code}): {error_msg[:100]}")
                                build_results.append({"step": step_name, "status": "error", "error": error_msg})
                        except Exception as e:
                            print(f"   ❌ Error: {str(e)[:100]}")
                            build_results.append({"step": step_name, "status": "error", "error": str(e)})
                    
                    elif user_input in ["no", "n"]:
                        print(f"   ❌ Rejected. Stopping build.")
                        build_results.append({"step": step_name, "status": "rejected", "reason": "User rejected"})
                        break  # Stop the build
                    
                    elif user_input == "skip":
                        print(f"   ⏭️  Skipped. Continuing to next step...")
                        build_results.append({"step": step_name, "status": "skipped", "reason": "User skipped"})
                        continue  # Skip this step, continue with next
                    
                    elif user_input == "abort":
                        print(f"   🛑 Build aborted by user.")
                        build_results.append({"step": step_name, "status": "aborted", "reason": "User aborted"})
                        return {
                            "status": "aborted",
                            "architecture": architecture,
                            "selected_option": {"name": selected_option.name, "description": selected_option.description},
                            "context": gathered_context,
                            "resource_quotas": quotas,
                            "build_result": {"status": "aborted", "completed_steps": build_results}
                        }
                    
                    else:
                        print(f"   ⚠️  Unknown response. Treating as 'no'.")
                        build_results.append({"step": step_name, "status": "rejected", "reason": "Unknown response"})
                        break
                
                except (EOFError, KeyboardInterrupt):
                    print(f"\n   🛑 Build cancelled.")
                    build_results.append({"step": step_name, "status": "cancelled"})
                    return {
                        "status": "cancelled",
                        "architecture": architecture,
                        "selected_option": {"name": selected_option.name, "description": selected_option.description},
                        "context": gathered_context,
                        "resource_quotas": quotas,
                        "build_result": {"status": "cancelled", "completed_steps": build_results}
                    }
            elif status == "error":
                print(f"   ❌ Failed: {message[:100]}..." if len(message) > 100 else f"   ❌ Failed: {message}")
                
                # Check if this is a "not found" error for optional tools
                if "install_if_missing" in step and ("not found" in message.lower() or "no such file" in message.lower()):
                    install_cmd = step["install_if_missing"]
                    print(f"   📦 Will install: {install_cmd}")
                    needs_install.append({"name": step_name, "command": install_cmd})
                elif step.get("required", False):
                    print(f"   🛑 Required step failed. Stopping build.")
                    build_results.append({"step": step_name, "status": "error", "error": message})
                    break
                else:
                    build_results.append({"step": step_name, "status": "skipped", "reason": message})
            else:
                print(f"   ⚠️  Unknown status: {status}")
                build_results.append({"step": step_name, "status": status, "details": result})
        
        # Execute installations if needed
        if needs_install:
            print(f"\n   📦 Installing {len(needs_install)} missing components...")
            for install in needs_install:
                print(f"\n   📥 Installing: {install['name']}")
                print(f"   📝 Command: {install['command']}")
                
                result = execution_agent.execute(
                    f"Execute this installation command: run_shell(\"{install['command']}\")",
                    execution_context
                )
                
                if result.get("status") == "needs_approval":
                    # INTERACTIVE APPROVAL for installation
                    approval_id = result.get("approval_id")
                    print(f"\n   🔴 INSTALLATION APPROVAL REQUIRED")
                    print(f"   {'─'*50}")
                    print(f"   📦 Tool: {install['name']}")
                    print(f"   📝 Command: {install['command']}")
                    print(f"   ⚠️  This will install software on your system.")
                    print(f"   {'─'*50}")
                    print(f"   Approve installation? (yes/no/abort): ", end="", flush=True)
                    
                    try:
                        user_input = input().strip().lower()
                        
                        if user_input in ["yes", "y"]:
                            # Execute installation DIRECTLY (bypass ConsultingAgent)
                            print(f"   ✅ Approved! Installing...")
                            
                            from tools import run_shell
                            try:
                                direct_result = run_shell(install['command'])
                                
                                stdout = direct_result.get("stdout", "") or direct_result.get("output", "")
                                stderr = direct_result.get("stderr", "")
                                exit_code = direct_result.get("exit_code", 0)
                                
                                if exit_code == 0:
                                    print(f"   ✅ {install['name']} installed successfully")
                                else:
                                    error_msg = stderr or stdout or f"Exit code {exit_code}"
                                    print(f"   ❌ Installation failed: {error_msg[:100]}")
                            except Exception as e:
                                print(f"   ❌ Installation error: {str(e)[:100]}")
                        
                        elif user_input in ["no", "n"]:
                            print(f"   ⏭️  Skipped installation of {install['name']}")
                        
                        elif user_input == "abort":
                            print(f"   🛑 Build aborted.")
                            return {
                                "status": "aborted",
                                "architecture": architecture,
                                "selected_option": {"name": selected_option.name, "description": selected_option.description},
                                "context": gathered_context,
                                "resource_quotas": quotas,
                                "build_result": {"status": "aborted", "reason": "User aborted during installation"}
                            }
                    
                    except (EOFError, KeyboardInterrupt):
                        print(f"\n   🛑 Build cancelled.")
                        return {
                            "status": "cancelled",
                            "architecture": architecture,
                            "selected_option": {"name": selected_option.name, "description": selected_option.description},
                            "context": gathered_context,
                            "resource_quotas": quotas,
                            "build_result": {"status": "cancelled"}
                        }
                
                elif result.get("status") == "success":
                    print(f"   ✅ Installed successfully")
                else:
                    print(f"   ❌ Installation failed: {result.get('message', 'Unknown error')}")
        
        # Summary
        print(f"\n   {'─'*50}")
        print(f"   📊 BUILD SUMMARY")
        print(f"   {'─'*50}")
        
        success_count = sum(1 for r in build_results if r.get("status") == "success")
        error_count = sum(1 for r in build_results if r.get("status") == "error")
        
        print(f"   ✅ Successful steps: {success_count}")
        print(f"   ❌ Failed steps: {error_count}")
        
        if error_count == 0:
            print(f"\n   🎉 BUILD COMPLETE: {selected_option.name}")
            print(f"\n   💡 Quick start commands:")
            print(f"      minikube dashboard    # Open web dashboard")
            print(f"      kubectl get pods      # List running pods")
            print(f"      minikube stop         # Stop the cluster")
            build_result = {"status": "success", "steps": build_results}
        else:
            print(f"\n   ⚠️  BUILD INCOMPLETE: Some steps failed")
            build_result = {"status": "partial", "steps": build_results}
        
        return {
            "status": "success",
            "architecture": architecture,
            "selected_option": {
                "name": selected_option.name,
                "description": selected_option.description
            },
            "context": gathered_context,
            "resource_quotas": quotas,
            "observability": observability_result,
            "build_result": build_result
        }
    
    def _identify_auth_requirements(self, architecture: Dict[str, Any], context: Dict[str, Any]) -> List[tuple]:
        """Identify authentication requirements from architecture.
        
        Args:
            architecture: System architecture
            context: Gathered context
            
        Returns:
            List of (auth_type, service_name) tuples
        """
        requirements = []
        
        # Check deployment strategy
        deployment = architecture.get("deployment", {})
        strategy = deployment.get("strategy", "").lower()
        
        if "kubernetes" in strategy or "k8s" in strategy:
            requirements.append(("host", "kubernetes"))
        if "aws" in strategy or "eks" in strategy:
            requirements.append(("host", "aws"))
        if "gcp" in strategy:
            requirements.append(("host", "gcp"))
        if "azure" in strategy:
            requirements.append(("host", "azure"))
        
        # Check components for auth needs
        for component in architecture.get("components", []):
            component_type = component.get("type", "").lower()
            if "database" in component_type:
                # May need database credentials
                pass
            if "api" in component_type:
                # May need API keys
                pass
        
        return requirements
    
    def _generate_troubleshooting_tools(self, architecture: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate troubleshooting MCP servers for the system.
        
        Args:
            architecture: System architecture
            context: Gathered context
            
        Returns:
            List of tool specifications
        """
        tools = []
        
        # Determine system type
        deployment = architecture.get("deployment", {})
        strategy = deployment.get("strategy", "").lower()
        
        # Generate tools based on deployment strategy
        if "docker" in strategy:
            tools.append({
                "tool_name": "docker_troubleshooter",
                "description": "Troubleshoot Docker containers, logs, and networking",
                "reason": "Need to debug Docker-based system",
                "auth_required": None
            })
        
        if "kubernetes" in strategy or "k8s" in strategy:
            tools.append({
                "tool_name": "k8s_troubleshooter",
                "description": "Troubleshoot Kubernetes pods, services, and deployments",
                "reason": "Need to debug Kubernetes-based system",
                "auth_required": "kubernetes"
            })
        
        # Always add log aggregator and error tracker
        tools.append({
            "tool_name": "log_aggregator",
            "description": "Aggregate and search logs from all system components",
            "reason": "Need centralized log access for troubleshooting",
            "auth_required": None
        })
        
        tools.append({
            "tool_name": "error_tracker",
            "description": "Track and analyze errors across the system",
            "reason": "Need error visibility for debugging",
            "auth_required": None
        })
        
        return tools


# Main entry point
def main():
    """Main entry point for autonomous builder."""
    import sys
    from config import get_llm_provider_from_user, get_config

    # Prompt for LLM provider selection at startup
    print("\n" + "="*70)
    print("🏗️  AUTONOMOUS SYSTEM BUILDER")
    print("="*70)

    # Get LLM provider (will prompt user if not configured)
    llm_provider = get_llm_provider_from_user()

    # Get environment from config
    config = get_config()
    environment = config["environment"]

    builder = AutonomousBuilder(environment=environment)

    if len(sys.argv) > 1:
        initial_prompt = " ".join(sys.argv[1:])
    else:
        print("\nEnter your system building request:")
        initial_prompt = input("> ").strip()

    if not initial_prompt:
        print("No request provided")
        return

    result = builder.build_system(initial_prompt)

    print("\n" + "="*70)
    print("📊 BUILD RESULT")
    print("="*70)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()


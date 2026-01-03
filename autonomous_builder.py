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
    
    def build_system(self, initial_prompt: str) -> Dict[str, Any]:
        """Complete system building workflow.
        
        Args:
            initial_prompt: Initial user request
            
        Returns:
            Build result
        """
        print("\n" + "="*70)
        print("🏗️  AUTONOMOUS SYSTEM BUILDER")
        print("="*70)
        print(f"\n📥 Initial Request: {initial_prompt}\n")
        
        # Step 1: Gather context through targeted questions
        print("\n" + "="*70)
        print("STEP 1: CONTEXT GATHERING")
        print("="*70)
        
        context = self.design_consultant.gather_context(initial_prompt)
        
        # Step 2: Generate design options
        print("\n" + "="*70)
        print("STEP 2: DESIGN OPTION GENERATION")
        print("="*70)
        
        options = self.design_consultant.generate_design_options(initial_prompt, context)
        
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
        context["resource_quotas"] = quotas
        
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
        
        auth_requirements = self._identify_auth_requirements(architecture, context)
        
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
        
        troubleshooting_tools = self._generate_troubleshooting_tools(architecture, context)
        
        if troubleshooting_tools:
            print(f"\n   🔧 Generating {len(troubleshooting_tools)} troubleshooting tools...")
            for tool_spec in troubleshooting_tools:
                result = self.meta_agent.toolsmith.generate_mcp_server(tool_spec)
                if result.get("status") == "success":
                    print(f"   ✅ Generated: {tool_spec['tool_name']}")
        
        # Step 9: Build the system using meta-agent (with governance)
        print("\n" + "="*70)
        print("STEP 8: SYSTEM BUILDING")
        print("="*70)
        
        # All tool executions in meta_agent will be checked by governance
        # (governance is enforced in base_agent._execute_tool)
        build_result = self.meta_agent.process_request(full_requirements)
        
        return {
            "status": "success",
            "architecture": architecture,
            "selected_option": {
                "name": selected_option.name,
                "description": selected_option.description
            },
            "context": context,
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


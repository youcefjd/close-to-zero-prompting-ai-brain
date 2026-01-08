"""Architecture Agent: Designs systems from requirements.

This module provides system architecture planning and design capabilities.
"""

from typing import Dict, Any, List, Optional
from llm_provider import LLMProvider, create_llm_provider
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import json
import re


class ArchitectureAgent:
    """Designs systems from requirements."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or create_llm_provider("ollama")
    
    def design_system(self, requirements: str) -> Dict[str, Any]:
        """Design a system architecture from requirements.
        
        Args:
            requirements: System requirements description
            
        Returns:
            Architecture design with components, dependencies, tools needed
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a system architect. Design a complete system architecture from requirements.

Provide a structured design with:
1. System components and their responsibilities
2. Dependencies between components
3. Required tools and capabilities
4. Deployment strategy
5. Observability needs (monitoring, logging, error tracking)
6. Security considerations

Return as valid JSON:
{{
    "components": [
        {{
            "name": "component_name",
            "type": "service|database|queue|cache|etc",
            "responsibility": "What it does",
            "dependencies": ["other_component"],
            "tools_needed": ["tool1", "tool2"]
        }}
    ],
    "deployment": {{
        "strategy": "docker|kubernetes|serverless|etc",
        "requirements": ["requirement1", "requirement2"]
    }},
    "observability": {{
        "monitoring": ["what to monitor"],
        "logging": ["log sources"],
        "error_tracking": ["error sources"]
    }},
    "tools_required": ["tool1", "tool2", "tool3"],
    "implementation_steps": ["step1", "step2", "step3"]
}}"""),
            HumanMessage(content=f"Requirements: {requirements}\n\nDesign the system architecture.")
        ])
        
        try:
            response = self.llm_provider.invoke([
                SystemMessage(content=prompt.format_messages()[0].content),
                HumanMessage(content=requirements)
            ])
            
            content = response if isinstance(response, str) else response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                architecture = json.loads(json_match.group())
                return architecture
        except Exception as e:
            print(f"⚠️  Architecture design failed: {e}")
        
        # Fallback: Simple architecture
        return {
            "components": [],
            "deployment": {"strategy": "docker"},
            "observability": {"monitoring": [], "logging": [], "error_tracking": []},
            "tools_required": [],
            "implementation_steps": []
        }
    
    def extract_tools_from_architecture(self, architecture: Dict[str, Any]) -> List[str]:
        """Extract list of required tools from architecture.
        
        Args:
            architecture: Architecture design
            
        Returns:
            List of required tool names
        """
        tools = set()
        
        # From components
        for component in architecture.get("components", []):
            tools.update(component.get("tools_needed", []))
        
        # From architecture level
        tools.update(architecture.get("tools_required", []))
        
        # From deployment strategy
        deployment = architecture.get("deployment", {})
        strategy = deployment.get("strategy", "").lower()
        if "docker" in strategy:
            tools.add("docker")
        if "kubernetes" in strategy or "k8s" in strategy:
            tools.add("kubernetes")
        
        # From observability
        observability = architecture.get("observability", {})
        if observability.get("monitoring"):
            tools.add("monitoring")
        if observability.get("logging"):
            tools.add("log_aggregator")
        if observability.get("error_tracking"):
            tools.add("error_tracker")
        
        return list(tools)


# Global instance
_architecture_agent = None

def get_architecture_agent() -> ArchitectureAgent:
    """Get or create global architecture agent instance."""
    global _architecture_agent
    if _architecture_agent is None:
        _architecture_agent = ArchitectureAgent()
    return _architecture_agent


"""Observability Generator: Automatically creates monitoring, logging, and error tracking tools.

This module automatically discovers observability needs and generates appropriate tools.
"""

from typing import Dict, Any, List, Optional
from llm_provider import LLMProvider, create_llm_provider
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
# from meta_agent import ToolsmithAgent
import json
import re


class ObservabilityGenerator:
    """Automatically generates observability tools (monitoring, logging, error tracking)."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        from meta_agent import ToolsmithAgent
        self.llm_provider = llm_provider or create_llm_provider("ollama")
        self.toolsmith = ToolsmithAgent()
    
    def auto_discover_observability_needs(self, system_description: str) -> List[Dict[str, Any]]:
        """Automatically determine what observability tools are needed.
        
        Args:
            system_description: Description of the system or task
            
        Returns:
            List of observability tool specifications
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an observability expert. Analyze a system/task and determine what monitoring, logging, and error tracking tools are needed.

Consider:
- Log aggregation (where logs are, what format, how to collect)
- Metrics collection (what metrics to track, how to expose them)
- Error tracking (where errors occur, how to capture them)
- Alerting (what to alert on, thresholds)
- Dashboards (what to visualize)

For each tool needed, provide:
1. Tool name (e.g., "log_aggregator", "error_tracker", "metrics_collector")
2. Description of what it does
3. Why it's needed
4. What it monitors/tracks

Return ONLY valid JSON array:
[
    {{
        "tool_name": "tool_name",
        "description": "What the tool does",
        "reason": "Why it's needed",
        "monitors": "What it monitors/tracks",
        "auth_required": null
    }}
]"""),
            HumanMessage(content=f"System/Task: {system_description}\n\nWhat observability tools are needed?")
        ])
        
        try:
            response = self.llm_provider.invoke([
                SystemMessage(content=prompt.format_messages()[0].content),
                HumanMessage(content=system_description)
            ])
            
            content = response if isinstance(response, str) else response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                tools = json.loads(json_match.group())
                return tools if isinstance(tools, list) else []
        except Exception as e:
            print(f"⚠️  Observability analysis failed: {e}")
        
        # Fallback: Return common observability tools
        return [
            {
                "tool_name": "log_aggregator",
                "description": "Aggregate and search logs from multiple sources",
                "reason": "Need centralized log management",
                "monitors": "Application and system logs",
                "auth_required": None
            },
            {
                "tool_name": "error_tracker",
                "description": "Track and analyze errors across the system",
                "reason": "Need error visibility and alerting",
                "monitors": "Errors, exceptions, and failures",
                "auth_required": None
            }
        ]
    
    def discover_log_locations(self, system_type: str) -> List[str]:
        """Automatically discover where logs are located.
        
        Args:
            system_type: Type of system (e.g., "docker", "kubernetes", "application")
            
        Returns:
            List of log locations
        """
        # Common log locations by system type
        log_locations = {
            "docker": [
                "/var/lib/docker/containers/*/*.log",
                "docker logs <container>",
                "/var/log/docker.log"
            ],
            "kubernetes": [
                "/var/log/pods/*/*/*.log",
                "kubectl logs <pod>",
                "/var/log/containers/*.log"
            ],
            "application": [
                "/var/log/app/*.log",
                "./logs/*.log",
                "stdout/stderr"
            ],
            "system": [
                "/var/log/syslog",
                "/var/log/messages",
                "/var/log/system.log"
            ]
        }
        
        return log_locations.get(system_type.lower(), log_locations["application"])
    
    def generate_observability_stack(self, system_description: str) -> Dict[str, Any]:
        """Generate complete observability stack for a system.
        
        Args:
            system_description: Description of the system
            
        Returns:
            Dict with generated tools and configuration
        """
        print("\n" + "="*70)
        print("OBSERVABILITY GENERATION")
        print("="*70)
        
        # Discover observability needs
        tools = self.auto_discover_observability_needs(system_description)
        
        if not tools:
            return {
                "status": "no_tools_needed",
                "message": "No observability tools needed"
            }
        
        print(f"\n   📊 Discovered {len(tools)} observability tools needed:")
        for tool in tools:
            print(f"      - {tool['tool_name']}: {tool['description']}")
        
        # Generate tools
        results = []
        for tool_spec in tools:
            print(f"\n   🔧 Generating: {tool_spec['tool_name']}")
            result = self.toolsmith.generate_mcp_server(tool_spec)
            results.append({
                "tool": tool_spec['tool_name'],
                "result": result
            })
        
        successful = [r for r in results if r["result"].get("status") == "success"]
        pending = [r for r in results if r["result"].get("status") == "pending_approval"]
        
        return {
            "status": "success" if len(pending) == 0 else "partial",
            "tools_generated": len(successful),
            "tools_pending": len(pending),
            "results": results
        }


# Global instance
_observability_generator = None

def get_observability_generator() -> ObservabilityGenerator:
    """Get or create global observability generator instance."""
    global _observability_generator
    if _observability_generator is None:
        _observability_generator = ObservabilityGenerator()
    return _observability_generator


"""Base class for all specialized sub-agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import write_file, run_shell
import json
from mcp_servers.docker_tools import (
    docker_ps, docker_logs, docker_exec, docker_restart,
    docker_inspect, docker_compose_up
)
from mcp_servers.homeassistant_tools import (
    ha_get_state, ha_call_service, ha_get_logs,
    ha_search_logs, ha_list_integrations, ha_get_config,
    init_ha_client
)
from mcp_servers.web_search_tools import web_search


class BaseSubAgent(ABC):
    """Base class for all sub-agents."""
    
    def __init__(self, agent_name: str, system_prompt: str):
        self.agent_name = agent_name
        self.llm = ChatOllama(model="llama3.1:latest", temperature=0.7)
        self.system_prompt = system_prompt
        self.tools = self._get_available_tools()
        self.execution_history = []
        
    def _get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools this agent can use."""
        return {
            # File operations
            "write_file": write_file,
            "run_shell": run_shell,
            
            # Docker tools
            "docker_ps": docker_ps,
            "docker_logs": docker_logs,
            "docker_exec": docker_exec,
            "docker_restart": docker_restart,
            "docker_inspect": docker_inspect,
            "docker_compose_up": docker_compose_up,
            
            # Home Assistant tools
            "ha_get_state": ha_get_state,
            "ha_call_service": ha_call_service,
            "ha_get_logs": ha_get_logs,
            "ha_search_logs": ha_search_logs,
            "ha_list_integrations": ha_list_integrations,
            "ha_get_config": ha_get_config,
            
            # Web search
            "web_search": web_search,
        }
    
    def _create_prompt(self, task: str, context: Optional[Dict] = None) -> ChatPromptTemplate:
        """Create prompt with system instructions and available tools."""
        tools_description = self._describe_tools()
        
        prompt_content = f"""{self.system_prompt}

AVAILABLE TOOLS:
{tools_description}

CRITICAL AUTONOMOUS RULES:
1. You MUST proceed autonomously - do NOT ask for permission or clarification
2. Use tools directly - call them with appropriate parameters
3. If a tool fails, try alternative approaches automatically
4. Only ask human for help if:
   - Authentication credentials are missing and required
   - Task is genuinely impossible without human input
   - Major architectural decision needed (e.g., "redesign everything")

WEB SEARCH RULES:
- Your knowledge cutoff is March 2024
- If the user asks about events, software versions, or news after this date, YOU MUST use web_search tool
- Do NOT guess or hallucinate information beyond your knowledge cutoff
- Use web_search for: current events, latest software releases, recent documentation, breaking news
- Do NOT use web_search for: information you already know, general knowledge, code examples

WORKFLOW:
1. Analyze the task
2. Plan your approach (mentally, no need to output)
3. Execute using tools
4. Verify results
5. Report success or retry with different approach

Task: {task}
"""
        
        if context:
            prompt_content += f"\nContext: {json.dumps(context, indent=2)}"
        
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=prompt_content),
            MessagesPlaceholder(variable_name="messages")
        ])
    
    def _describe_tools(self) -> str:
        """Describe available tools to the LLM."""
        descriptions = []
        
        # File tools
        descriptions.append("write_file(path, content) - Create/overwrite a file")
        descriptions.append("run_shell(command, timeout=30) - Execute shell command")
        
        # Docker tools
        descriptions.append("docker_ps() - List all containers")
        descriptions.append("docker_logs(container_name, tail=50) - Get container logs")
        descriptions.append("docker_exec(container_name, command) - Execute command in container")
        descriptions.append("docker_restart(container_name) - Restart container")
        descriptions.append("docker_inspect(container_name) - Inspect container")
        descriptions.append("docker_compose_up(services=None) - Start docker-compose services")
        
        # HA tools
        descriptions.append("ha_get_state(entity_id) - Get entity state")
        descriptions.append("ha_call_service(domain, service, service_data={}) - Call HA service")
        descriptions.append("ha_get_logs(tail=50) - Get HA logs")
        descriptions.append("ha_search_logs(query, tail=50) - Search HA logs")
        descriptions.append("ha_list_integrations() - List all integrations")
        descriptions.append("ha_get_config() - Get HA configuration")
        
        # Web search
        descriptions.append("web_search(query, max_results=5) - Search the web for current information")
        
        return "\n".join(f"  - {desc}" for desc in descriptions)
    
    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        import re
        import json
        
        tool_calls = []
        
        # Look for tool call patterns: tool_name(arg1=value1, arg2=value2)
        pattern = r'(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, response)
        
        for tool_name, args_str in matches:
            # Parse arguments
            args = {}
            kwargs = {}
            
            # Simple parsing - can be enhanced
            if args_str:
                # Try to parse as JSON-like
                try:
                    # Handle key=value pairs
                    for part in args_str.split(','):
                        part = part.strip()
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            kwargs[key] = value
                except:
                    pass
            
            tool_calls.append({
                "tool": tool_name,
                "args": args,
                "kwargs": kwargs
            })
        
        return tool_calls
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the task autonomously."""
        pass
    
    def _execute_tool(self, tool_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a tool and return result."""
        if tool_name not in self.tools:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not available"
            }
        
        try:
            tool = self.tools[tool_name]
            result = tool(*args, **kwargs)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _needs_human(self, reason: str) -> Dict[str, Any]:
        """Signal that human input is needed."""
        return {
            "status": "needs_human",
            "reason": reason,
            "agent": self.agent_name
        }


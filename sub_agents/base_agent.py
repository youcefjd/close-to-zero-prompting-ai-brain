"""Base class for all specialized sub-agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
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
from output_sanitizer import get_sanitizer
from emergency_stop import get_emergency_stop, EmergencyStopException
from llm_provider import LLMProvider, create_llm_provider
from cost_tracker import CostTracker, get_cost_tracker, CostLimit
from context_manager import ContextManager, get_context_manager
from dynamic_tool_registry import get_tool_registry, DynamicToolRegistry
import asyncio


class BaseSubAgent(ABC):
    """Base class for all sub-agents."""
    
    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        llm_provider: Optional[LLMProvider] = None,
        cost_tracker: Optional[CostTracker] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        
        # Use provided LLM provider or create default
        if llm_provider:
            self.llm_provider = llm_provider
        else:
            self.llm_provider = create_llm_provider("ollama", model="gemma3:4b", temperature=0.7)
        
        # Legacy LLM for backward compatibility
        self.llm = ChatOllama(model="gemma3:4b", temperature=0.7)
        
        # Cost tracker
        if cost_tracker:
            self.cost_tracker = cost_tracker
        else:
            costs = self.llm_provider.get_cost_per_1k_tokens()
            self.cost_tracker = get_cost_tracker(
                cost_per_1k_input=costs["input"],
                cost_per_1k_output=costs["output"]
            )
        
        # Context manager
        if context_manager:
            self.context_manager = context_manager
        else:
            self.context_manager = get_context_manager(max_tokens=8000)
        
        # Tool registry (dynamic)
        if hasattr(self, 'tool_registry') and self.tool_registry:
            self.tool_registry_instance = self.tool_registry
        else:
            self.tool_registry_instance = get_tool_registry()
        
        # Discover and register tools
        self.tool_registry_instance.discover_tools()
        
        # Get tools from registry
        self.tools = self._get_available_tools()
        self.execution_history = []
        self.sanitizer = get_sanitizer()
        self.emergency_stop = get_emergency_stop()
        
    def _get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools this agent can use (from dynamic registry)."""
        tools = {}
        
        # Get tools from dynamic registry
        for tool_name in self.tool_registry_instance.list_tools():
            tool_metadata = self.tool_registry_instance.get_tool(tool_name)
            if tool_metadata:
                tools[tool_name] = tool_metadata.function
        
        # Also include hardcoded tools for backward compatibility
        # (These should eventually be moved to tool registry)
        hardcoded_tools = {
            "write_file": write_file,
            "run_shell": run_shell,
            "docker_ps": docker_ps,
            "docker_logs": docker_logs,
            "docker_exec": docker_exec,
            "docker_restart": docker_restart,
            "docker_inspect": docker_inspect,
            "docker_compose_up": docker_compose_up,
            "ha_get_state": ha_get_state,
            "ha_call_service": ha_call_service,
            "ha_get_logs": ha_get_logs,
            "ha_search_logs": ha_search_logs,
            "ha_list_integrations": ha_list_integrations,
            "ha_get_config": ha_get_config,
            "web_search": web_search,
        }
        
        # Merge (registry tools take precedence)
        tools.update(hardcoded_tools)
        
        return tools
    
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
    
    def _prune_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Prune messages to stay within context limits."""
        return self.context_manager.prune_context(messages)
    
    async def _invoke_llm_async(self, messages: List[BaseMessage]) -> str:
        """Invoke LLM asynchronously with cost tracking.
        
        Args:
            messages: List of messages to send
            
        Returns:
            Response content as string
        """
        # Check cost limits before calling
        limit_check = self.cost_tracker.check_limits()
        if not limit_check["allowed"]:
            raise Exception(f"Cost limit exceeded: {limit_check['reason']}")
        
        # Prune context if needed
        pruned_messages = self._prune_messages(messages)
        
        # Estimate input tokens
        input_text = " ".join(
            msg.content if hasattr(msg, 'content') else str(msg)
            for msg in pruned_messages
        )
        input_tokens = self.llm_provider.estimate_tokens(input_text)
        
        # Invoke LLM
        try:
            response = await asyncio.wait_for(
                self.llm_provider.ainvoke(pruned_messages),
                timeout=60.0  # 60 second timeout
            )
        except asyncio.TimeoutError:
            raise Exception("LLM call timed out after 60 seconds")
        
        # Estimate output tokens
        output_tokens = self.llm_provider.estimate_tokens(response)
        
        # Record usage
        self.cost_tracker.record_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            operation=f"{self.agent_name}_llm_call"
        )
        
        # Check limits again after call
        limit_check = self.cost_tracker.check_limits()
        if limit_check.get("warnings"):
            for warning in limit_check["warnings"]:
                print(f"  ⚠️  {warning}")
        
        return response
    
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
        # Also look for tool_name() with no args
        pattern = r'(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, response)
        
        # Also check for standalone tool names that are known tools
        known_tools = list(self.tools.keys())
        for tool_name in known_tools:
            # Look for patterns like "I'll call docker_ps" or "calling docker_ps" or just "docker_ps()"
            if re.search(rf'\b{re.escape(tool_name)}\s*\(', response, re.IGNORECASE):
                # Already captured by pattern above
                continue
            # Check for explicit mentions like "I need to use docker_ps" - be more aggressive
            if re.search(rf'(call|use|execute|run)\s+{re.escape(tool_name)}', response, re.IGNORECASE):
                # If it's mentioned in context of calling, add it
                if tool_name not in [tc["tool"] for tc in tool_calls]:
                    tool_calls.append({
                        "tool": tool_name,
                        "args": [],
                        "kwargs": {}
                    })
        
        for tool_name, args_str in matches:
            # Only process if it's a known tool
            if tool_name not in self.tools:
                continue
                
            # Parse arguments
            args = []
            kwargs = {}
            
            # Simple parsing - can be enhanced
            if args_str:
                # Try to parse as JSON-like
                try:
                    # Handle key=value pairs
                    for part in args_str.split(','):
                        part = part.strip()
                        if not part:
                            continue
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            kwargs[key] = value
                        else:
                            # Positional argument
                            args.append(part.strip().strip('"').strip("'"))
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
        """Execute a tool and return sanitized result."""
        # Check emergency stop before execution
        self.emergency_stop.check_and_raise()
        
        # Check governance before execution
        from governance import get_governance
        governance = get_governance()
        context = kwargs.get("context", {}) or {}
        context.setdefault("environment", getattr(self, "environment", "production"))
        
        permission = governance.check_permission(tool_name, context)
        
        if not permission["allowed"]:
            # Tool requires approval
            if permission.get("requires_approval"):
                approval_id = governance.request_approval(
                    tool_name,
                    {"args": args, "kwargs": kwargs},
                    context
                )
                return {
                    "status": "pending_approval",
                    "approval_id": approval_id,
                    "message": permission.get("approval_message", f"Tool '{tool_name}' requires approval"),
                    "risk_level": permission.get("risk_level", "red")
                }
            else:
                return {
                    "status": "error",
                    "message": permission.get("message", f"Tool '{tool_name}' not allowed"),
                    "risk_level": permission.get("risk_level", "red")
                }
        
        if tool_name not in self.tools:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not available"
            }
        
        try:
            tool = self.tools[tool_name]
            result = tool(*args, **kwargs)
            
            # Sanitize result before returning
            if isinstance(result, dict):
                # Check for secrets before sanitizing
                result_str = json.dumps(result, default=str)
                if self.sanitizer.has_secrets(result_str):
                    # Log warning but don't block execution
                    print(f"  ⚠️  WARNING: Potential secrets detected in {tool_name} output - sanitizing")
                
                # Sanitize the result
                sanitized_result = self.sanitizer.sanitize_dict(result, context=tool_name)
                return sanitized_result
            elif isinstance(result, str):
                # Sanitize string result
                sanitization = self.sanitizer.sanitize(result, context=tool_name)
                if sanitization.redactions:
                    print(f"  ⚠️  Sanitized {tool_name} output: {', '.join(sanitization.redactions)}")
                return sanitization.sanitized_content
            else:
                # For other types, convert to string and sanitize
                result_str = str(result)
                sanitization = self.sanitizer.sanitize(result_str, context=tool_name)
                return sanitization.sanitized_content
                
        except EmergencyStopException:
            raise  # Re-raise emergency stop
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


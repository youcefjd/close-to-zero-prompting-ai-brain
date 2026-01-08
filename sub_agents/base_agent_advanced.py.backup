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
from output_sanitizer import get_sanitizer, SanitizationResult
from emergency_stop import get_emergency_stop, EmergencyStopException
from llm_provider import LLMProvider, create_llm_provider
from cost_tracker import CostTracker, get_cost_tracker, CostLimit
from context_manager import ContextManager, get_context_manager
from dynamic_tool_registry import get_tool_registry, DynamicToolRegistry
import asyncio
import re


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
        
        # Base tools
        tools["write_file"] = write_file
        tools["run_shell"] = run_shell
        
        # Docker tools
        tools["docker_ps"] = docker_ps
        tools["docker_logs"] = docker_logs
        tools["docker_exec"] = docker_exec
        tools["docker_restart"] = docker_restart
        tools["docker_inspect"] = docker_inspect
        tools["docker_compose_up"] = docker_compose_up
        
        # Home Assistant tools
        tools["ha_get_state"] = ha_get_state
        tools["ha_call_service"] = ha_call_service
        tools["ha_get_logs"] = ha_get_logs
        tools["ha_search_logs"] = ha_search_logs
        tools["ha_list_integrations"] = ha_list_integrations
        tools["ha_get_config"] = ha_get_config
        
        # Web search
        tools["web_search"] = web_search
        
        # Add tools from dynamic registry
        for tool_name, tool_func in self.tool_registry_instance.tools.items():
            if tool_name not in tools:
                tools[tool_name] = tool_func
        
        return tools
    
    def _call_llm(self, messages: List[BaseMessage]) -> str:
        """Call LLM with messages and track costs."""
        # Check cost limits before call
        limit_check = self.cost_tracker.check_limits()
        if limit_check.get("blocked"):
            raise CostLimit(f"Cost limit exceeded: {limit_check.get('message')}")
        
        # Estimate input tokens
        input_tokens = sum(self.llm_provider.estimate_tokens(str(msg)) for msg in messages)
        
        # Call LLM
        response = self.llm_provider.generate(messages)
        
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
        descriptions.append("run_shell(command) - Execute shell command")
        
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
    
    def _parse_tool_args(self, args_str: str) -> tuple[List, Dict[str, Any]]:
        """Parse tool arguments, properly handling quoted strings with nested quotes."""
        args = []
        kwargs = {}
        
        if not args_str or not args_str.strip():
            return args, kwargs
        
        args_str = args_str.strip()
        
        # Method 1: Parse key=value pairs character by character to handle nested quotes
        # This handles cases like: command="osascript -e 'output volume of (get volume settings)'"
        i = 0
        while i < len(args_str):
            # Skip whitespace
            while i < len(args_str) and args_str[i] in ' \t\n,':
                i += 1
            if i >= len(args_str):
                break
            
            # Find key
            key_start = i
            while i < len(args_str) and args_str[i] not in '= \t':
                i += 1
            key = args_str[key_start:i].strip()
            
            if not key:
                break
            
            # Skip to =
            while i < len(args_str) and args_str[i] in ' \t':
                i += 1
            if i >= len(args_str) or args_str[i] != '=':
                # Positional argument
                args.append(key)
                continue
            i += 1  # Skip =
            
            # Skip whitespace after =
            while i < len(args_str) and args_str[i] in ' \t':
                i += 1
            if i >= len(args_str):
                kwargs[key] = ""
                break
            
            # Parse value - handle quotes properly
            value = ""
            if args_str[i] in '"\'':
                # Quoted value - find matching closing quote
                quote_char = args_str[i]
                i += 1
                value_start = i
                escaped = False
                while i < len(args_str):
                    if escaped:
                        escaped = False
                    elif args_str[i] == '\\':
                        escaped = True
                    elif args_str[i] == quote_char:
                        # Found closing quote
                        value = args_str[value_start:i]
                        i += 1
                        break
                    i += 1
                else:
                    # No closing quote found, take rest of string
                    value = args_str[value_start:]
            else:
                # Unquoted value - read until comma or end
                value_start = i
                while i < len(args_str) and args_str[i] not in ',':
                    i += 1
                value = args_str[value_start:i].strip()
            
            kwargs[key] = value
        
        return args, kwargs
    
    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []
        known_tools = list(self.tools.keys())
        
        # Method 1: Find tool calls with balanced parentheses
        for tool_name in known_tools:
            # Find all occurrences of tool_name(
            pattern = re.escape(tool_name) + r'\s*\('
            for match in re.finditer(pattern, response):
                start = match.end()  # Position after the opening paren
                
                # Find the matching closing paren, accounting for nesting and quotes
                depth = 1
                in_single_quote = False
                in_double_quote = False
                escaped = False
                i = start
                
                while i < len(response) and depth > 0:
                    char = response[i]
                    
                    if escaped:
                        escaped = False
                    elif char == '\\':
                        escaped = True
                    elif char == '"' and not in_single_quote:
                        in_double_quote = not in_double_quote
                    elif char == "'" and not in_double_quote:
                        in_single_quote = not in_single_quote
                    elif not in_single_quote and not in_double_quote:
                        if char == '(':
                            depth += 1
                        elif char == ')':
                            depth -= 1
                    i += 1
                
                if depth == 0:
                    # Found matching paren
                    args_str = response[start:i-1]  # Exclude the closing paren
                    args, kwargs = self._parse_tool_args(args_str)
                    
                    # Avoid duplicates
                    if tool_name not in [tc["tool"] for tc in tool_calls]:
                        tool_calls.append({
                            "tool": tool_name,
                            "args": args,
                            "kwargs": kwargs
                        })
        
        return tool_calls
    
    def _create_prompt(self, task: str, context: Optional[Dict] = None) -> ChatPromptTemplate:
        """Create a prompt template for the agent."""
        tools_description = self._describe_tools()
        
        system_message = f"""{self.system_prompt}

AVAILABLE TOOLS:
{tools_description}

INSTRUCTIONS:
- Analyze the task and use the appropriate tools
- Call tools using the format: tool_name(param1=value1, param2=value2)
- For commands with spaces or special characters, use quotes: run_shell(command="command with spaces")
- Return results clearly and concisely"""
        
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="messages"),
            HumanMessage(content=task)
        ])
    
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
        
        # Extract context - ensure we have a dict to modify
        context = kwargs.pop("context", {}) or {}
        context.setdefault("environment", getattr(self, "environment", "production"))
        
        # For run_shell, ALWAYS pass command in context so governance can check if it's safe
        if tool_name == "run_shell":
            command = kwargs.get("command", "")
            # CRITICAL: Always add command to context, even if empty (for debugging)
            context["command"] = command
            context["kwargs"] = kwargs.copy()  # Also pass full kwargs (copy to avoid mutation)
        
        # Check if there's an approved approval_id in context (from previous approval)
        approved_approval_id = context.get("approved_approval_id")
        if approved_approval_id and governance.is_approved(approved_approval_id):
            # Use existing approval
            permission = {"allowed": True, "risk_level": "green"}
        else:
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
        
        # Execute the tool
        try:
            tool_func = self.tools[tool_name]
            result = tool_func(*args, **kwargs)
            
            # Handle parameter errors - auto-fix and retry
            if isinstance(result, dict) and result.get("status") == "error":
                error_msg = result.get("message", "")
                if "unexpected keyword argument" in error_msg or "got an unexpected keyword argument" in error_msg:
                    # Extract the invalid parameter name
                    param_match = re.search(r"unexpected keyword argument ['\"]([\w_]+)['\"]", error_msg)
                    if param_match:
                        invalid_param = param_match.group(1)
                        # Remove the invalid parameter from kwargs and retry
                        new_kwargs = {k: v for k, v in kwargs.items() if k != invalid_param}
                        # Mark as fixed for logging/tracking
                        new_kwargs["context"] = new_kwargs.get("context", {})
                        new_kwargs["context"]["parameter_error_fixed"] = True
                        new_kwargs["context"]["fixed_param"] = invalid_param
                        return self._execute_tool(tool_name, *args, **new_kwargs)  # Recursive retry
            
            # Sanitize result
            # Handle dict results with sanitize_dict, string results with sanitize
            if isinstance(result, dict):
                sanitized_result = self.sanitizer.sanitize_dict(result, context=f"tool_{tool_name}")
                has_secrets = any(
                    self.sanitizer.has_secrets(str(v)) for v in result.values() 
                    if isinstance(v, (str, dict))
                )
                # For dict results, preserve the structure but with sanitized values
                # This allows agents to access fields like stdout, stderr, etc.
                return {
                    "status": result.get("status", "success"),
                    **sanitized_result,  # Spread sanitized fields (stdout, stderr, exit_code, etc.)
                    "has_secrets": has_secrets,
                    "original": result  # Keep original for debugging
                }
            else:
                sanitized_obj = self.sanitizer.sanitize(str(result), context=f"tool_{tool_name}")
                sanitized_result = sanitized_obj.sanitized_content
                has_secrets = len(sanitized_obj.redactions) > 0
                
                return {
                    "status": "success",
                    "result": sanitized_result,
                    "has_secrets": has_secrets,
                    "original": result
                }
        except Exception as e:
            error_msg = str(e)
            sanitized_error = self.sanitizer.sanitize(error_msg, context=f"tool_{tool_name}_error")
            
            return {
                "status": "error",
                "message": sanitized_error.sanitized_content if isinstance(sanitized_error, SanitizationResult) else str(sanitized_error),
                "original_error": error_msg
            }

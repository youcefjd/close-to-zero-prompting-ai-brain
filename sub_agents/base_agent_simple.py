"""Simplified Base Agent - Phase 1: Working Core

This is the simplified version of BaseSubAgent that actually works.
Advanced features (cost tracking, sanitization, etc.) will be added incrementally in Phase 2.

Design: Keep it simple, make it work, prove the concept, then enhance.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import write_file, run_shell
import json
import os

# MCP Server imports
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

# GitHub tools (added from PR reviewer project)
try:
    from mcp_servers.github_tools import (
        github_get_pr_diff, github_get_pr_metadata, github_post_pr_comment,
        github_list_open_prs, github_create_pr, github_get_repo_info
    )
    HAS_GITHUB_TOOLS = True
except ImportError:
    HAS_GITHUB_TOOLS = False


class BaseSubAgent(ABC):
    """Simplified base class for all sub-agents.

    Phase 1: Core functionality only
    - LLM integration (Ollama)
    - Tool execution
    - Basic error handling

    Phase 2 (coming): Will add incrementally
    - Cost tracking
    - Output sanitization
    - Context management
    - Dynamic tool registry
    - Emergency stop
    """

    def __init__(self, agent_name: str, system_prompt: str):
        """Initialize agent with name and system prompt.

        Args:
            agent_name: Name of the agent (e.g., "Docker Agent")
            system_prompt: System instructions for the LLM
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt

        # Simple LLM setup - just Ollama for now
        # TODO Phase 2: Add auto-detection for Claude vs Ollama
        self.llm = ChatOllama(model="gemma3:4b", temperature=0.7)
        self.llm_type = "ollama"

        # Get available tools
        self.tools = self._get_available_tools()
        self.execution_history = []

    def _get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools this agent can use.

        Returns:
            Dict mapping tool names to tool functions
        """
        tools = {
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

        # Add GitHub tools if available
        if HAS_GITHUB_TOOLS:
            tools.update({
                "github_get_pr_diff": github_get_pr_diff,
                "github_get_pr_metadata": github_get_pr_metadata,
                "github_post_pr_comment": github_post_pr_comment,
                "github_list_open_prs": github_list_open_prs,
                "github_create_pr": github_create_pr,
                "github_get_repo_info": github_get_repo_info,
            })

        return tools

    def _create_prompt(self, task: str, context: Optional[Dict] = None) -> ChatPromptTemplate:
        """Create prompt with system instructions and available tools.

        Args:
            task: The task to execute
            context: Optional context dictionary

        Returns:
            ChatPromptTemplate for the LLM
        """
        tools_description = self._describe_tools()

        prompt_content = f"""{self.system_prompt}

AVAILABLE TOOLS:
{tools_description}

AUTONOMOUS RULES:
1. Proceed autonomously - do NOT ask for permission
2. Use tools directly with appropriate parameters
3. If a tool fails, try alternative approaches
4. Only ask human for:
   - Missing authentication credentials
   - Impossible tasks
   - Major architectural decisions

WORKFLOW:
1. Analyze the task
2. Plan approach (mentally)
3. Execute using tools
4. Verify results
5. Report success or retry

Task: {task}
"""

        if context:
            prompt_content += f"\nContext: {json.dumps(context, indent=2)}"

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=prompt_content),
            MessagesPlaceholder(variable_name="messages")
        ])

    def _describe_tools(self) -> str:
        """Describe available tools to the LLM.

        Returns:
            Formatted string describing all tools
        """
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
        descriptions.append("web_search(query, max_results=5) - Search the web")

        # GitHub tools (if available)
        if HAS_GITHUB_TOOLS:
            descriptions.append("github_get_pr_diff(repo_name, pr_number) - Get PR diff")
            descriptions.append("github_get_pr_metadata(repo_name, pr_number) - Get PR metadata")
            descriptions.append("github_post_pr_comment(repo_name, pr_number, comment) - Post PR comment")
            descriptions.append("github_list_open_prs(repo_name) - List open PRs")
            descriptions.append("github_create_pr(repo_name, title, body, head, base='main') - Create PR")
            descriptions.append("github_get_repo_info(repo_name) - Get repo info")

        return "\n".join(f"  - {desc}" for desc in descriptions)

    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response.

        Simple pattern matching for tool_name(args).

        Args:
            response: LLM response text

        Returns:
            List of tool call dictionaries
        """
        import re

        tool_calls = []

        # Look for tool call patterns: tool_name(arg1=value1, arg2=value2)
        pattern = r'(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, response)

        for tool_name, args_str in matches:
            # Only process if it's a known tool
            if tool_name not in self.tools:
                continue

            # Parse arguments
            kwargs = {}
            if args_str:
                # Simple parsing - split by comma, then by =
                for part in args_str.split(','):
                    part = part.strip()
                    if '=' in part:
                        key, value = part.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        kwargs[key] = value

            tool_calls.append({
                "tool": tool_name,
                "args": [],
                "kwargs": kwargs
            })

        return tool_calls

    @abstractmethod
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the task autonomously.

        Must be implemented by subclasses.

        Args:
            task: Task description
            context: Optional context

        Returns:
            Dict with status, message, and results
        """
        pass

    def _execute_tool(self, tool_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a tool and return result.

        TODO Phase 2: Add governance checks, output sanitization

        Args:
            tool_name: Name of tool to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Dict with status and result
        """
        if tool_name not in self.tools:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not available"
            }

        try:
            tool = self.tools[tool_name]
            result = tool(*args, **kwargs)

            # Handle different result types
            if isinstance(result, dict):
                return result
            else:
                return {
                    "status": "success",
                    "result": result
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _needs_human(self, reason: str) -> Dict[str, Any]:
        """Signal that human input is needed.

        Args:
            reason: Why human input is required

        Returns:
            Dict with needs_human status
        """
        return {
            "status": "needs_human",
            "reason": reason,
            "agent": self.agent_name
        }


# Export for backward compatibility
__all__ = ['BaseSubAgent']

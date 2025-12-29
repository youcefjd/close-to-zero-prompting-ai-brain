"""Builder Agent: LangGraph-based autonomous DevOps engineer."""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import operator
import re

from tools import write_file, run_shell
from mcp_servers.docker_tools import (
    docker_ps, docker_logs, docker_exec, docker_restart, 
    docker_inspect, docker_compose_up, DOCKER_TOOLS
)
from mcp_servers.homeassistant_tools import (
    ha_get_state, ha_call_service, ha_get_logs, 
    ha_search_logs, ha_list_integrations, ha_get_config,
    init_ha_client, HA_TOOLS
)


class AgentState(TypedDict, total=False):
    """State schema for the Builder Agent."""
    messages: Annotated[list, operator.add]  # Message history
    current_plan: str  # Current execution plan
    code_snippet: str  # Generated code/config
    file_path: str  # Target file path
    execution_output: dict  # Result from tool execution
    iteration_count: int  # Track iterations to prevent infinite loops
    error_history: list  # Track error patterns to detect loops
    attempted_fixes: list  # Track what fixes have been attempted
    complexity_level: int  # Track complexity (for enhanced agent)
    fact_check_results: list  # Store fact-check results (for enhanced agent)
    validation_results: list  # Store validation results (for enhanced agent)


def create_llm():
    """Create and return the Ollama LLM instance."""
    return ChatOllama(
        model="llama3.1:latest",  # Default model, can be overridden
        temperature=0.7,
    )


def planner_node(state: AgentState) -> AgentState:
    """Break down the user goal into actionable steps."""
    llm = create_llm()
    
    # Get the user's goal from messages
    user_goal = None
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_goal = msg.content
            break
    
    if not user_goal:
        user_goal = "No goal specified"
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a DevOps planning agent. Your job is to break down user goals into clear, actionable steps.
        
        Analyze the user's request and create a step-by-step plan. Be specific about:
        1. What files need to be created or modified
        2. What commands need to be executed
        3. The order of operations
        
        Format your response as a clear, numbered plan."""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    plan = response.content if hasattr(response, 'content') else str(response)
    
    return {
        **state,
        "current_plan": plan,
        "messages": state["messages"] + [response]
    }


def extract_code_from_markdown(text: str) -> str:
    """Extract code blocks from markdown text."""
    # Try to find code blocks (```language ... ```)
    code_block_pattern = r'```(?:\w+)?\n(.*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        # Return the first code block found
        return matches[0].strip()
    
    # If no code blocks, try to find Python code patterns
    # Look for lines that look like code (imports, def, etc.)
    lines = text.split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        # Detect start of code
        if any(line.strip().startswith(keyword) for keyword in ['import ', 'from ', 'def ', 'class ', 'if __name__']):
            in_code = True
        if in_code:
            code_lines.append(line)
        # Stop if we hit explanatory text after code
        if in_code and line.strip() and not line.strip().startswith('#') and not any(c in line for c in ['=', '(', ')', '[', ']', '{', '}']):
            if not any(keyword in line for keyword in ['import', 'def', 'class', 'if', 'return', 'print']):
                # Might be end of code block
                pass
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    # Fallback: return the text as-is
    return text.strip()


def extract_filename_from_text(text: str) -> str:
    """Extract filename from user request or plan."""
    # Look for patterns like "named 'filename.py'" or "filename.py"
    patterns = [
        r"named\s+['\"]([^'\"]+\.\w+)['\"]",
        r"['\"]([^'\"]+\.\w+)['\"]",
        r"(\w+\.py)",
        r"(\w+\.yml)",
        r"(\w+\.yaml)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]
    
    return ""


def coder_node(state: AgentState) -> AgentState:
    """Generate code/config based on the plan."""
    llm = create_llm()
    
    # Get user's original request to extract filename
    user_request = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a code generation agent. Based on the plan, generate the necessary code or configuration files.
        
        When generating code:
        1. Be precise and complete
        2. Include all necessary configurations
        3. For Docker Compose files, use proper YAML formatting
        4. For Python scripts, include all necessary imports and complete functionality
        5. For shell commands, provide the exact command to run
        
        Output the code/config content. You may wrap it in markdown code blocks if helpful, but the code itself should be complete and ready to execute."""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Add the plan to context
    messages_with_plan = state["messages"] + [
        SystemMessage(content=f"Current Plan:\n{state.get('current_plan', 'No plan available')}")
    ]
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages_with_plan})
    
    raw_code = response.content if hasattr(response, 'content') else str(response)
    
    # Extract code from markdown if present
    code = extract_code_from_markdown(raw_code)
    
    # Extract file path from user request, plan, or infer from code
    file_path = state.get("file_path", "")
    if not file_path:
        # Try to extract from user request first
        file_path = extract_filename_from_text(user_request)
        
        # If not found, try to infer from context
        if not file_path:
            if "docker-compose" in code.lower() or "docker compose" in state.get("current_plan", "").lower():
                file_path = "docker-compose.yml"
            elif "config" in code.lower() and ".yaml" in code.lower():
                file_path = "config.yaml"
            elif "import requests" in code or "def " in code:
                # Looks like Python code
                file_path = extract_filename_from_text(user_request) or "script.py"
            else:
                file_path = "output.txt"
    
    return {
        **state,
        "code_snippet": code,
        "file_path": file_path,
        "messages": state["messages"] + [response]
    }


def executor_node(state: AgentState) -> AgentState:
    """Execute the plan using tools (write_file and run_shell)."""
    code = state.get("code_snippet", "")
    file_path = state.get("file_path", "")
    plan = state.get("current_plan", "")
    
    execution_results = []
    
    # Step 1: Write the file if code snippet exists and is not empty
    if code and file_path and code.strip():
        # Skip if we've already written this exact content (prevent loops)
        attempted_fixes = state.get("attempted_fixes", [])
        fix_key = f"write:{file_path}:{hash(code)}"
        if fix_key in attempted_fixes:
            execution_results.append(f"Skipping duplicate file write to {file_path}")
        else:
            result = write_file(file_path, code)
            execution_results.append(f"File write: {result['message']}")
            
            # Track this attempt
            attempted_fixes = state.get("attempted_fixes", [])
            attempted_fixes.append(fix_key)
            state["attempted_fixes"] = attempted_fixes
            
            if result["status"] == "error":
                return {
                    **state,
                    "execution_output": {
                        "status": "error",
                        "message": result["message"],
                        "details": execution_results
                    }
                }
    
    # Step 2: Check for MCP tool usage (Docker, Home Assistant)
    # Get user request for better command detection
    user_request = ""
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break
    
    combined_text = (plan + " " + user_request).lower()
    
    # MCP Tool Detection and Execution
    # Check for Docker operations
    if any(keyword in combined_text for keyword in ["docker", "container"]):
        # Docker: Check container status
        if "check" in combined_text and ("running" in combined_text or "status" in combined_text):
            container_match = re.search(r"(\w+)\s+container|container\s+(\w+)", user_request, re.IGNORECASE)
            container_name = container_match.group(1) if container_match else None
            if container_name:
                result = docker_ps(filter_name=container_name)
                execution_results.append(f"Docker PS: {result['message']}")
                if result.get("containers"):
                    for c in result["containers"]:
                        execution_results.append(f"  Container: {c.get('Names', 'unknown')}, Status: {c.get('Status', 'unknown')}")
        
        # Docker: Get logs
        if "log" in combined_text or "error" in combined_text:
            container_match = re.search(r"(\w+)\s+container|container\s+(\w+)", user_request, re.IGNORECASE)
            container_name = container_match.group(1) or container_match.group(2) if container_match else None
            if not container_name:
                # Try to infer from context
                if "homeassistant" in combined_text:
                    container_name = "homeassistant"
                elif "ps5" in combined_text:
                    container_name = "ps5-mqtt"
            
            if container_name:
                tail = 100 if "error" in combined_text or "debug" in combined_text else 50
                result = docker_logs(container_name, tail=tail)
                execution_results.append(f"Docker Logs ({container_name}): {result['message']}")
                if result.get("logs"):
                    # Extract errors if searching for errors
                    if "error" in combined_text:
                        error_lines = [line for line in result["logs"].split("\n") if "error" in line.lower() or "exception" in line.lower()]
                        if error_lines:
                            execution_results.append(f"  Found {len(error_lines)} error line(s):")
                            for line in error_lines[:10]:  # Limit to 10 lines
                                execution_results.append(f"    {line[:200]}")
                    else:
                        execution_results.append(f"  Last 5 lines: {result['logs'].split(chr(10))[-5:]}")
        
        # Docker: Restart container
        if "restart" in combined_text:
            container_match = re.search(r"(\w+)\s+container|container\s+(\w+)", user_request, re.IGNORECASE)
            container_name = container_match.group(1) or container_match.group(2) if container_match else None
            if not container_name:
                if "homeassistant" in combined_text:
                    container_name = "homeassistant"
                elif "ps5" in combined_text:
                    container_name = "ps5-mqtt"
            
            if container_name:
                result = docker_restart(container_name)
                execution_results.append(f"Docker Restart: {result['message']}")
                if result["status"] == "error":
                    return {
                        **state,
                        "execution_output": {
                            "status": "error",
                            "message": result["message"],
                            "details": execution_results
                        }
                    }
    
    # Check for Home Assistant operations
    if any(keyword in combined_text for keyword in ["home assistant", "homeassistant", "ha ", "integration", "entity"]):
        # Initialize HA client if needed
        init_ha_client()
        
        # HA: Check integration status
        if "integration" in combined_text and ("list" in combined_text or "check" in combined_text or "status" in combined_text):
            result = ha_list_integrations()
            execution_results.append(f"HA Integrations: {result['message']}")
            if result.get("integrations"):
                for domain, entries in result["integrations"].items():
                    execution_results.append(f"  {domain}: {len(entries)} entry/entries")
                    for entry in entries[:3]:  # Show first 3
                        execution_results.append(f"    - {entry.get('title', 'Unknown')} ({entry.get('state', 'unknown')})")
        
        # HA: Search logs
        if "log" in combined_text and ("error" in combined_text or "debug" in combined_text):
            search_term = "error" if "error" in combined_text else "debug"
            result = ha_search_logs(search_term, tail=200)
            execution_results.append(f"HA Log Search: {result['message']}")
            if result.get("matches"):
                execution_results.append(f"  Found {len(result['matches'])} matching line(s):")
                for match in result["matches"][:10]:  # Limit to 10
                    execution_results.append(f"    {match[:200]}")
        
        # HA: Get entity state
        entity_match = re.search(r"entity[_\s]+id[:\s]+([\w\.]+)|([\w\.]+\.[\w\.]+)", user_request, re.IGNORECASE)
        if entity_match:
            entity_id = entity_match.group(1) or entity_match.group(2)
            result = ha_get_state(entity_id)
            if result["status"] == "success":
                state_data = result.get("state", {})
                execution_results.append(f"HA Entity State ({entity_id}): {state_data.get('state', 'unknown')}")
                if state_data.get("attributes"):
                    execution_results.append(f"  Attributes: {list(state_data['attributes'].keys())[:5]}")
    
    # Step 3: Check if plan contains commands to execute (fallback to shell)
    commands_to_run = []
    
    # Extract commands directly from user request (quoted commands)
    quoted_commands = re.findall(r"['\"]([^'\"]+)['\"]", user_request)
    for cmd in quoted_commands:
        if cmd.strip() and not cmd.startswith("http"):  # Skip URLs
            # Check if it's a command that should be run in a container
            if "docker exec" in user_request.lower() or "inside" in user_request.lower() or "container" in user_request.lower():
                # Extract container name
                container_match = re.search(r"['\"]?(\w+)['\"]?\s+container", user_request, re.IGNORECASE)
                if container_match:
                    container_name = container_match.group(1)
                    commands_to_run.append(f"docker exec {container_name} sh -c \"{cmd}\"")
                elif "homeassistant" in user_request.lower():
                    commands_to_run.append(f"docker exec homeassistant sh -c \"{cmd}\"")
            else:
                commands_to_run.append(cmd)
    
    # Check for file deletion commands - add existence check
    if "delete" in combined_text or "remove" in combined_text or "rm " in combined_text:
        # Look for file paths in the request (handle both absolute and relative paths)
        file_patterns = [
            r"['\"]([^'\"]+\.json)['\"]",
            r"['\"]([^'\"]+\.yaml)['\"]",
            r"['\"]([^'\"]+\.yml)['\"]",
            r"['\"]([^'\"]+\.py)['\"]",
            r"['\"]([^'\"]+\.txt)['\"]",
            r"['\"](/[^'\"]+)['\"]",  # Absolute paths
        ]
        from pathlib import Path
        import os
        
        for pattern in file_patterns:
            matches = re.findall(pattern, user_request)
            for match in matches:
                # Handle absolute paths (starting with /) and relative paths
                if match.startswith("/"):
                    # Absolute path - check as-is
                    file_to_check = Path(match)
                else:
                    # Relative path - check from current directory
                    file_to_check = Path(match)
                
                # Try both absolute and relative
                if file_to_check.exists() or os.path.exists(match):
                    commands_to_run.append(f"rm {match}")
                else:
                    # Also try with config/ prefix if it's a storage path
                    if "/.storage/" in match or ".storage" in match:
                        alt_path = match if match.startswith("config/") else f"config/{match.lstrip('/')}"
                        if Path(alt_path).exists():
                            commands_to_run.append(f"rm {alt_path}")
                        else:
                            execution_results.append(f"File {match} does not exist, skipping deletion")
                    else:
                        execution_results.append(f"File {match} does not exist, skipping deletion")
    
    # Check for docker exec commands in plan/user request
    if "docker exec" in combined_text or ("docker" in combined_text and "container" in combined_text):
        # Look for container name
        container_match = re.search(r"(\w+)\s+container", user_request, re.IGNORECASE)
        container_name = container_match.group(1) if container_match else "homeassistant"
        
        # Look for commands to run inside container
        if "wget" in combined_text or "install" in combined_text:
            # Extract the command from quotes or use a default
            if quoted_commands:
                cmd = quoted_commands[0]
                commands_to_run.append(f"docker exec {container_name} sh -c \"{cmd}\"")
    
    # Check for docker restart commands
    if "restart" in combined_text and ("container" in combined_text or "docker" in combined_text):
        container_match = re.search(r"(\w+)\s+container", user_request, re.IGNORECASE)
        if not container_match:
            # Try to find container name from context
            if "homeassistant" in combined_text:
                container_name = "homeassistant"
            elif "ps5" in combined_text:
                container_name = "ps5-mqtt"
            else:
                container_name = "homeassistant"  # Default
        else:
            container_name = container_match.group(1)
        commands_to_run.append(f"docker restart {container_name}")
    
    # Check for docker compose commands
    if "docker" in combined_text and ("up" in combined_text or "start" in combined_text or "run" in combined_text):
        if file_path and "docker-compose" in file_path:
            commands_to_run.append(f"docker compose -f {file_path} up -d")
        elif "docker compose" in combined_text:
            commands_to_run.append("docker compose up -d")
    
    # Check for Python script execution
    if file_path.endswith(".py") and ("run" in combined_text or "execute" in combined_text or "script" in combined_text):
        commands_to_run.append(f"python {file_path}")
    
    # Check for pip install commands
    if "pip install" in combined_text or ("install" in combined_text and "requirements" in combined_text):
        if "requirements.txt" in combined_text:
            commands_to_run.append("pip install -r requirements.txt")
    
    # Execute commands (skip duplicates to prevent loops)
    attempted_fixes = state.get("attempted_fixes", [])
    for cmd in commands_to_run:
        # Skip if we've already tried this exact command
        cmd_key = f"cmd:{hash(cmd)}"
        if cmd_key in attempted_fixes:
            execution_results.append(f"Skipping duplicate command: {cmd}")
            continue
        
        result = run_shell(cmd)
        execution_results.append(f"Command '{cmd}': {result['message']}")
        execution_results.append(f"  Exit code: {result['exit_code']}")
        if result['stdout']:
            execution_results.append(f"  Stdout: {result['stdout'][:500]}")  # Limit output
        if result['stderr']:
            execution_results.append(f"  Stderr: {result['stderr'][:500]}")
        
        # Track this attempt
        attempted_fixes.append(cmd_key)
        state["attempted_fixes"] = attempted_fixes
        
        if result["status"] == "error":
            return {
                **state,
                "execution_output": {
                    "status": "error",
                    "exit_code": result.get("exit_code", -1),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "message": result["message"],
                    "details": execution_results
                }
            }
    
    # Success
    return {
        **state,
        "execution_output": {
            "status": "success",
            "message": "Execution completed successfully",
            "details": execution_results
        }
    }


def reflector_node(state: AgentState) -> AgentState:
    """Analyze execution output and decide next step."""
    execution_output = state.get("execution_output", {})
    iteration_count = state.get("iteration_count", 0)
    error_history = state.get("error_history", [])
    
    # Prevent infinite loops
    if iteration_count >= 5:
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="Maximum iterations (5) reached. Stopping to prevent infinite loop.\n\n"
                         "The agent has attempted multiple fixes but continues to encounter errors. "
                         "Please review the error history and consider:\n"
                         "1. Manually fixing the issue\n"
                         "2. Providing more specific instructions\n"
                         "3. Checking if prerequisites are met")
            ]
        }
    
    status = execution_output.get("status", "unknown")
    
    if status == "success":
        # Success - end the workflow
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content=f"Task completed successfully!\n\nExecution details:\n" + 
                         "\n".join(execution_output.get("details", [])))
            ]
        }
    else:
        # Error - need to fix and retry
        error_msg = execution_output.get("message", "Unknown error")
        stderr = execution_output.get("stderr", "")
        stdout = execution_output.get("stdout", "")
        
        # Extract error signature for loop detection
        error_signature = f"{error_msg[:100]}:{stderr[:100]}"
        error_history.append(error_signature)
        
        # Check if we're seeing the same error repeatedly (loop detection)
        if len(error_history) >= 3:
            recent_errors = error_history[-3:]
            if len(set(recent_errors)) == 1:  # Same error 3 times in a row
                return {
                    **state,
                    "iteration_count": iteration_count + 1,
                    "error_history": error_history,
                    "messages": state["messages"] + [
                        AIMessage(content=f"⚠️ LOOP DETECTED: The same error has occurred 3 times in a row.\n\n"
                                 f"Error: {error_msg}\n\n"
                                 f"This suggests the current approach is not working. "
                                 f"Please try a different strategy or manually fix the issue.\n\n"
                                 f"Error details:\n{stderr[:500] if stderr else error_msg}")
                    ]
                }
        
        # Provide more context for fixing
        error_context = f"Error occurred: {error_msg}\n"
        if stderr:
            error_context += f"Stderr: {stderr[:1000]}\n"  # Limit length
        if stdout:
            error_context += f"Stdout: {stdout[:500]}\n"
        
        # Add guidance based on error type
        guidance = ""
        if "No such file or directory" in error_msg or "No such file" in stderr:
            guidance = "\n💡 Suggestion: Check if the file exists before trying to delete or modify it. Use 'ls' or 'test -f' to verify file existence first."
        elif "Permission denied" in error_msg or "Permission denied" in stderr:
            guidance = "\n💡 Suggestion: Check file permissions. You may need to use 'chmod' or run with appropriate permissions."
        elif "docker" in error_msg.lower() or "container" in error_msg.lower():
            guidance = "\n💡 Suggestion: Verify the container name and that Docker is running. Use 'docker ps' to list running containers."
        elif iteration_count >= 2:
            guidance = f"\n💡 Suggestion: This is attempt {iteration_count + 1}. Consider trying a completely different approach or checking if the task requirements are clear."
        
        return {
            **state,
            "iteration_count": iteration_count + 1,
            "error_history": error_history,
            "messages": state["messages"] + [
                SystemMessage(content=f"Execution failed. Error details:\n{error_context}{guidance}\n\n"
                            f"Please fix the code and try again. (Attempt {iteration_count + 1}/5)")
            ]
        }


def should_continue(state: AgentState) -> Literal["coder", "end"]:
    """Conditional edge: continue to coder if error, end if success."""
    execution_output = state.get("execution_output", {})
    status = execution_output.get("status", "unknown")
    iteration_count = state.get("iteration_count", 0)
    error_history = state.get("error_history", [])
    
    # Stop if max iterations reached
    if iteration_count >= 5:
        return "end"
    
    # Stop if we detect a loop (same error 3+ times)
    if len(error_history) >= 3:
        recent_errors = error_history[-3:]
        if len(set(recent_errors)) == 1:
            return "end"  # Stop the loop
    
    if status == "error":
        return "coder"  # Loop back to fix
    else:
        return "end"  # Success, finish


def create_agent_graph():
    """Create and compile the Builder Agent graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reflector", reflector_node)
    
    # Define the flow
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")
    workflow.add_edge("executor", "reflector")
    
    # Conditional edge from reflector
    workflow.add_conditional_edges(
        "reflector",
        should_continue,
        {
            "coder": "coder",
            "end": END
        }
    )
    
    # Compile the graph
    return workflow.compile()



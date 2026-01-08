"""Enhanced Builder Agent with fact-checking, learning, and complexity reduction."""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import operator
import re
import os
from pathlib import Path

from tools import write_file, run_shell
from mcp_servers.docker_tools import (
    docker_ps, docker_logs, docker_exec, docker_restart, 
    docker_inspect, docker_compose_up
)
from mcp_servers.homeassistant_tools import (
    ha_get_state, ha_call_service, ha_get_logs, 
    ha_search_logs, ha_list_integrations, ha_get_config,
    init_ha_client
)
from fact_checker import FactChecker
from emergency_stop import get_emergency_stop, EmergencyStopException


class AgentState(TypedDict):
    """Enhanced state schema with fact-checking and learning."""
    messages: Annotated[list, operator.add]
    current_plan: str
    code_snippet: str
    file_path: str
    execution_output: dict
    iteration_count: int
    error_history: list
    attempted_fixes: list
    complexity_level: int  # Track complexity (0=simple, 1=medium, 2=complex)
    fact_check_results: list  # Store fact-check results
    validation_results: list  # Store validation results


def create_llm():
    """Create and return the Ollama LLM instance."""
    return ChatOllama(
        model="gemma3:4b",
        temperature=0.7,
    )


def planner_node(state: AgentState) -> AgentState:
    """Break down the user goal into actionable steps with complexity awareness."""
    # Check emergency stop
    emergency_stop = get_emergency_stop()
    emergency_stop.check_and_raise()
    
    llm = create_llm()
    fact_checker = FactChecker()
    
    # Get the user's goal
    user_goal = None
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_goal = msg.content
            break
    
    if not user_goal:
        user_goal = "No goal specified"
    
    # Check if similar tasks have failed before
    similar_failures = fact_checker.check_similar_failures("planning", user_goal)
    complexity_hint = ""
    if similar_failures.get("should_avoid"):
        complexity_hint = f"\n\n⚠️ WARNING: Similar tasks have failed {similar_failures['failure_count']} time(s) before. Keep the plan SIMPLE and focus on one step at a time."
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a DevOps planning agent. Your job is to break down user goals into clear, actionable steps.
        
        CRITICAL RULES:
        1. Keep plans SIMPLE - one step at a time
        2. If a task seems complex, break it into smaller steps
        3. Always verify prerequisites before executing
        4. Start with the simplest approach first{complexity_hint}
        
        Analyze the user's request and create a step-by-step plan. Be specific about:
        1. What files need to be created or modified
        2. What commands need to be executed
        3. The order of operations
        4. What to verify after each step
        
        Format your response as a clear, numbered plan. Keep it simple and focused."""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    plan = response.content if hasattr(response, 'content') else str(response)
    
    # Assess complexity
    complexity = 0
    if len(plan.split('\n')) > 10:
        complexity = 1
    if "complex" in plan.lower() or "multiple" in plan.lower() or "several" in plan.lower():
        complexity = 2
    
    return {
        **state,
        "current_plan": plan,
        "complexity_level": complexity,
        "messages": state["messages"] + [response]
    }


def extract_code_from_markdown(text: str) -> str:
    """Extract code blocks from markdown text."""
    code_block_pattern = r'```(?:\w+)?\n(.*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    lines = text.split('\n')
    code_lines = []
    in_code = False
    for line in lines:
        if any(line.strip().startswith(keyword) for keyword in ['import ', 'from ', 'def ', 'class ', 'if __name__']):
            in_code = True
        if in_code:
            code_lines.append(line)
        if in_code and line.strip() and not line.strip().startswith('#') and not any(c in line for c in ['=', '(', ')', '[', ']', '{', '}']):
            if not any(keyword in line for keyword in ['import', 'def', 'class', 'if', 'return', 'print']):
                pass
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return text.strip()


def extract_filename_from_text(text: str) -> str:
    """Extract filename from user request or plan."""
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
    """Generate code/config with fact-checking and complexity reduction."""
    llm = create_llm()
    fact_checker = FactChecker()
    
    # Get user's original request
    user_request = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break
    
    # Reduce complexity if we've failed multiple times
    complexity = state.get("complexity_level", 0)
    iteration_count = state.get("iteration_count", 0)
    
    complexity_hint = ""
    if iteration_count >= 2:
        complexity_hint = "\n\n⚠️ CRITICAL: Previous attempts failed. Generate SIMPLER code. Use the most basic approach possible. Avoid complex logic."
        complexity = 0  # Force simple approach
    
    # Check for similar successful patterns
    similar_successes = fact_checker.check_similar_successes("code_generation")
    if similar_successes.get("has_similar_successes"):
        complexity_hint += f"\n\n💡 TIP: Similar code has worked before. Use a similar pattern."
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a code generation agent. Based on the plan, generate the necessary code or configuration files.
        
        CRITICAL RULES:
        1. Generate SIMPLE, working code - avoid over-engineering
        2. Include all necessary imports and configurations
        3. Use proper formatting (YAML for configs, Python for scripts)
        4. Keep it minimal - only what's needed{complexity_hint}
        
        When generating code:
        1. Be precise and complete
        2. Include all necessary configurations
        3. For Docker Compose files, use proper YAML formatting
        4. For Python scripts, include all necessary imports and complete functionality
        5. For shell commands, provide the exact command to run
        
        Output the code/config content. You may wrap it in markdown code blocks if helpful, but the code itself should be complete and ready to execute."""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    messages_with_plan = state["messages"] + [
        SystemMessage(content=f"Current Plan:\n{state.get('current_plan', 'No plan available')}")
    ]
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages_with_plan})
    
    raw_code = response.content if hasattr(response, 'content') else str(response)
    code = extract_code_from_markdown(raw_code)
    
    # Extract file path
    file_path = state.get("file_path", "")
    if not file_path:
        file_path = extract_filename_from_text(user_request)
        if not file_path:
            if "docker-compose" in code.lower() or "docker compose" in state.get("current_plan", "").lower():
                file_path = "docker-compose.yml"
            elif "config" in code.lower() and ".yaml" in code.lower():
                file_path = "config.yaml"
            elif "import requests" in code or "def " in code:
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
    """Execute with fact-checking and validation."""
    fact_checker = FactChecker()
    code = state.get("code_snippet", "")
    file_path = state.get("file_path", "")
    plan = state.get("current_plan", "")
    
    execution_results = []
    fact_check_results = []
    validation_results = []
    
    # Step 1: Write file with fact-checking
    if code and file_path and code.strip():
        # Fact-check before execution
        action_details = {"file_path": file_path, "content_length": len(code)}
        validation = fact_checker.validate_action_before_execution("file_write", action_details)
        
        if not validation["should_proceed"]:
            return {
                **state,
                "execution_output": {
                    "status": "error",
                    "message": f"Fact-check failed: {', '.join(validation['warnings'])}",
                    "details": execution_results
                },
                "fact_check_results": fact_check_results + [validation]
            }
        
        fact_check_results.append(validation)
        
        # Check for duplicate writes
        attempted_fixes = state.get("attempted_fixes", [])
        fix_key = f"write:{file_path}:{hash(code)}"
        if fix_key in attempted_fixes:
            execution_results.append(f"Skipping duplicate file write to {file_path}")
        else:
            result = write_file(file_path, code)
            execution_results.append(f"File write: {result['message']}")
            
            # Validate after execution
            post_validation = fact_checker.validate_action_after_execution(
                "file_write", 
                action_details, 
                result
            )
            validation_results.append(post_validation)
            
            if not post_validation.get("verified"):
                execution_results.append(f"⚠️ Validation warning: {', '.join(post_validation.get('warnings', []))}")
            
            # Record success/failure
            if result["status"] == "success":
                fact_checker.record_success("file_write", action_details, pattern=file_path)
            else:
                fact_checker.record_failure("file_write", result.get("message", "Unknown error"), action_details)
            
            attempted_fixes.append(fix_key)
            state["attempted_fixes"] = attempted_fixes
            
            if result["status"] == "error":
                return {
                    **state,
                    "execution_output": {
                        "status": "error",
                        "message": result["message"],
                        "details": execution_results
                    },
                    "fact_check_results": fact_check_results,
                    "validation_results": validation_results
                }
    
    # Step 2: MCP tools (Docker, Home Assistant) - same as before but with fact-checking
    user_request = ""
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break
    
    combined_text = (plan + " " + user_request).lower()
    
    # Docker operations with fact-checking
    if any(keyword in combined_text for keyword in ["docker", "container"]):
        if "restart" in combined_text:
            container_match = re.search(r"(\w+)\s+container|container\s+(\w+)", user_request, re.IGNORECASE)
            container_name = container_match.group(1) or container_match.group(2) if container_match else None
            if not container_name:
                if "homeassistant" in combined_text:
                    container_name = "homeassistant"
                elif "ps5" in combined_text:
                    container_name = "ps5-mqtt"
            
            if container_name:
                # Fact-check: verify container exists
                container_check = fact_checker.verify_docker_container(container_name)
                if not container_check.get("container_exists"):
                    return {
                        **state,
                        "execution_output": {
                            "status": "error",
                            "message": f"Container {container_name} does not exist",
                            "details": execution_results
                        },
                        "fact_check_results": fact_check_results + [container_check]
                    }
                
                result = docker_restart(container_name)
                execution_results.append(f"Docker Restart: {result['message']}")
                
                if result["status"] == "error":
                    fact_checker.record_failure("docker_operation", result["message"], {"container": container_name})
                    return {
                        **state,
                        "execution_output": {
                            "status": "error",
                            "message": result["message"],
                            "details": execution_results
                        },
                        "fact_check_results": fact_check_results
                    }
                else:
                    fact_checker.record_success("docker_operation", {"container": container_name})
    
    # Home Assistant operations
    if any(keyword in combined_text for keyword in ["home assistant", "homeassistant", "ha ", "integration"]):
        init_ha_client()
        
        if "integration" in combined_text and ("list" in combined_text or "check" in combined_text):
            result = ha_list_integrations()
            execution_results.append(f"HA Integrations: {result['message']}")
            if result.get("integrations"):
                for domain, entries in result["integrations"].items():
                    execution_results.append(f"  {domain}: {len(entries)} entry/entries")
                    for entry in entries[:3]:
                        execution_results.append(f"    - {entry.get('title', 'Unknown')} ({entry.get('state', 'unknown')})")
    
    # Step 3: Shell commands with fact-checking
    commands_to_run = []
    
    # Extract commands (same logic as before)
    quoted_commands = re.findall(r"['\"]([^'\"]+)['\"]", user_request)
    for cmd in quoted_commands:
        if cmd.strip() and not cmd.startswith("http"):
            if "docker exec" in user_request.lower() or "inside" in user_request.lower():
                container_match = re.search(r"['\"]?(\w+)['\"]?\s+container", user_request, re.IGNORECASE)
                if container_match:
                    container_name = container_match.group(1)
                    commands_to_run.append(f"docker exec {container_name} sh -c \"{cmd}\"")
                elif "homeassistant" in user_request.lower():
                    commands_to_run.append(f"docker exec homeassistant sh -c \"{cmd}\"")
            else:
                commands_to_run.append(cmd)
    
    # Execute commands with fact-checking
    attempted_fixes = state.get("attempted_fixes", [])
    for cmd in commands_to_run:
        # Fact-check before execution
        action_details = {"command": cmd}
        validation = fact_checker.validate_action_before_execution("command_exec", action_details)
        
        if not validation["should_proceed"]:
            execution_results.append(f"⚠️ Skipping command due to fact-check: {', '.join(validation['warnings'])}")
            continue
        
        # Check for duplicates
        cmd_key = f"cmd:{hash(cmd)}"
        if cmd_key in attempted_fixes:
            execution_results.append(f"Skipping duplicate command: {cmd}")
            continue
        
        result = run_shell(cmd)
        execution_results.append(f"Command '{cmd}': {result['message']}")
        
        # Validate after execution
        post_validation = fact_checker.validate_action_after_execution("command_exec", action_details, result)
        validation_results.append(post_validation)
        
        if not post_validation.get("verified"):
            execution_results.append(f"⚠️ Validation warning: {', '.join(post_validation.get('warnings', []))}")
        
        # Record success/failure
        if result["status"] == "success":
            fact_checker.record_success("command_exec", action_details, pattern=cmd.split()[0] if cmd.split() else "")
        else:
            fact_checker.record_failure("command_exec", result.get("message", "Unknown error"), action_details)
        
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
                },
                "fact_check_results": fact_check_results,
                "validation_results": validation_results
            }
    
    # Success
    return {
        **state,
        "execution_output": {
            "status": "success",
            "message": "Execution completed successfully",
            "details": execution_results
        },
        "fact_check_results": fact_check_results,
        "validation_results": validation_results
    }


def reflector_node(state: AgentState) -> AgentState:
    """Enhanced reflection with fact-checking and complexity reduction."""
    # Check emergency stop
    emergency_stop = get_emergency_stop()
    emergency_stop.check_and_raise()
    
    execution_output = state.get("execution_output", {})
    iteration_count = state.get("iteration_count", 0)
    error_history = state.get("error_history", [])
    complexity = state.get("complexity_level", 0)
    fact_checker = FactChecker()
    
    # Enhanced loop detection
    if iteration_count >= 5:
        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content="⚠️ MAXIMUM ITERATIONS REACHED (5). Stopping to prevent infinite loop.\n\n"
                         "The agent has attempted multiple fixes but continues to encounter errors.\n\n"
                         "Error history:\n" + "\n".join(error_history[-5:]) + "\n\n"
                         "Please review and consider:\n"
                         "1. Manually fixing the issue\n"
                         "2. Providing more specific instructions\n"
                         "3. Checking if prerequisites are met\n"
                         "4. Trying a completely different approach")
            ]
        }
    
    status = execution_output.get("status", "unknown")
    
    if status == "success":
        # Success - verify with fact-checking
        validation_results = state.get("validation_results", [])
        all_verified = all(v.get("verified", False) for v in validation_results) if validation_results else True
        
        success_msg = "Task completed successfully!\n\nExecution details:\n" + "\n".join(execution_output.get("details", []))
        
        if not all_verified:
            success_msg += "\n\n⚠️ Some validations had warnings. Please verify the results manually."
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=success_msg)]
        }
    else:
        # Error - analyze and learn
        error_msg = execution_output.get("message", "Unknown error")
        stderr = execution_output.get("stderr", "")
        stdout = execution_output.get("stdout", "")
        
        # Enhanced error signature
        error_signature = f"{error_msg[:100]}:{stderr[:100]}:{stdout[:50]}"
        error_history.append(error_signature)
        
        # Check for loops with more sophisticated detection
        if len(error_history) >= 3:
            recent_errors = error_history[-3:]
            # Check if errors are similar (not just identical)
            error_similarity = len(set(recent_errors))
            if error_similarity == 1:  # Exactly the same
                return {
                    **state,
                    "iteration_count": iteration_count + 1,
                    "error_history": error_history,
                    "complexity_level": 0,  # Force simple approach
                    "messages": state["messages"] + [
                        AIMessage(content=f"⚠️ LOOP DETECTED: Same error 3 times in a row.\n\n"
                                 f"Error: {error_msg}\n\n"
                                 f"The current approach is not working. "
                                 f"Switching to SIMPLEST possible approach.\n\n"
                                 f"Error details:\n{stderr[:500] if stderr else error_msg}")
                    ]
                }
            elif error_similarity <= 2:  # Similar errors
                # Reduce complexity
                new_complexity = max(0, complexity - 1)
                return {
                    **state,
                    "iteration_count": iteration_count + 1,
                    "error_history": error_history,
                    "complexity_level": new_complexity,
                    "messages": state["messages"] + [
                        SystemMessage(content=f"Similar errors detected. Reducing complexity to level {new_complexity}.\n\n"
                                    f"Error: {error_msg}\n\n"
                                    f"Try a SIMPLER approach. (Attempt {iteration_count + 1}/5)")
                    ]
                }
        
        # Provide context and guidance
        error_context = f"Error occurred: {error_msg}\n"
        if stderr:
            error_context += f"Stderr: {stderr[:1000]}\n"
        if stdout:
            error_context += f"Stdout: {stdout[:500]}\n"
        
        # Enhanced guidance based on fact-checker memory
        guidance = ""
        if "No such file" in error_msg or "No such file" in stderr:
            guidance = "\n💡 Suggestion: Verify file exists before operations. Use fact-checker to validate paths."
        elif "Permission denied" in error_msg or "Permission denied" in stderr:
            guidance = "\n💡 Suggestion: Check file permissions. Use 'ls -l' to verify."
        elif "docker" in error_msg.lower() or "container" in error_msg.lower():
            guidance = "\n💡 Suggestion: Verify container exists with 'docker ps'. Check container name spelling."
        elif iteration_count >= 2:
            guidance = f"\n💡 Suggestion: This is attempt {iteration_count + 1}. Use the SIMPLEST possible approach. Break the task into smaller steps."
        
        # Check fact-checker for similar failures
        similar_failures = fact_checker.check_similar_failures("execution", error_signature)
        if similar_failures.get("has_similar_failures"):
            guidance += f"\n\n⚠️ This error pattern has occurred {similar_failures['failure_count']} time(s) before. "
            guidance += similar_failures.get("suggestion", "Try a completely different approach.")
        
        return {
            **state,
            "iteration_count": iteration_count + 1,
            "error_history": error_history,
            "complexity_level": max(0, complexity - 1) if iteration_count >= 2 else complexity,  # Reduce complexity after 2 failures
            "messages": state["messages"] + [
                SystemMessage(content=f"Execution failed. Error details:\n{error_context}{guidance}\n\n"
                            f"Please fix and try again with a SIMPLER approach. (Attempt {iteration_count + 1}/5)")
            ]
        }


def should_continue(state: AgentState) -> Literal["coder", "end"]:
    """Enhanced conditional edge with fact-checking awareness."""
    execution_output = state.get("execution_output", {})
    status = execution_output.get("status", "unknown")
    iteration_count = state.get("iteration_count", 0)
    error_history = state.get("error_history", [])
    
    # Stop if max iterations reached
    if iteration_count >= 5:
        return "end"
    
    # Enhanced loop detection
    if len(error_history) >= 3:
        recent_errors = error_history[-3:]
        error_similarity = len(set(recent_errors))
        if error_similarity == 1:  # Same error 3 times
            return "end"
        elif error_similarity <= 2 and iteration_count >= 3:  # Similar errors, 3+ attempts
            return "end"  # Stop to prevent further loops
    
    if status == "error":
        return "coder"  # Loop back to fix
    else:
        return "end"  # Success, finish


def create_agent_graph():
    """Create and compile the enhanced Builder Agent graph."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reflector", reflector_node)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")
    workflow.add_edge("executor", "reflector")
    
    workflow.add_conditional_edges(
        "reflector",
        should_continue,
        {
            "coder": "coder",
            "end": END
        }
    )
    
    return workflow.compile()


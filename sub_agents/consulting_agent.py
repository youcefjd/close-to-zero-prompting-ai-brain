"""Consulting Sub-Agent: Handles analysis, comparison, and recommendation tasks."""

from typing import Dict, Any, Optional
from sub_agents.base_agent import BaseSubAgent
from langchain_core.messages import HumanMessage, AIMessage
import json
import platform


def _get_os_info() -> Dict[str, str]:
    """Detect the current operating system and provide context."""
    system = platform.system().lower()
    if system == "darwin":
        return {
            "os": "macOS",
            "shell_type": "zsh/bash",
            "audio_tool": "osascript (AppleScript)",
            "volume_cmd": "osascript -e 'output volume of (get volume settings)'",
            "battery_cmd": "pmset -g batt",
            "disk_cmd": "df -h",
            "memory_cmd": "vm_stat",
            "time_cmd": "date",
            "running_apps_cmd": "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false'",
            "all_processes_cmd": "ps aux | head -20"
        }
    elif system == "linux":
        return {
            "os": "Linux",
            "shell_type": "bash",
            "audio_tool": "amixer or pactl",
            "volume_cmd": "amixer get Master | grep -o '[0-9]*%'",
            "battery_cmd": "upower -i /org/freedesktop/UPower/devices/battery_BAT0",
            "disk_cmd": "df -h",
            "memory_cmd": "free -h",
            "time_cmd": "date",
            "running_apps_cmd": "wmctrl -l 2>/dev/null || ps aux --sort=-%mem | head -20",
            "all_processes_cmd": "ps aux --sort=-%mem | head -20"
        }
    else:
        return {
            "os": system,
            "shell_type": "unknown",
            "audio_tool": "unknown",
            "volume_cmd": "unknown",
            "battery_cmd": "unknown",
            "disk_cmd": "unknown",
            "memory_cmd": "unknown",
            "time_cmd": "date",
            "running_apps_cmd": "unknown",
            "all_processes_cmd": "unknown"
        }


class ConsultingAgent(BaseSubAgent):
    """Specialized agent for analysis, comparison, and recommendations."""
    
    def __init__(self):
        # Initialize output formatter LLM (lightweight model for formatting)
        from langchain_ollama import ChatOllama
        self.formatter_llm = ChatOllama(model="gemma3:4b", temperature=0.1)
        
        # Get OS-specific context
        self.os_info = _get_os_info()
        
        system_prompt = f"""You are a Consulting Agent with full autonomy and semantic understanding.

CURRENT SYSTEM: {self.os_info['os']}
- Shell: {self.os_info['shell_type']}
- Audio control: {self.os_info['audio_tool']}

PRINCIPLES:
1. Understand semantic meaning and context, not surface patterns
2. Generalize understanding to similar situations
3. Think about user intent and what they're trying to accomplish
4. Choose tools based on understanding, not pattern matching
5. You have FULL AUTONOMY - execute tasks directly, don't just answer questions

TOOL SELECTION:
- Understand whether the query is about LOCAL system information (use run_shell) or EXTERNAL information (use web_search)
- LOCAL queries: Information about THIS computer/system

OS DETECTION (ALREADY DONE - USE THIS):
  * Current system: {self.os_info['os']}
  * Shell: {self.os_info['shell_type']}

GENERALIZATION PRINCIPLES FOR {self.os_info['os']}:
  * On macOS: Use 'osascript' for AppleScript queries (GUI apps, system settings, dialogs)
  * On macOS: Use standard Unix commands (ps, df, date, etc.) for system info
  * On macOS: Use 'pmset' for power/battery, 'defaults' for preferences
  * On Linux: Use standard GNU tools (ps, free, df, amixer, etc.)
  * THINK about what tool would logically provide the information requested
  * If a command fails, understand WHY and try a different approach for THIS OS
  * Do NOT use Linux commands on macOS or vice versa
  
SEMANTIC UNDERSTANDING:
  * "apps" or "applications" = GUI applications (use AppleScript on macOS)
  * "processes" = all running processes (use ps)
  * "volume" = audio level (use osascript on macOS, amixer on Linux)
  * "battery" = power status (use pmset on macOS, upower on Linux)
  * Understand what the user MEANS, not just the words they use
- EXTERNAL queries: Information from the internet/world (sports scores, news, current events, etc.)
  * Use web_search with effective search queries

AVAILABLE TOOLS:
- run_shell(command): Execute system commands (command should be a valid shell command string)
- web_search(query, max_results=5): Search the web

CRITICAL: 
- This is {self.os_info['os']} - do NOT use Linux commands like amixer
- For macOS audio, use osascript with AppleScript syntax
- Execute directly - don't just explain how to do it"""
        
        super().__init__("ConsultingAgent", system_prompt)
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute consultation/analysis task."""
        print(f"💡 ConsultingAgent: {task}")
        
        # Store original task for output formatting
        self._current_task = task
        
        # Always use tool-calling mechanism - let LLM decide what tools to use
        # The LLM understands context and will choose appropriate tools
        return self._execute_with_tools(task, context)
    
    def _format_output(self, raw_output: str, original_query: str) -> str:
        """Use LLM to clean up raw command output and extract relevant information.
        
        This transforms verbose technical output into a clean, user-friendly answer.
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # If output is already short and clean, return as-is
        if len(raw_output) < 200 and '\n' not in raw_output:
            return raw_output.strip()
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an output formatter. Your job is to extract the relevant answer from raw command output.

RULES:
1. Extract ONLY the information that answers the user's question
2. Remove all technical noise, debug info, and irrelevant data
3. Format the answer clearly and concisely
4. If the output contains a specific value (like volume level, battery percentage, time), just return that value with context
5. If the output is an error or shows no relevant data, say so clearly
6. NEVER include raw technical output like IOKit registry, hex values, or system internals
7. Keep the response SHORT - one line if possible, max 2-3 sentences

Examples:
- Query: "what's the volume?" Raw: "output volume:75, input volume:50" → "Your volume is set to 75%"
- Query: "battery status?" Raw: "Now drawing from 'AC Power'\n-InternalBattery-0 (id=123)\t95%; charged; 0:00 remaining" → "Battery is at 95%, fully charged, connected to AC power"
- Query: "what time is it?" Raw: "Sun Jan  4 10:30:45 PST 2026" → "It's 10:30 AM PST on Sunday, January 4, 2026"

If you cannot extract relevant information, respond with: "Could not find [what user asked for] in the output."
"""),
            HumanMessage(content=f"User's question: {original_query}\n\nRaw command output:\n{raw_output[:2000]}")
        ])
        
        try:
            chain = prompt | self.formatter_llm
            response = chain.invoke({})
            formatted = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # If formatter returns something useful, use it
            if formatted and len(formatted) > 5 and "Could not find" not in formatted:
                return formatted
            
            # Fallback: return first meaningful line of output
            lines = [l.strip() for l in raw_output.split('\n') if l.strip() and not l.startswith('{') and not l.startswith('|')]
            if lines:
                return lines[0][:200]
            
            return raw_output[:200] + "..." if len(raw_output) > 200 else raw_output
            
        except Exception:
            # If formatting fails, return truncated raw output
            return raw_output[:300] + "..." if len(raw_output) > 300 else raw_output
    
    def _execute_with_tools(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute query using tools - LLM decides which tools to use based on semantic understanding.
        
        NO HARDCODED PATTERNS - the LLM analyzes the task semantically to determine:
        1. Is this a LOCAL system query or EXTERNAL information query?
        2. What SPECIFIC information is the user asking for?
        3. Which tool and command/query would retrieve that information?
        """
        context = context or {}
        
        # Let the LLM understand the task and decide which tools to use
        # No hardcoded patterns - the LLM generalizes based on context
        prompt = self._create_prompt(task, context)
        chain = prompt | self.llm
        
        messages = []
        
        # Add conversation history to messages for context preservation
        conversation_history = context.get("conversation_history", [])
        if conversation_history:
            for entry in conversation_history[-6:]:  # Last 3 exchanges (6 messages)
                role = entry.get("role", "user")
                content = entry.get("content", "")
                if role in ["user", "user_clarification"]:
                    messages.append(HumanMessage(content=content))
                elif role == "assistant" and content:
                    messages.append(AIMessage(content=content))
        
        max_iterations = 5
        iteration = 0
        last_tool_succeeded = False  # Track if we got any successful tool result
        self._run_shell_failures = 0  # Reset failure counter for new task
        
        # Store task for reference in error messages
        self._current_task = task
        
        while iteration < max_iterations:
            if iteration > 0:
                print(f"  🔄 Retry attempt {iteration + 1}/{max_iterations}...")
            
            response = chain.invoke({"messages": messages})
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            messages.append(HumanMessage(content=task if iteration == 0 else "Continue"))
            messages.append(response)
            
            # Extract tool calls - let LLM decide what tools to use
            tool_calls = self._extract_tool_calls(response_text)
            
            # If no tool calls detected, ask LLM to reconsider with semantic understanding
            if not tool_calls and iteration == 0:
                print(f"  ⚠️  No tool call detected, prompting LLM to use tools...")
                # Let LLM understand context semantically - no specific command hints
                messages.append(HumanMessage(content="You MUST call a tool. For local system info (this computer), use: run_shell(command=\"your_command_here\"). For internet queries, use: web_search(query=\"your_query_here\"). Analyze the task and call the appropriate tool NOW."))
                iteration += 1
                continue
            
            # If no tool calls on retry, LLM might be giving up - force it to try again or use web search
            if not tool_calls and iteration > 0:
                print(f"  ⚠️  LLM responded without tool call on retry {iteration}...")
                if self._run_shell_failures >= 2:
                    print(f"  🔄 Suggesting web search fallback...")
                    messages.append(HumanMessage(content=f"You haven't called a tool. Since previous commands failed on {self.os_info['os']}, use web_search to find 'how to list running apps on {self.os_info['os']} terminal'. Then use what you learn."))
                else:
                    messages.append(HumanMessage(content=f"You must call a tool. Previous command failed - try a DIFFERENT approach. This is {self.os_info['os']}."))
                iteration += 1
                continue
            
            # If tool call has empty kwargs (no command), ask LLM to be more specific
            if tool_calls and tool_calls[0].get("tool") == "run_shell" and not tool_calls[0].get("kwargs", {}).get("command"):
                messages.append(HumanMessage(content="You called run_shell but did not include a command. You MUST specify the command parameter. Use: run_shell(command=\"your_shell_command_here\"). Determine the correct command for the user's request based on the operating system (macOS/Linux/Windows) and call the tool with that command."))
                iteration += 1
                continue
            
            if tool_calls:
                tool_call_succeeded = False  # Initialize before loop
                run_shell_failures = getattr(self, '_run_shell_failures', 0)
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool")
                    tool_kwargs = tool_call.get("kwargs", {})  # Use kwargs, not args
                    
                    # Log the actual command being tried for debugging
                    if tool_name == "run_shell":
                        cmd = tool_kwargs.get("command", "")
                        print(f"  🔧 Calling tool: {tool_name}")
                        print(f"     📝 Command: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
                    else:
                        print(f"  🔧 Calling tool: {tool_name}")
                    
                    result = self._execute_tool(tool_name, **tool_kwargs)
                    
                    if result.get("status") == "error":
                        error_msg = result.get('message', '')
                        print(f"  ❌ Tool error: {error_msg}")
                        
                        # For codebase-related errors (like encoding issues in tools.py), raise exception to trigger self-healing
                        if "codec can't decode" in error_msg or "UnicodeDecodeError" in error_msg or "encoding" in error_msg.lower():
                            # This is a codebase issue - raise exception to trigger self-healing
                            raise RuntimeError(f"Tool execution failed due to codebase issue: {error_msg}")
                        
                        # For tool execution errors that indicate agent mistakes, self-heal immediately
                        # This provides full autonomy - agent fixes its own mistakes without prompts
                        
                        # Check if it's a parameter error that was already fixed
                        if "Parameter error (fixed" in error_msg:
                            # Parameter was fixed but still failed - ask LLM to reconsider
                            messages.append(AIMessage(content=f"Tool {tool_name} had a parameter error that was automatically fixed, but it still failed: {error_msg}. Please check the tool signature and try again with correct parameters."))
                            iteration += 1
                            continue
                        
                        # Check if it's a parameter error that can be fixed
                        if "unexpected keyword argument" in error_msg or "got an unexpected keyword argument" in error_msg:
                            # This should have been auto-fixed by base_agent, but if it wasn't, we'll handle it
                            # Don't give up - this is fixable
                            messages.append(AIMessage(content=f"Tool {tool_name} had a parameter error: {error_msg}. The system should auto-fix this. If you see this message, the error handling needs improvement."))
                            iteration += 1
                            continue
                        
                        # For run_shell errors on local queries, self-heal by detecting wrong commands
                        if tool_name == "run_shell":
                            # Detect common command errors and auto-correct
                            command = tool_kwargs.get("command", "")
                            exit_code = result.get("exit_code", -1)
                            stderr = result.get("stderr", "")
                            
                            # Check if command doesn't exist (Errno 2) - guide LLM to think about OS
                            if "[Errno 2]" in error_msg and "No such file or directory" in error_msg:
                                import re
                                cmd_match = re.search(r"No such file or directory: ['\"]([^'\"]+)['\"]", error_msg)
                                wrong_cmd = cmd_match.group(1) if cmd_match else command
                                
                                # Guide LLM to generalize based on OS understanding
                                os_hint = f"IMPORTANT: This is {self.os_info['os']}, not Linux. "
                                os_hint += f"The command '{wrong_cmd}' does not exist on {self.os_info['os']}. "
                                os_hint += "Think about what tools ARE available on this OS for this type of query. "
                                if self.os_info['os'] == 'macOS':
                                    os_hint += "macOS uses: osascript (AppleScript) for GUI/system queries, pmset for power, defaults for preferences, and standard Unix commands."
                                elif self.os_info['os'] == 'Linux':
                                    os_hint += "Linux uses: GNU tools like amixer, upower, free, etc."
                                
                                messages.append(AIMessage(content=f"Tool {tool_name} failed: {os_hint} Determine the correct approach for {self.os_info['os']}."))
                                iteration += 1
                                continue
                            
                            # Check for quote/syntax errors
                            if "No closing quotation" in error_msg or "syntax error" in error_msg.lower():
                                os_hint = ""
                                if self.os_info['os'] == 'macOS':
                                    os_hint = "For macOS volume: osascript -e 'output volume of (get volume settings)' (note the correct AppleScript syntax with single quotes around the whole expression)."
                                
                                messages.append(AIMessage(content=f"Tool {tool_name} failed: syntax error in command. {os_hint} Fix the command syntax and try again."))
                                iteration += 1
                                continue
                            
                            # Check for command execution failure (exit code != 0)
                            if exit_code != 0:
                                # Track run_shell failures for fallback logic
                                self._run_shell_failures = getattr(self, '_run_shell_failures', 0) + 1
                                print(f"  📊 Shell failure count: {self._run_shell_failures}")
                                
                                # After 2 failed attempts, suggest using web search to find the right command
                                if self._run_shell_failures >= 2:
                                    print(f"  🔄 Multiple command failures ({self._run_shell_failures}) - using web search fallback")
                                    search_query = f"how to list running apps on {self.os_info['os']} using terminal command"
                                    messages.append(AIMessage(content=f"Commands keep failing on {self.os_info['os']}. Use web_search(query=\"{search_query}\") to find the correct command. Do NOT guess - search and learn first."))
                                    # Don't increment iteration here - let the outer loop handle it
                                    break  # Break to let LLM try web search
                                
                                # Extract error details to help LLM understand and generalize
                                error_details = stderr if stderr else error_msg
                                
                                # Build helpful context - include the ACTUAL error from stderr
                                os_context = f"This is {self.os_info['os']}. "
                                os_context += f"The command '{command}' failed. "
                                if stderr:
                                    os_context += f"Error output: {stderr[:300]}. "
                                os_context += f"Try a COMPLETELY DIFFERENT approach. Do NOT repeat the same command."
                                
                                messages.append(AIMessage(content=f"Tool {tool_name} failed: {os_context}"))
                                # Don't increment iteration here - let the outer loop handle it
                                break  # Break to retry with new approach
                            
                            # For other run_shell errors, let LLM understand context semantically
                            messages.append(AIMessage(content=f"Tool {tool_name} returned error: {error_msg}. The command was: {command}. Understand the query semantically: Is this about local system information or external information? If external, use web_search. If local, determine the correct run_shell command for the information the user is seeking."))
                            iteration += 1
                            continue
                        
                        # For other errors, let LLM decide
                        messages.append(AIMessage(content=f"Tool {tool_name} returned error: {error_msg}. Please reconsider the approach."))
                        iteration += 1
                        break  # Break out of tool_calls loop to retry
                    
                    # Check if approval is required
                    if result.get("status") == "pending_approval":
                        print(f"  ⏸️  Tool '{tool_name}' requires approval")
                        approval_id = result.get("approval_id")
                        return {
                            "status": "needs_approval",
                            "reason": "tool_approval_required",
                            "message": result.get("message", f"Tool '{tool_name}' requires approval"),
                            "approval_id": approval_id,
                            "tool_name": tool_name,
                            "agent": self.agent_name,
                            "task_type": "query"
                        }
                    
                    # If we got here, tool succeeded (status != "error")
                    tool_call_succeeded = True
                    last_tool_succeeded = True  # Track for the whole execution
                    
                    # Handle run_shell results - return directly for local queries
                    if tool_name == "run_shell":
                        
                        # Check exit code - if non-zero, this should have been handled in error handling above
                        # But double-check here as a safety net
                        exit_code = result.get("exit_code", 0)
                        if exit_code != 0:
                            # Command failed - this should have been caught above, but handle it here as fallback
                            stderr = result.get("stderr", "")
                            command = tool_kwargs.get("command", "")
                            messages.append(AIMessage(content=f"Tool {tool_name} failed: command '{command}' returned exit code {exit_code}. Error: {stderr}. This is a LOCAL system query - determine the correct command to get the information the user is asking for. Think about what command would actually work for this specific query."))
                            iteration += 1
                            continue
                        
                        # Try multiple ways to get output (handle both wrapped and unwrapped results)
                        output = (
                            result.get("stdout", "") or 
                            result.get("output", "") or
                            (result.get("result", {}) if isinstance(result.get("result"), dict) else {}).get("stdout", "") or
                            (result.get("original", {}) if isinstance(result.get("original"), dict) else {}).get("stdout", "")
                        )
                        
                        if output:
                            # Format the output to extract relevant information
                            original_query = getattr(self, '_current_task', task)
                            formatted_output = self._format_output(output, original_query)
                            
                            return {
                                "status": "success",
                                "message": formatted_output,
                                "agent": self.agent_name,
                                "task_type": "query"
                            }
                        else:
                            stderr = (
                                result.get("stderr", "") or
                                (result.get("result", {}) if isinstance(result.get("result"), dict) else {}).get("stderr", "") or
                                (result.get("original", {}) if isinstance(result.get("original"), dict) else {}).get("stderr", "")
                            )
                            if stderr:
                                return {
                                    "status": "error",
                                    "message": f"Command error: {stderr}",
                                    "agent": self.agent_name,
                                    "task_type": "query"
                                }
                            return {
                                "status": "error",
                                "message": f"Command executed but no output. Result keys: {list(result.keys())}",
                                "agent": self.agent_name,
                                "task_type": "query"
                            }
                    
                    # Add tool result to messages for LLM to process
                    # Format result nicely for LLM
                    if tool_name == "web_search":
                        # Extract key info from web_search result
                        answer = result.get("answer", "")
                        sources = result.get("sources", [])
                        content = result.get("content", "")
                        
                        # Check for stale dates in search results (always check, not keyword-based)
                        import re
                        from datetime import datetime
                        
                        # Check for dates in answer
                        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(20\d{2})'
                        date_matches = re.findall(date_pattern, answer)
                        
                        today = datetime.now()
                        current_year = today.year
                        
                        stale_detected = False
                        for month, year_str in date_matches:
                            try:
                                year = int(year_str)
                                # If date is in future (more than current year) or very old, it's stale
                                if year > current_year + 1 or year < current_year - 1:
                                    stale_detected = True
                                    break
                            except:
                                pass
                        
                        if stale_detected:
                            # Information is stale - try to extract current info from content
                            
                            # Look for current/live indicators in content (let LLM understand what's "current")
                            if content:
                                # Extract relevant parts from content that might contain current info
                                lines = content.split('\n')
                                relevant_lines = []
                                for l in lines:
                                    l_lower = l.lower()
                                    # Look for indicators of current information (generalized, not keyword-matched)
                                    if len(l.strip()) > 10 and not l_lower.startswith(('http', 'www', 'source')):
                                        cleaned = l.strip()
                                        cleaned = ' '.join(cleaned.split())
                                        if cleaned:
                                            relevant_lines.append(cleaned)
                                
                                if relevant_lines:
                                    answer = "\n".join(relevant_lines[:5])
                                else:
                                    # No current info - return clear error
                                    source_urls = [s.get('url', s) if isinstance(s, dict) else s for s in sources[:3]]
                                    return {
                                        "status": "error",
                                        "message": f"Unable to find current information. The search returned information from a past or future date (dates: {', '.join([f'{m} {y}' for m, y in date_matches[:2]])}).\n\nFor the most current information, please check these sources:\n" + "\n".join([f"• {url}" for url in source_urls]),
                                        "agent": self.agent_name,
                                        "task_type": "query",
                                        "sources": sources
                                    }
                            else:
                                # No content - return error with sources
                                source_urls = [s.get('url', s) if isinstance(s, dict) else s for s in sources[:3]]
                                return {
                                    "status": "error",
                                    "message": f"Unable to find current information. The search returned information that appears to be from a past or future date.\n\nFor the most current information, please check these sources:\n" + "\n".join([f"• {url}" for url in source_urls]),
                                    "agent": self.agent_name,
                                    "task_type": "query",
                                    "sources": sources
                                }
                        
                        # Clean up answer - remove redundant information and format nicely
                        if answer:
                            # Remove duplicate information
                            lines = answer.split('\n')
                            seen = set()
                            cleaned_lines = []
                            for line in lines:
                                line_stripped = line.strip()
                                if not line_stripped:
                                    continue
                                line_lower = line_stripped.lower()
                                # Skip lines that are just metadata or noise
                                if any(skip in line_lower for skip in ["note:", "warning:", "⚠️", "for the most current"]):
                                    continue
                                if line_lower and line_lower not in seen and len(line_stripped) > 10:
                                    seen.add(line_lower)
                                    cleaned_lines.append(line_stripped)
                            
                            # Join and clean up
                            answer = "\n".join(cleaned_lines)
                            # Remove excessive whitespace
                            answer = ' '.join(answer.split())
                            # Add back line breaks for readability (max 100 chars per line)
                            if len(answer) > 100:
                                words = answer.split()
                                lines = []
                                current_line = []
                                current_len = 0
                                for word in words:
                                    if current_len + len(word) + 1 > 100 and current_line:
                                        lines.append(' '.join(current_line))
                                        current_line = [word]
                                        current_len = len(word)
                                    else:
                                        current_line.append(word)
                                        current_len += len(word) + 1
                                if current_line:
                                    lines.append(' '.join(current_line))
                                answer = '\n'.join(lines)
                        
                        # For simple queries, return the answer directly
                        # Let LLM determine if it's a simple query - no keyword matching
                        if answer and iteration == 0 and len(answer) < 500:
                            # Return answer directly without LLM processing
                            return {
                                "status": "success",
                                "message": answer,
                                "agent": self.agent_name,
                                "task_type": "query",
                                "sources": sources[:3] if sources else []
                            }
                        
                        if answer:
                            result_summary = f"Web search result:\n{answer}"
                            if sources:
                                result_summary += f"\n\nSources: {', '.join([s.get('url', '') for s in sources[:3]])}"
                        else:
                            result_summary = json.dumps(result, indent=2)
                    else:
                        result_summary = json.dumps(result, indent=2)
                    
                    messages.append(AIMessage(content=f"Tool {tool_name} result: {result_summary}"))
                
                # If a tool call failed and we're retrying, don't continue to next iteration yet
                if not tool_call_succeeded:
                    iteration += 1
                    continue
                
                # After tool execution, explicitly ask LLM to provide answer
                messages.append(HumanMessage(content="Based on the tool results above, provide a clear and direct answer to the user's question. Extract the key information and present it clearly. Do not include code examples or tool call syntax - just provide the answer."))
                
                # Continue loop to let LLM process results and generate answer
                iteration += 1
                continue
            
            # No tool calls - check if we have a final answer
            # Only return success if we actually got a successful tool result
            # Or if this is a direct answer without needing tools
            if last_tool_succeeded or (iteration == 0 and len(response_text) > 50):
                # Clean up the answer - remove code blocks and tool call suggestions
                answer = response_text
                
                # Remove code blocks
                import re
                answer = re.sub(r'```[^`]*```', '', answer, flags=re.DOTALL)
                answer = re.sub(r'`[^`]*`', '', answer)
                
                # Remove tool call patterns like "web_search(...)" or "print(web_search(...))"
                answer = re.sub(r'print\s*\([^)]*web_search[^)]*\)', '', answer, flags=re.IGNORECASE)
                answer = re.sub(r'web_search\s*\([^)]*\)', '', answer, flags=re.IGNORECASE)
                
                # Remove lines that are just tool code
                lines = answer.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Skip lines that are just tool calls or code
                    if re.match(r'^(print|web_search|tool_|def |import |from )', line, re.IGNORECASE):
                        continue
                    cleaned_lines.append(line)
                
                answer = '\n'.join(cleaned_lines).strip()
                
                # If answer is too short or empty, use original response
                if len(answer) < 20:
                    answer = response_text
                    # Still clean it
                    answer = re.sub(r'```[^`]*```', '', answer, flags=re.DOTALL)
                
                return {
                    "status": "success",
                    "message": answer,
                    "agent": self.agent_name,
                    "task_type": "query"
                }
            
            iteration += 1
        
        # Return final response from last iteration
        # Only return success if we actually got a successful tool result
        if messages and last_tool_succeeded:
            # Find the last AI response (not a HumanMessage we added)
            for i in range(len(messages) - 1, -1, -1):
                if hasattr(messages[i], 'content'):
                    content = messages[i].content
                    # Skip our own prompts
                    if "Based on the tool results above" in content:
                        continue
                    if content == "Continue":
                        continue
                    if content == task:
                        continue
                    # This should be an actual response
                    return {
                        "status": "success",
                        "message": content,
                        "agent": self.agent_name,
                        "task_type": "query"
                    }
        
        # If no tool succeeded, return error with helpful message
        return {
            "status": "error",
            "message": f"Unable to complete the task after {iteration} attempts. The commands tried did not succeed on this system ({self.os_info.get('os', 'Unknown OS')}). Please try rephrasing your request or check system permissions.",
            "agent": self.agent_name,
            "task_type": "query"
        }


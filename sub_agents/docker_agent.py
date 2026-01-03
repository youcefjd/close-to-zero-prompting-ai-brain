"""Docker Sub-Agent: Handles all Docker-related tasks autonomously."""

from typing import Dict, Any, Optional
from sub_agents.base_agent import BaseSubAgent
from langchain_core.messages import HumanMessage, AIMessage
from emergency_stop import get_emergency_stop, EmergencyStopException
import json
import re
import asyncio


class DockerAgent(BaseSubAgent):
    """Specialized agent for Docker operations."""
    
    def __init__(self):
        system_prompt = """You are a Docker expert agent. You handle:
- Container management (start, stop, restart, inspect)
- Docker Compose operations
- Container logs and debugging
- Image management
- Network and volume operations

You work AUTONOMOUSLY - analyze the task, use Docker tools, and complete it without asking for permission."""
        
        super().__init__("DockerAgent", system_prompt)
    
    async def execute_async(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Docker-related task asynchronously."""
        print(f"🐳 DockerAgent: {task}")
        
        # Check emergency stop before starting
        self.emergency_stop.check_and_raise()
        
        # Reset cost tracker for new task
        self.cost_tracker.reset_task()
        
        messages = []
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            # Check emergency stop at start of each iteration
            self.emergency_stop.check_and_raise()
            
            # Check cost limits
            limit_check = self.cost_tracker.check_limits()
            if not limit_check["allowed"]:
                return {
                    "status": "error",
                    "message": f"Cost limit exceeded: {limit_check['reason']}",
                    "agent": self.agent_name,
                    "cost_summary": self.cost_tracker.get_summary()
                }
            
            # Invoke LLM asynchronously
            try:
                response_text = await self._invoke_llm_async(messages + [HumanMessage(content=task if iteration == 0 else "Continue")])
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"LLM call failed: {str(e)}",
                    "agent": self.agent_name
                }
            
            messages.append(HumanMessage(content=task if iteration == 0 else "Continue"))
            messages.append(AIMessage(content=response_text))
            
            # Extract tool calls from response
            tool_calls = self._extract_tool_calls(response_text)
            
            if not tool_calls:
                # Check if task is complete
                if "success" in response_text.lower() or "complete" in response_text.lower():
                    return {
                        "status": "success",
                        "message": response_text,
                        "agent": self.agent_name
                    }
                iteration += 1
                continue
            
            # Execute tool calls
            results = []
            for tool_call in tool_calls:
                tool_name = tool_call["tool"]
                kwargs = tool_call.get("kwargs", {})
                
                print(f"  🔧 Executing: {tool_name}({kwargs})")
                result = self._execute_tool(tool_name, **kwargs)
                results.append(result)
                
                if result.get("status") == "error":
                    # Try alternative approach
                    print(f"  ⚠️  Tool failed: {result.get('message')}")
            
            # Sanitize and add results to context for next iteration
            # Results are already sanitized by _execute_tool, but double-check
            sanitized_results = []
            for result in results:
                if isinstance(result, dict):
                    # Results should already be sanitized, but ensure no secrets leaked
                    result_str = json.dumps(result, default=str)
                    if self.sanitizer.has_secrets(result_str):
                        # Re-sanitize if somehow secrets got through
                        print(f"  ⚠️  WARNING: Secrets detected in tool results - re-sanitizing")
                        result = self.sanitizer.sanitize_dict(result, context="tool_results")
                    sanitized_results.append(result)
                else:
                    sanitized_results.append(result)
            
            # Final check before adding to context
            results_str = json.dumps(sanitized_results, indent=2, default=str)
            if self.sanitizer.has_secrets(results_str):
                print(f"  ⚠️  WARNING: Secrets still detected after sanitization - applying additional sanitization")
                sanitization = self.sanitizer.sanitize(results_str, context="final_context")
                messages.append(AIMessage(content=f"Tool execution results: {sanitization.sanitized_content}"))
            else:
                messages.append(AIMessage(content=f"Tool execution results: {results_str}"))
            
            # Check if we're done
            if all(r.get("status") == "success" for r in results):
                return {
                    "status": "success",
                    "message": "Task completed successfully",
                    "results": results,
                    "agent": self.agent_name
                }
            
            iteration += 1
        
        return {
            "status": "partial",
            "message": "Task partially completed after max iterations",
            "agent": self.agent_name,
            "cost_summary": self.cost_tracker.get_summary()
        }
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Docker-related task (synchronous wrapper for async)."""
        # Run async version in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute_async(task, context))
                    return future.result()
            else:
                return loop.run_until_complete(self.execute_async(task, context))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.execute_async(task, context))


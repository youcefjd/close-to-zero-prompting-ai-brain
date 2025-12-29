"""Docker Sub-Agent: Handles all Docker-related tasks autonomously."""

from typing import Dict, Any, Optional
from sub_agents.base_agent import BaseSubAgent
from langchain_core.messages import HumanMessage, AIMessage
import json
import re


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
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute Docker-related task."""
        print(f"🐳 DockerAgent: {task}")
        
        # Analyze task and plan
        prompt = self._create_prompt(task, context)
        chain = prompt | self.llm
        
        messages = []
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            response = chain.invoke({"messages": messages})
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            messages.append(HumanMessage(content=task if iteration == 0 else "Continue"))
            messages.append(response)
            
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
            
            # Add results to context for next iteration
            messages.append(AIMessage(content=f"Tool execution results: {json.dumps(results, indent=2)}"))
            
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
            "agent": self.agent_name
        }


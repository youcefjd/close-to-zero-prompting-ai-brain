"""Autonomous Orchestrator: Coordinates all agents without human prompts."""

from typing import Dict, Any, List, Optional
from autonomous_router import AutonomousRouter
from sub_agents.docker_agent import DockerAgent
from sub_agents.config_agent import ConfigAgent
from fact_checker import FactChecker
from emergency_stop import get_emergency_stop, EmergencyStopException
import json


class AutonomousOrchestrator:
    """Main orchestrator that coordinates all agents autonomously."""
    
    def __init__(self):
        self.router = AutonomousRouter()
        self.fact_checker = FactChecker()
        self.emergency_stop = get_emergency_stop()
        
        # Initialize sub-agents
        from sub_agents.consulting_agent import ConsultingAgent
        
        self.agents = {
            "docker": DockerAgent(),
            "config": ConfigAgent(),
            "consulting": ConsultingAgent(),
            "cloud": ConsultingAgent(),  # Cloud questions use consulting agent
            # Add more agents as they're implemented
            # "python": PythonAgent(),
            # "homeassistant": HomeAssistantAgent(),
            # "system": SystemAgent(),
            # "general": GeneralAgent(),
        }
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a task fully autonomously."""
        # Check emergency stop before starting
        self.emergency_stop.check_and_raise()
        
        print(f"\n{'='*70}")
        print(f"🧠 AUTONOMOUS EXECUTION: {task}")
        print(f"{'='*70}\n")
        
        # Step 1: Check if similar task was solved before
        similar_solution = self.fact_checker.retrieve_solution(task)
        if similar_solution:
            print(f"📚 Found similar solution in memory:")
            print(f"   {similar_solution.get('summary', '')[:100]}...")
            # Use as context but still execute to verify
        
        # Step 2: Route task
        routing = self.router.route(task)
        
        if routing.get("action") == "ask_human":
            return {
                "status": "needs_human",
                "question": routing.get("question"),
                "reason": "Task requires clarification"
            }
        
        # Check if this is a design task (complex system building)
        primary_agent_name = routing.get("primary_agent", "general")
        if primary_agent_name == "design":
            # Use autonomous builder for design tasks
            from autonomous_builder import AutonomousBuilder
            builder = AutonomousBuilder(environment=context.get("environment", "production") if context else "production")
            return builder.build_system(task)
        
        # Check if this is a consultation task (no execution needed)
        task_type = routing.get("analysis", {}).get("task_type") or routing.get("task_type", "execution")
        if task_type == "consultation":
            print("\n💡 This is a consultation/analysis task - providing analysis without execution\n")
        
        # Step 3: Execute with primary agent
        
        if primary_agent_name not in self.agents:
            # Fallback to general agent or create on-the-fly
            print(f"⚠️  Agent '{primary_agent_name}' not available, using fallback")
            return self._execute_fallback(task, context)
        
        agent = self.agents[primary_agent_name]
        
        # Step 5: Pre-execution fact check
        fact_check = self.fact_checker.pre_execution_check(task, routing.get("analysis", {}))
        if fact_check.get("should_abort"):
            return {
                "status": "aborted",
                "reason": fact_check.get("reason"),
                "suggestion": fact_check.get("suggestion")
            }
        
        # Step 6: Execute
        # Check emergency stop before execution
        self.emergency_stop.check_and_raise()
        
        print(f"🚀 Executing with {agent.agent_name}...\n")
        try:
            # Try async execution first, fall back to sync
            if hasattr(agent, 'execute_async'):
                import asyncio
                try:
                    result = asyncio.run(agent.execute_async(task, context))
                except RuntimeError:
                    # Event loop already running, use sync
                    result = agent.execute(task, context)
            else:
                result = agent.execute(task, context)
        except EmergencyStopException as e:
            return {
                "status": "stopped",
                "reason": str(e),
                "message": "Execution halted by emergency stop"
            }
        except Exception as e:
            # Check if it's a cost limit error
            if "Cost limit exceeded" in str(e) or "cost limit" in str(e).lower():
                return {
                    "status": "error",
                    "reason": "cost_limit_exceeded",
                    "message": str(e),
                    "cost_summary": getattr(agent, 'cost_tracker', {}).get_summary() if hasattr(agent, 'cost_tracker') else {}
                }
            raise
        
        # Step 7: Post-execution validation
        if result.get("status") == "success":
            validation = self.fact_checker.post_execution_validation(task, result)
            if not validation.get("is_valid"):
                print(f"⚠️  Validation warning: {validation.get('warning')}")
            
            # Store solution in memory
            self.fact_checker.store_solution(task, result)
            
            # Record routing success for learning
            if hasattr(self.router, 'semantic_router') and self.router.semantic_router:
                self.router.semantic_router.record_success(
                    task=task,
                    agent_used=primary_agent_name,
                    success=True
                )
        elif result.get("status") == "error":
            # Record routing failure for learning
            if hasattr(self.router, 'semantic_router') and self.router.semantic_router:
                self.router.semantic_router.record_success(
                    task=task,
                    agent_used=primary_agent_name,
                    success=False
                )
        
        # Step 8: Handle secondary agents if needed
        secondary_agents = routing.get("secondary_agents", [])
        if secondary_agents and result.get("status") == "success":
            for sec_agent_name in secondary_agents:
                if sec_agent_name in self.agents:
                    print(f"\n🔄 Executing secondary agent: {sec_agent_name}")
                    sec_result = self.agents[sec_agent_name].execute(task, {"primary_result": result})
                    if sec_result.get("status") != "success":
                        result["secondary_errors"] = result.get("secondary_errors", [])
                        result["secondary_errors"].append({
                            "agent": sec_agent_name,
                            "error": sec_result.get("message")
                        })
        
        return result
    
    def _execute_fallback(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Fallback execution when specialized agent not available."""
        # Use the base LangGraph agent as fallback
        try:
            from agent_enhanced import create_agent_graph, AgentState
            from langchain_core.messages import HumanMessage
            
            graph = create_agent_graph()
            initial_state: AgentState = {
                "messages": [HumanMessage(content=task)],
                "current_plan": "",
                "code_snippet": "",
                "file_path": "",
                "execution_output": {},
                "iteration_count": 0,
                "error_history": [],
                "attempted_fixes": [],
                "complexity_level": 0,
                "fact_check_results": [],
                "validation_results": []
            }
            
            final_state = graph.invoke(initial_state)
            
            return {
                "status": "success",
                "message": "Task completed using fallback agent",
                "agent": "FallbackAgent",
                "result": final_state
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fallback execution failed: {str(e)}"
            }


def main():
    """Main entry point for autonomous execution."""
    import sys
    
    orchestrator = AutonomousOrchestrator()
    
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("Enter task (or 'exit' to quit):")
        task = input("> ").strip()
        if not task or task.lower() == "exit":
            return
    
    result = orchestrator.execute(task)
    
    print(f"\n{'='*70}")
    print("📊 EXECUTION RESULT")
    print(f"{'='*70}")
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("status") == "needs_human":
        print(f"\n❓ Human input needed: {result.get('question')}")
    elif result.get("status") == "success":
        print("\n✅ Task completed autonomously!")
    else:
        print(f"\n⚠️  Task status: {result.get('status')}")


if __name__ == "__main__":
    main()


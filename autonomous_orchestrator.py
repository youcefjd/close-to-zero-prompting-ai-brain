"""Autonomous Orchestrator: Coordinates all agents without human prompts."""

from typing import Dict, Any, List, Optional
from autonomous_router import AutonomousRouter
from sub_agents.docker_agent import DockerAgent
from sub_agents.config_agent import ConfigAgent
from fact_checker import FactChecker
from emergency_stop import get_emergency_stop, EmergencyStopException
import json
import asyncio


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
                try:
                    # Check if event loop is already running
                    loop = asyncio.get_running_loop()
                    # If we get here, loop is running - need to use sync or create task
                    # For now, fall back to sync to avoid nesting issues
                    result = agent.execute(task, context)
                except RuntimeError:
                    # No event loop running, create one
                    result = asyncio.run(agent.execute_async(task, context))
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
            
            # Attempt self-healing for codebase errors
            try:
                from self_healing import get_self_healing_system
                import traceback
                
                stack_trace = traceback.format_exc()
                healing_system = get_self_healing_system()
                
                healing_result = healing_system.detect_and_heal(
                    error=e,
                    stack_trace=stack_trace,
                    context={
                        "task": task,
                        "agent": agent.agent_name,
                        "environment": context.get("environment", "production") if context else "production"
                    }
                )
                
                if healing_result.success:
                    print(f"\n✅ SELF-HEALING SUCCESS: {healing_result.message}")
                    # Retry execution after healing
                    try:
                        if hasattr(agent, 'execute_async'):
                            try:
                                loop = asyncio.get_running_loop()
                                result = agent.execute(task, context)
                            except RuntimeError:
                                result = asyncio.run(agent.execute_async(task, context))
                        else:
                            result = agent.execute(task, context)
                        
                        # If retry succeeds, return success
                        if result.get("status") == "success":
                            result["self_healed"] = True
                            result["healing_details"] = {
                                "issue_type": healing_result.issue.issue_type if healing_result.issue else None,
                                "fix_applied": healing_result.fix_applied
                            }
                            return result
                    except Exception as retry_error:
                        print(f"  ⚠️  Retry after healing failed: {retry_error}")
                        # Fall through to return error
                
                elif healing_result.issue_detected:
                    print(f"\n🔍 SELF-HEALING DETECTED ISSUE: {healing_result.message}")
                    if healing_result.fix_proposed and not healing_result.fix_applied:
                        if "approval" in healing_result.message.lower():
                            return {
                                "status": "needs_approval",
                                "reason": "self_healing_approval_required",
                                "message": healing_result.message,
                                "healing_details": {
                                    "issue_type": healing_result.issue.issue_type if healing_result.issue else None,
                                    "approval_id": next((c.get("approval_id") for c in healing_result.changes if c.get("type") == "approval_requested"), None)
                                }
                            }
            except Exception as healing_error:
                print(f"  ⚠️  Self-healing system error: {healing_error}")
                # Fall through to raise original error
            
            # If self-healing didn't work or wasn't applicable, raise original error
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
        
        # Step 8: Handle secondary agents if needed (parallelize if async)
        secondary_agents = routing.get("secondary_agents", [])
        if secondary_agents and result.get("status") == "success":
            # Collect async-capable agents for parallel execution
            async_agents = []
            sync_agents = []
            
            for sec_agent_name in secondary_agents:
                if sec_agent_name in self.agents:
                    sec_agent = self.agents[sec_agent_name]
                    if hasattr(sec_agent, 'execute_async'):
                        async_agents.append((sec_agent_name, sec_agent))
                    else:
                        sync_agents.append((sec_agent_name, sec_agent))
            
            # Execute async agents in parallel
            if async_agents:
                async def execute_secondary_async():
                    tasks = [
                        agent.execute_async(task, {"primary_result": result})
                        for _, agent in async_agents
                    ]
                    return await asyncio.gather(*tasks, return_exceptions=True)
                
                try:
                    # Try to get running loop
                    loop = asyncio.get_running_loop()
                    # If loop is running, we can't use asyncio.run, so execute sequentially
                    # This is a limitation - ideally the orchestrator would be async too
                    for sec_agent_name, sec_agent in async_agents:
                        print(f"\n🔄 Executing secondary agent: {sec_agent_name}")
                        sec_result = sec_agent.execute(task, {"primary_result": result})
                        if sec_result.get("status") != "success":
                            result["secondary_errors"] = result.get("secondary_errors", [])
                            result["secondary_errors"].append({
                                "agent": sec_agent_name,
                                "error": sec_result.get("message")
                            })
                except RuntimeError:
                    # No loop running, can parallelize
                    print(f"\n🔄 Executing {len(async_agents)} secondary agents in parallel...")
                    async_results = asyncio.run(execute_secondary_async())
                    
                    for (sec_agent_name, _), sec_result in zip(async_agents, async_results):
                        if isinstance(sec_result, Exception):
                            result["secondary_errors"] = result.get("secondary_errors", [])
                            result["secondary_errors"].append({
                                "agent": sec_agent_name,
                                "error": str(sec_result)
                            })
                        elif isinstance(sec_result, dict) and sec_result.get("status") != "success":
                            result["secondary_errors"] = result.get("secondary_errors", [])
                            result["secondary_errors"].append({
                                "agent": sec_agent_name,
                                "error": sec_result.get("message")
                            })
            
            # Execute sync agents sequentially
            for sec_agent_name, sec_agent in sync_agents:
                print(f"\n🔄 Executing secondary agent: {sec_agent_name}")
                sec_result = sec_agent.execute(task, {"primary_result": result})
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


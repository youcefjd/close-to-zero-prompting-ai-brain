"""Autonomous Router: Intelligently routes tasks to specialized sub-agents without prompts."""

from typing import Dict, Any, List, Optional, Literal
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from semantic_router import get_semantic_router
import json
import re


class AutonomousRouter:
    """Routes tasks to appropriate sub-agents based on task analysis."""
    
    # Available sub-agents
    SUB_AGENTS = {
        "docker": "DockerAgent - Handles container management, docker-compose, container operations",
        "config": "ConfigAgent - Handles YAML, JSON, configuration files, Home Assistant config",
        "python": "PythonAgent - Handles Python scripts, code generation, debugging",
        "homeassistant": "HomeAssistantAgent - Handles HA integrations, entities, automations, services",
        "system": "SystemAgent - Handles file operations, shell commands, system-level tasks",
        "cloud": "ConsultingAgent - Handles cloud architecture, EKS, EMR, ACK, infrastructure decisions",
        "consulting": "ConsultingAgent - Handles analysis, comparison, recommendations, architectural decisions",
        "design": "DesignConsultant - Handles complex system design with Q&A, options, and resource planning",
        "general": "GeneralAgent - Handles tasks that don't fit other categories"
    }
    
    def __init__(self, use_semantic: bool = True):
        self.llm = ChatOllama(model="gemma3:4b", temperature=0.3)
        self.routing_history = []  # Learn from routing decisions
        self.use_semantic = use_semantic
        self.semantic_router = get_semantic_router() if use_semantic else None
        
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze task to determine complexity, domain, and required sub-agents."""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous task router with semantic understanding.

PRINCIPLES:
1. Understand the semantic meaning and intent of the user's task
2. Generalize understanding to similar tasks
3. Route based on what the user is trying to accomplish, not surface patterns

ROUTING:
- Understand if the task is a QUESTION/INFORMATION REQUEST (consultation) or ACTION/EXECUTION REQUEST (execution)
- Select the appropriate agent based on domain understanding:
  * consulting: ALL questions, information queries, analysis - including queries about local system (battery, disk, memory, etc.) and external information (sports, news, facts, etc.)
  * config: Creating/editing configuration files (YAML, JSON, etc.)
  * docker: Container operations (list, start, stop, etc.)
  * python: Code generation/execution
  * system: System-level operations (execution, not queries)
  * design: BUILDING systems from scratch (k8s clusters, applications, assistants, infrastructure, etc.) - asks clarifying questions then builds

CRITICAL ROUTING RULES:
- If the user is ASKING FOR INFORMATION → "consulting" (handles local system queries with run_shell and external queries with web_search)
- If the user wants to BUILD/CREATE something from scratch → "design" (will ask clarifying questions then build)
- If the user wants to EXECUTE operations → appropriate agent (docker, config, python, system)
- "design" agent: Handles complex system building (k8s clusters, applications, assistants, infrastructure) - asks clarifying questions when needed, then builds autonomously

- Generalize your understanding to handle ANY task type - read/write, local/external, execution/research, analysis/design

Respond ONLY with valid JSON:
{
    "task_type": "execution|consultation",
    "primary_agent": "docker|config|python|homeassistant|system|cloud|general|consulting|design",
    "secondary_agents": [],
    "complexity": "simple|medium|complex",
    "needs_clarification": false,
    "clarification_question": null,
    "required_tools": ["tool1", "tool2"],
    "estimated_steps": 1,
    "confidence": 0.9
}

CRITICAL: 
- Information queries (even about local system) → consulting
- BUILDING/CREATING systems from scratch (k8s clusters, applications, assistants, infrastructure) → design (will ask clarifying questions then build)
- Simple execution tasks → appropriate agent (docker, config, python, system)
- The system has FULL AUTONOMY - it can execute, build, create, analyze, research - ANY operation"""),
            HumanMessage(content=task)
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        # Extract JSON from response
        content = response.content if hasattr(response, 'content') else str(response)
        
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                
                # Trust LLM routing - no hardcoded overrides
                # The LLM should understand context and route correctly
                
                return analysis
            except Exception:
                # LLM response parsing failed - use fallback routing
                pass
        
        # Fallback: Simple keyword-based routing
        return self._fallback_routing(task)
    
    def _fallback_routing(self, task: str) -> Dict[str, Any]:
        """Minimal fallback routing - default to consulting when LLM fails."""
        # Minimal fallback - default to consulting for safety
        # LLM should handle routing, this is only for catastrophic failures
        return {
            "task_type": "consultation",
            "primary_agent": "consulting",
            "secondary_agents": [],
            "complexity": "medium",
            "needs_clarification": False,
            "clarification_question": None,
            "required_tools": [],
            "estimated_steps": 1,
            "confidence": 0.5  # Low confidence - LLM failed
        }
    
    def route(self, task: str) -> Dict[str, Any]:
        """Route task to appropriate sub-agent(s)."""
        # ALWAYS use LLM analysis first (semantic understanding)
        analysis = self.analyze_task(task)
        
        # Trust LLM routing - no keyword-based overrides
        # The LLM should understand semantic meaning and route correctly
        
        # Check if clarification is needed
        if analysis.get("needs_clarification"):
            return {
                "action": "ask_human",
                "question": analysis.get("clarification_question", "Need clarification on this task."),
                "analysis": analysis
            }
        
        # Route to primary agent - trust LLM's understanding
        primary = analysis.get("primary_agent", "general")
        
        # Build routing plan
        routing_plan = {
            "action": "execute",
            "primary_agent": primary,
            "secondary_agents": analysis.get("secondary_agents", []),
            "task": task,
            "analysis": analysis,
            "autonomous": True  # Proceed without prompts
        }
        
        # Store in history for learning
        self.routing_history.append({
            "task": task,
            "routing": routing_plan,
            "timestamp": str(__import__("datetime").datetime.now())
        })
        
        return routing_plan


if __name__ == "__main__":
    router = AutonomousRouter()
    
    # Test routing
    test_tasks = [
        "Add a new Docker service for Redis to docker-compose.yml",
        "Create a Python script to backup Home Assistant config",
        "Fix the YouTube Music integration error in Home Assistant",
        "Improve the system performance"  # Should ask for clarification
    ]
    
    for task in test_tasks:
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}")
        result = router.route(task)
        print(json.dumps(result, indent=2))


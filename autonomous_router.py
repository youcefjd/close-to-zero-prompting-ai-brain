"""Autonomous Router: Intelligently routes tasks to specialized sub-agents without prompts."""

from typing import Dict, Any, List, Optional, Literal
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
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
        "general": "GeneralAgent - Handles tasks that don't fit other categories"
    }
    
    def __init__(self):
        self.llm = ChatOllama(model="llama3.1:latest", temperature=0.3)
        self.routing_history = []  # Learn from routing decisions
        
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze task to determine complexity, domain, and required sub-agents."""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous task router. Analyze the user's task and determine:
1. Task type: "execution" (do something) OR "consultation" (analyze/compare/recommend)
2. Primary domain (docker, config, python, homeassistant, system, cloud, general, consulting)
3. Secondary domains (if task spans multiple)
4. Complexity level (simple, medium, complex)
5. Whether human clarification is needed (only for: ambiguous requirements, missing auth, major architectural decisions)
6. Required tools/capabilities

Respond ONLY with valid JSON:
{
    "task_type": "execution|consultation",
    "primary_agent": "docker|config|python|homeassistant|system|cloud|general|consulting",
    "secondary_agents": ["agent1", "agent2"],
    "complexity": "simple|medium|complex",
    "needs_clarification": false,
    "clarification_question": null,
    "required_tools": ["tool1", "tool2"],
    "estimated_steps": 3,
    "confidence": 0.9
}

TASK TYPE DETECTION:
- "execution": Task asks to DO something (create, fix, deploy, run, etc.)
- "consultation": Task asks to ANALYZE, COMPARE, ASSESS, RECOMMEND, EVALUATE (no execution needed)

DOMAIN DETECTION:
- "cloud": EKS, EMR, ACK, AWS, Kubernetes, Terraform, infrastructure decisions
- "consulting": Analysis, comparison, recommendations, architectural decisions
- "docker": Container operations, docker-compose
- "config": YAML, JSON, configuration files
- "python": Python scripts, code generation
- "homeassistant": HA integrations, entities, automations
- "system": File operations, shell commands
- "general": Fallback

CRITICAL: Only set needs_clarification=true if:
- Task is genuinely ambiguous (e.g., "improve performance" without context)
- Authentication credentials are missing and required
- Major architectural decision needed (e.g., "redesign the system")

For consultation tasks, route to "consulting" agent which provides analysis without execution.
Otherwise, proceed autonomously."""),
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
                return analysis
            except:
                pass
        
        # Fallback: Simple keyword-based routing
        return self._fallback_routing(task)
    
    def _fallback_routing(self, task: str) -> Dict[str, Any]:
        """Fallback routing based on keywords."""
        task_lower = task.lower()
        
        # Check for consultation/analysis tasks first
        consultation_keywords = ["assess", "compare", "recommend", "evaluate", "analysis", "which is better", "should i use", "better suited"]
        is_consultation = any(kw in task_lower for kw in consultation_keywords)
        
        primary = "general"
        if is_consultation:
            # Check for cloud-specific consultation
            if any(kw in task_lower for kw in ["eks", "emr", "ack", "aws", "kubernetes", "terraform", "cloud", "infrastructure"]):
                primary = "cloud"
            else:
                primary = "consulting"
        elif any(kw in task_lower for kw in ["docker", "container", "compose", "image"]):
            primary = "docker"
        elif any(kw in task_lower for kw in ["yaml", "json", "config", "configuration", "home assistant", "ha"]):
            primary = "config"
        elif any(kw in task_lower for kw in ["python", "script", "code", "function", "class"]):
            primary = "python"
        elif any(kw in task_lower for kw in ["integration", "entity", "automation", "service", "homeassistant"]):
            primary = "homeassistant"
        elif any(kw in task_lower for kw in ["file", "directory", "shell", "command", "system"]):
            primary = "system"
        elif any(kw in task_lower for kw in ["eks", "emr", "ack", "aws", "kubernetes", "terraform"]):
            primary = "cloud"
        
        return {
            "task_type": "consultation" if is_consultation else "execution",
            "primary_agent": primary,
            "secondary_agents": [],
            "complexity": "medium",
            "needs_clarification": False,
            "clarification_question": None,
            "required_tools": [],
            "estimated_steps": 3,
            "confidence": 0.7
        }
    
    def route(self, task: str) -> Dict[str, Any]:
        """Route task to appropriate sub-agent(s)."""
        analysis = self.analyze_task(task)
        
        # Check if clarification is needed
        if analysis.get("needs_clarification"):
            return {
                "action": "ask_human",
                "question": analysis.get("clarification_question", "Need clarification on this task."),
                "analysis": analysis
            }
        
        # Route to primary agent
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


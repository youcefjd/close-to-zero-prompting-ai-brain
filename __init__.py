"""Close-to-Zero Prompting AI Brain

An autonomous, self-evolving agent system that minimizes human intervention.

Quick Start:
    >>> from ai_brain import BaseSubAgent
    >>>
    >>> class MyAgent(BaseSubAgent):
    ...     def execute(self, task, context=None):
    ...         return {"status": "success", "message": "Task completed"}
    >>>
    >>> agent = MyAgent("My Agent", "You are a helpful assistant")
    >>> result = agent.execute("Hello world")

Main Components:
    - BaseSubAgent: Base class for all agents
    - AutonomousRouter: Routes tasks to specialized agents
    - AutonomousOrchestrator: Coordinates multi-agent execution
    - Tools: Docker, HomeAssistant, WebSearch, GitHub integrations
"""

__version__ = "0.1.0"
__author__ = "Youcef Djeddar"

# Core exports
from sub_agents import BaseSubAgent, DockerAgent, ConfigAgent, ConsultingAgent
from autonomous_router import AutonomousRouter
from autonomous_orchestrator import AutonomousOrchestrator
from governance import Governance
from fact_checker import FactChecker
from auth_broker import AuthBroker

__all__ = [
    # Core agent framework
    "BaseSubAgent",
    "DockerAgent",
    "ConfigAgent",
    "ConsultingAgent",

    # Orchestration
    "AutonomousRouter",
    "AutonomousOrchestrator",

    # Supporting systems
    "Governance",
    "FactChecker",
    "AuthBroker",

    # Metadata
    "__version__",
]

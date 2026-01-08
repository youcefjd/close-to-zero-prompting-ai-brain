"""Autonomous Engineer - Build features from request to production.

This module provides a multi-agent system that can:
- Understand feature requests
- Design architecture
- Implement backend and frontend code
- Write comprehensive tests
- Review for security and quality
- Deploy to staging/production
- Create pull requests

Usage:
    from autonomous_engineer import AutonomousEngineer

    engineer = AutonomousEngineer(
        repo_path="/path/to/project",
        github_token="your-token"
    )

    result = engineer.build_feature(
        "Add user authentication with OAuth"
    )

    print(f"PR created: {result['pr_url']}")

Agents:
    - OrchestratorAgent: Coordinates the entire workflow
    - ArchitectAgent: Designs the solution
    - BackendAgent: Implements server-side code
    - FrontendAgent: Implements client-side UI
    - TestAgent: Generates comprehensive tests
    - FixAgent: Addresses review feedback
    - DeployAgent: Handles deployment and PR creation
"""

from autonomous_engineer.orchestrator_agent import OrchestratorAgent
from autonomous_engineer.architect_agent import ArchitectAgent
from autonomous_engineer.backend_agent import BackendAgent
from autonomous_engineer.frontend_agent import FrontendAgent
from autonomous_engineer.test_agent import TestAgent
from autonomous_engineer.fix_agent import FixAgent
from autonomous_engineer.deploy_agent import DeployAgent

__all__ = [
    "OrchestratorAgent",
    "ArchitectAgent",
    "BackendAgent",
    "FrontendAgent",
    "TestAgent",
    "FixAgent",
    "DeployAgent",
]

__version__ = "0.1.0"

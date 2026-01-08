# Quick Start Guide - ai-brain

**ai-brain is NOW pip installable!** Build autonomous agents in minutes.

## Installation

```bash
# Navigate to ai-brain directory
cd close-to-zero-prompting-ai-brain

# Install in editable mode (recommended for development)
pip install -e .

# Or install normally
pip install .

# With GitHub support
pip install -e ".[github]"

# With Claude API support
pip install -e ".[anthropic]"

# With everything
pip install -e ".[all]"
```

## Verify Installation

```bash
python -c "from sub_agents import BaseSubAgent; print('✅ ai-brain installed successfully!')"
```

## Your First Agent (3 minutes)

### Step 1: Create a new file `my_agent.py`

```python
from sub_agents import BaseSubAgent

class HelloAgent(BaseSubAgent):
    """My first autonomous agent!"""

    def execute(self, task, context=None):
        # Your autonomous logic here
        print(f"🤖 {self.agent_name} executing: {task}")

        # Access LLM
        print(f"   Using LLM: {self.llm_type}")

        # Access tools
        print(f"   Available tools: {len(self.tools)}")

        return {
            "status": "success",
            "message": f"Completed: {task}",
            "agent": self.agent_name
        }

# Create and run the agent
if __name__ == "__main__":
    agent = HelloAgent(
        agent_name="Hello Agent",
        system_prompt="You are a friendly autonomous agent"
    )

    result = agent.execute("Say hello to the world!")
    print(f"\n✅ Result: {result}")
```

### Step 2: Run it

```bash
python my_agent.py
```

**Output:**
```
🤖 Hello Agent executing: Say hello to the world!
   Using LLM: ollama
   Available tools: 22

✅ Result: {'status': 'success', 'message': 'Completed: Say hello to the world!', 'agent': 'Hello Agent'}
```

**Congratulations! You just built your first autonomous agent!**

---

## Using Existing Agents

```python
from sub_agents import DockerAgent

# Use the built-in Docker agent
agent = DockerAgent()
result = agent.execute("list all running containers")
print(result)
```

---

## Using the Orchestrator

```python
from autonomous_orchestrator import AutonomousOrchestrator

# Create orchestrator
orchestrator = AutonomousOrchestrator()

# Execute task - automatically routes to correct agent!
result = orchestrator.execute("what docker containers are running?")
print(result)
```

Or from command line:
```bash
ai-brain "analyze my docker setup"
```

---

## Package Structure

```
ai-brain (pip package)
├── sub_agents/
│   ├── BaseSubAgent         # Base class for all agents
│   ├── DockerAgent          # Docker operations
│   ├── ConfigAgent          # Config file management
│   └── ConsultingAgent      # Analysis & recommendations
│
├── mcp_servers/
│   ├── docker_tools         # Docker MCP server
│   ├── homeassistant_tools  # Home Assistant MCP
│   ├── web_search_tools     # Web search MCP
│   └── github_tools         # GitHub MCP
│
├── autonomous_orchestrator  # Multi-agent coordinator
├── autonomous_router        # Intelligent task routing
├── governance              # Traffic Light Protocol
├── fact_checker            # Memory & validation
└── auth_broker             # Identity management
```

---

## Import Examples

```python
# Agents
from sub_agents import BaseSubAgent, DockerAgent, ConfigAgent, ConsultingAgent

# Orchestration
from autonomous_orchestrator import AutonomousOrchestrator
from autonomous_router import AutonomousRouter

# Tools
from mcp_servers.docker_tools import docker_ps, docker_logs
from mcp_servers.github_tools import github_get_pr_diff
from mcp_servers.web_search_tools import web_search

# Supporting systems
from governance import Governance
from fact_checker import FactChecker
from auth_broker import AuthBroker
```

---

## Real-World Agent Example

```python
from sub_agents import BaseSubAgent

class MonitorAgent(BaseSubAgent):
    """Monitors Docker containers for issues."""

    def execute(self, task, context=None):
        # Get all containers
        containers_result = self._execute_tool("docker_ps")

        if containers_result["status"] == "success":
            containers = containers_result.get("containers", [])

            # Check each container
            issues = []
            for container in containers:
                # Get logs
                logs_result = self._execute_tool(
                    "docker_logs",
                    container_name=container["name"],
                    tail=100
                )

                # Look for errors (simplified)
                if "error" in str(logs_result).lower():
                    issues.append({
                        "container": container["name"],
                        "issue": "Errors found in logs"
                    })

            return {
                "status": "success",
                "containers_checked": len(containers),
                "issues_found": len(issues),
                "issues": issues
            }
        else:
            return {
                "status": "error",
                "message": "Could not fetch containers"
            }

# Use it
if __name__ == "__main__":
    agent = MonitorAgent(
        "Monitor Agent",
        "You monitor Docker containers for problems"
    )

    result = agent.execute("check all containers")
    print(f"Checked {result['containers_checked']} containers")
    print(f"Found {result['issues_found']} issues")
```

---

## Next Steps

1. **Build your own agent** - Inherit from `BaseSubAgent`
2. **Use existing agents** - `DockerAgent`, `ConfigAgent`, etc.
3. **Add tools** - Create new MCP servers in `mcp_servers/`
4. **Orchestrate** - Use `AutonomousOrchestrator` for multi-agent workflows

---

## Environment Setup (Optional)

```bash
# For Claude API (instead of Ollama)
export ANTHROPIC_API_KEY="your-key"

# For GitHub integration
export GITHUB_TOKEN="your-token"

# For Home Assistant
export HA_TOKEN="your-ha-token"

# For web search
export TAVILY_API_KEY="your-key"
```

---

## Testing Your Installation

```python
# test_installation.py
from sub_agents import BaseSubAgent, DockerAgent
from autonomous_orchestrator import AutonomousOrchestrator

print("✅ All imports successful!")
print(f"✅ BaseSubAgent available")
print(f"✅ DockerAgent available")
print(f"✅ AutonomousOrchestrator available")
print("\n🎉 ai-brain is ready to use!")
```

Run:
```bash
python test_installation.py
```

---

## Troubleshooting

### Import errors?
```bash
# Make sure you're in the venv
pip show ai-brain

# Reinstall in editable mode
pip uninstall ai-brain
pip install -e .
```

### Ollama not running?
```bash
# Check if Ollama is running
ollama list

# If not, start it
# (Install from https://ollama.com if needed)
```

### Need help?
- Check `PACKAGE_README.md` for detailed docs
- See `PHASE_2_ROADMAP.md` for future features
- Look at `AI_BRAIN_CAPABILITY_ASSESSMENT.md` for architecture

---

**You're ready to build autonomous agents!**

Start with the examples above, then check out `NEXT_BREAKTHROUGH.md` for ambitious projects to build.

Happy autonomous coding! 🤖

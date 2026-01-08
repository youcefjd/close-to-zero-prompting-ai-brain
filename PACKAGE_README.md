# ai-brain - Autonomous Agent Framework

Build autonomous AI agents in minutes, not weeks.

## Quick Start

### Installation

```bash
# Local development (editable install)
pip install -e .

# From directory
pip install .

# With all optional dependencies
pip install ".[all]"

# With specific features
pip install ".[github]"      # GitHub integration
pip install ".[anthropic]"   # Claude API support
```

### Your First Agent

```python
from ai_brain import BaseSubAgent

class MyAgent(BaseSubAgent):
    """My custom autonomous agent."""

    def execute(self, task, context=None):
        # Your autonomous logic here
        self.llm  # Access to LLM
        self.tools  # Access to all tools

        # Use tools
        result = self._execute_tool("docker_ps")

        return {
            "status": "success",
            "message": "Task completed",
            "result": result
        }

# Create and run
agent = MyAgent(
    agent_name="My Agent",
    system_prompt="You are a helpful assistant that manages Docker containers"
)

result = agent.execute("List all running containers")
print(result)
```

### Using the Orchestrator

```bash
# Command line
ai-brain "what docker containers are running?"

# In Python
from ai_brain import AutonomousOrchestrator

orchestrator = AutonomousOrchestrator()
result = orchestrator.execute("analyze my kubernetes pods")
```

## What's Included

### Core Framework
- **BaseSubAgent**: Build custom agents
- **AutonomousRouter**: Smart task routing
- **AutonomousOrchestrator**: Multi-agent coordination
- **Governance**: Traffic Light Protocol (Green/Yellow/Red)
- **FactChecker**: Memory and validation

### Built-in Agents
- **DockerAgent**: Container management
- **ConfigAgent**: Configuration files (YAML, JSON)
- **ConsultingAgent**: Analysis and recommendations

### MCP Servers (Tools)
- **Docker**: ps, logs, exec, restart, inspect, compose
- **Home Assistant**: get_state, call_service, logs, search
- **Web Search**: Tavily AI integration
- **GitHub**: PRs, diffs, comments (optional: `pip install ".[github]"`)

## Features

### Phase 1 (Current - WORKING)
- ✅ Autonomous task execution
- ✅ Intelligent task routing
- ✅ Tool-augmented LLMs
- ✅ Multi-agent orchestration
- ✅ Clean, documented code

### Phase 2 (Planned - 9 weeks)
- ⏭️ Auto-detect Claude vs Ollama (Week 1-2)
- ⏭️ Output sanitization (remove secrets) (Week 3-4)
- ⏭️ Cost tracking and budget limits (Week 5)
- ⏭️ Context management (Week 6)
- ⏭️ Dynamic tool registry (Week 7-8)
- ⏭️ Emergency stop system (Week 9)

## Architecture

```
┌─────────────────────────────────────────┐
│ Layer 1: Foundation (Fixed Tools)      │
│ - MCP servers (Docker, HA, GitHub)     │
│ - Core tools (write_file, run_shell)   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Layer 2: Orchestration                  │
│ - AutonomousRouter                       │
│ - Governance Framework                   │
│ - FactChecker & Memory                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Layer 3: Your Custom Agents            │
│ - Inherit from BaseSubAgent             │
│ - Autonomous task execution             │
└─────────────────────────────────────────┘
```

## Examples

### Example 1: Custom Code Review Agent

```python
from ai_brain import BaseSubAgent
import subprocess

class CodeReviewAgent(BaseSubAgent):
    def execute(self, task, context=None):
        # Get git diff
        diff = subprocess.check_output(["git", "diff"]).decode()

        # Analyze with LLM
        prompt = f"Review this code:\n{diff}"
        # Agent logic here...

        return {"status": "success", "issues_found": 5}
```

### Example 2: Using Existing Agents

```python
from ai_brain import DockerAgent

agent = DockerAgent()
result = agent.execute("restart the nginx container")
# Automatically routes to docker_restart tool
```

### Example 3: Multi-Agent Workflow

```python
from ai_brain import AutonomousOrchestrator

orchestrator = AutonomousOrchestrator()

# Automatically routes to appropriate agents
result = orchestrator.execute(
    "check docker logs for errors and summarize"
)

# DockerAgent gets logs, ConsultingAgent analyzes
print(result)
```

## Requirements

- Python 3.9+
- Ollama (for local LLM) or Anthropic API key (for Claude)

## Environment Variables

```bash
# Optional: Use Claude instead of Ollama
export ANTHROPIC_API_KEY="your-key-here"

# Optional: Home Assistant integration
export HA_TOKEN="your-ha-token"

# Optional: Web search
export TAVILY_API_KEY="your-tavily-key"

# Optional: GitHub integration
export GITHUB_TOKEN="your-github-token"
```

## Development

### Install for development

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Format code

```bash
black .
```

## Documentation

- [Full Documentation](https://github.com/youcefjd/close-to-zero-prompting-ai-brain)
- [Architecture Deep Dive](ARCHITECTURE_DEEP_DIVE.md)
- [Phase 2 Roadmap](PHASE_2_ROADMAP.md)
- [Capability Assessment](AI_BRAIN_CAPABILITY_ASSESSMENT.md)

## Proven Track Record

**Built in 4 hours using ai-brain:**
- [Autonomous PR Reviewer](https://github.com/youcefjd/ai-pr-review)
- Monitors GitHub repos 24/7
- Reviews PRs autonomously
- Posts security analysis
- Detects SQL injection, XSS, command injection

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! See GitHub repository for details.

## Support

- Issues: [GitHub Issues](https://github.com/youcefjd/close-to-zero-prompting-ai-brain/issues)
- Discussions: [GitHub Discussions](https://github.com/youcefjd/close-to-zero-prompting-ai-brain/discussions)

---

**Built with ai-brain? Share your agent!**

From zero to autonomous in minutes. That's the power of ai-brain.

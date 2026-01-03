# Test Examples for Zero Prompting AI Brain

## Quick Start Test

Run the autonomous orchestrator with a test task:

```bash
python autonomous_orchestrator.py "Check if Docker is running and list all containers"
```

## Comprehensive Test Examples

### 1. Docker Operations (Tests: Routing, Tool Execution, Sanitization)

```bash
# Simple container check
python autonomous_orchestrator.py "List all running Docker containers"

# Container logs (will test PII sanitization if logs contain secrets)
python autonomous_orchestrator.py "Show me the last 50 lines of logs from the homeassistant container"

# Container management
python autonomous_orchestrator.py "Check the status of all Docker containers and restart any that are stopped"
```

### 2. File Operations (Tests: Tool Execution, Context Management)

```bash
# Create a configuration file
python autonomous_orchestrator.py "Create a docker-compose.yml file with a Redis service on port 6379"

# File analysis
python autonomous_orchestrator.py "Read the requirements.txt file and tell me what Python packages are needed"
```

### 3. Consultation Tasks (Tests: Semantic Routing, No Execution)

```bash
# Architecture consultation
python autonomous_orchestrator.py "Compare Docker Compose vs Kubernetes for running a small application with 3 services"

# Best practices
python autonomous_orchestrator.py "What are the best practices for securing Docker containers in production?"
```

### 4. Complex Multi-Step Tasks (Tests: All Features)

```bash
# Multi-step Docker setup
python autonomous_orchestrator.py "Create a docker-compose.yml file with a PostgreSQL database and a Python web service, then start the services"

# Configuration management
python autonomous_orchestrator.py "Check if there's a .env file, and if not, create one with placeholder values for DATABASE_URL and API_KEY"
```

### 5. Error Handling Tests (Tests: Error Recovery, Loop Detection)

```bash
# Intentional error to test recovery
python autonomous_orchestrator.py "Restart a container named 'nonexistent-container'"

# Invalid operation
python autonomous_orchestrator.py "Delete the file /etc/passwd"  # Should be blocked by safety checks
```

### 6. Semantic Routing Tests (Tests: Generalization)

```bash
# Paraphrased requests (tests semantic understanding)
python autonomous_orchestrator.py "I need to see what containers are currently active"
python autonomous_orchestrator.py "Display the status of my Docker containers"
python autonomous_orchestrator.py "What Docker containers do I have running?"

# Unseen task types
python autonomous_orchestrator.py "Help me set up a development environment with Node.js and PostgreSQL"
```

## Interactive Testing

### Using the Interactive Mode

```bash
python autonomous_orchestrator.py
```

Then enter tasks interactively:
```
> Check Docker containers
> Create a test.py file with a hello world function
> What's the difference between Docker and Podman?
> exit
```

### Using Meta-Agent (Self-Evolution)

```bash
python meta_agent.py "I need to check AWS costs but don't have an AWS tool"
```

This will test the meta-agent's ability to:
1. Detect missing tools
2. Generate new tool code
3. Request approval
4. Deploy new capabilities

## Testing Specific Features

### Test Emergency Stop

Terminal 1:
```bash
python autonomous_orchestrator.py "List all Docker containers and show detailed information for each"
```

Terminal 2 (while first is running):
```bash
python stop.py stop "Testing emergency stop"
python stop.py status
```

### Test Cost Tracking

```bash
# Run a task and check cost
python autonomous_orchestrator.py "Analyze the architecture of a microservices application with 5 services"
```

Then check `.cost_history.json` for cost tracking.

### Test Context Pruning

```bash
# Long conversation that will trigger context pruning
python autonomous_orchestrator.py "Create a complex docker-compose.yml with 10 services, then modify it to add health checks, then create a README explaining the setup"
```

### Test Semantic Routing

```bash
# These should route to the same agent despite different wording
python autonomous_orchestrator.py "Show me my Docker containers"
python autonomous_orchestrator.py "Display container status"
python autonomous_orchestrator.py "What containers are running?"
```

## Expected Behaviors

### Safety Features
- ✅ Tool outputs should be sanitized (no secrets in logs)
- ✅ Emergency stop should halt execution gracefully
- ✅ Dangerous commands should be blocked

### Stability Features
- ✅ Execution should be non-blocking (async)
- ✅ Context should be pruned if too large
- ✅ Cost limits should prevent runaway spending

### Generalization Features
- ✅ Similar tasks should route to same agent
- ✅ New tools should be discovered automatically
- ✅ Routing should improve over time (learning)

## Troubleshooting

### If Semantic Routing Doesn't Work

Install sentence-transformers:
```bash
pip install sentence-transformers
```

Or disable semantic routing:
```python
# In autonomous_router.py
router = AutonomousRouter(use_semantic=False)
```

### If Tools Aren't Discovered

Check that tools are in discoverable locations:
- `mcp_servers/*.py`
- `tools/*.py`
- Current directory `*.py`

### If Cost Tracking Shows 0

This is normal for Ollama (local, free). Cost tracking is more relevant for:
- OpenAI (paid API)
- Anthropic (paid API)

## Recommended First Test

Start with this simple test to verify everything works:

```bash
python autonomous_orchestrator.py "List all Docker containers and show their status"
```

This will test:
1. ✅ Routing (should route to DockerAgent)
2. ✅ Tool execution (docker_ps)
3. ✅ Output sanitization
4. ✅ Emergency stop checks
5. ✅ Cost tracking (even if $0 for Ollama)

## Advanced Test Scenarios

### Test Full Workflow

```bash
# 1. Create a service
python autonomous_orchestrator.py "Create a docker-compose.yml with a Redis service"

# 2. Start it
python autonomous_orchestrator.py "Start the Redis service using docker-compose"

# 3. Check it
python autonomous_orchestrator.py "Verify the Redis container is running and show its logs"

# 4. Consult on it
python autonomous_orchestrator.py "What are the best practices for running Redis in Docker?"
```

### Test Learning

Run the same type of task multiple times:
```bash
python autonomous_orchestrator.py "List Docker containers"
python autonomous_orchestrator.py "Show me my containers"
python autonomous_orchestrator.py "What containers are running?"
```

Then check routing history:
```python
from semantic_router import get_semantic_router
router = get_semantic_router()
insights = router.learn_from_history()
print(insights)
```


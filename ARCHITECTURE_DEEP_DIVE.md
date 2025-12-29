# Architecture Deep Dive: Close-to-Zero Prompting AI Brain

## System Architecture

### High-Level Overview

The system is built on three fundamental layers, each providing increasing levels of autonomy and capability:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                             │
│         "check s3 logs for errors"                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              META-AGENT (Orchestrator)                      │
│  - Request Classification                                   │
│  - Tool Discovery                                           │
│  - Self-Evolution Trigger                                   │
│  - Authentication Check                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────┐                  ┌───────────────────┐
│  AUTONOMOUS       │                  │   TOOLSMITH       │
│  ROUTER           │                  │   AGENT            │
│  - Route to       │                  │   - Generate      │
│    sub-agents     │                  │     MCP servers   │
│  - Determine      │                  │   - Validate      │
│    complexity     │                  │   - Deploy        │
└───────────────────┘                  └───────────────────┘
        ↓                                       ↓
┌─────────────────────────────────────────────────────────────┐
│              SPECIALIZED SUB-AGENTS                         │
│  - ConsultingAgent (Analysis)                             │
│  - DockerAgent (Containers)                                 │
│  - ConfigAgent (Configuration)                              │
│  - GeneralAgent (General tasks)                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              GOVERNANCE FRAMEWORK                           │
│  - Risk Assessment (Green/Yellow/Red)                      │
│  - Plan & Apply Pattern                                    │
│  - Approval Gates                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              MCP SERVERS (Tools)                           │
│  - docker_tools.py                                          │
│  - homeassistant_tools.py                                   │
│  - web_search_tools.py                                      │
│  - [Dynamically Generated Tools]                           │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. MetaAgent

**Purpose**: Main orchestrator that processes requests with self-evolution capability.

**Key Methods**:
- `process_request(request)`: Main entry point
- `_classify_request(request)`: Classifies intent and risk
- `_discover_tools()`: Scans for available tools
- `_deploy_mcp_server()`: Deploys new tools (MVP: process reload)

**State Management**:
- Tracks available tools
- Manages authentication state
- Coordinates with sub-agents

### 2. AutonomousRouter

**Purpose**: Intelligently routes tasks to specialized agents.

**Analysis Process**:
1. **Intent Detection**: Analysis, Drafting, Execution
2. **Complexity Assessment**: Simple, Medium, Complex
3. **Agent Selection**: Primary + Secondary agents
4. **Clarification Check**: Determines if human input needed

**Routing Logic**:
```python
if "assess" in task or "compare" in task:
    → ConsultingAgent
elif "docker" in task or "container" in task:
    → DockerAgent
elif "yaml" in task or "config" in task:
    → ConfigAgent
else:
    → GeneralAgent
```

### 3. GovernanceFramework

**Purpose**: Traffic Light Protocol for safe operations.

**Risk Levels**:

| Level | Color | Auto-Execute | Approval | Examples |
|-------|-------|--------------|----------|----------|
| Green | 🟢 | ✅ Yes | ❌ No | `docker_ps`, `ha_get_state`, `web_search` |
| Yellow | 🟡 | ⚠️ Dev/Staging | ✅ Production | `write_file`, `docker_exec` |
| Red | 🔴 | ❌ Never | ✅ Always | `docker_restart`, `deploy_mcp_server` |

**Plan & Apply Pattern**:
```
1. PLAN: Generate change plan
   - List all actions
   - Assess risk levels
   - Calculate risk summary

2. REVIEW: Human reviews plan
   - Check proposed changes
   - Understand impact
   - Approve or reject

3. APPLY: Execute after approval
   - Validate approval
   - Execute actions
   - Report results
```

### 4. AuthBroker

**Purpose**: Identity management with three patterns.

**Pattern 1: Host Inheritance**
```
Service: AWS, Kubernetes, Terraform
Mechanism: Agent inherits from host CLI credentials
Check: ~/.aws/credentials, ~/.kube/config
Prompt: "Run 'aws configure', then 'Ready'"
```

**Pattern 2: Secret Vault**
```
Service: Cookidoo, API keys
Mechanism: Environment variables in .env file
Check: os.getenv("KEY_NAME")
Prompt: "Run './scripts/add_secret.sh KEY_NAME'"
```

**Pattern 3: OAuth 2.0**
```
Service: Gmail, Calendar, Spotify
Mechanism: OAuth token in .secrets/
Check: .secrets/{service}_token.json
Prompt: "Click authorization link"
```

### 5. ToolsmithAgent

**Purpose**: Generates new MCP servers when tools are missing.

**Generation Process**:
1. **Detection**: Identifies missing tool from task
2. **Specification**: Creates tool spec with requirements
3. **Generation**: LLM generates MCP server code
4. **Validation**: Syntax check with `ast.parse()`
5. **Approval**: Requests approval (🟡 Yellow)
6. **Deployment**: Hot-reloads tool registry (🔴 Red)

**MVP Deployment**:
```python
# Not Docker containers (too complex)
# Instead: Process reload
import importlib
import sys

# Clear cached imports
modules_to_remove = [name for name in sys.modules.keys() 
                     if name.startswith('mcp_servers.')]
for module_name in modules_to_remove:
    del sys.modules[module_name]

# Force re-discovery on next import
# Tools are now available
```

### 6. FactChecker

**Purpose**: Validation, error learning, and loop prevention.

**Pre-Execution Validation**:
- Check file existence
- Verify command safety
- Validate parameters
- Check similar past failures

**Post-Execution Verification**:
- Verify file was created
- Check command output
- Validate results
- Record success/failure

**Memory System**:
```json
{
  "successes": [
    {
      "action_type": "write_file",
      "pattern": "created config file",
      "count": 5
    }
  ],
  "failures": [
    {
      "action_type": "docker_exec",
      "error": "container not found",
      "count": 3,
      "suggestions": ["Check container name", "Verify container is running"]
    }
  ]
}
```

### 7. Web Search Integration

**Purpose**: Access current information beyond knowledge cutoff.

**Flow**:
```
User: "What is the latest Kubernetes version?"
    ↓
Agent: Checks knowledge cutoff (March 2024)
    ↓
Agent: Determines need for current info
    ↓
Agent: Calls web_search("latest kubernetes version")
    ↓
Tavily API: Returns current information
    ↓
Agent: Synthesizes answer
```

**Privacy Filter**:
```python
blocked_keywords = [
    "password", "secret", "api key", "token", 
    "credential", "auth", "login", "ssh key"
]
```

## Data Flow

### Request Processing

```
1. User Request
   ↓
2. MetaAgent.process_request()
   ↓
3. Classification (Intent, Risk, Routing)
   ↓
4. Tool Discovery
   ↓
5. Missing Tool? → Toolsmith → Generate → Approve → Deploy
   ↓
6. Authentication Check → AuthBroker → User Action
   ↓
7. Route to Sub-Agent
   ↓
8. Governance Check → Plan & Apply
   ↓
9. Execute Tools
   ↓
10. Fact Check → Verify Results
   ↓
11. Return Response
```

### Self-Evolution Flow

```
1. Missing Tool Detected
   ↓
2. Toolsmith Generates Code (🟡 Yellow)
   ↓
3. User Approves Code
   ↓
4. Authentication Check
   ↓
5. User Authenticates
   ↓
6. Deployment (🔴 Red)
   ↓
7. User Approves Deployment
   ↓
8. Hot-Reload Tool Registry
   ↓
9. Tool Available
   ↓
10. Re-execute Original Request
```

## Security Architecture

### Defense in Depth

```
Layer 1: Privacy Filters
  - Block sensitive queries
  - Filter secrets from search

Layer 2: Authentication
  - Never ask for raw credentials
  - Use host inheritance
  - Secure secret storage

Layer 3: Governance
  - Risk-based classification
  - Approval gates
  - Plan & Apply pattern

Layer 4: Validation
  - Pre-execution checks
  - Post-execution verification
  - Memory-based learning
```

### Traffic Light Protocol

```
🟢 Green: Safe to execute
   - Read-only operations
   - No state changes
   - Idempotent

🟡 Yellow: Review before execute
   - Reversible changes
   - Draft operations
   - Auto-approve in dev

🔴 Red: Always require approval
   - Destructive operations
   - Production changes
   - New capabilities
```

## Memory and Learning

### Success Patterns
- Record successful actions
- Identify patterns
- Reuse successful approaches

### Failure Patterns
- Track error signatures
- Learn from mistakes
- Suggest fixes based on history

### Loop Prevention
- Track iteration count
- Detect repeated errors
- Stop after max attempts

## Extension Points

### Adding New Tools

1. **Create MCP Server**: `mcp_servers/my_tool_tools.py`
2. **Register in Governance**: Add to `governance.py`
3. **Add to Base Agent**: Update `sub_agents/base_agent.py`
4. **Update Tool Discovery**: Add to `MetaAgent._discover_tools()`

### Adding New Sub-Agents

1. **Create Agent Class**: Inherit from `BaseSubAgent`
2. **Implement `execute()` method**
3. **Register in Router**: Update `AutonomousRouter`
4. **Add to Orchestrator**: Update `AutonomousOrchestrator`

### Adding New Auth Patterns

1. **Update `AuthBroker._detect_auth_pattern()`**
2. **Add check method**: `_check_{pattern}_credentials()`
3. **Add error method**: `_raise_{pattern}_auth_error()`

## Performance Considerations

### Tool Discovery
- Cached on startup
- Refreshed after tool deployment
- Fast lookup via dictionary

### Memory System
- JSON file-based (simple)
- Can upgrade to database if needed
- Periodic cleanup of old entries

### Hot-Reload
- MVP: Process reload (fast)
- Future: Docker containers (isolated)

## Monitoring and Debugging

### Logs
- Request processing logs
- Tool execution logs
- Error logs
- Approval logs

### Memory Inspection
```bash
# View agent memory
cat .agent_memory.json | jq

# Check success patterns
cat .agent_memory.json | jq '.successes'

# Check failure patterns
cat .agent_memory.json | jq '.failures'
```

### Approval Inspection
```bash
# List pending approvals
python approve.py list

# View approval details
cat .agent_approvals.json | jq
```

## Future Enhancements

### Planned
- [ ] Docker container deployment for tools
- [ ] Database-backed memory system
- [ ] Real-time monitoring dashboard
- [ ] Multi-agent collaboration
- [ ] Advanced OAuth flows

### Under Consideration
- [ ] GraphQL API for tool discovery
- [ ] WebSocket for real-time updates
- [ ] Distributed agent network
- [ ] Advanced learning algorithms

---

This architecture enables **close-to-zero prompting** by making the agent autonomous, self-evolving, and secure.


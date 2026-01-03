# Governance Integration & Design Agent Routing

## Answer to Your Question

> "Is it general enough to invoke the design agent when needed, and other agents when design isn't needed, and it operates within the specified strict governance frame?"

## ✅ YES - Both Requirements Are Now Implemented!

### 1. Automatic Design Agent Routing ✅

The system now **automatically detects** when to use the design consultant:

**Router Detection:**
- Keywords: "build system", "create system", "design system", "from scratch", "microservices", "architecture"
- Routes to `"design"` agent when detected
- Falls back to other agents (docker, config, consulting, etc.) when design isn't needed

**Integration Points:**
1. **`autonomous_router.py`** - Detects design tasks and routes to `"design"` agent
2. **`autonomous_orchestrator.py`** - Automatically invokes `AutonomousBuilder` when routed to design agent
3. **Other agents** - Used normally when design isn't needed

**Example Flow:**
```
Task: "Build a microservices application"
  ↓
Router detects: "build" + "microservices" → "design" agent
  ↓
Orchestrator invokes: AutonomousBuilder.build_system()
  ↓
Design consultant workflow (Q&A, options, quotas, etc.)

Task: "Add Redis to docker-compose.yml"
  ↓
Router detects: "docker" + "compose" → "docker" agent
  ↓
Orchestrator invokes: DockerAgent.execute()
  ↓
Normal Docker agent execution
```

### 2. Strict Governance Enforcement ✅

Governance is now enforced at **every tool execution**:

**Integration Points:**
1. **`sub_agents/base_agent.py`** - `_execute_tool()` checks governance before every tool call
2. **`autonomous_builder.py`** - Uses governance-aware meta_agent
3. **All sub-agents** - Inherit governance checks from base_agent

**Governance Flow:**
```
Tool Execution Request
  ↓
BaseAgent._execute_tool()
  ↓
Governance.check_permission()
  ↓
🟢 GREEN: Auto-execute (read-only, safe)
🟡 YELLOW: Auto-approve in dev/staging, require approval in production
🔴 RED: Always require approval (never auto-approve)
  ↓
If requires approval:
  - Request approval
  - Return pending_approval status
  - Wait for human approval
  ↓
Execute tool (if approved)
  ↓
Sanitize output (PII, secrets)
```

## Implementation Details

### Router Changes

**`autonomous_router.py`:**
- Added `"design"` to `SUB_AGENTS`
- Added design detection keywords
- Routes to design agent when system building is detected

### Orchestrator Changes

**`autonomous_orchestrator.py`:**
- Checks if `primary_agent == "design"`
- Automatically invokes `AutonomousBuilder` for design tasks
- Falls back to normal agent execution for other tasks

### Base Agent Changes

**`sub_agents/base_agent.py`:**
- `_execute_tool()` now checks governance before execution
- Returns `pending_approval` status if approval needed
- Respects risk levels (Green/Yellow/Red)
- Enforces environment restrictions

### Autonomous Builder Changes

**`autonomous_builder.py`:**
- Initializes governance framework
- All tool executions go through base_agent (which enforces governance)
- Meta-agent respects governance when generating/deploying tools

## Governance Rules

### 🟢 GREEN Tools (Auto-execute)
- `docker_ps`, `docker_logs`, `docker_inspect`
- `ha_get_state`, `ha_get_logs`, `ha_search_logs`
- `web_search`
- **No approval needed** - fully autonomous

### 🟡 YELLOW Tools (Conditional)
- `write_file` - Auto-approve in dev/staging, require approval in production
- `docker_exec` - Auto-approve in dev/staging, require approval in production
- `ha_call_service` - Auto-approve in dev/staging, require approval in production

### 🔴 RED Tools (Always Require Approval)
- `docker_restart` - Never auto-approve
- `docker_compose_up` - Never auto-approve
- `run_shell` - Never auto-approve
- `deploy_mcp_server` - Never auto-approve (most dangerous)

## Examples

### Example 1: Design Task (Automatic Routing)

```python
orchestrator = AutonomousOrchestrator()
result = orchestrator.execute("Build a production-ready microservices application")
```

**What happens:**
1. Router detects "build" + "microservices" → routes to `"design"`
2. Orchestrator invokes `AutonomousBuilder.build_system()`
3. Design consultant asks questions, presents options
4. User selects option, provides quotas
5. System builds (all tool executions checked by governance)
6. Governance enforces approvals for Yellow/Red tools

### Example 2: Docker Task (Normal Routing)

```python
orchestrator = AutonomousOrchestrator()
result = orchestrator.execute("Add Redis service to docker-compose.yml")
```

**What happens:**
1. Router detects "docker" + "compose" → routes to `"docker"`
2. Orchestrator invokes `DockerAgent.execute()`
3. Docker agent executes (governance checks `write_file` - Yellow)
4. In production: Requires approval
5. In dev/staging: Auto-approves

### Example 3: Consultation Task

```python
orchestrator = AutonomousOrchestrator()
result = orchestrator.execute("Compare EKS vs EMR for data processing")
```

**What happens:**
1. Router detects "compare" → routes to `"consulting"`
2. Orchestrator invokes `ConsultingAgent.execute()`
3. Consulting agent provides analysis (no tool execution needed)
4. No governance checks (read-only analysis)

## Governance Enforcement Points

1. **Tool Execution** - Every tool call checks governance
2. **Environment Context** - Dev/staging vs production restrictions
3. **Risk Levels** - Green/Yellow/Red classification
4. **Approval Workflow** - Human-in-the-loop for risky operations
5. **Output Sanitization** - PII and secrets removed from outputs

## Testing

### Test Design Routing
```bash
python autonomous_orchestrator.py "Build a microservices application"
# Should route to design agent automatically
```

### Test Normal Routing
```bash
python autonomous_orchestrator.py "List Docker containers"
# Should route to docker agent
```

### Test Governance
```bash
# In production environment
python autonomous_orchestrator.py "Restart Docker container"
# Should require approval (RED tool)
```

## Conclusion

✅ **Design agent is automatically invoked when needed**
✅ **Other agents are used when design isn't needed**
✅ **Strict governance is enforced at every tool execution**
✅ **All operations respect risk levels and environment restrictions**

The system is now fully integrated with both automatic routing and strict governance enforcement!


# Governance Framework - Established Patterns

## Traffic Light Protocol

### 🟢 GREEN: Read-Only Operations
**Pattern**: NO approval needed - auto-execute

**Examples**:
- `docker_ps` - List containers
- `docker_logs` - Read logs
- `web_search` - Search the web
- `run_shell` with read-only commands:
  - `pmset -g batt` (battery status)
  - `df -h` (disk usage)
  - `osascript -e 'output volume of (get volume settings)'` (volume status)
  - `date` (current time)
  - Any command with read-only flags: `-g`, `-h`, `-l`, `-a`, `-i`, `show`, `list`, `status`, `info`, `get`, `output`

**Behavior**: 
- `allowed: True`
- `requires_approval: False`
- Execute immediately without prompting

---

### 🟡 YELLOW: Reversible Operations
**Pattern**: Auto-approve in dev/staging, require approval in production

**Examples**:
- `write_file` - Create/modify files
- `docker_exec` - Execute command in container
- `ha_call_service` - Call Home Assistant service

**Behavior**:
- In `dev`, `staging`, `local`: Auto-approve
- In `production`: Require approval

---

### 🔴 RED: Destructive Operations
**Pattern**: ALWAYS require approval (never auto-approve)

**Examples**:
- `docker_restart` - Restart container
- `docker_compose_up` - Start/update services
- `run_shell` with dangerous commands:
  - Commands with `rm`, `delete`, `format`, `wipe`, `>`, `>>`, `sudo`, `chmod`, `chown`
  - Commands that modify system state
- `deploy_mcp_server` - Deploy new capabilities
- `self_modify_codebase` - Self-healing (except in dev/staging for critical issues)

**Behavior**:
- `allowed: False`
- `requires_approval: True`
- Always prompt for approval

---

## Special Handling: `run_shell`

`run_shell` is registered as 🔴 RED by default, BUT:

1. **Read-Only Detection**: Special logic detects read-only commands and returns 🟢 GREEN
2. **Auto-Approval**: If detected as read-only, returns `requires_approval: False`
3. **No Prompting**: Read-only commands execute immediately without asking

**Detection Logic**:
- Checks if command matches safe read-only patterns
- Checks for read-only flags
- Checks for dangerous operations (if found, requires approval)
- If safe and read-only → 🟢 GREEN, no approval needed

---

## Clarification Requests

The system should ask for clarification when:
- Task is ambiguous
- Essential information is missing for building/creating
- User intent is unclear

**NOT** for:
- Read-only queries (execute directly)
- Simple information requests (execute directly)

---

## Key Principles

1. ✅ **Read-only = No approval** - Execute immediately
2. ✅ **Writes in dev/staging = Auto-approve** - Execute after auto-approval
3. ✅ **Writes in production = Require approval** - Prompt user
4. ✅ **Destructive = Always require approval** - Prompt user
5. ✅ **Clarification = Ask when ambiguous** - Prompt for missing info

---

## Current Implementation

- `governance.py`: Implements traffic light protocol
- `check_permission()`: Returns `allowed` and `requires_approval` based on risk level
- `base_agent.py`: Checks permission before executing tools
- `meta_agent.py`: Handles approval prompts interactively

**Flow**:
1. Agent calls `check_permission(tool_name, context)`
2. If `allowed: True` and `requires_approval: False` → Execute immediately
3. If `allowed: False` and `requires_approval: True` → Prompt for approval
4. If `allowed: False` and `requires_approval: False` → Error (not allowed)


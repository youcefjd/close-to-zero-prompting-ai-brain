# MCP Servers for Agent

This directory contains MCP (Model Context Protocol) tools that allow the agent to directly interact with Docker and Home Assistant without requiring manual copy-paste.

## Docker Tools

**Location:** `docker_tools.py`

**Available Tools:**
- `docker_ps(filter_name=None)` - List containers
- `docker_logs(container, tail=50)` - Get container logs
- `docker_exec(container, command)` - Execute command in container
- `docker_restart(container)` - Restart container
- `docker_inspect(container)` - Inspect container details
- `docker_compose_up(compose_file=None, service=None)` - Start services

**Example Usage:**
```python
from mcp_servers.docker_tools import docker_ps, docker_logs

# List all containers
result = docker_ps()
print(result["containers"])

# Get logs from homeassistant
result = docker_logs("homeassistant", tail=100)
print(result["logs"])
```

## Home Assistant Tools

**Location:** `homeassistant_tools.py`

**Available Tools:**
- `ha_get_state(entity_id)` - Get entity state
- `ha_call_service(domain, service, service_data=None, entity_id=None)` - Call service
- `ha_get_logs(tail=50)` - Get HA logs
- `ha_search_logs(search_term, tail=100)` - Search logs
- `ha_list_integrations()` - List all integrations
- `ha_get_config()` - Get HA configuration

**Setup:**
1. Get a Long-Lived Access Token from Home Assistant:
   - Go to Profile → Long-Lived Access Tokens
   - Create a new token
   - Copy the token

2. Set environment variable:
   ```bash
   export HA_TOKEN='your-token-here'
   ```

   Or initialize in code:
   ```python
   from mcp_servers.homeassistant_tools import init_ha_client
   init_ha_client(token="your-token-here")
   ```

**Example Usage:**
```python
from mcp_servers.homeassistant_tools import ha_get_state, ha_list_integrations

# Get entity state
result = ha_get_state("light.living_room")
print(result["state"])

# List integrations
result = ha_list_integrations()
print(result["integrations"])
```

## Agent Integration

The agent automatically detects when to use these tools based on the user's request:

**Docker Operations:**
- "Check if homeassistant container is running" → Uses `docker_ps()`
- "Get logs from homeassistant" → Uses `docker_logs()`
- "Restart the ps5-mqtt container" → Uses `docker_restart()`

**Home Assistant Operations:**
- "List all integrations" → Uses `ha_list_integrations()`
- "Check Home Assistant logs for errors" → Uses `ha_search_logs()`
- "Get state of light.living_room" → Uses `ha_get_state()`

## Testing

Run the test script:
```bash
python test_mcp_tools.py
```

This will test all MCP tools and show their output.

## Benefits

**Before MCP:**
- Agent: "Please run `docker logs homeassistant` and paste output"
- You: (manually runs command, copies output)
- Agent: (analyzes your paste)

**After MCP:**
- Agent: (automatically calls `docker_logs("homeassistant")`)
- Agent: (analyzes logs directly)
- You: (did nothing, agent did it all)

This makes the agent **truly autonomous** for infrastructure operations.


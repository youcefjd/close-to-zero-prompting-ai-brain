# Phase 4 Test Examples: Full Autonomy

## Quick Test: Verify Full Autonomy

### Test 1: Green Task (Fully Autonomous)
```bash
python meta_agent.py "List all Docker containers and show their status"
```
**Expected:** Executes immediately, no approval needed ✅

### Test 2: Yellow Task in Dev (Auto-Approved)
```bash
ENVIRONMENT=dev python meta_agent.py "Create a test configuration file"
```
**Expected:** Auto-approves and executes ✅

### Test 3: Yellow Task in Production (Requires Approval)
```bash
ENVIRONMENT=production python meta_agent.py "Create a test configuration file"
```
**Expected:** Requests approval ⏸️

### Test 4: Red Task (Always Requires Approval)
```bash
python meta_agent.py "Deploy a new MCP server for monitoring"
```
**Expected:** Always requests approval ⏸️

## System Building Tests

### Test: Build Complete System
```bash
python meta_agent.py "Build a monitoring system for Docker containers with:
- Log aggregation from all containers
- Error tracking and alerting
- Metrics collection
- Health check monitoring"
```

**What should happen:**
1. ✅ Designs architecture automatically
2. ✅ Discovers all needed tools (LLM-based)
3. ✅ Generates observability tools automatically
4. ✅ Generates tools in batch
5. ✅ Auto-approves green/yellow tools
6. ✅ Requests approval for red tools only
7. ✅ Builds the system

### Test: Automatic Observability
```bash
python meta_agent.py "I need to monitor my application logs and track errors automatically"
```

**What should happen:**
1. ✅ Discovers log locations automatically
2. ✅ Generates log aggregation tool
3. ✅ Generates error tracking tool
4. ✅ Auto-approves if green/yellow
5. ✅ Deploys and uses tools

## Advanced Tests

### Test: Complex Multi-Tool System
```bash
python meta_agent.py "Build a complete CI/CD pipeline with:
- Git integration
- Docker builds
- Kubernetes deployment
- Monitoring and alerting
- Log aggregation"
```

**Expected:** 
- Generates all tools automatically
- Auto-approves green/yellow
- Requests approval for red only

### Test: Unseen Task Type
```bash
python meta_agent.py "I need to integrate with a new API service that doesn't have tools yet"
```

**Expected:**
- LLM analyzes and determines needed tools
- Generates API integration tools
- Auto-approves if safe

## Verification

After running tests, verify:

1. **Check generated tools:**
   ```bash
   ls -la mcp_servers/*_tools.py
   ```

2. **Check approval history:**
   ```bash
   python approve.py list
   ```

3. **Check tool registry:**
   ```python
   from dynamic_tool_registry import get_tool_registry
   registry = get_tool_registry()
   print(registry.list_tools())
   ```

4. **Check routing history:**
   ```python
   from semantic_router import get_semantic_router
   router = get_semantic_router()
   insights = router.learn_from_history()
   print(insights)
   ```


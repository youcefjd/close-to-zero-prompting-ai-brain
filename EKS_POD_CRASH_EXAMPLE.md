# Example: EKS Pods Crashing - Brain Self-Evolution Flow

## Scenario

**Request**: "My pods in EKS cluster are crashing, check the logs and diagnose the issue"

## What Happens: Step-by-Step

### Step 1: Request Entry

```bash
python meta_agent.py "My pods in EKS cluster are crashing, check the logs and diagnose the issue"
```

### Step 2: Classification

```
======================================================================
STEP 1: CLASSIFICATION (The Sorting Hat)
======================================================================

   Intent: DIAGNOSIS
   Risk Level: 🟢 Green (read-only diagnosis)
   Routing: Docker/Diagnosis Agent
```

**Analysis**:
- Keywords: "check", "diagnose" → Diagnosis intent
- Risk: Read-only operations (checking logs) → 🟢 Green
- However, the **tool generation and deployment** will be 🟡 Yellow and 🔴 Red

### Step 3: Tool Discovery

```
======================================================================
STEP 2: TOOL DISCOVERY
======================================================================

   ⚠️  Missing Tool Detected:
      Tool: kubectl
      Description: Kubernetes cluster management
      Reason: Task requires Kubernetes operations
      Auth Required: kubernetes
```

**What Happens**:
- `ToolsmithAgent.detect_missing_tool()` scans request
- Finds keywords: "pods", "eks", "cluster", "kubernetes"
- Checks available tools: `MetaAgent._discover_tools()`
- Detects missing: `kubectl_tools` (not in `mcp_servers/`)
- Notes authentication requirement: `kubernetes` (needs kubeconfig)

### Step 4: Self-Evolution Trigger (🟡 Yellow - Drafting)

```
======================================================================
STEP 3: SELF-EVOLUTION (Toolsmith Agent)
======================================================================

   🔧 Agent realizes it needs: kubectl
   💡 Switching to 'Developer' mode...

🔧 Toolsmith Agent: Generating MCP server for kubectl
   Reason: Task requires Kubernetes operations

   ⏸️  Code generation requires approval
      Approval ID: xyz78901
      File: mcp_servers/kubectl_tools.py
      Risk Level: 🟡 YELLOW (drafting code)
```

**Risk Level**: 🟡 **YELLOW**
- **Why Yellow?**: Writing code is reversible (can delete file)
- **Action**: Drafting MCP server code
- **Approval**: Required in production, auto-approve in dev/staging

**Generated Code Preview**:
```python
"""MCP Server for kubectl: Kubernetes cluster management."""

import subprocess
from typing import Dict, Any, List

def kubectl_get_pods(namespace: str = "default") -> Dict[str, Any]:
    """Get pods in namespace."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        
        import json
        pods = json.loads(result.stdout)
        return {"status": "success", "pods": pods}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def kubectl_get_logs(pod_name: str, namespace: str = "default", tail: int = 100) -> Dict[str, Any]:
    """Get logs from a pod."""
    try:
        result = subprocess.run(
            ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(tail)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        
        return {"status": "success", "logs": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def kubectl_describe_pod(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
    """Describe a pod (events, status, etc.)."""
    # Implementation...
```

### Step 5: Approve Code Generation (🟡 Yellow)

```bash
python approve.py approve xyz78901
```

**Output**:
```
✅ Code generated: mcp_servers/kubectl_tools.py
   Risk: 🟡 YELLOW (drafting - reversible)
   Status: Approved
```

**What Happens**:
- `GovernanceFramework.approve()` marks approval
- Code file written to `mcp_servers/kubectl_tools.py`
- Status: 🟡 Yellow approved → Proceeds to next step

### Step 6: Authentication Check

```
======================================================================
STEP 3.5: AUTHENTICATION CHECK
======================================================================

   ⚠️  Authentication required for kubernetes
   📋 I need Kubernetes access. Please configure kubectl (e.g., 'aws eks update-kubeconfig --name <cluster>'), then tell me 'Ready'.
   💡 Action: aws eks update-kubeconfig --name <cluster-name>
```

**What Happens**:
- `AuthBroker.require_auth("kubernetes")` is called
- Checks `~/.kube/config` file
- Verifies with `kubectl cluster-info`
- If not found: Raises `NeedAuthError` with Host Inheritance pattern
- Pattern: **Host Inheritance** (like AWS - uses CLI credentials)

### Step 7: User Authenticates

```bash
$ aws eks update-kubeconfig --name my-cluster --region us-east-1
Added new context arn:aws:eks:us-east-1:123456789012:cluster/my-cluster

$ kubectl cluster-info
Kubernetes control plane is running at https://xxx.yl4.us-east-1.eks.amazonaws.com

$ # User types "Ready" in agent
```

**What Happens**:
- User configures kubeconfig via AWS CLI
- Credentials stored in `~/.kube/config`
- Agent retries authentication check
- `AuthBroker._check_host_credentials("kubernetes")` succeeds
- Authentication verified ✅

### Step 8: Deployment Approval (🔴 Red - Critical)

```
======================================================================
STEP 4: MVP DEPLOYMENT (Red Risk)
======================================================================

   🚀 Deploying MCP server: kubectl
   ⚠️  CRITICAL: This gives the agent new capabilities
   ⚠️  This is RED risk - requires explicit approval
   📝 MVP Approach: Restarting MCP process (not Docker container)

   ⏸️  Deployment requires approval
      Approval ID: abc45678
      Risk Level: 🔴 RED (critical - giving agent new powers)
```

**Risk Level**: 🔴 **RED**
- **Why Red?**: Deploying new tools gives the agent new capabilities
- **Action**: Hot-reloading tool registry (MVP: process reload)
- **Approval**: **ALWAYS REQUIRED** (even in dev/staging)
- **Reason**: This is the most dangerous operation - agent gains new powers

**What Happens**:
- `MetaAgent._deploy_mcp_server()` is called
- Validates Python syntax with `ast.parse()`
- Requests approval via `GovernanceFramework.request_approval()`
- Status: 🔴 Red → **Always requires human approval**

### Step 9: Approve Deployment (🔴 Red)

```bash
python approve.py approve abc45678
```

**Output**:
```
✅ Deployment approved - deploying (MVP method)...
   🔍 Step 1: Validating code syntax...
   ✅ Code syntax valid
   🔄 Step 2: Reloading MCP tool registry...
   ✅ Tool registry reloaded
   ✅ Step 3: Verifying tool availability...
   ✅ Tool kubectl is now available
```

**What Happens**:
- `MetaAgent._validate_python_code()` checks syntax ✅
- `MetaAgent._reload_mcp_tools()` clears `sys.modules` cache
- `MetaAgent._discover_tools()` refreshes tool list
- Tool `kubectl` is now available ✅

### Step 10: Execute Original Request

```
   ✅ Tool deployed and hot-reloaded (MVP: process reload)
   🔄 Re-running original request with new tool...

======================================================================
🧠 AUTONOMOUS EXECUTION: My pods in EKS cluster are crashing
======================================================================

💡 DockerAgent: Diagnosing EKS pod crashes
```

**What Happens**:
- `MetaAgent._process_with_tools()` re-executes original request
- Routes to `DockerAgent` (Kubernetes is container-related)
- Agent now has `kubectl_get_pods()` and `kubectl_get_logs()` tools

### Step 11: Tool Execution (🟢 Green - Read-Only)

```
📊 Using kubectl tools:
   1. kubectl_get_pods(namespace="default")
   2. kubectl_get_logs(pod_name="my-app-xxx", namespace="default")
   3. kubectl_describe_pod(pod_name="my-app-xxx", namespace="default")
```

**Risk Level**: 🟢 **GREEN**
- **Why Green?**: Read-only operations (getting logs, describing pods)
- **Action**: Auto-execute (no approval needed)
- **Tools Used**: 
  - `kubectl_get_pods()` → List all pods
  - `kubectl_get_logs()` → Get crash logs
  - `kubectl_describe_pod()` → Get events and status

**Execution**:
```python
# Agent calls tools automatically (🟢 Green - no approval)
pods_result = kubectl_get_pods(namespace="default")
# Returns: {"status": "success", "pods": [...]}

# Find crashing pods
crashing_pods = [p for p in pods_result["pods"]["items"] 
                 if p["status"]["phase"] != "Running"]

# Get logs for first crashing pod
logs_result = kubectl_get_logs(
    pod_name=crashing_pods[0]["metadata"]["name"],
    namespace="default",
    tail=200
)
# Returns: {"status": "success", "logs": "Error: OutOfMemoryError..."}
```

### Step 12: Diagnosis and Response

```
======================================================================
📊 DIAGNOSIS RESULTS
======================================================================

**Pod Status Analysis**

Found 3 pods in CrashLoopBackOff state:
1. my-app-deployment-abc123 (namespace: default)
2. my-app-deployment-def456 (namespace: default)
3. my-app-deployment-ghi789 (namespace: default)

**Error Analysis**

Pod: my-app-deployment-abc123
- Status: CrashLoopBackOff
- Last Error: OutOfMemoryError
- Logs: "java.lang.OutOfMemoryError: Java heap space"
- Restart Count: 15
- Events:
  - Back-off restarting failed container
  - Failed to pull image (retry)

**Root Cause**

1. **Memory Issue**: Pods are running out of memory (OOMKilled)
2. **Resource Limits**: Memory limits too low for workload
3. **Image Pull Issues**: Some pods failing to pull container image

**Recommendations**

1. Increase memory limits in deployment:
   ```yaml
   resources:
     limits:
       memory: "2Gi"  # Increase from 512Mi
   ```

2. Check image pull secrets for authentication issues

3. Review application memory usage patterns

4. Consider horizontal pod autoscaling (HPA)
```

## Risk Level Summary

| Step | Operation | Risk Level | Approval Required |
|------|-----------|------------|-------------------|
| 1 | Request Classification | 🟢 Green | ❌ No |
| 2 | Tool Discovery | 🟢 Green | ❌ No |
| 3 | Code Generation | 🟡 **YELLOW** | ✅ Yes (production) |
| 4 | Code Approval | 🟡 Yellow | ✅ User action |
| 5 | Authentication Check | 🟢 Green | ❌ No (user configures) |
| 6 | User Authentication | N/A | ✅ User action |
| 7 | Deployment | 🔴 **RED** | ✅ **ALWAYS** |
| 8 | Deployment Approval | 🔴 Red | ✅ User action |
| 9 | Tool Execution | 🟢 Green | ❌ No (read-only) |
| 10 | Diagnosis | 🟢 Green | ❌ No |

## Key Points

### ✅ Yes, the Brain Will:
1. **Detect missing tool** (kubectl for EKS)
2. **Generate MCP server code** (🟡 Yellow - requires approval)
3. **Check authentication** (kubernetes - Host Inheritance)
4. **Request deployment approval** (🔴 Red - always required)
5. **Execute diagnosis** (🟢 Green - read-only, auto-execute)

### 🟡 Yellow Risk: Code Generation
- **Reversible**: Can delete generated file
- **Approval**: Required in production
- **Action**: Writing code to `mcp_servers/kubectl_tools.py`

### 🔴 Red Risk: Deployment
- **Critical**: Gives agent new capabilities
- **Approval**: **ALWAYS REQUIRED** (even in dev)
- **Action**: Hot-reloading tool registry
- **Reason**: Most dangerous operation - agent gains new powers

### 🟢 Green Risk: Tool Execution
- **Safe**: Read-only operations
- **Approval**: Not required
- **Action**: Getting logs, describing pods, listing resources

## Complete Flow Diagram

```
User Request: "Pods crashing, check logs"
    ↓
Classification: Diagnosis → 🟢 Green
    ↓
Tool Discovery: Missing kubectl_tools
    ↓
Self-Evolution: Generate code → 🟡 YELLOW (approval needed)
    ↓
User Approves Code
    ↓
Authentication Check: Needs kubeconfig
    ↓
User Configures: aws eks update-kubeconfig
    ↓
Deployment: Hot-reload → 🔴 RED (approval needed)
    ↓
User Approves Deployment
    ↓
Tool Available: kubectl_get_pods(), kubectl_get_logs()
    ↓
Execute: Get pods, logs, describe → 🟢 GREEN (auto-execute)
    ↓
Diagnosis: Analyze crashes, provide recommendations
    ↓
✅ Complete
```

## Answer to Your Question

**Yes**, the brain will:
1. ✅ Determine it needs an MCP server (kubectl_tools)
2. 🟡 **Yellow**: Ask for permission to generate code
3. 🔴 **Red**: Ask for permission to deploy (critical - always required)
4. 🟢 **Green**: Execute diagnosis tools (read-only, auto-execute)

The **deployment is RED** because it gives the agent new capabilities (ability to query Kubernetes clusters), which is the most dangerous operation in the system.


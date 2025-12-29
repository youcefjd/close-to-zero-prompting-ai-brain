# Usage Example: Complete Brain Agent Workflow

## Overview

This document demonstrates how to use the Close-to-Zero Prompting AI Brain with all its components for a real-world task.

## Example Task

**Request**: "Check S3 logs for errors and analyze the latest Kubernetes version"

This task requires:
1. S3 access (missing tool - will trigger self-evolution)
2. AWS authentication (Host Inheritance pattern)
3. Web search (for latest Kubernetes version)
4. Analysis and reporting

## Step-by-Step Walkthrough

### Step 1: Initial Request

```bash
python meta_agent.py "check s3 logs for errors and analyze the latest Kubernetes version"
```

### Step 2: System Processing

#### 2.1 Classification (The Sorting Hat)

```
======================================================================
🧠 META-AGENT: Self-Evolving Request Processing
======================================================================

📥 Request: check s3 logs for errors and analyze the latest Kubernetes version

======================================================================
STEP 1: CLASSIFICATION (The Sorting Hat)
======================================================================

   Intent: ANALYSIS
   Risk Level: 🟢 Green
   Routing: Diagnosis/Consulting Agent
```

**What Happens**:
- `MetaAgent._classify_request()` analyzes the request
- Identifies keywords: "check", "analyze" → Analysis intent
- Determines risk: Read-only operations → 🟢 Green
- Routes to: Consulting/Diagnosis Agent

#### 2.2 Tool Discovery

```
======================================================================
STEP 2: TOOL DISCOVERY
======================================================================

   ⚠️  Missing Tool Detected:
      Tool: s3
      Description: AWS S3 access
      Reason: Task requires S3 bucket access
      Auth Required: aws
```

**What Happens**:
- `ToolsmithAgent.detect_missing_tool()` scans the request
- Finds "s3" and "logs" keywords
- Checks available tools: `MetaAgent._discover_tools()`
- Detects missing: `s3_tools`
- Notes authentication requirement: `aws`

#### 2.3 Self-Evolution (Toolsmith)

```
======================================================================
STEP 3: SELF-EVOLUTION (Toolsmith Agent)
======================================================================

   🔧 Agent realizes it needs: s3
   💡 Switching to 'Developer' mode...

🔧 Toolsmith Agent: Generating MCP server for s3
   Reason: Task requires S3 bucket access

   ⏸️  Code generation requires approval
      Approval ID: abc12345
      File: mcp_servers/s3_tools.py

   📋 Code Preview:
      """MCP Server for s3: AWS S3 access."""
      
      import boto3
      from typing import Dict, Any
      
      def s3_list_buckets() -> Dict[str, Any]:
          # Implementation...
      
      def s3_get_logs(bucket: str, prefix: str = "") -> Dict[str, Any]:
          # Implementation...
```

**What Happens**:
- `ToolsmithAgent.generate_mcp_server()` is called
- LLM generates complete MCP server code
- Code includes: boto3 integration, error handling, tool registry
- Status: 🟡 Yellow (drafting) - requires approval

#### 2.4 Approve Code Generation

```bash
python approve.py approve abc12345
```

**Output**:
```
✅ Code generated: mcp_servers/s3_tools.py
```

**What Happens**:
- `GovernanceFramework.approve()` marks approval
- Code file is written to `mcp_servers/s3_tools.py`
- Status changes from "pending" to "approved"

#### 2.5 Authentication Check

```
======================================================================
STEP 3.5: AUTHENTICATION CHECK
======================================================================

   ⚠️  Authentication required for aws
   📋 I need AWS access. Please run 'aws configure' in your terminal, then tell me 'Ready'.
   💡 Action: aws configure
```

**What Happens**:
- `AuthBroker.require_auth("aws")` is called
- Checks `~/.aws/credentials` and `~/.aws/config`
- Verifies with `aws sts get-caller-identity`
- If not found: Raises `NeedAuthError` with host inheritance pattern
- User action required: Run `aws configure`

#### 2.6 User Authenticates

```bash
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json

$ # User types "Ready" in agent
```

**What Happens**:
- User configures AWS credentials
- Credentials stored in `~/.aws/credentials`
- Agent retries authentication check
- `AuthBroker._check_host_credentials("aws")` succeeds
- Authentication verified ✅

#### 2.7 Deployment Approval

```
======================================================================
STEP 4: MVP DEPLOYMENT (Red Risk)
======================================================================

   🚀 Deploying MCP server: s3
   ⚠️  CRITICAL: This gives the agent new capabilities
   ⚠️  This is RED risk - requires explicit approval

   ⏸️  Deployment requires approval
      Approval ID: def67890
```

**What Happens**:
- `MetaAgent._deploy_mcp_server()` is called
- Validates Python syntax with `ast.parse()`
- Requests approval via `GovernanceFramework.request_approval()`
- Status: 🔴 Red (critical) - always requires approval

#### 2.8 Approve Deployment

```bash
python approve.py approve def67890
```

**Output**:
```
✅ Deployment approved - deploying (MVP method)...
   🔍 Step 1: Validating code syntax...
   ✅ Code syntax valid
   🔄 Step 2: Reloading MCP tool registry...
   ✅ Tool registry reloaded
   ✅ Step 3: Verifying tool availability...
   ✅ Tool s3 is now available
```

**What Happens**:
- `MetaAgent._validate_python_code()` checks syntax
- `MetaAgent._reload_mcp_tools()` clears `sys.modules` cache
- `MetaAgent._discover_tools()` refreshes tool list
- Tool `s3` is now available ✅

#### 2.9 Re-execute with New Tool

```
   ✅ Tool deployed and hot-reloaded (MVP: process reload)
   🔄 Re-running original request with new tool...

======================================================================
🧠 AUTONOMOUS EXECUTION: check s3 logs for errors and analyze the latest Kubernetes version
======================================================================
```

**What Happens**:
- `MetaAgent._process_with_tools()` is called
- Routes to `AutonomousOrchestrator.execute()`
- `AutonomousRouter.analyze_task()` determines:
  - Primary agent: ConsultingAgent (analysis task)
  - Secondary agents: DockerAgent (if needed)
  - Complexity: Medium
  - Needs clarification: False

#### 2.10 Tool Execution

```
💡 ConsultingAgent: check s3 logs for errors and analyze the latest Kubernetes version

📊 Using available tools:
   - s3_get_logs() (newly deployed)
   - web_search() (for Kubernetes version)
```

**What Happens**:
- `ConsultingAgent.execute()` is called
- Agent uses `s3_get_logs(bucket="my-bucket")` to query logs
- Agent uses `web_search("latest kubernetes version release notes")` for current info
- Both tools are 🟢 Green - auto-execute (no approval needed)

#### 2.11 Web Search Execution

```
🔍 Web Search: "latest kubernetes version release notes"
   Provider: Tavily AI
   Results:
   - Kubernetes 1.30 was released in April 2024
   - Latest stable: 1.30.2
   - Sources: [kubernetes.io/releases, github.com/kubernetes/kubernetes]
```

**What Happens**:
- `web_search()` is called from `mcp_servers/web_search_tools.py`
- Checks `TAVILY_API_KEY` environment variable
- Calls Tavily API with query
- Privacy filter checks for sensitive keywords (none found)
- Returns summarized answer + sources

#### 2.12 S3 Logs Analysis

```
📊 S3 Logs Analysis:
   Bucket: my-bucket
   Prefix: logs/
   Errors Found: 3
   
   Error 1: AccessDenied at 2024-01-15 10:30:00
   Error 2: RequestTimeout at 2024-01-15 11:45:00
   Error 3: InvalidRequest at 2024-01-15 14:20:00
```

**What Happens**:
- `s3_get_logs()` is called from newly deployed `mcp_servers/s3_tools.py`
- Uses boto3 to query S3 bucket
- Parses CloudTrail logs
- Identifies errors and timestamps
- Returns structured results

#### 2.13 Synthesis and Response

```
======================================================================
📊 CONSULTATION ANALYSIS
======================================================================

**S3 Logs Analysis**

Found 3 errors in S3 logs:
1. AccessDenied (2024-01-15 10:30:00) - Check IAM permissions
2. RequestTimeout (2024-01-15 11:45:00) - Network/connectivity issue
3. InvalidRequest (2024-01-15 14:20:00) - Review request format

**Latest Kubernetes Version**

Current stable version: Kubernetes 1.30.2 (released April 2024)
- Latest features: Enhanced security, improved performance
- Upgrade path: 1.29.x → 1.30.2
- Breaking changes: See release notes

**Recommendations**

1. Investigate AccessDenied errors - review IAM policies
2. Address RequestTimeout - check network configuration
3. Fix InvalidRequest - validate request parameters
4. Consider upgrading to Kubernetes 1.30.2 for latest features
```

**What Happens**:
- `ConsultingAgent` synthesizes results from both tools
- Combines S3 log analysis with Kubernetes version info
- Provides structured analysis with recommendations
- Returns comprehensive response

### Step 3: Final Result

```
======================================================================
📊 META-AGENT RESULT
======================================================================
{
  "status": "success",
  "message": "Analysis complete",
  "analysis": "...",
  "agent": "ConsultingAgent",
  "task_type": "consultation",
  "tools_used": ["s3_get_logs", "web_search"],
  "self_evolution": {
    "tool_generated": "s3_tools",
    "deployed": true
  }
}
```

## Complete Component Interaction

### Components Used

1. **MetaAgent** (`meta_agent.py`)
   - Orchestrates entire flow
   - Manages self-evolution
   - Coordinates authentication

2. **ToolsmithAgent** (within MetaAgent)
   - Detects missing tools
   - Generates MCP server code
   - Validates and deploys

3. **AuthBroker** (`auth_broker.py`)
   - Checks AWS credentials
   - Uses Host Inheritance pattern
   - Prompts user for authentication

4. **GovernanceFramework** (`governance.py`)
   - Manages approval workflow
   - Enforces Traffic Light Protocol
   - Tracks pending approvals

5. **AutonomousRouter** (`autonomous_router.py`)
   - Analyzes task complexity
   - Routes to ConsultingAgent
   - Determines tool requirements

6. **ConsultingAgent** (`sub_agents/consulting_agent.py`)
   - Executes analysis task
   - Uses available tools
   - Synthesizes results

7. **Web Search Tool** (`mcp_servers/web_search_tools.py`)
   - Accesses current information
   - Uses Tavily AI API
   - Privacy filter protection

8. **S3 Tool** (`mcp_servers/s3_tools.py`)
   - Newly generated tool
   - Uses boto3 for S3 access
   - Queries CloudTrail logs

## Key Features Demonstrated

✅ **Self-Evolution**: Agent generated missing S3 tool
✅ **Authentication**: Host Inheritance pattern for AWS
✅ **Governance**: Approval workflow for code generation and deployment
✅ **Tool Integration**: Seamless use of multiple tools
✅ **Web Search**: Current information beyond knowledge cutoff
✅ **Autonomous Routing**: Intelligent agent selection
✅ **Synthesis**: Combined analysis from multiple sources

## Alternative Usage Patterns

### Pattern 1: Simple Query (No Self-Evolution)

```bash
python meta_agent.py "what is the latest version of Kubernetes?"
```

**Flow**:
- Classification: Analysis → 🟢 Green
- Tool Discovery: No missing tools
- Web Search: Uses existing `web_search()` tool
- Response: Direct answer (no approvals needed)

### Pattern 2: Execution Task (With Approval)

```bash
python meta_agent.py "restart the homeassistant container"
```

**Flow**:
- Classification: Execution → 🔴 Red
- Tool Discovery: `docker_restart` available
- Governance: Requires approval (🔴 Red)
- Plan & Apply: Shows plan, waits for approval
- Execution: After approval, restarts container

### Pattern 3: Consultation (No Execution)

```bash
python meta_agent.py "should I use EKS or EC2 for my workload?"
```

**Flow**:
- Classification: Consultation → 🟢 Green
- Routing: ConsultingAgent
- Analysis: Provides comparison and recommendation
- No tools executed: Pure analysis

## Configuration Checklist

Before using the brain, ensure:

- [ ] Python 3.11+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Ollama running: `ollama serve`
- [ ] Environment variables set (if needed):
  - `TAVILY_API_KEY` (for web search)
  - `HA_TOKEN` (for Home Assistant)
- [ ] AWS credentials configured (if using AWS tools):
  - `aws configure` or `aws sso login`
- [ ] Approval system ready:
  - `approve.py` script available
  - `.agent_approvals.json` will be created automatically

## Troubleshooting

### Tool Not Found
```bash
# Check available tools
python -c "from meta_agent import MetaAgent; print(MetaAgent()._discover_tools())"
```

### Authentication Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check environment variables
env | grep -E "TAVILY|SERPER|HA_TOKEN"
```

### Approval Stuck
```bash
# List pending approvals
python approve.py list

# Approve manually
python approve.py approve <approval_id>
```

## Next Steps

1. **Try the example**: Run the complete workflow above
2. **Experiment**: Try different task types
3. **Extend**: Add new MCP servers for your use cases
4. **Monitor**: Check `.agent_memory.json` for learned patterns

---

This example demonstrates the **complete power** of the Close-to-Zero Prompting AI Brain: autonomous, self-evolving, and secure.


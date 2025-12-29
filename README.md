# Close-to-Zero Prompting AI Brain

## Overview

The **Close-to-Zero Prompting AI Brain** is an autonomous, self-evolving agent system that minimizes human intervention through intelligent routing, governance, and self-extension capabilities. The system operates with minimal prompts, making autonomous decisions and only consulting humans for critical operations, authentication, and major architectural decisions.

## Core Philosophy

> **"The agent should figure it out itself"**

The system is designed to:
- **Autonomously route** tasks to specialized agents
- **Self-evolve** by generating new tools when needed
- **Govern itself** using a Traffic Light Protocol
- **Learn from memory** to avoid repeating mistakes
- **Only ask humans** when truly necessary (authentication, approvals, clarifications)

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────┐
│ Layer 1: Foundation (Fixed Tools)      │
│ - Pre-built MCP servers                 │
│ - Core tools (write_file, run_shell)    │
│ - Stable infrastructure                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Layer 2: Orchestration (Smart Routing)  │
│ - AutonomousRouter                       │
│ - GovernanceFramework                    │
│ - Plan & Apply Pattern                   │
│ - FactChecker & Memory                   │
│ - AuthBroker                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Layer 3: Evolution (Self-Extension)    │
│ - MetaAgent                              │
│ - ToolsmithAgent                         │
│ - Tool Discovery & Hot-Reload            │
│ - Web Search Integration                 │
└─────────────────────────────────────────┘
```

## Key Components

### 1. MetaAgent (`meta_agent.py`)

The main orchestrator that processes requests with self-evolution capability.

**Features**:
- Request classification (The "Sorting Hat")
- Tool discovery and missing tool detection
- Self-evolution trigger (Toolsmith)
- Authentication checks
- Hot-reload of new capabilities

**Flow**:
```
Request → Classification → Tool Discovery → Self-Evolution → Authentication → Deployment → Execution
```

### 2. AutonomousRouter (`autonomous_router.py`)

Intelligently routes tasks to specialized sub-agents.

**Capabilities**:
- Analyzes task intent and complexity
- Determines primary/secondary agents
- Identifies if human clarification is needed
- Routes to appropriate specialized agent

**Agent Types**:
- **ConsultingAgent**: Analysis and recommendations
- **DockerAgent**: Container operations
- **ConfigAgent**: Configuration management
- **GeneralAgent**: General tasks

### 3. GovernanceFramework (`governance.py`)

Traffic Light Protocol for safe autonomous operations.

**Risk Levels**:
- 🟢 **Green**: Read-only, safe (auto-execute)
- 🟡 **Yellow**: Drafts, reversible (approval in production)
- 🔴 **Red**: Destructive, critical (always requires approval)

**Pattern**: Plan & Apply (like Terraform)
1. **Plan**: Generate change plan
2. **Review**: Human reviews plan
3. **Apply**: Execute after approval

### 4. AuthBroker (`auth_broker.py`)

Identity management with three authentication patterns.

**Patterns**:
1. **Host Inheritance**: AWS, Kubernetes (CLI credentials)
2. **Secret Vault**: API keys (.env file)
3. **OAuth 2.0**: Gmail, Calendar (OAuth tokens)

**Golden Rule**: Context is Public, Environment is Private
- Never asks for raw credentials in chat
- Prompts user to provision identity on host machine

### 5. ToolsmithAgent

Generates new MCP servers when tools are missing.

**Process**:
1. Detects missing tool
2. Generates MCP server code (🟡 Yellow)
3. Validates syntax
4. Requests approval (🔴 Red)
5. Hot-reloads tool registry

**MVP Approach**: Process reload (not Docker containers)
- 90% of value with 10% of code
- Can upgrade to Docker later if needed

### 6. FactChecker (`fact_checker.py`)

Validation, error learning, and loop prevention.

**Features**:
- Pre-execution validation
- Post-execution verification
- Memory of past successes/failures
- Suggests fixes based on history
- Prevents infinite loops

### 7. Web Search (`mcp_servers/web_search_tools.py`)

🟢 Green tool for accessing current information.

**Features**:
- Tavily AI integration (preferred)
- Serper.dev fallback
- Privacy filter (blocks sensitive queries)
- Knowledge cutoff awareness (March 2024)

## How It Works

### Request Processing Flow

```
┌─────────────────────────────────────────┐
│ 1. REQUEST ENTRY                        │
│    User: "check s3 logs for errors"     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 2. CLASSIFICATION                       │
│    Intent: ANALYSIS → 🟢 Green          │
│    Risk: Read-only                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 3. TOOL DISCOVERY                       │
│    Available: [docker, ha, ...]         │
│    Missing: s3_tools                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 4. SELF-EVOLUTION                       │
│    Toolsmith generates: s3_tools.py    │
│    Status: Pending approval (🟡 Yellow) │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 5. AUTHENTICATION CHECK                 │
│    Auth required: aws                   │
│    Pattern: Host Inheritance            │
│    Prompt: "Run 'aws configure', then   │
│            'Ready'"                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 6. USER ACTION                          │
│    User: Runs 'aws configure'           │
│    User: Types "Ready"                  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 7. DEPLOYMENT                           │
│    Validate code syntax                 │
│    Hot-reload tool registry              │
│    Status: Pending approval (🔴 Red)    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 8. USER APPROVAL                        │
│    User: python approve.py approve <id>│
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 9. EXECUTION                            │
│    Tool deployed and available          │
│    Re-runs original request             │
│    Uses: s3_tools.query_logs()         │
└─────────────────────────────────────────┘
                    ↓
              ✅ COMPLETE
```

## Getting Started

### Prerequisites

- **Python 3.11+** installed
- **Ollama** installed and running (for local LLM)
- **Git** for cloning the repository
- **Terminal/Command Line** access

### Step 1: Clone the Repository

```bash
git clone https://github.com/youcefjd/close-to-zero-prompting-ai-brain.git
cd close-to-zero-prompting-ai-brain
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install and Start Ollama

```bash
# Install Ollama (if not already installed)
# macOS/Linux: https://ollama.ai/download
# Or use: curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# In a separate terminal, pull the model
ollama pull llama3.1:latest
```

**Note**: Keep the `ollama serve` process running in a separate terminal.

### Step 4: Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# Web Search (choose one)
TAVILY_API_KEY=your-tavily-api-key-here
# OR
SERPER_API_KEY=your-serper-api-key-here

# Home Assistant (if using HA integration)
HA_TOKEN=your-home-assistant-token

# Other API keys as needed
COOKIDOO_API_KEY=your-cookidoo-key
```

**Get API Keys**:
- **Tavily AI**: https://tavily.com (recommended for web search)
- **Serper.dev**: https://serper.dev (alternative for web search)

**Note**: The `.env` file is gitignored for security. Never commit secrets.

### Step 5: Configure Authentication (As Needed)

#### AWS (Host Inheritance Pattern)

```bash
# Configure AWS credentials
aws configure

# Or use SSO
aws sso login

# Verify it works
aws sts get-caller-identity
```

#### Kubernetes (Host Inheritance Pattern)

```bash
# Configure kubectl (example for EKS)
aws eks update-kubeconfig --name your-cluster-name --region us-east-1

# Verify it works
kubectl cluster-info
```

#### API Keys (Secret Vault Pattern)

```bash
# Use the secure script
./scripts/add_secret.sh COOKIDOO_API_KEY

# Or manually add to .env
echo "COOKIDOO_API_KEY=your-key" >> .env
```

### Step 6: Test the Brain

```bash
# Simple test (consultation - no execution)
python meta_agent.py "what is the latest version of Kubernetes?"

# The brain will:
# 1. Classify the request
# 2. Use web_search tool (if configured)
# 3. Return current information
```

### Step 7: First Real Task

Try a task that requires self-evolution:

```bash
python meta_agent.py "check s3 logs for errors"
```

**What to Expect**:
1. Brain detects missing S3 tool
2. Generates MCP server code (🟡 Yellow - asks permission)
3. Checks AWS authentication (prompts if needed)
4. Requests deployment approval (🔴 Red - always required)
5. Executes diagnosis after approval

**Approve Requests**:
```bash
# List pending approvals
python approve.py list

# Approve a request
python approve.py approve <approval_id>
```

### Step 8: Verify Installation

Check that everything is working:

```bash
# Check Python version
python --version  # Should be 3.11+

# Check Ollama is running
curl http://localhost:11434/api/tags  # Should return model list

# Check dependencies
pip list | grep -E "langchain|langgraph|ollama"

# Check available tools
python -c "from meta_agent import MetaAgent; print(MetaAgent()._discover_tools())"
```

### Troubleshooting Setup

#### Ollama Not Running
```bash
# Start Ollama
ollama serve

# Check if it's running
curl http://localhost:11434/api/tags
```

#### Model Not Found
```bash
# Pull the model
ollama pull llama3.1:latest

# List available models
ollama list
```

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check virtual environment is activated
which python  # Should show venv path
```

#### Permission Errors
```bash
# Make scripts executable
chmod +x scripts/add_secret.sh

# Check file permissions
ls -la scripts/
```

### Quick Start Checklist

- [ ] Repository cloned
- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama installed and running
- [ ] Model pulled (`ollama pull llama3.1:latest`)
- [ ] Environment variables configured (`.env` file)
- [ ] Authentication configured (AWS, K8s, etc. as needed)
- [ ] Test query successful
- [ ] Approval system working (`approve.py`)

### Next Steps

Once setup is complete:
1. Read the [Usage Example](USAGE_EXAMPLE.md) for detailed workflows
2. Check [Architecture Deep Dive](ARCHITECTURE_DEEP_DIVE.md) for technical details
3. Review [EKS Pod Crash Example](EKS_POD_CRASH_EXAMPLE.md) for risk level examples
4. Start using the brain for your tasks!

## Usage

### Basic Usage

```bash
# Run the meta-agent with a request
python meta_agent.py "check s3 logs for errors"

# The agent will:
# 1. Classify the request
# 2. Detect missing tools
# 3. Generate code (if needed)
# 4. Check authentication
# 5. Request approvals
# 6. Execute autonomously
```

### Consultation Request

```bash
python meta_agent.py "help me decide between emr ack on eks vs custom emr wrapper"

# Routes to ConsultingAgent
# Provides analysis without execution
# No approvals needed (🟢 Green)
```

### Approval Workflow

```bash
# List pending approvals
python approve.py list

# Approve a request
python approve.py approve <approval_id>

# Reject a request
python approve.py reject <approval_id> "reason"
```

### Authentication Setup

#### AWS (Host Inheritance)
```bash
# Configure AWS credentials
aws configure

# Or use SSO
aws sso login

# Tell agent when ready
# (Agent will detect credentials automatically)
```

#### API Keys (Secret Vault)
```bash
# Add secret securely
./scripts/add_secret.sh COOKIDOO_API_KEY

# Or add to .env manually
echo "COOKIDOO_API_KEY=your-key" >> .env
```

#### OAuth (Gmail, Calendar)
```bash
# Agent will provide authorization link
# Click link → Approve → Tell agent "Ready"
```

## Example Walkthrough

### Scenario: "Check S3 logs for errors"

#### Step 1: Request Entry
```bash
$ python meta_agent.py "check s3 logs for errors"
```

**Output**:
```
======================================================================
🧠 META-AGENT: Self-Evolving Request Processing
======================================================================

📥 Request: check s3 logs for errors

======================================================================
STEP 1: CLASSIFICATION (The Sorting Hat)
======================================================================

   Intent: ANALYSIS
   Risk Level: 🟢 Green
   Routing: Diagnosis/Consulting Agent
```

#### Step 2: Tool Discovery
```
======================================================================
STEP 2: TOOL DISCOVERY
======================================================================

   ⚠️  Missing Tool Detected:
      Tool: s3
      Description: AWS S3 access
      Reason: Task requires S3 bucket access
```

#### Step 3: Self-Evolution
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
```

#### Step 4: Approve Code Generation
```bash
$ python approve.py approve abc12345
```

**Output**:
```
✅ Code generated: mcp_servers/s3_tools.py
```

#### Step 5: Authentication Check
```
======================================================================
STEP 3.5: AUTHENTICATION CHECK
======================================================================

   ⚠️  Authentication required for aws
   📋 I need AWS access. Please run 'aws configure' in your terminal, then tell me 'Ready'.
   💡 Action: aws configure
```

#### Step 6: User Authenticates
```bash
$ aws configure
AWS Access Key ID [None]: AKIA...
AWS Secret Access Key [None]: ***
Default region name [None]: us-east-1
Default output format [None]: json

$ # User types "Ready" in agent
```

#### Step 7: Deployment Approval
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

#### Step 8: Approve Deployment
```bash
$ python approve.py approve def67890
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

#### Step 9: Execution
```
   ✅ Tool deployed and hot-reloaded (MVP: process reload)
   🔄 Re-running original request with new tool...

   Using: s3.query_logs(bucket="my-bucket")
   Result: Found 3 errors in S3 logs:
   - Error 1: Access denied at 2024-01-15 10:30:00
   - Error 2: Timeout at 2024-01-15 11:45:00
   - Error 3: Invalid request at 2024-01-15 14:20:00
```

#### Final Result
```
✅ COMPLETE: S3 logs analyzed
   Status: 3 errors found
   Agent: Successfully used newly generated s3_tools
```

## Configuration

### Environment Variables

```bash
# Web Search (Tavily AI - preferred)
export TAVILY_API_KEY="your-key-here"

# Web Search (Serper.dev - fallback)
export SERPER_API_KEY="your-key-here"

# Home Assistant
export HA_TOKEN="your-token-here"

# AWS (via aws configure, not env var)
# Kubernetes (via kubectl config, not env var)
```

### .env File

Create `.env` file (gitignored):
```
TAVILY_API_KEY=your-key-here
COOKIDOO_API_KEY=your-key-here
```

## File Structure

```
mini-jarvis-1/
├── meta_agent.py              # Main meta-agent orchestrator
├── autonomous_router.py       # Intelligent task routing
├── governance.py              # Traffic Light Protocol
├── auth_broker.py            # Identity management
├── fact_checker.py           # Validation & memory
├── autonomous_orchestrator.py # Execution coordinator
├── approve.py                # Approval CLI
├── sub_agents/
│   ├── base_agent.py         # Base class for all agents
│   ├── consulting_agent.py   # Analysis & recommendations
│   ├── docker_agent.py       # Container operations
│   └── config_agent.py       # Configuration management
├── mcp_servers/
│   ├── docker_tools.py       # Docker MCP server
│   ├── homeassistant_tools.py # HA MCP server
│   └── web_search_tools.py   # Web search MCP server
├── scripts/
│   └── add_secret.sh         # Secure secret injection
├── .env                      # Environment variables (gitignored)
├── .secrets/                 # OAuth tokens (gitignored)
└── .agent_memory.json        # Agent learning memory
```

## Key Features

### ✅ Autonomous Operation
- Minimal human intervention
- Intelligent routing
- Self-correction and learning

### ✅ Self-Evolution
- Detects missing tools
- Generates new capabilities
- Hot-reloads without restart

### ✅ Security
- Traffic Light Protocol
- Authentication patterns
- Privacy filters
- Approval gates

### ✅ Learning
- Memory of past solutions
- Error pattern detection
- Success pattern reuse
- Loop prevention

## Best Practices

### 1. Start Simple
- Let the agent handle routine tasks
- Only intervene for critical operations
- Trust the governance framework

### 2. Use Approvals Wisely
- Review plans before approval
- Understand what the agent will do
- Reject if unsure

### 3. Authentication
- Never paste credentials in chat
- Use host inheritance for CLI tools
- Use .env for API keys
- Use OAuth for user data

### 4. Monitor Memory
- Check `.agent_memory.json` periodically
- Review learned patterns
- Clear if needed

## Troubleshooting

### Agent Stuck in Loop
```bash
# Check error history
cat .agent_memory.json | grep error_history

# Clear memory if needed
rm .agent_memory.json
```

### Tool Not Found
```bash
# Check available tools
python -c "from meta_agent import MetaAgent; print(MetaAgent()._discover_tools())"

# Check MCP servers directory
ls mcp_servers/
```

### Authentication Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check .env file
cat .env | grep -v "KEY\|PASSWORD"

# Check OAuth tokens
ls .secrets/
```

## Contributing

When adding new capabilities:

1. **Create MCP Server**: Add to `mcp_servers/`
2. **Register in Governance**: Add to `governance.py`
3. **Add to Base Agent**: Update `sub_agents/base_agent.py`
4. **Update Documentation**: Add examples and walkthroughs

## License

[Your License Here]

## Support

For issues or questions:
- Check documentation in `/docs`
- Review example walkthroughs
- Check `.agent_memory.json` for learned patterns

---

**The Close-to-Zero Prompting AI Brain** - Autonomous, Self-Evolving, Secure.


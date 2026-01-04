# Close-to-Zero Prompting AI Brain

**An autonomous, self-evolving AI agent system that builds complete systems from scratch with minimal human intervention.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The **Close-to-Zero Prompting AI Brain** is an autonomous agent system that minimizes human intervention through intelligent routing, self-evolution, and governance. Give it a single high-level request like "Build a Raspberry Pi ad-blocker" and it will autonomously plan, generate tools, configure authentication, and execute—only asking for approval at critical decision points.

## Core Philosophy

> **"The agent should figure it out itself"**

The system is designed to:
- **Autonomously build** complete systems from scratch
- **Self-evolve** by generating new tools when needed
- **Govern itself** using a Traffic Light Protocol (Green/Yellow/Red)
- **Learn from memory** to avoid repeating mistakes
- **Only ask humans** for authentication, critical approvals, and architectural decisions

## Table of Contents

- [Key Features](#key-features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Usage Examples](#usage-examples)
- [Conversation Mode](#conversation-mode)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Documentation

Essential guides for understanding and using the system:

- **[SETUP.md](SETUP.md)** - Setup and installation instructions
- **[COMPREHENSIVE_SAFETY_AUDIT.md](COMPREHENSIVE_SAFETY_AUDIT.md)** - Complete safety, governance, and autonomy audit
- **[SELF_HEALING_GUIDE.md](SELF_HEALING_GUIDE.md)** - Self-healing system documentation
- **[VERSATILITY_ARCHITECTURE.md](VERSATILITY_ARCHITECTURE.md)** - Architecture and versatility explanation

---

## Key Features

### 🏗️ **Autonomous System Building**
Build complete systems from a single prompt:
- Design consultation with Q&A workflow
- Multiple architecture options with pros/cons
- Resource quota planning
- Automatic observability generation
- Complete deployment with governance

### 🧠 **Intelligent LLM Provider Selection**
Choose your AI backend at startup:
- **Ollama (Local)** - FREE, private, default
- **OpenAI** - Commercial, GPT-4
- **Anthropic Claude** - Commercial, Claude-3

### 🔄 **Self-Evolution**
Automatically generates new capabilities:
- Detects missing tools using LLM analysis
- Generates MCP (Model Context Protocol) servers
- Hot-reloads new tools without restart
- Batch tool generation for complex systems

### 🛡️ **Governance Framework**
Traffic Light Protocol ensures safety:
- 🟢 **Green**: Read-only operations (auto-execute)
- 🟡 **Yellow**: Reversible changes (auto-approve in dev)
- 🔴 **Red**: Critical operations (always require approval)

### 🔐 **Smart Authentication**
Three authentication patterns:
- **Host Inheritance**: AWS, Kubernetes (uses CLI credentials)
- **Secret Vault**: API keys in `.env` file
- **OAuth 2.0**: Gmail, Calendar (OAuth tokens)

### 📚 **Learning & Memory**
Improves over time:
- Stores past successes/failures
- Suggests fixes based on history
- Prevents infinite loops
- Pattern recognition for similar tasks

### 🔍 **Observability Generation**
Automatically creates monitoring:
- Log aggregation tools
- Error tracking systems
- Health check monitors
- Custom troubleshooting tools

### 🌐 **Web Search Integration**
Access current information:
- Tavily AI or Serper.dev integration
- Knowledge cutoff awareness
- Privacy filters for sensitive queries

### 💬 **Conversation Mode with Context Preservation**
Natural follow-up conversations:
- Context preserved between requests
- Follow-up questions reference previous answers
- Conversation history passed to agents
- `clear` command to reset context

### 🧑‍💻 **Human-in-the-Loop Clarification**
Interactive clarification when needed:
- System asks targeted questions when ambiguous
- User responds inline in terminal
- Clarification automatically incorporated
- No need to restart or re-prompt

### 🔧 **Self-Healing System**
Automatic error detection and recovery:
- Detects command failures and errors
- Analyzes root cause using LLM
- Proposes and validates fixes
- Self-corrects invalid parameters
- Learns from past failures

### 🖥️ **OS-Aware Execution**
Automatic operating system detection:
- Detects macOS, Linux, Windows
- Uses OS-specific commands (e.g., `pmset` vs `upower`)
- Provides OS context to LLM
- Prevents cross-platform command errors

### 📊 **Smart Output Formatting**
Clean, user-friendly responses:
- Transforms verbose technical output
- Extracts only relevant information
- Removes system internals and noise
- Concise, human-readable answers

### ✅ **Interactive Approvals**
Inline approval workflow:
- Prompts for approval in terminal
- Shows command details and risk level
- Approve with `yes`, reject with `no`
- No separate approval CLI needed

---

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Foundation (Fixed Tools)                          │
│ ─────────────────────────────────────────────────────────  │
│ • Pre-built MCP servers (Docker, Home Assistant, Web)      │
│ • Core tools (write_file, run_shell)                       │
│ • Stable infrastructure components                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Orchestration (Smart Routing & Governance)        │
│ ─────────────────────────────────────────────────────────  │
│ • AutonomousRouter - Task classification & routing         │
│ • GovernanceFramework - Traffic Light Protocol            │
│ • FactChecker - Validation & memory                        │
│ • AuthBroker - Identity management                         │
│ • Plan & Apply Pattern (Terraform-like)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Evolution (Self-Extension & Building)             │
│ ─────────────────────────────────────────────────────────  │
│ • MetaAgent - Main orchestrator                            │
│ • AutonomousBuilder - Complete system building             │
│ • ToolsmithAgent - MCP server generation                   │
│ • DesignConsultant - Architecture design with Q&A          │
│ • ObservabilityGenerator - Monitoring tool creation        │
│ • Tool Discovery & Hot-Reload                              │
└─────────────────────────────────────────────────────────────┘
```

### Request Processing Flow

```
User Request → LLM Provider Selection → Classification →
Tool Discovery → Self-Evolution → Authentication →
Deployment → Execution → Memory Storage
```

---

## Getting Started

### Prerequisites

- **Python 3.11+** installed
- **Ollama** installed and running (for local LLM - recommended)
  - Or OpenAI/Anthropic API keys (for commercial LLMs)
- **Git** for cloning the repository
- **Terminal/Command Line** access

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/youcefjd/close-to-zero-prompting-ai-brain.git
cd close-to-zero-prompting-ai-brain
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 3. Install and Configure Ollama (Recommended - Free & Local)

```bash
# Install Ollama
# macOS/Linux: https://ollama.ai/download
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# In a separate terminal, pull the model
ollama pull gemma3:4b
```

**Keep the `ollama serve` process running in a separate terminal.**

#### 4. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# LLM Provider (optional - will be prompted if not set)
AI_BRAIN_LLM_PROVIDER=ollama  # or openai, anthropic
AI_BRAIN_LLM_MODEL=gemma3:4b

# Environment
AI_BRAIN_ENVIRONMENT=production  # or dev, staging

# Web Search (choose one)
TAVILY_API_KEY=your-tavily-api-key-here
# OR
SERPER_API_KEY=your-serper-api-key-here

# OpenAI (if using OpenAI provider)
OPENAI_API_KEY=sk-...

# Anthropic (if using Anthropic provider)
ANTHROPIC_API_KEY=sk-ant-...

# Home Assistant (if using HA integration)
HA_TOKEN=your-home-assistant-token
```

**Get API Keys**:
- **Tavily AI**: https://tavily.com (recommended for web search)
- **Serper.dev**: https://serper.dev (alternative for web search)
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/

#### 5. Run Your First Request

```bash
python meta_agent.py "what is the latest version of Kubernetes?"
```

**What Happens:**
1. You'll be prompted to select an LLM provider (or it uses Ollama by default)
2. The agent classifies your request
3. Uses web search to get current information
4. Returns the result

### LLM Provider Selection

When you run the system for the first time, you'll see:

```
======================================================================
🧠 CLOSE-TO-ZERO PROMPTING AI BRAIN
======================================================================

🧠 AI BRAIN - LLM PROVIDER SELECTION
======================================================================

   This system can use different LLM providers. Choose one:

   1. Ollama (Local) - RECOMMENDED ✅
      • Runs locally on your machine (private, free)
      • Model: gemma3:4b
      • Requires: Ollama installed (https://ollama.ai)
      • Cost: Free
      • Privacy: Complete (data never leaves your machine)

   2. OpenAI (Commercial)
      • Uses OpenAI's GPT models
      • Model: gpt-4 (configurable)
      • Requires: OpenAI API key
      • Cost: ~$0.03 per 1K tokens (input)

   3. Anthropic Claude (Commercial)
      • Uses Anthropic's Claude models
      • Model: claude-3-sonnet (configurable)
      • Requires: Anthropic API key
      • Cost: ~$0.003 per 1K tokens (input)

   Enter your choice (1-3) [default: 1 - Ollama]:
```

**Just press Enter to use Ollama (local, free).**

To skip the prompt and use defaults:
```bash
export AI_BRAIN_LLM_PROVIDER=ollama
python meta_agent.py "your task"
```

---

## Complete Functionality Reference

### 1. **MetaAgent** (`meta_agent.py`)

**Main orchestrator with self-evolution capability.**

**Features**:
- Request classification (The "Sorting Hat")
- Tool discovery and missing tool detection
- Self-evolution trigger (activates Toolsmith)
- Authentication checks via AuthBroker
- Hot-reload of new capabilities
- Tool registry management

**Usage**:
```bash
python meta_agent.py "your request"
```

**Flow**:
```
Request → Classification → Tool Discovery → Self-Evolution →
Authentication → Deployment → Execution
```

---

### 2. **AutonomousBuilder** (`autonomous_builder.py`)

**Complete system building from scratch.**

**Features**:
- Context gathering through Q&A
- Architecture design options with pros/cons
- Resource quota planning
- Authentication verification
- Automatic observability generation
- Troubleshooting tool creation
- Complete deployment orchestration

**Usage**:
```bash
python autonomous_builder.py "Build a Raspberry Pi server to block ads on my network"
```

**Workflow**:
1. **Context Gathering**: Asks targeted questions (network size, availability, budget)
2. **Design Options**: Presents 2-4 architecture options with pros/cons
3. **User Selection**: You choose your preferred option
4. **Resource Quotas**: Gathers sizing information (CPU, memory, storage)
5. **Architecture Design**: Generates detailed architecture
6. **Authentication**: Checks and prompts for required credentials
7. **Observability**: Auto-generates monitoring tools
8. **Troubleshooting Tools**: Creates debugging MCP servers
9. **System Building**: Executes deployment with governance checks

**Example Output**:
```
Step 1: Context Gathering (3-5 questions)
Step 2: Design Options (Pi-hole, AdGuard, Custom)
Step 3: Resource Quotas (cluster size, CPU, memory)
Step 4: Architecture Design (components, deployment strategy)
Step 5: Authentication (SSH, API keys)
Step 6: Observability (4 monitoring tools generated)
Step 7: Troubleshooting Tools (log_aggregator, error_tracker)
Step 8: System Building (with governance approvals)
```

---

### 3. **DesignConsultant** (`design_consultant.py`)

**Structured Q&A for complex system design.**

**Features**:
- Analyzes requirements to determine needed context
- Generates targeted questions
- Presents design options with pros/cons
- Recommendation scoring (0-1)
- Cost and complexity estimates
- Resource quota gathering

**Methods**:
- `gather_context()`: Asks targeted questions
- `generate_design_options()`: Creates architecture options
- `present_options()`: Shows options and gets user selection
- `gather_resource_quotas()`: Collects sizing information

**Example Questions**:
```
1. What is the expected scale (users, requests/sec)?
2. What is your availability requirement? (99.9%, 99.99%, 99.999%)
3. What is your budget range?
4. What are your security requirements?
5. Do you have existing infrastructure?
```

---

### 4. **AutonomousRouter** (`autonomous_router.py`)

**Intelligent task routing to specialized agents.**

**Features**:
- LLM-powered intent analysis
- Complexity assessment
- Primary/secondary agent determination
- Human clarification detection
- Semantic routing support

**Agent Types**:
- **ConsultingAgent**: Analysis, recommendations, comparisons
- **DockerAgent**: Container operations, Docker Compose
- **ConfigAgent**: Configuration file management
- **DesignConsultant**: Complex system design with Q&A
- **GeneralAgent**: Fallback for uncategorized tasks

**Routing Logic**:
```python
Intent Detection → Complexity Analysis → Agent Selection →
Clarification Check → Route to Agent
```

**Example Routing**:
```
"Help me decide between EMR and EKS" → ConsultingAgent
"Check Docker logs for errors" → DockerAgent
"Build a microservices system" → DesignConsultant
"Create YAML config for app" → ConfigAgent
```

---

### 5. **GovernanceFramework** (`governance.py`)

**Traffic Light Protocol for safe autonomous operations.**

**Risk Levels**:

**🟢 Green (Auto-Execute)**:
- Read-only operations
- Status checks, logs, queries
- No state changes
- Examples: `docker_ps`, `docker_logs`, `ha_get_state`, `web_search`

**🟡 Yellow (Context-Aware)**:
- Reversible operations
- File creation, configuration changes
- Auto-approved in dev/staging
- Requires approval in production
- Examples: `write_file`, `docker_exec`, `ha_call_service`

**🔴 Red (Always Approve)**:
- Destructive operations
- Service deployment, container restart
- Network changes, system packages
- Never auto-approved
- Examples: `docker_restart`, `run_shell`, `deploy_mcp_server`

**Plan & Apply Pattern**:
```
1. Plan: Generate change plan with risk assessment
2. Review: Human reviews plan (for yellow/red tasks)
3. Apply: Execute after approval
```

**Usage**:
```bash
# List pending approvals
python approve.py list

# Approve a request
python approve.py approve <approval_id>

# Reject a request
python approve.py reject <approval_id> "reason"

# Show approval details
python approve.py show <approval_id>
```

---

### 6. **AuthBroker** (`auth_broker.py`)

**Identity management with three authentication patterns.**

**Golden Rule**: Context is Public, Environment is Private
- Never asks for raw credentials in chat
- Prompts user to provision identity on host machine

**Authentication Patterns**:

**1. Host Inheritance** (AWS, Kubernetes):
```bash
# AWS
aws configure
aws sso login

# Kubernetes
aws eks update-kubeconfig --name cluster --region us-east-1
kubectl cluster-info

# Agent detects credentials automatically
```

**2. Secret Vault** (API Keys):
```bash
# Add to .env file
echo "TAVILY_API_KEY=your-key" >> .env
echo "SERPER_API_KEY=your-key" >> .env

# Agent reads from .env securely
```

**3. OAuth 2.0** (Gmail, Calendar):
```
# Agent provides authorization link
# User clicks link → Approves → Tells agent "Ready"
# Tokens stored in .secrets/ directory
```

**Verification**:
```python
# Agent checks before execution
auth_broker.require_auth("aws")  # Checks ~/.aws/credentials
auth_broker.require_auth("kubernetes")  # Checks ~/.kube/config
```

---

### 7. **ToolsmithAgent** (in `meta_agent.py`)

**Generates new MCP servers when tools are missing.**

**Process**:
1. Detects missing tool using LLM analysis
2. Generates MCP server code (🟡 Yellow risk)
3. Validates Python syntax
4. Requests code generation approval
5. Requests deployment approval (🔴 Red risk)
6. Hot-reloads tool registry
7. Verifies tool availability

**MVP Approach**: Process reload (not Docker containers)
- 90% of value with 10% of code
- Instant hot-reload without container overhead
- Can upgrade to Docker containers later

**Example**:
```
Request: "Check S3 logs"
Detects: s3_tools missing
Generates: mcp_servers/s3_tools.py
Approvals: 2 (code generation + deployment)
Result: s3_tools available for use
```

---

### 8. **FactChecker** (`fact_checker.py`)

**Validation, error learning, and loop prevention.**

**Features**:
- **Pre-execution validation**: Checks file existence, permissions, dangerous commands
- **Post-execution verification**: Validates results
- **Memory**: Stores past successes/failures in `.agent_memory.json`
- **Fix suggestions**: Based on error history
- **Loop prevention**: Max 5 iterations, detects repeated errors
- **Pattern recognition**: Identifies similar failure patterns

**Validation Examples**:
```python
# Before deleting a file
fact_checker.validate_action("delete_file", {"path": "/path/to/file"})
# Checks: File exists? Not a system file? User has permission?

# After execution
fact_checker.verify_result(result)
# Checks: Expected output? No errors? State consistent?
```

**Loop Detection**:
```
Same error 3 times in a row → Abort
Max 5 iterations per task → Abort
Suggests alternative approaches from memory
```

---

### 9. **ObservabilityGenerator** (`observability_generator.py`)

**Automatic monitoring and observability tool creation.**

**Features**:
- Log location discovery (auto-detects log paths)
- Monitoring stack generation
- Error tracking tools
- Health check monitors
- Custom troubleshooting MCP servers

**Generated Tools**:
- `log_aggregator`: Centralized log access
- `error_tracker`: Error analysis and tracking
- `health_monitor`: Service health checks
- System-specific tools (e.g., `k8s_troubleshooter`, `docker_troubleshooter`)

**Usage**:
```python
observability_gen.generate_observability_stack(requirements)
# Returns: List of generated monitoring tools
```

**Example Output**:
```
Generated 4 observability tools:
✅ log_aggregator - Aggregate logs from all components
✅ error_tracker - Track and analyze errors
✅ k8s_troubleshooter - Kubernetes debugging
✅ health_monitor - Service health checks
```

---

### 10. **Configuration System** (`config.py`)

**Centralized configuration and LLM provider management.**

**Features**:
- Interactive LLM provider selection
- Environment variable support
- Default configurations
- Provider-specific settings

**Environment Variables**:
```bash
AI_BRAIN_LLM_PROVIDER=ollama  # ollama, openai, anthropic
AI_BRAIN_LLM_MODEL=gemma3:4b
AI_BRAIN_LLM_TEMPERATURE=0.7
AI_BRAIN_ENVIRONMENT=production  # production, dev, staging
AI_BRAIN_MAX_RETRIES=5
AI_BRAIN_TIMEOUT=30

# Provider-specific
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Usage**:
```python
from config import get_llm_provider_from_user, get_config

# Interactive prompt (or uses env vars)
llm_provider = get_llm_provider_from_user()

# Get configuration
config = get_config()
```

---

### 11. **Specialized Sub-Agents**

#### **ConsultingAgent** (`sub_agents/consulting_agent.py`)
- Analysis and recommendations
- Technology comparisons
- Architecture advice
- No execution (read-only)

#### **DockerAgent** (`sub_agents/docker_agent.py`)
- Container operations
- Docker Compose management
- Log analysis
- Health checks

#### **ConfigAgent** (`sub_agents/config_agent.py`)
- YAML/JSON file generation
- Configuration validation
- Template-based generation

#### **BaseAgent** (`sub_agents/base_agent.py`)
- Base class for all agents
- Tool execution with governance
- Error handling and retries
- LLM interaction

---

### 12. **MCP Servers** (Model Context Protocol)

Pre-built tool servers in `mcp_servers/`:

#### **Docker Tools** (`docker_tools.py`)
```python
docker_ps()           # List containers
docker_logs()         # Get container logs
docker_inspect()      # Inspect container
docker_exec()         # Execute command in container
docker_restart()      # Restart container
docker_compose_up()   # Start compose stack
docker_compose_down() # Stop compose stack
```

#### **Home Assistant Tools** (`homeassistant_tools.py`)
```python
ha_get_state()         # Get entity state
ha_call_service()      # Call HA service
ha_get_logs()          # Get HA logs
ha_search_logs()       # Search logs
ha_list_integrations() # List integrations
```

#### **Web Search Tools** (`web_search_tools.py`)
```python
web_search()  # Search the web (Tavily or Serper)
# Privacy filter, knowledge cutoff awareness
```

---

### 13. **Self-Healing System** (`self_healing.py`)

**Automatic error detection, analysis, and recovery.**

**Features**:
- Detects codebase errors (syntax, import, runtime)
- Analyzes root cause using LLM
- Proposes validated fixes
- Applies fixes with rollback capability
- Learns from past errors to prevent recurrence

**Error Types Handled**:

| Error Type | Detection | Action |
|------------|-----------|--------|
| `SyntaxError` | Import failure | Analyze and fix syntax |
| `ImportError` | Missing module | Suggest pip install |
| `TypeError` | Invalid parameter | Remove/fix parameter |
| `[Errno 2]` | Command not found | Use OS-specific alternative |
| `Exit code != 0` | Command failure | Analyze stderr, retry |

**Self-Healing Flow**:
```
Error Detected → Root Cause Analysis → Propose Fix → 
Validate Fix → Governance Check → Apply Fix → Verify
```

**Example: Invalid Parameter**:
```python
# LLM calls: run_shell(command="date", timeout=30)
# Error: run_shell() got an unexpected keyword argument 'timeout'

# Self-healing:
# 1. Detects TypeError with "unexpected keyword argument"
# 2. Extracts invalid parameter: "timeout"
# 3. Retries without: run_shell(command="date")
# 4. Success!
```

**Example: OS-Specific Command**:
```python
# On macOS, LLM tries: run_shell(command="amixer get Master")
# Error: [Errno 2] No such file or directory: 'amixer'

# Self-healing:
# 1. Detects command not found error
# 2. Identifies: 'amixer' is Linux-only
# 3. OS detection: macOS
# 4. Retries with: osascript -e 'output volume of (get volume settings)'
# 5. Success!
```

**Configuration**:
```python
# Maximum healing attempts per error
MAX_HEALING_ATTEMPTS = 3

# Healing requires approval for code changes (🔴 Red)
# Auto-approved for parameter fixes (🟢 Green)
```

---

### 14. **Emergency Stop** (`emergency_stop.py`)

**Global kill switch for all operations.**

**Usage**:
```bash
# Trigger emergency stop
python emergency_stop.py

# Checked before every tool execution
# All operations abort immediately
```

---

### 15. **OS Detection** (in `consulting_agent.py`)

**Automatic operating system detection for command selection.**

**Detected Systems**:
- macOS (Darwin)
- Linux
- Windows

**OS-Specific Commands**:

| Query | macOS | Linux | Windows |
|-------|-------|-------|---------|
| Volume | `osascript -e 'output volume of (get volume settings)'` | `amixer get Master` | PowerShell |
| Battery | `pmset -g batt` | `upower -i ...` | `powercfg /batteryreport` |
| Time | `date` | `date` | `Get-Date` |
| Disk | `df -h` | `df -h` | `Get-WmiObject` |
| Memory | `sysctl + top` | `free -h` | `Get-WmiObject` |

**How It Works**:
```python
import platform
system = platform.system().lower()  # 'darwin', 'linux', 'windows'
```

**Usage in Agent**:
```
System Prompt includes:
"CURRENT SYSTEM: macOS"
"For volume on macOS: osascript -e '...'"
```

---

### 16. **Output Formatting** (in `consulting_agent.py`)

**LLM-powered cleanup of raw command output.**

**Problem**: Raw command output is often verbose and technical:
```
Now playing:
    0:CoreAudio 0 (Built-in Output), muted:0, volume:0.500000
    HDMI 0
```

**Solution**: Format to user-friendly answer:
```
Your volume is set to 50%.
```

**Features**:
- Extracts only relevant information
- Removes technical noise (hex values, PIDs, etc.)
- Formats as concise, natural language
- Falls back to truncation if formatting fails

**Formatting Rules**:
1. Be concise (one line if possible)
2. Be direct (no filler)
3. Be accurate (match the query)
4. Remove noise (system internals)
5. Format clearly (human-readable)

**Example Transformations**:

| Query | Raw Output | Formatted |
|-------|------------|-----------|
| "battery status" | `Now drawing from 'AC Power'... 85%; charging` | Battery at 85%, charging |
| "what time is it" | `Sun Jan  4 14:30:00 PST 2026` | It's 2:30 PM PST |
| "volume level" | `output volume:50` | Volume is set to 50% |

---

### 17. **Cost Tracking** (`cost_tracker.py`)

**Monitor token usage and API costs.**

**Features**:
- Token usage tracking
- Cost estimation per request
- Hourly/daily limits
- Warnings before hitting limits

---

### 18. **Context Management** (`context_manager.py`)

**Prune messages to fit token limits.**

**Features**:
- Message prioritization
- Context window management
- Important message retention
- Out-of-memory prevention

---

### 19. **Output Sanitization** (`output_sanitizer.py`)

**Remove sensitive information from logs.**

**Features**:
- API key redaction
- Password removal
- Token sanitization
- Context-aware filtering

**Patterns Detected**:
- API keys, passwords, tokens
- AWS credentials
- Private keys
- Database URLs
- Generic secrets

---

## Usage Examples

### Example 1: Simple Consultation

```bash
python meta_agent.py "Help me decide between EMR ACK on EKS vs custom EMR wrapper"
```

**What Happens**:
1. Routes to ConsultingAgent
2. Provides analysis without execution
3. No approvals needed (🟢 Green)

---

### Example 2: Tool Generation & Execution

```bash
python meta_agent.py "Check S3 logs for errors"
```

**Workflow**:
1. Detects missing S3 tool
2. Generates `mcp_servers/s3_tools.py` (approval required)
3. Checks AWS authentication
4. Deploys tool (approval required)
5. Executes query
6. Returns results

**Approvals**: 2 (code generation + deployment)

---

### Example 3: Autonomous System Building

```bash
python autonomous_builder.py "Build a Raspberry Pi server to block ads on my network"
```

**Complete Workflow**:
```
Step 1: Context Gathering
   Q: Network size? A: 10-20 devices
   Q: Availability? A: Best effort
   Q: Existing hardware? A: Raspberry Pi 4

Step 2: Design Options
   Option 1: Pi-hole (Docker) - Recommended (0.85/1.0)
   Option 2: AdGuard Home - Alternative (0.75/1.0)
   Selection: 1

Step 3: Resource Quotas
   Cluster: Single Raspberry Pi
   CPU: 4 cores
   Memory: 4GB
   Storage: 32GB

Step 4: Architecture Design
   ✅ Docker-based deployment
   ✅ Pi-hole container
   ✅ DNS configuration
   ✅ Backup strategy

Step 5: Authentication
   ⚠️  SSH to Raspberry Pi required
   Action: ssh-copy-id pi@raspberrypi

Step 6: Observability (Auto-generated)
   ✅ pi_monitor
   ✅ dns_query_logger
   ✅ block_list_manager
   ✅ network_health_checker

Step 7: Troubleshooting Tools (Auto-generated)
   ✅ docker_troubleshooter
   ✅ log_aggregator
   ✅ error_tracker
   ✅ pihole_diagnostics

Step 8: System Building (with Approvals)
   🔴 Install Docker → Approve
   🟡 Create config files → Auto-approved (reversible)
   🔴 Deploy Pi-hole → Approve
   🟡 Configure DNS → Approve (production)

Result: Complete ad-blocking system deployed
```

**Total Interaction**: 5-8 approval clicks, 10-15 minutes
**Traditional Approach**: 2-4 hours of manual work

---

### Example 4: Conversation Mode with Follow-ups

```bash
python meta_agent.py
```

**Interactive Session**:
```
======================================================================
  💬 CONVERSATION MODE - Context is preserved between requests
  💡 Type 'exit' or 'quit' to end, 'clear' to reset context
======================================================================

Enter request:
  > what's my macbook battery status?

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Battery is at 85%, charging, connected to AC power.

----------------------------------------------------------------------
  💬 Follow-up (context preserved) or 'exit' to quit:
  > and what about the volume level?

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Your volume is set to 50%.

----------------------------------------------------------------------
  💬 Follow-up (context preserved) or 'exit' to quit:
  > clear

  🧹 Context cleared. Starting fresh.

  Enter new request:
  > exit
  👋 Goodbye!
```

**What Happens**:
1. System enters conversation mode (no command-line arguments)
2. Each follow-up preserves context from previous exchanges
3. `clear` resets context for fresh start
4. `exit` or `quit` ends the session

---

### Example 5: Human-in-the-Loop Clarification

```bash
python meta_agent.py "help me decide between EMR options"
```

**With Clarification**:
```
──────────────────────────────────────────────────────────────────────
  Clarification Needed
──────────────────────────────────────────────────────────────────────
  ❓ Could you clarify what you mean by 'EMR options'? 
     Are you referring to:
     - EMR ACK (AWS Controllers for Kubernetes)
     - Native EMR API
     - EMR Serverless
     - EMR on EKS?

  💬 Your response: I mean ACK vs native EMR API for managing clusters

  🔄 Processing with clarification...

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Here's my analysis of EMR ACK vs Native EMR API:
  
  **EMR ACK (AWS Controllers for Kubernetes)**:
  - Kubernetes-native approach
  - Uses CRDs for cluster management
  - Better GitOps integration
  ...
```

**What Happens**:
1. System detects ambiguous request
2. Returns `needs_human` status with clarifying question
3. User provides clarification inline
4. System re-processes with clarification context
5. Returns refined answer

---

### Example 6: Interactive Approval

```bash
python meta_agent.py "restart the nginx container"
```

**With Approval Prompt**:
```
──────────────────────────────────────────────────────────────────────
  Approval Required
──────────────────────────────────────────────────────────────────────
  ⏸️  Tool 'docker_restart' requires approval
  📋 Approval ID: a1b2c3d4
  📝 Command: docker restart nginx
  ⚠️  Risk Level: red
  💬 Message: Container restart will cause brief service interruption

  ⚠️  Approve this request? (yes/no): yes

  ✅ Approved! Continuing execution...

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Container 'nginx' restarted successfully.
```

**What Happens**:
1. System detects 🔴 Red risk operation
2. Shows approval details inline
3. User approves or rejects in terminal
4. Continues execution on approval

---

### Example 7: Self-Healing Error Recovery

```bash
python meta_agent.py "what's the system volume?"
```

**With Self-Healing**:
```
💡 ConsultingAgent: what's the system volume?
  🔧 Calling tool: run_shell
  ❌ Tool error: Failed to execute command: [Errno 2] No such file or directory: 'amixer'

  🔄 Self-healing: Command 'amixer' failed - this is macOS, not Linux.
     Trying OS-specific command: osascript -e 'output volume of (get volume settings)'

  🔧 Calling tool: run_shell
  ✅ Tool result: 50

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Your volume is set to 50%.
```

**What Happens**:
1. System attempts Linux command on macOS
2. Detects failure and analyzes error
3. Identifies OS mismatch
4. Self-corrects with macOS-specific command
5. Returns clean result

---

### Example 8: Local System Queries

```bash
python meta_agent.py "give me the time"
```

**Output**:
```
──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  It's 2:30 PM PST on Sunday, January 4, 2026.
```

**What Happens**:
1. Semantic understanding detects LOCAL system query
2. Uses `run_shell` with `date` command
3. Formats raw output into human-readable answer
4. No approval needed (🟢 Green - read-only)

---

### Example 10: Docker Operations

```bash
python meta_agent.py "Check Docker logs for errors in the last hour"
```

**What Happens**:
1. Routes to DockerAgent
2. Lists containers (🟢 Green - auto-executed)
3. Fetches logs (🟢 Green - auto-executed)
4. Analyzes errors
5. Returns results

**No approvals needed** (all read-only operations)

---

### Example 11: Development Environment

```bash
# Set dev environment
export AI_BRAIN_ENVIRONMENT=dev

python meta_agent.py "Deploy new version of my app"
```

**What Happens**:
- 🟢 Green tasks: Auto-executed
- 🟡 Yellow tasks: Auto-approved (dev environment)
- 🔴 Red tasks: Still require approval

**In dev**: More autonomous, faster iteration
**In production**: More cautious, requires approvals

---

## Conversation Mode

### Overview

The AI Brain supports two execution modes:

1. **Single Command Mode**: Pass task as command-line argument
2. **Conversation Mode**: Interactive session with context preservation

### Starting Conversation Mode

```bash
# No arguments = conversation mode
python meta_agent.py
```

**Output**:
```
======================================================================
  💬 CONVERSATION MODE - Context is preserved between requests
  💡 Type 'exit' or 'quit' to end, 'clear' to reset context
======================================================================

Enter request:
  > _
```

### Context Preservation

Each request and response is stored in conversation history:

```python
conversation_history = [
    {"role": "user", "content": "what's my battery level?"},
    {"role": "assistant", "content": "Battery is at 85%, charging."},
    {"role": "user", "content": "and the volume?"},
    {"role": "assistant", "content": "Volume is set to 50%."}
]
```

**Benefits**:
- Follow-up questions work naturally ("and what about X?")
- Previous context informs current answers
- Reduces repetition in multi-step tasks

### Commands

| Command | Action |
|---------|--------|
| `exit` or `quit` | End session |
| `clear` | Reset conversation history |
| Any other text | Execute as new task |

### Example Session

```
Enter request:
  > help me compare kubernetes deployment options

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Here are the main Kubernetes deployment options:
  1. **Managed (EKS, GKE, AKS)**: Lowest operational overhead...
  2. **Self-managed (kubeadm)**: Full control, higher overhead...
  3. **Lightweight (k3s, kind)**: Great for edge/dev...

----------------------------------------------------------------------
  💬 Follow-up (context preserved) or 'exit' to quit:
  > tell me more about EKS specifically

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Amazon EKS specifics:
  - Control plane managed by AWS (99.95% SLA)
  - Node groups: Managed, Self-managed, or Fargate
  - Pricing: $0.10/hour per cluster + node costs...

----------------------------------------------------------------------
  💬 Follow-up (context preserved) or 'exit' to quit:
  > what's the pricing comparison with GKE?

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  EKS vs GKE Pricing:
  - EKS: $0.10/hour (~$73/month) per cluster
  - GKE: Free for one zonal cluster, $0.10/hour for Autopilot
  - GKE Autopilot often more cost-effective for variable workloads...
```

### Clarification Flow

When the system needs clarification:

```
Enter request:
  > set up monitoring

──────────────────────────────────────────────────────────────────────
  Clarification Needed
──────────────────────────────────────────────────────────────────────
  ❓ What type of monitoring would you like to set up?
     - Application metrics (Prometheus/Grafana)
     - Log aggregation (ELK/Loki)
     - Infrastructure monitoring (CloudWatch/Datadog)
     - All of the above

  💬 Your response: prometheus and grafana for kubernetes

  🔄 Processing with clarification...

──────────────────────────────────────────────────────────────────────
  Task Result
──────────────────────────────────────────────────────────────────────
  Setting up Prometheus + Grafana for Kubernetes...
```

### Single Command Mode

For scripts or one-off tasks:

```bash
# Single command - exits after execution
python meta_agent.py "what is the current time"

# With verbose output
python meta_agent.py --verbose "deploy the application"
```

---

## Configuration

### LLM Provider Configuration

**Default (Ollama - Local)**:
```bash
# No configuration needed
python meta_agent.py "your task"
# Will prompt for provider selection or use Ollama by default
```

**Environment Variables**:
```bash
export AI_BRAIN_LLM_PROVIDER=ollama
export AI_BRAIN_LLM_MODEL=gemma3:4b
```

**OpenAI**:
```bash
export AI_BRAIN_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export AI_BRAIN_LLM_MODEL=gpt-4
```

**Anthropic**:
```bash
export AI_BRAIN_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export AI_BRAIN_LLM_MODEL=claude-3-sonnet-20240229
```

### Environment Configuration

```bash
# Development (auto-approve yellow tasks)
export AI_BRAIN_ENVIRONMENT=dev

# Staging
export AI_BRAIN_ENVIRONMENT=staging

# Production (require approvals - default)
export AI_BRAIN_ENVIRONMENT=production
```

### Web Search Configuration

```bash
# Tavily AI (recommended)
export TAVILY_API_KEY=your-key

# Serper.dev (alternative)
export SERPER_API_KEY=your-key
```

---

## File Structure

```
close-to-zero-prompting-ai-brain/
├── config.py                    # Central configuration & LLM provider
├── meta_agent.py                # Main orchestrator
├── autonomous_builder.py        # Complete system building
├── autonomous_router.py         # Intelligent task routing
├── design_consultant.py         # Architecture design with Q&A
├── architecture_agent.py        # System architecture generation
├── observability_generator.py   # Monitoring tool creation
├── governance.py                # Traffic Light Protocol
├── auth_broker.py              # Identity management
├── fact_checker.py             # Validation & memory
├── autonomous_orchestrator.py  # Execution coordinator
├── llm_provider.py             # LLM abstraction layer
├── output_sanitizer.py         # Sensitive data removal
├── cost_tracker.py             # Token/cost tracking
├── context_manager.py          # Context window management
├── emergency_stop.py           # Global kill switch
├── approve.py                  # Approval CLI
├── sub_agents/
│   ├── base_agent.py          # Base class for all agents
│   ├── consulting_agent.py    # Analysis & recommendations
│   ├── docker_agent.py        # Container operations
│   └── config_agent.py        # Configuration management
├── mcp_servers/
│   ├── docker_tools.py        # Docker MCP server
│   ├── homeassistant_tools.py # Home Assistant MCP server
│   └── web_search_tools.py    # Web search MCP server
├── .env                       # Environment variables (gitignored)
├── .secrets/                  # OAuth tokens (gitignored)
├── .agent_memory.json         # Agent learning memory
└── requirements.txt           # Python dependencies
```

---

## Best Practices

### 1. **Start Simple**
- Let the agent handle routine tasks autonomously
- Only intervene for critical operations
- Trust the governance framework

### 2. **Use Approvals Wisely**
- Review change plans before approval
- Understand what the agent will do
- Reject if unsure—you can always try again

### 3. **Authentication Security**
- **Never** paste credentials in chat
- Use host inheritance for CLI tools (AWS, K8s)
- Use `.env` file for API keys
- Use OAuth for user data (Gmail, Calendar)

### 4. **Monitor Memory**
- Check `.agent_memory.json` periodically
- Review learned patterns
- Clear if agent behavior becomes stale

### 5. **Environment-Aware Development**
- Use `dev` environment for fast iteration
- Use `production` for safety-critical operations
- Test in `staging` before production

### 6. **LLM Provider Selection**
- **Ollama**: Free, private, good for most tasks
- **OpenAI**: Better reasoning, costs money
- **Anthropic**: Good balance, costs money
- Start with Ollama, upgrade if needed

---

## Troubleshooting

### Ollama Issues

**Ollama not running**:
```bash
# Start Ollama
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

**Model not found**:
```bash
# Pull the model
ollama pull gemma3:4b

# List available models
ollama list
```

### Agent Stuck in Loop

```bash
# Check error history
cat .agent_memory.json | jq '.error_history'

# Clear memory if needed
rm .agent_memory.json
```

### Tool Not Found

```bash
# Check available tools
python -c "from meta_agent import MetaAgent; print(MetaAgent()._discover_tools())"

# Check MCP servers directory
ls mcp_servers/

# Verify hot-reload worked
grep "Tool.*available" logs/
```

### Authentication Issues

**AWS**:
```bash
# Check credentials
aws sts get-caller-identity

# Configure if needed
aws configure
```

**Kubernetes**:
```bash
# Check config
kubectl cluster-info

# Update kubeconfig
aws eks update-kubeconfig --name cluster --region region
```

**API Keys**:
```bash
# Check .env file (without exposing keys)
cat .env | grep -v "KEY\|PASSWORD"

# Verify environment variables
env | grep AI_BRAIN
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check virtual environment is activated
which python  # Should show venv path

# Verify Python version
python --version  # Should be 3.11+
```

### LLM Provider Issues

**OpenAI/Anthropic**:
```bash
# Check API key is set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test API connection
python -c "from config import get_llm_provider_from_user; get_llm_provider_from_user(skip_prompt=True)"
```

---

## Advanced Usage

### Non-Interactive Mode

```bash
# Use environment variables to skip prompts
export AI_BRAIN_LLM_PROVIDER=ollama
export AI_BRAIN_ENVIRONMENT=dev

# Run without interaction
python meta_agent.py "your task"
```

### Batch Operations

```bash
# Create a task file
cat > tasks.txt << EOF
Check Docker logs
Deploy new version
Run health checks
EOF

# Process tasks
while read task; do
  python meta_agent.py "$task"
done < tasks.txt
```

### Custom Tool Development

```python
# Create a new MCP server in mcp_servers/

# Example: mcp_servers/custom_tool.py
from typing import Dict, Any

def custom_operation(param: str) -> Dict[str, Any]:
    """Your custom tool logic."""
    return {"result": "success"}

# Register in governance.py
TOOL_RISK_MAP = {
    "custom_operation": RiskLevel.GREEN,  # or YELLOW, RED
}

# Tool will be auto-discovered on next run
```

---

## Contributing

Contributions are welcome! When adding new features:

1. **Create MCP Server**: Add to `mcp_servers/`
2. **Register in Governance**: Add to `governance.py`
3. **Update Documentation**: Add examples and usage
4. **Test**: Verify in dev environment
5. **Submit PR**: With clear description

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues or questions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs in `/docs` folder
- **Memory**: Review `.agent_memory.json` for learned patterns
- **Community**: Join discussions

---

## Acknowledgments

Built with:
- **LangChain** & **LangGraph** - Agent orchestration
- **Ollama** - Local LLM runtime
- **Model Context Protocol (MCP)** - Tool abstraction

---

**The Close-to-Zero Prompting AI Brain** - *Autonomous, Self-Evolving, Secure.*

> "Give it a goal, approve critical steps, let it build."

**Version**: 1.0.0
**Status**: Production Ready
**Philosophy**: Close to Zero Prompting

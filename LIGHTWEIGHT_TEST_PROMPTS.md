# Lightweight Test Prompts for AI Brain

## Quick Test Scenarios (Resource-Friendly)

These prompts test the system's capabilities without requiring heavy resources:

### 🎯 Recommended Test (Best Balance)

**Prompt:**
```
Build a simple log monitoring system that watches a log file and alerts on errors - keep it lightweight for a small laptop
```

**What it tests:**
- ✅ Design consultant (Q&A about log format, alerting needs)
- ✅ Design options (file watcher vs polling, simple vs complex)
- ✅ Governance (file reading/writing permissions)
- ✅ System building (creates monitoring script)
- ✅ Lightweight (no containers, minimal dependencies)

**Expected flow:**
1. Asks: "What log file format?" (JSON, plain text, etc.)
2. Asks: "How should alerts be delivered?" (console, file, email)
3. Presents options: Simple file watcher vs Advanced monitoring
4. You select option
5. Asks for resource quotas (minimal - just file watching)
6. Builds Python script with file watching
7. Governance checks file operations

---

### 🧪 Alternative Test 1: Configuration Manager

**Prompt:**
```
Build a simple configuration management tool that can read, validate, and update YAML config files safely
```

**What it tests:**
- ✅ Design consultant (Q&A about config structure)
- ✅ Design options (CLI tool vs library, validation level)
- ✅ Governance (file write permissions - YELLOW)
- ✅ System building (creates config tool)
- ✅ Lightweight (Python script, YAML library)

---

### 🧪 Alternative Test 2: API Health Checker

**Prompt:**
```
Build a lightweight API health checker that monitors endpoints and reports status - no heavy dependencies
```

**What it tests:**
- ✅ Design consultant (Q&A about endpoints, check frequency)
- ✅ Design options (simple polling vs advanced monitoring)
- ✅ Governance (network operations - GREEN)
- ✅ System building (creates health checker)
- ✅ Lightweight (requests library, simple polling)

---

### 🧪 Alternative Test 3: File Backup Tool

**Prompt:**
```
Build a simple file backup tool that can backup directories with versioning - keep it simple and lightweight
```

**What it tests:**
- ✅ Design consultant (Q&A about backup location, retention)
- ✅ Design options (simple copy vs compression, local vs remote)
- ✅ Governance (file operations - YELLOW)
- ✅ System building (creates backup script)
- ✅ Lightweight (Python stdlib, no external deps)

---

## Running the Tests

### Option 1: Single Test (Recommended)
```bash
python autonomous_orchestrator.py "Build a simple log monitoring system that watches a log file and alerts on errors - keep it lightweight for a small laptop"
```

### Option 2: Batch Test
```bash
chmod +x QUICK_TEST_LIGHTWEIGHT.sh
./QUICK_TEST_LIGHTWEIGHT.sh
```

### Option 3: Direct Design Consultant Test
```bash
python autonomous_builder.py "Build a simple log monitoring system that watches a log file and alerts on errors - keep it lightweight for a small laptop"
```

---

## What to Observe

### ✅ Design Consultant Behavior
- Does it ask targeted questions?
- Are the questions relevant?
- Does it present multiple options?
- Are pros/cons clear?

### ✅ Governance Behavior
- Does it check permissions before file operations?
- Are YELLOW operations flagged for approval?
- Are GREEN operations auto-executed?

### ✅ System Building Behavior
- Does it create the system?
- Are files created in appropriate locations?
- Does it handle errors gracefully?

### ✅ Resource Usage
- Does it stay lightweight?
- No heavy containers started?
- Minimal dependencies?

---

## Expected Output Example

```
🧠 AUTONOMOUS EXECUTION: Build a simple log monitoring system...
======================================================================

📋 DESIGN CONSULTATION: Gathering Context
======================================================================

   I need to ask 3 question(s) to make the best design decisions:

   1. What log file format do you need to monitor?
      Options: JSON, Plain text, CSV, Other
   > Plain text

   2. How should alerts be delivered?
      Options: Console output, File, Email, None
   > Console output

   3. What error patterns should trigger alerts?
   > ERROR, FATAL, CRITICAL

======================================================================
🎯 DESIGN OPTIONS
======================================================================

   Option 1: Simple File Watcher
   ✅ Pros:
      • Lightweight and fast
      • No external dependencies
      • Easy to understand
   ❌ Cons:
      • Basic functionality only
      • No advanced filtering
   📊 Recommendation Score: 0.85/1.0
   💰 Estimated Cost: Low
   🔧 Complexity: Simple

   Option 2: Advanced Monitoring with Regex
   ✅ Pros:
      • Powerful pattern matching
      • Configurable filters
      • Better error detection
   ❌ Cons:
      • More complex
      • Requires regex knowledge
   📊 Recommendation Score: 0.70/1.0
   💰 Estimated Cost: Low
   🔧 Complexity: Medium

   💡 Recommendation: Option 1 (Simple File Watcher)

   Which option would you like to proceed with? (1-2)
   > 1

======================================================================
📊 RESOURCE QUOTAS
======================================================================

   Cluster/Infrastructure Sizing:
   What size cluster do you need?
   > None - single script

   Compute Resources:
   CPU cores per node?
   > 1

   Memory per node?
   > 100MB

   Storage:
   Total storage needed?
   > 10MB

======================================================================
🔐 AUTHENTICATION
======================================================================

   ✅ No authentication required

======================================================================
🚀 SYSTEM BUILDING
======================================================================

   📐 Architecture designed:
      Components: 1
      Deployment: local script

   🔧 Generating tools...
   ✅ Generated: log_monitor.py

   ✅ System built successfully!
```

---

## Troubleshooting

### If design consultant doesn't activate:
- Check that the prompt contains keywords: "build", "create", "system"
- Try using `autonomous_builder.py` directly instead of `autonomous_orchestrator.py`

### If governance doesn't enforce:
- Check that `base_agent.py` has governance checks
- Verify environment is set correctly (production = stricter)

### If system doesn't build:
- Check Ollama is running: `ollama list`
- Verify Python dependencies are installed
- Check for error messages in output

---

## Success Criteria

✅ **Design Consultant:**
- Asked at least 2 targeted questions
- Presented 2+ design options
- Got user selection

✅ **Governance:**
- Checked permissions before file operations
- Flagged YELLOW operations appropriately
- Auto-executed GREEN operations

✅ **System Building:**
- Created at least one file
- File is functional (can be run/tested)
- No heavy resource usage

✅ **Overall:**
- Completed in < 5 minutes
- Used < 500MB memory
- No containers or heavy processes started


# Self-Healing System Guide

## Overview

The AI Brain now has **self-healing capabilities** that allow it to detect, analyze, and fix issues in its own codebase. When the system encounters errors related to scalability, reliability, auditability, or governance, it can:

1. **Detect** if the error is in its own codebase
2. **Analyze** the root cause and classify the issue
3. **Propose** fixes using LLM
4. **Validate** fixes before applying
5. **Apply** fixes safely with rollback capability
6. **Learn** from successes and failures

---

## How It Works

### 1. Error Detection

When an exception occurs during execution, the self-healing system:

- Analyzes the stack trace to determine if the error is in the codebase
- Checks for codebase file patterns (e.g., `autonomous_orchestrator.py`, `sub_agents/`, etc.)
- Identifies error types that indicate codebase issues (AttributeError, NameError, etc.)

**Example:**
```python
# If this error occurs:
AttributeError: 'OutputSanitizer' object has no attribute 'has_secrets'

# The system detects:
- File: output_sanitizer.py
- Issue Type: reliability
- Severity: critical
- Root Cause: Missing method 'has_secrets'
```

### 2. Issue Classification

Issues are classified into categories:

- **Scalability**: Timeouts, blocking operations, deadlocks
- **Reliability**: Missing methods, undefined variables, NoneType errors
- **Auditability**: Logging issues, missing audit trails
- **Governance**: Permission errors, approval workflow issues
- **Performance**: Slow operations, resource leaks
- **Bug**: General code bugs

### 3. Fix Proposal

The system uses an LLM to propose fixes:

- Analyzes the error and root cause
- Reads the relevant file (if available)
- Proposes a fix that:
  - Addresses the immediate error
  - Fixes the root cause
  - Maintains backward compatibility
  - Follows existing code style
  - Improves scalability, reliability, auditability, governance

### 4. Fix Validation

Before applying, fixes are validated:

- ✅ **Syntax Check**: Ensures valid Python syntax
- ✅ **Safety Check**: Detects dangerous patterns (exec, eval, destructive operations)
- ✅ **Import Check**: Validates imports are reasonable
- ✅ **Issue Coverage**: Ensures fix addresses the actual issue

### 5. Governance Integration

Self-modification requires governance approval:

- **Dev/Staging**: Auto-approved for critical reliability issues
- **Production**: Always requires approval
- Uses the Traffic Light Protocol (RED risk level)

### 6. Safe Application

Fixes are applied with safety measures:

- **Backup**: Creates backup before modification
- **Validation**: Syntax checks after application
- **Rollback**: Automatically rolls back if fix introduces errors
- **History**: Records all healing attempts for learning

---

## Integration Points

### Orchestrator Integration

The self-healing system is integrated into `autonomous_orchestrator.py`:

```python
except Exception as e:
    # Attempt self-healing for codebase errors
    healing_result = healing_system.detect_and_heal(
        error=e,
        stack_trace=traceback.format_exc(),
        context={"task": task, "agent": agent.agent_name}
    )
    
    if healing_result.success:
        # Retry execution after healing
        result = agent.execute(task, context)
```

### Governance Registration

Self-modification is registered in `governance.py`:

```python
ToolGovernance(
    "self_modify_codebase",
    RiskLevel.RED,
    "Self-modify codebase (self-healing)",
    True,
    "⚠️ CRITICAL: I want to modify my own codebase to fix an issue. Approve?",
    allowed_contexts=["dev", "staging"]
)
```

---

## Usage Examples

### Example 1: Missing Method

**Error:**
```
AttributeError: 'OutputSanitizer' object has no attribute 'has_secrets'
```

**Self-Healing Process:**
1. Detects codebase error in `output_sanitizer.py`
2. Classifies as "reliability" issue, severity "critical"
3. Proposes fix: Adds `has_secrets()` method
4. Validates fix (syntax OK, safe)
5. Requests approval (if in production)
6. Applies fix with backup
7. Retries execution

### Example 2: Scalability Issue

**Error:**
```
TimeoutError: Operation timed out after 60 seconds
```

**Self-Healing Process:**
1. Detects timeout in async operation
2. Classifies as "scalability" issue
3. Proposes fix: Adds timeout handling, async improvements
4. Validates and applies
5. Improves system scalability

### Example 3: Governance Issue

**Error:**
```
PermissionError: Tool requires approval but approval not granted
```

**Self-Healing Process:**
1. Detects governance workflow issue
2. Classifies as "governance" issue
3. Proposes fix: Improves approval workflow
4. Requires approval (meta-governance!)
5. Applies fix to improve governance

---

## Configuration

### Environment-Based Behavior

- **Dev/Staging**: Auto-approves critical reliability fixes
- **Production**: Always requires approval
- **Local**: Full self-healing enabled

### Learning and Memory

The system learns from healing attempts:

- Records successful fixes
- Tracks failed attempts
- Avoids retrying same fix immediately
- Uses FactChecker for pattern recognition

---

## Safety Features

### 1. Backup System

All modifications are backed up to `.self_healing_backups/`:
```
.self_healing_backups/
  output_sanitizer.py.20241201_143022.bak
  autonomous_orchestrator.py.20241201_150145.bak
```

### 2. Rollback Capability

If a fix introduces errors:
- Automatically rolls back to backup
- Reports rollback in result
- Records failure for learning

### 3. Validation Layers

Multiple validation layers:
- Syntax validation
- Safety pattern detection
- Import validation
- Issue coverage check

### 4. Governance Oversight

- Requires approval for self-modification
- Tracks all modifications
- Can be disabled via governance

---

## Limitations

### Current Limitations

1. **Partial Fixes**: AST-based merging for partial fixes not fully implemented
2. **Complex Refactoring**: Can't handle large-scale refactorings
3. **Test Coverage**: Doesn't run tests before applying fixes
4. **Multi-File Changes**: Currently handles single-file fixes

### Future Enhancements

- [ ] AST-based code merging for partial fixes
- [ ] Test execution before applying fixes
- [ ] Multi-file fix coordination
- [ ] Learning from external codebases
- [ ] Proactive issue detection (before errors occur)

---

## Monitoring

### Healing History

All healing attempts are recorded in `self_healing.healing_history`:

```python
{
    "timestamp": "2024-12-01T14:30:22",
    "issue_hash": "a1b2c3d4",
    "issue_type": "reliability",
    "severity": "critical",
    "file": "output_sanitizer.py",
    "validation": {...},
    "success": True,
    "fix_preview": "def has_secrets(self, text: str) -> bool:..."
}
```

### FactChecker Integration

Healing attempts are recorded in FactChecker:
- Successes: `fact_checker.record_success("self_healing", ...)`
- Failures: `fact_checker.record_failure("self_healing", ...)`

---

## Best Practices

### 1. Review Healing Attempts

Regularly review `.self_healing_backups/` to understand what was fixed.

### 2. Monitor Approval Requests

In production, monitor approval requests for self-modification.

### 3. Test After Healing

After self-healing, run tests to ensure system still works correctly.

### 4. Version Control

Commit self-healing changes to version control for audit trail.

---

## Troubleshooting

### Issue: Self-healing not triggering

**Check:**
- Error is in codebase (not external)
- Stack trace includes codebase files
- Error type is recognized

### Issue: Fix not applied

**Check:**
- Governance approval granted (if required)
- Fix validation passed
- File exists and is writable

### Issue: Rollback occurred

**Check:**
- Fix introduced syntax error
- Fix didn't address the issue
- File permissions issue

---

## API Reference

### `SelfHealingSystem.detect_and_heal()`

Main entry point for self-healing.

**Parameters:**
- `error`: Exception that occurred
- `stack_trace`: Full stack trace string
- `context`: Execution context dict

**Returns:**
- `SelfHealingResult` with healing details

### `CodebaseAnalyzer.is_codebase_error()`

Determines if error is in codebase.

**Returns:**
- `bool`: True if codebase error

### `FixProposer.propose_fix()`

Proposes fix for issue.

**Returns:**
- `str`: Proposed fix code, or None

### `FixValidator.validate_fix()`

Validates proposed fix.

**Returns:**
- `Dict` with validation results

---

## Conclusion

The self-healing system enables the AI Brain to improve itself autonomously while maintaining safety through governance, validation, and rollback capabilities. It learns from its mistakes and becomes more reliable over time.

**Key Benefits:**
- ✅ Automatic bug fixes
- ✅ Scalability improvements
- ✅ Reliability enhancements
- ✅ Governance improvements
- ✅ Self-improvement over time

**Safety Guarantees:**
- ✅ Governance oversight
- ✅ Validation before application
- ✅ Backup and rollback
- ✅ Learning from failures


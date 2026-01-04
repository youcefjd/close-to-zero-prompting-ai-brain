# Query Capabilities & Generalization

## Overview

The AI Brain is **fully general** and can handle **any type of query** - not just local system queries. The system uses semantic understanding to determine whether a query is about:

1. **LOCAL system information** (this computer) → uses `run_shell`
2. **EXTERNAL information** (internet/world) → uses `web_search`

---

## Query Types Supported

### ✅ Local System Queries
- Battery status: "what's my macbook battery status"
- Volume: "what's my macbook volume status"
- Disk usage: "how much disk space do I have"
- Memory: "what's my memory usage"
- Processes: "what processes are running"
- System info: "what OS am I running"
- **Any system information about THIS computer**

### ✅ External Information Queries
- **Sports scores**: "what's the score of tunisia vs mali"
- **Current events**: "latest news about X"
- **General knowledge**: "how does Y work"
- **Comparisons**: "compare A vs B"
- **Facts**: "what is X", "when did Y happen"
- **Technical information**: "latest version of X", "how to do Y"
- **Any information from the internet/world**

### ✅ Analysis & Recommendations
- "Should I use X or Y?"
- "What's the best approach for Z?"
- "Compare these options"
- "Analyze this situation"

---

## How It Works

### Semantic Understanding (Not Keyword Matching)

The system uses **LLM semantic understanding** to determine query type:

```python
# System Prompt (ConsultingAgent):
- Understand whether the query is about LOCAL system information 
  (use run_shell) or EXTERNAL information (use web_search)
- LOCAL: Information about THIS computer/system
- EXTERNAL: Information from the internet/world
- Generalize understanding to handle ANY query type
```

### No Hardcoding

- ❌ **No keyword lists** - understands context semantically
- ❌ **No pattern matching** - generalizes to new query types
- ✅ **Pure semantic understanding** - LLM determines intent
- ✅ **Self-healing** - corrects mistakes automatically

---

## Examples

### Local System Query
```
User: "what's my macbook volume status currently"
→ System understands: LOCAL system query
→ Uses: run_shell("osascript -e 'output volume of (get volume settings)'")
→ Returns: Actual volume status
```

### External Information Query
```
User: "what's the score of tunisia vs mali"
→ System understands: EXTERNAL information query
→ Uses: web_search("tunisia vs mali score live")
→ Returns: Current score from web
```

### General Knowledge Query
```
User: "how does Kubernetes work"
→ System understands: EXTERNAL information query
→ Uses: web_search("how does Kubernetes work")
→ Returns: Explanation from web
```

### Comparison Query
```
User: "compare Docker vs Podman"
→ System understands: EXTERNAL information query
→ Uses: web_search("Docker vs Podman comparison")
→ Returns: Comparison from web
```

---

## Error Handling & Self-Healing

### When run_shell Fails

If `run_shell` fails, the system:
1. **Understands semantically** whether the query is local or external
2. **If local**: Tries to determine the correct command
3. **If external**: Suggests using `web_search` instead
4. **Self-heals** by retrying with corrected approach

### No Assumptions

The system **does not assume** all queries are local. It:
- Analyzes the query semantically
- Determines if it's local or external
- Uses the appropriate tool
- Self-corrects if wrong

---

## Generalization

The system can handle **any query type** because:

1. **Semantic understanding** - not limited to specific patterns
2. **Tool selection** - chooses the right tool based on understanding
3. **Self-healing** - corrects mistakes automatically
4. **No hardcoding** - generalizes to new query types

### What It Can Handle

✅ Local system queries (any OS)
✅ External information queries (any topic)
✅ Analysis & recommendations
✅ Comparisons
✅ Current events
✅ Technical questions
✅ General knowledge
✅ **Any query that requires information**

---

## Architecture

### ConsultingAgent
- Handles **all information queries** (local + external)
- Uses semantic understanding to choose tools
- Self-heals on errors
- Generalizes to new query types

### Tool Selection
- **run_shell**: For local system information
- **web_search**: For external information
- **Both available** - system chooses based on query

---

## Key Points

1. ✅ **Fully general** - handles any query type
2. ✅ **Semantic understanding** - not keyword matching
3. ✅ **Self-healing** - corrects mistakes automatically
4. ✅ **No hardcoding** - generalizes to new queries
5. ✅ **Local + External** - handles both types seamlessly

The system is **not limited** to local system queries - it can answer **any question** by understanding whether it needs local system information or external information.


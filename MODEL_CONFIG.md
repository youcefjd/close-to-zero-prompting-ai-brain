# Model Configuration

## Current Model: `gemma3:4b`

The system is now configured to use **Gemma 3 4B** as the default LLM model.

## Updated Files

All model references have been updated in:
- `llm_provider.py` - Default model in OllamaProvider
- `autonomous_router.py` - Router LLM
- `meta_agent.py` - Meta agent LLM instances
- `sub_agents/base_agent.py` - Base agent LLM
- `agent.py` - LangGraph agent
- `agent_enhanced.py` - Enhanced agent

## Verify Model is Installed

```bash
ollama list | grep gemma3
```

Should show:
```
gemma3:4b    ...    3.3 GB    ...
```

## If Model Not Installed

```bash
ollama pull gemma3:4b
```

## Test the Configuration

```bash
source venv/bin/activate
python3 autonomous_orchestrator.py "build a raspberry pie type of server that blocks ads on my network"
```

The system will now use `gemma3:4b` for all LLM operations.


"""Central configuration for the AI Brain system.

This module provides centralized configuration and LLM provider selection.
"""

import os
from typing import Optional, Dict, Any
from llm_provider import create_llm_provider, LLMProvider


# Default Configuration
DEFAULT_LLM_PROVIDER = "ollama"  # Default to local Ollama (free, private)
DEFAULT_LLM_MODEL = "gemma3:4b"
DEFAULT_LLM_TEMPERATURE = 0.7
DEFAULT_ENVIRONMENT = "production"  # Safe default: requires approvals
MAX_RETRIES = 5
TIMEOUT = 30


def get_llm_provider_from_user(skip_prompt: bool = False) -> LLMProvider:
    """Prompt user for LLM provider selection or use defaults.

    Args:
        skip_prompt: If True, skip user prompt and use defaults

    Returns:
        Configured LLMProvider instance
    """
    # Check if already configured via environment variable
    provider_type = os.getenv("AI_BRAIN_LLM_PROVIDER")
    if provider_type:
        print(f"   Using LLM provider from environment: {provider_type}")
        return _create_provider_from_env(provider_type)

    # Skip prompt if requested (for non-interactive usage)
    if skip_prompt:
        return create_llm_provider(DEFAULT_LLM_PROVIDER, model=DEFAULT_LLM_MODEL)

    # Interactive prompt
    print("\n" + "="*70)
    print("🧠 AI BRAIN - LLM PROVIDER SELECTION")
    print("="*70)

    print(f"""
   This system can use different LLM providers. Choose one:

   1. Ollama (Local) - RECOMMENDED ✅
      • Runs locally on your machine (private, free)
      • Model: {DEFAULT_LLM_MODEL}
      • Requires: Ollama installed (https://ollama.ai)
      • Cost: Free
      • Privacy: Complete (data never leaves your machine)

   2. OpenAI (Commercial)
      • Uses OpenAI's GPT models
      • Model: gpt-4 (configurable)
      • Requires: OpenAI API key
      • Cost: ~$0.03 per 1K tokens (input)
      • Privacy: Data sent to OpenAI

   3. Anthropic Claude (Commercial)
      • Uses Anthropic's Claude models
      • Model: claude-3-sonnet (configurable)
      • Requires: Anthropic API key
      • Cost: ~$0.003 per 1K tokens (input)
      • Privacy: Data sent to Anthropic
    """)

    print("   Enter your choice (1-3) [default: 1 - Ollama]: ", end="")

    try:
        choice = input().strip()
    except EOFError:
        # Non-interactive mode, use default
        choice = "1"

    if not choice or choice == "1":
        # Ollama (default)
        print("\n   ✅ Using Ollama (local)")
        print(f"   Model: {DEFAULT_LLM_MODEL}")
        print(f"\n   💡 Make sure Ollama is running: ollama serve")
        print(f"   💡 Pull the model if needed: ollama pull {DEFAULT_LLM_MODEL}")
        return create_llm_provider("ollama", model=DEFAULT_LLM_MODEL)

    elif choice == "2":
        # OpenAI
        print("\n   Selected: OpenAI")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            print("\n   ⚠️  OpenAI API key not found in environment")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
            print("   Or add to .env file: OPENAI_API_KEY=your-key-here")
            print("\n   Falling back to Ollama...")
            return create_llm_provider("ollama", model=DEFAULT_LLM_MODEL)

        print("   ✅ OpenAI API key found")

        # Ask for model
        print("   Enter model [default: gpt-4]: ", end="")
        model = input().strip() or "gpt-4"

        return create_llm_provider("openai", model=model, api_key=api_key)

    elif choice == "3":
        # Anthropic
        print("\n   Selected: Anthropic Claude")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("\n   ⚠️  Anthropic API key not found in environment")
            print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")
            print("   Or add to .env file: ANTHROPIC_API_KEY=your-key-here")
            print("\n   Falling back to Ollama...")
            return create_llm_provider("ollama", model=DEFAULT_LLM_MODEL)

        print("   ✅ Anthropic API key found")

        # Ask for model
        print("   Enter model [default: claude-3-sonnet-20240229]: ", end="")
        model = input().strip() or "claude-3-sonnet-20240229"

        return create_llm_provider("anthropic", model=model, api_key=api_key)

    else:
        print(f"\n   ⚠️  Invalid choice: {choice}")
        print("   Falling back to Ollama (local)")
        return create_llm_provider("ollama", model=DEFAULT_LLM_MODEL)


def _create_provider_from_env(provider_type: str) -> LLMProvider:
    """Create LLM provider from environment configuration.

    Args:
        provider_type: Provider type from environment

    Returns:
        Configured LLMProvider instance
    """
    model = os.getenv("AI_BRAIN_LLM_MODEL")

    if provider_type.lower() == "ollama":
        return create_llm_provider(
            "ollama",
            model=model or DEFAULT_LLM_MODEL
        )
    elif provider_type.lower() == "openai":
        return create_llm_provider(
            "openai",
            model=model or "gpt-4",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif provider_type.lower() == "anthropic":
        return create_llm_provider(
            "anthropic",
            model=model or "claude-3-sonnet-20240229",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    else:
        print(f"   ⚠️  Unknown provider: {provider_type}, using Ollama")
        return create_llm_provider("ollama", model=DEFAULT_LLM_MODEL)


def get_config() -> Dict[str, Any]:
    """Get system configuration.

    Returns:
        Configuration dictionary
    """
    return {
        "llm_provider": os.getenv("AI_BRAIN_LLM_PROVIDER", DEFAULT_LLM_PROVIDER),
        "llm_model": os.getenv("AI_BRAIN_LLM_MODEL", DEFAULT_LLM_MODEL),
        "llm_temperature": float(os.getenv("AI_BRAIN_LLM_TEMPERATURE", str(DEFAULT_LLM_TEMPERATURE))),
        "environment": os.getenv("AI_BRAIN_ENVIRONMENT", DEFAULT_ENVIRONMENT),
        "max_retries": int(os.getenv("AI_BRAIN_MAX_RETRIES", str(MAX_RETRIES))),
        "timeout": int(os.getenv("AI_BRAIN_TIMEOUT", str(TIMEOUT))),
    }


# Environment variable documentation
"""
Environment Variables:
----------------------

AI_BRAIN_LLM_PROVIDER: LLM provider to use (ollama, openai, anthropic)
    Default: ollama
    Example: export AI_BRAIN_LLM_PROVIDER=ollama

AI_BRAIN_LLM_MODEL: Model name for the provider
    Default: gemma3:4b (for ollama)
    Example: export AI_BRAIN_LLM_MODEL=gemma3:4b

AI_BRAIN_LLM_TEMPERATURE: Temperature for LLM responses (0.0-1.0)
    Default: 0.7
    Example: export AI_BRAIN_LLM_TEMPERATURE=0.7

AI_BRAIN_ENVIRONMENT: Execution environment (dev, staging, production)
    Default: production
    Example: export AI_BRAIN_ENVIRONMENT=dev

AI_BRAIN_MAX_RETRIES: Maximum retries for failed operations
    Default: 5
    Example: export AI_BRAIN_MAX_RETRIES=5

AI_BRAIN_TIMEOUT: Timeout for operations in seconds
    Default: 30
    Example: export AI_BRAIN_TIMEOUT=30

OPENAI_API_KEY: API key for OpenAI (if using OpenAI provider)
    Example: export OPENAI_API_KEY=sk-...

ANTHROPIC_API_KEY: API key for Anthropic (if using Anthropic provider)
    Example: export ANTHROPIC_API_KEY=sk-ant-...

Usage Examples:
--------------

# Use local Ollama (default):
python meta_agent.py "your task"

# Use OpenAI with environment variable:
export AI_BRAIN_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
python meta_agent.py "your task"

# Use Anthropic:
export AI_BRAIN_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python meta_agent.py "your task"

# Use dev environment (auto-approve yellow tasks):
export AI_BRAIN_ENVIRONMENT=dev
python meta_agent.py "your task"
"""

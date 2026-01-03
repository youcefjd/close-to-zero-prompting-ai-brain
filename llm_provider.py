"""LLM Provider Abstraction: Allows swapping LLM providers without code changes.

This module provides an abstraction layer for LLM providers, enabling
easy switching between Ollama, OpenAI, Anthropic, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama

# Try to import AsyncChatOllama, fallback to ChatOllama if not available
try:
    from langchain_ollama import AsyncChatOllama
except ImportError:
    # AsyncChatOllama not available in this version, use ChatOllama for both
    AsyncChatOllama = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def ainvoke(self, messages: List[BaseMessage]) -> str:
        """Invoke LLM asynchronously.
        
        Args:
            messages: List of messages to send to LLM
            
        Returns:
            Response content as string
        """
        pass
    
    @abstractmethod
    def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke LLM synchronously.
        
        Args:
            messages: List of messages to send to LLM
            
        Returns:
            Response content as string
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get cost per 1k tokens (input and output).
        
        Returns:
            Dict with 'input' and 'output' costs per 1k tokens
        """
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation."""
    
    def __init__(self, model: str = "gemma3:4b", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.llm = ChatOllama(model=model, temperature=temperature)
        # Use AsyncChatOllama if available, otherwise use sync ChatOllama
        if AsyncChatOllama is not None:
            self.async_llm = AsyncChatOllama(model=model, temperature=temperature)
        else:
            self.async_llm = None  # Will use sync version in ainvoke
    
    async def ainvoke(self, messages: List[BaseMessage]) -> str:
        """Invoke Ollama asynchronously."""
        if self.async_llm is not None:
            response = await self.async_llm.ainvoke(messages)
        else:
            # Fallback to sync version (not ideal but works)
            import asyncio
            response = await asyncio.to_thread(self.llm.invoke, messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke Ollama synchronously."""
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for Ollama (rough approximation: ~4 chars per token)."""
        # Rough approximation: Ollama models typically use ~4 characters per token
        return len(text) // 4
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Ollama is free (local), so cost is 0."""
        return {"input": 0.0, "output": 0.0}


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7, api_key: Optional[str] = None):
        from langchain_openai import ChatOpenAI, AsyncChatOpenAI
        
        self.model = model
        self.temperature = temperature
        self.llm = ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
        self.async_llm = AsyncChatOpenAI(model=model, temperature=temperature, api_key=api_key)
        
        # Cost per 1k tokens (as of 2024)
        self.cost_map = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        }
    
    async def ainvoke(self, messages: List[BaseMessage]) -> str:
        """Invoke OpenAI asynchronously."""
        response = await self.async_llm.ainvoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke OpenAI synchronously."""
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for OpenAI (rough approximation: ~4 chars per token)."""
        # OpenAI uses tiktoken, but for estimation: ~4 chars per token
        return len(text) // 4
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get cost per 1k tokens for the model."""
        return self.cost_map.get(self.model, {"input": 0.01, "output": 0.03})


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    def __init__(self, model: str = "claude-3-opus-20240229", temperature: float = 0.7, api_key: Optional[str] = None):
        from langchain_anthropic import ChatAnthropic, AsyncChatAnthropic
        
        self.model = model
        self.temperature = temperature
        self.llm = ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        self.async_llm = AsyncChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        
        # Cost per 1k tokens (as of 2024)
        self.cost_map = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }
    
    async def ainvoke(self, messages: List[BaseMessage]) -> str:
        """Invoke Anthropic asynchronously."""
        response = await self.async_llm.ainvoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def invoke(self, messages: List[BaseMessage]) -> str:
        """Invoke Anthropic synchronously."""
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for Anthropic (rough approximation: ~4 chars per token)."""
        return len(text) // 4
    
    def get_cost_per_1k_tokens(self) -> Dict[str, float]:
        """Get cost per 1k tokens for the model."""
        return self.cost_map.get(self.model, {"input": 0.003, "output": 0.015})


def create_llm_provider(
    provider_type: str = "ollama",
    model: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> LLMProvider:
    """Factory function to create LLM provider.
    
    Args:
        provider_type: Type of provider ("ollama", "openai", "anthropic")
        model: Model name (optional, uses defaults)
        temperature: Temperature setting
        **kwargs: Additional provider-specific arguments
        
    Returns:
        LLMProvider instance
    """
    if provider_type.lower() == "ollama":
        return OllamaProvider(
            model=model or "gemma3:4b",
            temperature=temperature
        )
    elif provider_type.lower() == "openai":
        return OpenAIProvider(
            model=model or "gpt-4",
            temperature=temperature,
            api_key=kwargs.get("api_key")
        )
    elif provider_type.lower() == "anthropic":
        return AnthropicProvider(
            model=model or "claude-3-sonnet-20240229",
            temperature=temperature,
            api_key=kwargs.get("api_key")
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


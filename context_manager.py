"""Context Manager: Manages LLM context with pruning and token counting.

This module provides context management to prevent context window overflow
and optimize token usage.
"""

from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from dataclasses import dataclass
import json


@dataclass
class MessageRelevance:
    """Relevance score for a message."""
    message: BaseMessage
    relevance_score: float  # 0.0 to 1.0
    token_count: int
    is_critical: bool  # System messages, recent user messages, etc.


class ContextManager:
    """Manages LLM context with pruning and optimization."""
    
    def __init__(
        self,
        max_tokens: int = 8000,
        keep_system_messages: bool = True,
        keep_last_n_user_messages: int = 3,
        keep_last_n_assistant_messages: int = 3
    ):
        """Initialize context manager.
        
        Args:
            max_tokens: Maximum tokens to keep in context
            keep_system_messages: Always keep system messages
            keep_last_n_user_messages: Always keep last N user messages
            keep_last_n_assistant_messages: Always keep last N assistant messages
        """
        self.max_tokens = max_tokens
        self.keep_system_messages = keep_system_messages
        self.keep_last_n_user_messages = keep_last_n_user_messages
        self.keep_last_n_assistant_messages = keep_last_n_assistant_messages
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough: ~4 chars per token).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def estimate_message_tokens(self, message: BaseMessage) -> int:
        """Estimate tokens for a message.
        
        Args:
            message: Message to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if isinstance(message, SystemMessage):
            content = message.content if hasattr(message, 'content') else str(message)
            return self.estimate_tokens(content) + 10  # Add overhead for message type
        elif isinstance(message, HumanMessage):
            content = message.content if hasattr(message, 'content') else str(message)
            return self.estimate_tokens(content) + 10
        elif isinstance(message, AIMessage):
            content = message.content if hasattr(message, 'content') else str(message)
            return self.estimate_tokens(content) + 10
        else:
            return self.estimate_tokens(str(message)) + 10
    
    def calculate_relevance(self, message: BaseMessage, index: int, total: int) -> MessageRelevance:
        """Calculate relevance score for a message.
        
        Args:
            message: Message to score
            index: Index of message in list
            total: Total number of messages
            
        Returns:
            MessageRelevance with score
        """
        token_count = self.estimate_message_tokens(message)
        is_critical = False
        relevance_score = 0.5  # Default relevance
        
        # System messages are always critical
        if isinstance(message, SystemMessage):
            is_critical = True
            relevance_score = 1.0
        
        # Recent messages are more relevant
        elif index >= total - 5:  # Last 5 messages
            relevance_score = 0.9 - (total - index - 1) * 0.1
        
        # User messages are more relevant than assistant messages
        elif isinstance(message, HumanMessage):
            relevance_score = 0.7
        
        # Tool results might be less relevant if old
        elif isinstance(message, AIMessage):
            if "Tool execution results" in str(message.content):
                relevance_score = 0.4  # Tool results can be summarized
            else:
                relevance_score = 0.6
        
        return MessageRelevance(
            message=message,
            relevance_score=relevance_score,
            token_count=token_count,
            is_critical=is_critical
        )
    
    def prune_context(
        self,
        messages: List[BaseMessage],
        max_tokens: Optional[int] = None
    ) -> List[BaseMessage]:
        """Prune context to stay within token limits.
        
        Args:
            messages: List of messages to prune
            max_tokens: Maximum tokens (uses self.max_tokens if not provided)
            
        Returns:
            Pruned list of messages
        """
        max_tokens = max_tokens or self.max_tokens
        
        if not messages:
            return messages
        
        # Calculate relevance for all messages
        relevances = [
            self.calculate_relevance(msg, i, len(messages))
            for i, msg in enumerate(messages)
        ]
        
        # Always keep system messages and recent user/assistant messages
        critical_indices = set()
        
        # Keep system messages
        if self.keep_system_messages:
            for i, rel in enumerate(relevances):
                if rel.is_critical:
                    critical_indices.add(i)
        
        # Keep last N user messages
        user_messages = [
            i for i, msg in enumerate(messages)
            if isinstance(msg, HumanMessage)
        ]
        for i in user_messages[-self.keep_last_n_user_messages:]:
            critical_indices.add(i)
        
        # Keep last N assistant messages
        assistant_messages = [
            i for i, msg in enumerate(messages)
            if isinstance(msg, AIMessage)
        ]
        for i in assistant_messages[-self.keep_last_n_assistant_messages:]:
            critical_indices.add(i)
        
        # Calculate current token count
        current_tokens = sum(rel.token_count for rel in relevances)
        
        # If within limits, return as-is
        if current_tokens <= max_tokens:
            return messages
        
        # Need to prune - keep critical messages first
        kept_messages = []
        kept_tokens = 0
        
        # First, add all critical messages
        for i in sorted(critical_indices):
            kept_messages.append((i, messages[i]))
            kept_tokens += relevances[i].token_count
        
        # Then, add messages by relevance until we hit the limit
        remaining_messages = [
            (i, rel) for i, rel in enumerate(relevances)
            if i not in critical_indices
        ]
        
        # Sort by relevance (highest first)
        remaining_messages.sort(key=lambda x: x[1].relevance_score, reverse=True)
        
        for i, rel in remaining_messages:
            if kept_tokens + rel.token_count <= max_tokens:
                kept_messages.append((i, messages[i]))
                kept_tokens += rel.token_count
            else:
                break
        
        # Sort by original index to maintain order
        kept_messages.sort(key=lambda x: x[0])
        
        # If we still have too many tokens, summarize old messages
        if kept_tokens > max_tokens * 0.9:  # If we're at 90% capacity
            # Create summary of oldest messages
            oldest_messages = [
                msg for idx, msg in kept_messages
                if idx < len(kept_messages) // 2
            ]
            
            if oldest_messages:
                summary = self._summarize_messages(oldest_messages)
                summary_tokens = self.estimate_tokens(summary)
                
                # Replace oldest messages with summary if it saves tokens
                oldest_tokens = sum(
                    self.estimate_message_tokens(msg) for msg in oldest_messages
                )
                
                if summary_tokens < oldest_tokens * 0.5:  # Summary is at least 50% smaller
                    # Remove oldest messages and add summary
                    kept_messages = [
                        (idx, msg) for idx, msg in kept_messages
                        if idx >= len(kept_messages) // 2
                    ]
                    summary_msg = SystemMessage(
                        content=f"Previous context summary: {summary}"
                    )
                    kept_messages.insert(0, (-1, summary_msg))
        
        # Return messages in order
        return [msg for _, msg in sorted(kept_messages, key=lambda x: x[0] if x[0] >= 0 else -1)]
    
    def compress_tool_output(self, output: str, max_length: int = 1000) -> str:
        """Compress large tool outputs before adding to context.
        
        Args:
            output: Tool output to compress
            max_length: Maximum length before compression
            
        Returns:
            Compressed output
        """
        if len(output) <= max_length:
            return output
        
        # Try to extract key information from JSON-like output
        import json
        try:
            # Try to parse as JSON
            data = json.loads(output)
            if isinstance(data, dict):
                # Extract status and key fields
                compressed = {
                    "status": data.get("status", "unknown"),
                    "message": data.get("message", "")[:200] if data.get("message") else "",
                }
                # Keep important fields
                for key in ["exit_code", "file_path", "container_name", "entity_id"]:
                    if key in data:
                        compressed[key] = data[key]
                
                compressed_str = json.dumps(compressed, indent=2)
                if len(compressed_str) <= max_length:
                    return compressed_str
        except:
            pass
        
        # If not JSON or compression didn't help, truncate
        return output[:max_length] + f"\n... [TRUNCATED: {len(output)} chars total]"
    
    def _summarize_messages(self, messages: List[BaseMessage]) -> str:
        """Summarize a list of messages.
        
        Args:
            messages: Messages to summarize
            
        Returns:
            Summary string
        """
        # Simple summarization: extract key information
        summary_parts = []
        
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            if isinstance(msg, HumanMessage):
                # Extract task/request
                if len(content) > 100:
                    summary_parts.append(f"User request: {content[:100]}...")
                else:
                    summary_parts.append(f"User request: {content}")
            
            elif isinstance(msg, AIMessage):
                # Extract key results
                if "Tool execution results" in content:
                    # Extract status
                    if "status" in content.lower():
                        if "success" in content.lower():
                            summary_parts.append("Tool execution: success")
                        elif "error" in content.lower():
                            summary_parts.append("Tool execution: error")
                    else:
                        summary_parts.append("Tool execution completed")
                elif len(content) > 100:
                    summary_parts.append(f"Assistant: {content[:100]}...")
                else:
                    summary_parts.append(f"Assistant: {content}")
        
        return " | ".join(summary_parts)
    
    def get_context_stats(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Get statistics about current context.
        
        Args:
            messages: List of messages
            
        Returns:
            Dict with context statistics
        """
        total_tokens = sum(self.estimate_message_tokens(msg) for msg in messages)
        
        message_types = {
            "system": sum(1 for msg in messages if isinstance(msg, SystemMessage)),
            "user": sum(1 for msg in messages if isinstance(msg, HumanMessage)),
            "assistant": sum(1 for msg in messages if isinstance(msg, AIMessage)),
        }
        
        return {
            "total_messages": len(messages),
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": (total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            "message_types": message_types
        }


# Global context manager instance
_context_manager: Optional[ContextManager] = None

def get_context_manager(max_tokens: int = 8000) -> ContextManager:
    """Get or create global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager(max_tokens=max_tokens)
    return _context_manager


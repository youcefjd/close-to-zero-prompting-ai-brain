"""Cost Tracker: Tracks token usage and costs for LLM operations.

This module provides cost tracking and circuit breaker functionality
to prevent runaway costs in autonomous agent execution.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class TokenUsage:
    """Token usage for a single operation."""
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    operation: str = ""
    cost: float = 0.0


@dataclass
class CostLimit:
    """Cost limit configuration."""
    max_cost_per_task: float = 0.50  # $0.50 per task
    max_cost_per_hour: float = 10.0  # $10 per hour
    max_tokens_per_task: int = 100000  # 100k tokens per task
    warn_at_percent: float = 0.8  # Warn at 80% of limit


class CostTracker:
    """Tracks token usage and costs for LLM operations."""
    
    def __init__(
        self,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        limits: Optional[CostLimit] = None
    ):
        """Initialize cost tracker.
        
        Args:
            cost_per_1k_input: Cost per 1k input tokens
            cost_per_1k_output: Cost per 1k output tokens
            limits: Cost limit configuration
        """
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.limits = limits or CostLimit()
        
        # Current session tracking
        self.current_task_tokens: TokenUsage = TokenUsage()
        self.current_task_cost: float = 0.0
        self.usage_history: List[TokenUsage] = []
        
        # Hourly tracking
        self.hourly_usage: Dict[str, float] = {}  # hour -> cost
        self.hourly_tokens: Dict[str, int] = {}  # hour -> tokens
    
    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        operation: str = "llm_call"
    ) -> TokenUsage:
        """Record token usage for an operation.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Operation name/description
            
        Returns:
            TokenUsage record
        """
        # Calculate cost
        input_cost = (input_tokens / 1000.0) * self.cost_per_1k_input
        output_cost = (output_tokens / 1000.0) * self.cost_per_1k_output
        total_cost = input_cost + output_cost
        
        # Create usage record
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=input_tokens,
            operation=operation,
            cost=total_cost,
            timestamp=datetime.now().isoformat()
        )
        
        # Update current task tracking
        self.current_task_tokens.input_tokens += input_tokens
        self.current_task_tokens.output_tokens += output_tokens
        self.current_task_cost += total_cost
        
        # Update hourly tracking
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        self.hourly_usage[hour_key] = self.hourly_usage.get(hour_key, 0.0) + total_cost
        self.hourly_tokens[hour_key] = self.hourly_tokens.get(hour_key, 0) + input_tokens + output_tokens
        
        # Store in history
        self.usage_history.append(usage)
        
        return usage
    
    def check_limits(self) -> Dict[str, Any]:
        """Check if cost/token limits are exceeded.
        
        Returns:
            Dict with 'allowed', 'reason', 'current_cost', 'current_tokens'
        """
        total_tokens = self.current_task_tokens.input_tokens + self.current_task_tokens.output_tokens
        
        # Check per-task cost limit
        if self.current_task_cost >= self.limits.max_cost_per_task:
            return {
                "allowed": False,
                "reason": f"Cost limit exceeded: ${self.current_task_cost:.4f} >= ${self.limits.max_cost_per_task:.2f}",
                "current_cost": self.current_task_cost,
                "current_tokens": total_tokens,
                "limit_type": "cost_per_task"
            }
        
        # Check per-task token limit
        if total_tokens >= self.limits.max_tokens_per_task:
            return {
                "allowed": False,
                "reason": f"Token limit exceeded: {total_tokens} >= {self.limits.max_tokens_per_task}",
                "current_cost": self.current_task_cost,
                "current_tokens": total_tokens,
                "limit_type": "tokens_per_task"
            }
        
        # Check hourly cost limit
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        hourly_cost = self.hourly_usage.get(hour_key, 0.0)
        if hourly_cost >= self.limits.max_cost_per_hour:
            return {
                "allowed": False,
                "reason": f"Hourly cost limit exceeded: ${hourly_cost:.4f} >= ${self.limits.max_cost_per_hour:.2f}",
                "current_cost": hourly_cost,
                "current_tokens": self.hourly_tokens.get(hour_key, 0),
                "limit_type": "cost_per_hour"
            }
        
        # Check warning thresholds
        warnings = []
        if self.current_task_cost >= self.limits.max_cost_per_task * self.limits.warn_at_percent:
            warnings.append(f"Approaching cost limit: ${self.current_task_cost:.4f} / ${self.limits.max_cost_per_task:.2f}")
        
        if total_tokens >= self.limits.max_tokens_per_task * self.limits.warn_at_percent:
            warnings.append(f"Approaching token limit: {total_tokens} / {self.limits.max_tokens_per_task}")
        
        return {
            "allowed": True,
            "current_cost": self.current_task_cost,
            "current_tokens": total_tokens,
            "warnings": warnings
        }
    
    def reset_task(self):
        """Reset current task tracking (call at start of new task)."""
        self.current_task_tokens = TokenUsage()
        self.current_task_cost = 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current usage.
        
        Returns:
            Dict with usage summary
        """
        total_tokens = self.current_task_tokens.input_tokens + self.current_task_tokens.output_tokens
        
        return {
            "current_task": {
                "cost": self.current_task_cost,
                "input_tokens": self.current_task_tokens.input_tokens,
                "output_tokens": self.current_task_tokens.output_tokens,
                "total_tokens": total_tokens
            },
            "limits": {
                "max_cost_per_task": self.limits.max_cost_per_task,
                "max_tokens_per_task": self.limits.max_tokens_per_task,
                "max_cost_per_hour": self.limits.max_cost_per_hour
            },
            "usage_percentage": {
                "cost": (self.current_task_cost / self.limits.max_cost_per_task * 100) if self.limits.max_cost_per_task > 0 else 0,
                "tokens": (total_tokens / self.limits.max_tokens_per_task * 100) if self.limits.max_tokens_per_task > 0 else 0
            }
        }
    
    def save_history(self, file_path: str = ".cost_history.json"):
        """Save usage history to file.
        
        Args:
            file_path: Path to save history
        """
        history_data = {
            "usage_history": [
                {
                    "input_tokens": u.input_tokens,
                    "output_tokens": u.output_tokens,
                    "cost": u.cost,
                    "operation": u.operation,
                    "timestamp": u.timestamp
                }
                for u in self.usage_history[-1000:]  # Keep last 1000 records
            ],
            "hourly_usage": self.hourly_usage,
            "hourly_tokens": self.hourly_tokens
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cost history: {e}")


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None

def get_cost_tracker(
    cost_per_1k_input: float = 0.0,
    cost_per_1k_output: float = 0.0,
    limits: Optional[CostLimit] = None
) -> CostTracker:
    """Get or create global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker(
            cost_per_1k_input=cost_per_1k_input,
            cost_per_1k_output=cost_per_1k_output,
            limits=limits
        )
    return _cost_tracker


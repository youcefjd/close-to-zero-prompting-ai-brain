"""Semantic Router: Embedding-based task routing for better generalization.

This module provides semantic routing using embeddings instead of
hard-coded keyword matching, enabling better generalization to unseen tasks.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class RoutingDecision:
    """A routing decision with metadata."""
    task: str
    primary_agent: str
    secondary_agents: List[str]
    confidence: float
    method: str  # "semantic" or "fallback"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: Optional[bool] = None  # Track if routing was successful


class SemanticRouter:
    """Semantic router using embeddings for task classification."""
    
    # Agent descriptions for embedding comparison
    AGENT_DESCRIPTIONS = {
        "docker": "Docker container management, docker-compose, container operations, images, networks, volumes",
        "config": "YAML, JSON, configuration files, Home Assistant config, settings, configuration management",
        "python": "Python scripts, code generation, debugging, programming, software development",
        "homeassistant": "Home Assistant integrations, entities, automations, services, HA configuration",
        "system": "File operations, shell commands, system-level tasks, file system, operating system",
        "cloud": "Cloud architecture, EKS, EMR, ACK, AWS, Kubernetes, Terraform, infrastructure, cloud services",
        "consulting": "Analysis, comparison, recommendations, architectural decisions, consulting, advice",
        "general": "General tasks, miscellaneous, fallback for tasks that don't fit other categories"
    }
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize semantic router.
        
        Args:
            embedding_model: Model to use for embeddings (default: lightweight sentence transformer)
        """
        self.embedding_model = embedding_model
        self.embeddings = None
        self.agent_embeddings = {}
        self.routing_history: List[RoutingDecision] = []
        self.history_file = Path(".routing_history.json")
        self._load_history()
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize embedding model (lazy loading)."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model_instance = SentenceTransformer(self.embedding_model)
            self.embeddings_available = True
            
            # Pre-compute agent embeddings
            for agent_name, description in self.AGENT_DESCRIPTIONS.items():
                self.agent_embeddings[agent_name] = self.embedding_model_instance.encode(
                    description,
                    convert_to_numpy=True
                )
        except ImportError:
            print("⚠️  sentence-transformers not available, falling back to keyword routing")
            self.embeddings_available = False
            self.embedding_model_instance = None
    
    def route_semantic(self, task: str) -> Dict[str, Any]:
        """Route task using semantic similarity.
        
        Args:
            task: Task description
            
        Returns:
            Dict with routing decision
        """
        if not self.embeddings_available:
            return self._fallback_routing(task)
        
        try:
            # Encode task
            task_embedding = self.embedding_model_instance.encode(
                task,
                convert_to_numpy=True
            )
            
            # Calculate similarity with each agent
            similarities = {}
            for agent_name, agent_embedding in self.agent_embeddings.items():
                # Cosine similarity
                similarity = self._cosine_similarity(task_embedding, agent_embedding)
                similarities[agent_name] = similarity
            
            # Find best match
            best_agent = max(similarities.items(), key=lambda x: x[1])
            primary_agent = best_agent[0]
            confidence = best_agent[1]
            
            # Find secondary agents (similarity > 0.5)
            secondary_agents = [
                agent for agent, sim in similarities.items()
                if sim > 0.5 and agent != primary_agent
            ]
            
            # Determine task type
            task_type = "execution"
            consultation_keywords = ["assess", "compare", "recommend", "evaluate", "analyze", "which", "should"]
            if any(kw in task.lower() for kw in consultation_keywords):
                task_type = "consultation"
            
            return {
                "primary_agent": primary_agent,
                "secondary_agents": secondary_agents,
                "confidence": float(confidence),
                "method": "semantic",
                "task_type": task_type,
                "similarities": {k: float(v) for k, v in similarities.items()}
            }
        except Exception as e:
            print(f"⚠️  Semantic routing failed: {e}, falling back to keyword routing")
            return self._fallback_routing(task)
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        import numpy as np
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def _fallback_routing(self, task: str) -> Dict[str, Any]:
        """Fallback to keyword-based routing.
        
        Args:
            task: Task description
            
        Returns:
            Dict with routing decision
        """
        task_lower = task.lower()
        
        # Check for consultation/analysis tasks first
        consultation_keywords = ["assess", "compare", "recommend", "evaluate", "analysis", "which is better", "should i use"]
        is_consultation = any(kw in task_lower for kw in consultation_keywords)
        
        primary = "general"
        if is_consultation:
            if any(kw in task_lower for kw in ["eks", "emr", "ack", "aws", "kubernetes", "terraform", "cloud", "infrastructure"]):
                primary = "cloud"
            else:
                primary = "consulting"
        elif any(kw in task_lower for kw in ["docker", "container", "compose", "image"]):
            primary = "docker"
        elif any(kw in task_lower for kw in ["yaml", "json", "config", "configuration", "home assistant", "ha"]):
            primary = "config"
        elif any(kw in task_lower for kw in ["python", "script", "code", "function", "class"]):
            primary = "python"
        elif any(kw in task_lower for kw in ["integration", "entity", "automation", "service", "homeassistant"]):
            primary = "homeassistant"
        elif any(kw in task_lower for kw in ["file", "directory", "shell", "command", "system"]):
            primary = "system"
        elif any(kw in task_lower for kw in ["eks", "emr", "ack", "aws", "kubernetes", "terraform"]):
            primary = "cloud"
        
        return {
            "primary_agent": primary,
            "secondary_agents": [],
            "confidence": 0.7,
            "method": "fallback",
            "task_type": "consultation" if is_consultation else "execution"
        }
    
    def route(self, task: str) -> Dict[str, Any]:
        """Route task (main entry point).
        
        Args:
            task: Task description
            
        Returns:
            Dict with routing decision
        """
        # Try semantic routing first
        routing = self.route_semantic(task)
        
        # Create routing decision record
        decision = RoutingDecision(
            task=task,
            primary_agent=routing["primary_agent"],
            secondary_agents=routing.get("secondary_agents", []),
            confidence=routing.get("confidence", 0.5),
            method=routing.get("method", "unknown")
        )
        
        # Store in history
        self.routing_history.append(decision)
        self._save_history()
        
        return routing
    
    def record_success(self, task: str, agent_used: str, success: bool):
        """Record routing success/failure for learning.
        
        Args:
            task: Task that was routed
            agent_used: Agent that was used
            success: Whether the routing was successful
        """
        # Find matching routing decision
        for decision in reversed(self.routing_history):
            if decision.task == task and decision.primary_agent == agent_used:
                decision.success = success
                break
        
        self._save_history()
    
    def learn_from_history(self) -> Dict[str, Any]:
        """Learn from routing history to improve routing.
        
        Returns:
            Dict with learning insights
        """
        if not self.routing_history:
            return {"message": "No routing history available"}
        
        # Analyze success rates by agent
        agent_success = {}
        for decision in self.routing_history:
            if decision.success is not None:
                agent = decision.primary_agent
                if agent not in agent_success:
                    agent_success[agent] = {"success": 0, "failure": 0}
                
                if decision.success:
                    agent_success[agent]["success"] += 1
                else:
                    agent_success[agent]["failure"] += 1
        
        # Calculate success rates
        success_rates = {}
        for agent, counts in agent_success.items():
            total = counts["success"] + counts["failure"]
            if total > 0:
                success_rates[agent] = counts["success"] / total
        
        return {
            "total_routings": len(self.routing_history),
            "agent_success_rates": success_rates,
            "agent_counts": agent_success
        }
    
    def _save_history(self):
        """Save routing history to file."""
        try:
            history_data = [
                {
                    "task": d.task,
                    "primary_agent": d.primary_agent,
                    "secondary_agents": d.secondary_agents,
                    "confidence": d.confidence,
                    "method": d.method,
                    "timestamp": d.timestamp,
                    "success": d.success
                }
                for d in self.routing_history[-1000:]  # Keep last 1000
            ]
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save routing history: {e}")
    
    def _load_history(self):
        """Load routing history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    history_data = json.load(f)
                
                self.routing_history = [
                    RoutingDecision(**d) for d in history_data
                ]
            except Exception as e:
                print(f"Warning: Could not load routing history: {e}")
                self.routing_history = []


# Global router instance
_semantic_router = None

def get_semantic_router() -> SemanticRouter:
    """Get or create global semantic router instance."""
    global _semantic_router
    if _semantic_router is None:
        _semantic_router = SemanticRouter()
    return _semantic_router


"""Consulting Sub-Agent: Handles analysis, comparison, and recommendation tasks."""

from typing import Dict, Any, Optional
from sub_agents.base_agent import BaseSubAgent
from langchain_core.messages import HumanMessage, AIMessage
import json


class ConsultingAgent(BaseSubAgent):
    """Specialized agent for analysis, comparison, and recommendations."""
    
    def __init__(self):
        system_prompt = """You are a Cloud Engineering Consultant Agent. You handle:
- Architecture analysis and recommendations
- Technology comparison (e.g., EMR on ACK vs custom wrapper)
- Cost-benefit analysis
- Best practices and patterns
- Risk assessment
- Performance evaluation

CRITICAL: You provide detailed analysis, comparisons, and recommendations WITHOUT executing any tools or making changes.
- DO NOT call tools like run_shell, docker_compose_up, ha_call_service, etc.
- DO NOT attempt to execute commands or make changes
- ONLY provide analysis, comparison, and recommendations in text

You work AUTONOMOUSLY - analyze the question, apply cloud engineering knowledge, and provide comprehensive answers based on:
- AWS best practices
- Kubernetes/EKS patterns
- Cost considerations
- Operational complexity
- Scalability and reliability
- Industry standards

Format your response as a structured analysis with:
1. Problem statement
2. Option comparison (pros/cons)
3. Key factors to consider
4. Recommendation with justification
5. Implementation considerations (if applicable)"""
        
        super().__init__("ConsultingAgent", system_prompt)
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute consultation/analysis task."""
        print(f"💡 ConsultingAgent: {task}")
        
        # Create prompt for analysis
        prompt = self._create_prompt(task, context)
        chain = prompt | self.llm
        
        messages = []
        max_iterations = 3
        iteration = 0
        
        analysis_result = ""
        
        while iteration < max_iterations:
            response = chain.invoke({"messages": messages})
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            messages.append(HumanMessage(content=task if iteration == 0 else "Continue analysis"))
            messages.append(response)
            
            analysis_result += response_text + "\n\n"
            
            # Check if analysis is complete
            if "conclusion" in response_text.lower() or "recommendation" in response_text.lower() or iteration >= 2:
                break
            
            iteration += 1
        
        # Format analysis
        print("\n" + "="*70)
        print("📊 CONSULTATION ANALYSIS")
        print("="*70)
        print(f"\n{analysis_result}")
        print("="*70)
        
        return {
            "status": "success",
            "message": "Analysis complete",
            "analysis": analysis_result,
            "agent": self.agent_name,
            "task_type": "consultation"
        }


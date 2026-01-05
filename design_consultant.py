"""Design Consultant: Gathers context, presents options, and gets user decisions.

This module implements the structured Q&A flow for complex system design,
presenting options with pros/cons and getting user decisions.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from llm_provider import LLMProvider, create_llm_provider
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import json
import re


@dataclass
class DesignOption:
    """A design option with pros/cons."""
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    recommendation_score: float  # 0-1
    estimated_cost: Optional[str] = None
    complexity: str = "medium"  # "simple", "medium", "complex"


@dataclass
class ContextQuestion:
    """A targeted question to gather context."""
    question: str
    context_key: str  # What this question is gathering
    required: bool = False
    options: Optional[List[str]] = None  # If multiple choice
    answer: Optional[str] = None


class DesignConsultant:
    """Consultant that gathers context and presents design options."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or create_llm_provider("ollama")
        self.context: Dict[str, Any] = {}
        self.questions: List[ContextQuestion] = []
    
    def analyze_requirements(self, initial_prompt: str) -> List[ContextQuestion]:
        """Analyze requirements and determine what context is needed.
        
        Args:
            initial_prompt: Initial user request
            
        Returns:
            List of questions to ask
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a system design consultant. Analyze a user's request and determine what information you need to make good design decisions.

For complex systems, you need to know:
- Scale/load requirements (users, requests per second, data volume)
- Availability requirements (uptime, redundancy)
- Budget/cost constraints
- Security requirements
- Compliance needs
- Existing infrastructure
- Team expertise
- Timeline/deadlines

IMPORTANT: 
- If the user has ALREADY PROVIDED information (shown after "USER HAS ALREADY PROVIDED"), DO NOT ask about those topics again
- Only generate questions for MISSING information
- If the user has provided enough context, return an empty array []
- Do not ask redundant or repetitive questions

Generate targeted questions to gather ONLY MISSING context. Return as JSON array:
[
    {{
        "question": "What is the expected number of concurrent users?",
        "context_key": "scale_users",
        "required": true,
        "options": null
    }},
    {{
        "question": "What is your availability requirement?",
        "context_key": "availability",
        "required": true,
        "options": ["99.9% (3 nines)", "99.99% (4 nines)", "99.999% (5 nines)"]
    }}
]

Return [] if no additional questions are needed."""),
            HumanMessage(content=f"User request: {initial_prompt}\n\nWhat NEW questions do you need to ask? (Check what's already provided above)")
        ])
        
        try:
            response = self.llm_provider.invoke([
                SystemMessage(content=prompt.format_messages()[0].content),
                HumanMessage(content=initial_prompt)
            ])
            
            content = response if isinstance(response, str) else response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions_data = json.loads(json_match.group())
                self.questions = [
                    ContextQuestion(**q) for q in questions_data
                ]
                return self.questions
        except Exception as e:
            print(f"⚠️  Question generation failed: {e}")
        
        # Fallback: Generic questions
        return [
            ContextQuestion(
                question="What is the expected scale (users, requests/sec)?",
                context_key="scale",
                required=True
            ),
            ContextQuestion(
                question="What is your availability requirement?",
                context_key="availability",
                required=True,
                options=["99.9%", "99.99%", "99.999%"]
            ),
            ContextQuestion(
                question="What is your budget range?",
                context_key="budget",
                required=False
            )
        ]
    
    def gather_context(self, initial_prompt: str, existing_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gather context through targeted questions.
        
        Args:
            initial_prompt: Initial user request
            existing_context: Optional context with previous clarifications to avoid redundant questions
            
        Returns:
            Gathered context dictionary
        """
        existing_context = existing_context or {}
        
        # Extract previous clarifications for context
        all_clarifications = existing_context.get("all_clarifications", [])
        clarification_text = "\n".join(all_clarifications) if all_clarifications else ""
        
        print("\n" + "="*70)
        print("📋 DESIGN CONSULTATION: Gathering Context")
        print("="*70)
        
        # Analyze requirements - pass existing clarifications so LLM can avoid redundant questions
        if clarification_text:
            enhanced_prompt = f"{initial_prompt}\n\nUSER HAS ALREADY PROVIDED:\n{clarification_text}"
        else:
            enhanced_prompt = initial_prompt
            
        questions = self.analyze_requirements(enhanced_prompt)
        
        if not questions:
            # Return combined existing context
            self.context.update({k: v for k, v in existing_context.items() if k not in ["all_clarifications", "force_proceed"]})
            return self.context
        
        # Filter out questions that might already be answered in clarifications
        # Let LLM's analysis handle this - but we can check for obvious duplicates
        questions_to_ask = []
        for q in questions:
            # Check if this question's context_key is already answered
            if q.context_key in existing_context and existing_context[q.context_key]:
                print(f"   ✅ Already answered: {q.context_key}")
                q.answer = existing_context[q.context_key]
                self.context[q.context_key] = q.answer
            else:
                questions_to_ask.append(q)
        
        if not questions_to_ask:
            print(f"\n   ✅ All context already gathered from previous clarifications!")
            return self.context
        
        # Ask remaining questions
        print(f"\n   I need to ask {len(questions_to_ask)} question(s) to make the best design decisions:\n")
        
        for i, question in enumerate(questions_to_ask, 1):
            print(f"   {i}. {question.question}")
            if question.options:
                print(f"      Options: {', '.join(question.options)}")
            
            if question.required:
                print(f"      (Required)")
            
            # Get answer
            answer = input(f"\n   > ").strip()
            
            if not answer and question.required:
                print(f"   ⚠️  This is required. Please provide an answer.")
                answer = input(f"   > ").strip()
            
            question.answer = answer
            self.context[question.context_key] = answer
        
        return self.context
    
    def generate_design_options(self, requirements: str, context: Dict[str, Any]) -> List[DesignOption]:
        """Generate design options with pros/cons.
        
        Args:
            requirements: Original requirements
            context: Gathered context
            
        Returns:
            List of design options
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a system architect. Generate multiple design options for a system, each with pros/cons and a recommendation score.

Consider:
- Cost vs. performance tradeoffs
- Complexity vs. maintainability
- Scalability options
- Security implications
- Operational overhead

For each option, provide:
- Name and description
- Pros (advantages)
- Cons (disadvantages)
- Recommendation score (0-1, where 1 is best)
- Estimated cost/complexity

Return as JSON array:
[
    {{
        "name": "Option Name",
        "description": "What this option is",
        "pros": ["pro1", "pro2"],
        "cons": ["con1", "con2"],
        "recommendation_score": 0.8,
        "estimated_cost": "Low/Medium/High",
        "complexity": "simple|medium|complex"
    }}
]"""),
            HumanMessage(content=f"""Requirements: {requirements}

Context:
{json.dumps(context, indent=2)}

Generate 2-4 design options with pros/cons.""")
        ])
        
        try:
            response = self.llm_provider.invoke([
                SystemMessage(content=prompt.format_messages()[0].content),
                HumanMessage(content=f"Requirements: {requirements}\n\nContext: {json.dumps(context, indent=2)}")
            ])
            
            content = response if isinstance(response, str) else response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                options_data = json.loads(json_match.group())
                return [DesignOption(**opt) for opt in options_data]
        except Exception as e:
            print(f"⚠️  Design option generation failed: {e}")
        
        return []
    
    def present_options(self, options: List[DesignOption]) -> int:
        """Present design options and get user selection.
        
        Args:
            options: List of design options
            
        Returns:
            Selected option index (0-based)
        """
        print("\n" + "="*70)
        print("🎯 DESIGN OPTIONS")
        print("="*70)
        
        for i, option in enumerate(options, 1):
            print(f"\n   Option {i}: {option.name}")
            print(f"   {'='*60}")
            print(f"   Description: {option.description}")
            print(f"\n   ✅ Pros:")
            for pro in option.pros:
                print(f"      • {pro}")
            print(f"\n   ❌ Cons:")
            for con in option.cons:
                print(f"      • {con}")
            print(f"\n   📊 Recommendation Score: {option.recommendation_score:.2f}/1.0")
            if option.estimated_cost:
                print(f"   💰 Estimated Cost: {option.estimated_cost}")
            print(f"   🔧 Complexity: {option.complexity}")
        
        # Show recommendation
        best_option = max(options, key=lambda x: x.recommendation_score)
        best_index = options.index(best_option)
        
        print(f"\n   💡 Recommendation: Option {best_index + 1} ({best_option.name})")
        print(f"      Score: {best_option.recommendation_score:.2f}/1.0")
        
        # Get user selection
        print(f"\n   Which option would you like to proceed with? (1-{len(options)})")
        while True:
            try:
                selection = int(input(f"   > ").strip())
                if 1 <= selection <= len(options):
                    return selection - 1  # Convert to 0-based
                else:
                    print(f"   ⚠️  Please enter a number between 1 and {len(options)}")
            except ValueError:
                print(f"   ⚠️  Please enter a valid number")
    
    def gather_resource_quotas(self, selected_option: DesignOption) -> Dict[str, Any]:
        """Gather resource quotas and sizing information.
        
        Args:
            selected_option: Selected design option
            
        Returns:
            Resource quota configuration
        """
        print("\n" + "="*70)
        print("📊 RESOURCE QUOTAS")
        print("="*70)
        
        quotas = {}
        
        # Ask for cluster size
        print(f"\n   Cluster/Infrastructure Sizing:")
        print(f"   What size cluster do you need?")
        print(f"   (e.g., 'small: 3 nodes', 'medium: 5 nodes', 'large: 10 nodes')")
        cluster_size = input(f"   > ").strip()
        quotas["cluster_size"] = cluster_size
        
        # Ask for compute resources
        print(f"\n   Compute Resources:")
        print(f"   CPU cores per node? (e.g., '4', '8', '16')")
        cpu_cores = input(f"   > ").strip()
        quotas["cpu_cores"] = cpu_cores
        
        print(f"   Memory per node? (e.g., '8GB', '16GB', '32GB')")
        memory = input(f"   > ").strip()
        quotas["memory"] = memory
        
        # Ask for storage
        print(f"\n   Storage:")
        print(f"   Total storage needed? (e.g., '100GB', '500GB', '1TB')")
        storage = input(f"   > ").strip()
        quotas["storage"] = storage
        
        return quotas


# Global instance
_design_consultant = None

def get_design_consultant() -> DesignConsultant:
    """Get or create global design consultant instance."""
    global _design_consultant
    if _design_consultant is None:
        _design_consultant = DesignConsultant()
    return _design_consultant


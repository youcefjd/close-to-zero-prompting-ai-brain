"""Config Sub-Agent: Handles configuration files (YAML, JSON, etc.) autonomously."""

from typing import Dict, Any, Optional
from sub_agents.base_agent import BaseSubAgent
import json
import yaml
import re
from pathlib import Path


class ConfigAgent(BaseSubAgent):
    """Specialized agent for configuration file operations."""
    
    def __init__(self):
        system_prompt = """You are a configuration expert agent. You handle:
- YAML files (docker-compose.yml, Home Assistant config, etc.)
- JSON files (package.json, config.json, etc.)
- Configuration file creation, modification, validation
- Home Assistant configuration (configuration.yaml, automations, etc.)

You work AUTONOMOUSLY - read existing configs, understand structure, make changes, validate syntax."""
        
        super().__init__("ConfigAgent", system_prompt)
    
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute configuration-related task."""
        print(f"📝 ConfigAgent: {task}")
        
        # Extract file paths from task
        file_paths = self._extract_file_paths(task)
        
        # Read existing files if mentioned
        existing_configs = {}
        for file_path in file_paths:
            if Path(file_path).exists():
                try:
                    with open(file_path) as f:
                        content = f.read()
                        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                            existing_configs[file_path] = yaml.safe_load(content)
                        elif file_path.endswith('.json'):
                            existing_configs[file_path] = json.loads(content)
                        else:
                            existing_configs[file_path] = content
                except Exception as e:
                    print(f"  ⚠️  Could not read {file_path}: {e}")
        
        # Create prompt with context
        context_with_configs = {**(context or {}), "existing_configs": existing_configs}
        prompt = self._create_prompt(task, context_with_configs)
        chain = prompt | self.llm
        
        messages = []
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            response = chain.invoke({"messages": messages})
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            messages.append(HumanMessage(content=task if iteration == 0 else "Continue"))
            messages.append(response)
            
            # Look for file write operations in response
            file_writes = self._extract_file_writes(response_text)
            
            if file_writes:
                for file_path, content in file_writes.items():
                    print(f"  📝 Writing: {file_path}")
                    result = self._execute_tool("write_file", file_path, content)
                    if result.get("status") == "error":
                        print(f"  ❌ Failed: {result.get('message')}")
                        return result
            
            # Check if task is complete
            if "success" in response_text.lower() or "complete" in response_text.lower():
                return {
                    "status": "success",
                    "message": response_text,
                    "agent": self.agent_name
                }
            
            iteration += 1
        
        return {
            "status": "partial",
            "message": "Task completed",
            "agent": self.agent_name
        }
    
    def _extract_file_paths(self, task: str) -> list:
        """Extract file paths mentioned in task."""
        # Look for common file patterns
        patterns = [
            r'([\w/\.-]+\.(yaml|yml|json|conf|config))',
            r'([\w/\.-]+/[\w\.-]+\.(yaml|yml|json))',
        ]
        
        paths = []
        for pattern in patterns:
            matches = re.findall(pattern, task)
            for match in matches:
                paths.append(match[0] if isinstance(match, tuple) else match)
        
        return list(set(paths))
    
    def _extract_file_writes(self, response: str) -> Dict[str, str]:
        """Extract file write operations from response."""
        file_writes = {}
        
        # Look for code blocks with file paths
        code_block_pattern = r'```(?:yaml|yml|json)?\n(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        # Try to infer file path from context or use default
        if matches:
            # Look for file path hints in response
            path_hints = re.findall(r'(?:file|path|write|create)[:\s]+([\w/\.-]+\.(?:yaml|yml|json))', response, re.IGNORECASE)
            
            for i, content in enumerate(matches):
                file_path = path_hints[i] if i < len(path_hints) else None
                if file_path:
                    file_writes[file_path] = content.strip()
        
        return file_writes


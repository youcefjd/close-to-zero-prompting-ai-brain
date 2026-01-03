"""Dynamic Tool Registry: Runtime tool discovery and validation.

This module provides dynamic tool discovery, validation, and registration
at runtime, enabling the system to adapt to new tools without code changes.
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import importlib
import importlib.util
import inspect
import ast
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]
    return_type: str
    source_file: str
    risk_level: str = "unknown"  # "green", "yellow", "red"
    validated: bool = False
    validation_errors: List[str] = None


class ToolValidator:
    """Validates tools for safety and correctness."""
    
    def __init__(self):
        self.validation_rules = {
            "dangerous_imports": ["subprocess", "os.system", "eval", "exec"],
            "required_docstring": True,
            "required_type_hints": True,
            "max_parameters": 10
        }
    
    def validate_tool(self, tool_func: Callable, source_file: str) -> Dict[str, Any]:
        """Validate a tool function.
        
        Args:
            tool_func: Tool function to validate
            source_file: Path to source file
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Check docstring
        if not tool_func.__doc__:
            if self.validation_rules["required_docstring"]:
                errors.append("Missing docstring")
            else:
                warnings.append("No docstring provided")
        
        # Check type hints
        sig = inspect.signature(tool_func)
        has_type_hints = any(
            param.annotation != inspect.Parameter.empty
            for param in sig.parameters.values()
        )
        
        if not has_type_hints and self.validation_rules["required_type_hints"]:
            warnings.append("Missing type hints")
        
        # Check parameter count
        if len(sig.parameters) > self.validation_rules["max_parameters"]:
            warnings.append(f"Too many parameters: {len(sig.parameters)}")
        
        # Static analysis of source code
        try:
            source_code = inspect.getsource(tool_func)
            tree = ast.parse(source_code)
            
            # Check for dangerous patterns
            dangerous_patterns = self._check_dangerous_patterns(tree)
            if dangerous_patterns:
                errors.extend(dangerous_patterns)
        except Exception as e:
            warnings.append(f"Could not analyze source code: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "risk_level": "red" if errors else ("yellow" if warnings else "green")
        }
    
    def _check_dangerous_patterns(self, tree: ast.AST) -> List[str]:
        """Check AST for dangerous patterns.
        
        Args:
            tree: AST to check
            
        Returns:
            List of error messages
        """
        errors = []
        
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "compile"]:
                        errors.append(f"Dangerous function call: {node.func.id}")
            
            # Check for subprocess calls without safety checks
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "run" and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "subprocess":
                            # Check if there's a safety check nearby
                            # This is a simplified check
                            pass
        
        return errors


class DynamicToolRegistry:
    """Dynamic registry for tools discovered at runtime."""
    
    def __init__(self):
        self.tools: Dict[str, ToolMetadata] = {}
        self.validator = ToolValidator()
        self.discovery_paths = [
            Path("mcp_servers"),
            Path("tools"),
            Path(".")  # Current directory
        ]
    
    def discover_tools(self, directory: Optional[Path] = None) -> List[str]:
        """Discover tools in a directory.
        
        Args:
            directory: Directory to search (uses discovery_paths if None)
            
        Returns:
            List of discovered tool names
        """
        discovered = []
        
        if directory:
            search_paths = [directory]
        else:
            search_paths = self.discovery_paths
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            # Look for Python files
            for py_file in search_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                try:
                    tools_in_file = self._discover_tools_in_file(py_file)
                    discovered.extend(tools_in_file)
                except Exception as e:
                    print(f"Warning: Could not discover tools in {py_file}: {e}")
        
        return discovered
    
    def _discover_tools_in_file(self, file_path: Path) -> List[str]:
        """Discover tools in a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of tool names discovered
        """
        discovered = []
        
        try:
            # Parse file
            with open(file_path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if it looks like a tool (returns Dict, has docstring, etc.)
                    if self._is_tool_function(node, source):
                        tool_name = node.name
                        
                        # Try to import and register
                        try:
                            self.register_tool_from_file(file_path, tool_name)
                            discovered.append(tool_name)
                        except Exception as e:
                            print(f"Warning: Could not register {tool_name} from {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
        
        return discovered
    
    def _is_tool_function(self, node: ast.FunctionDef, source: str) -> bool:
        """Check if a function looks like a tool.
        
        Args:
            node: Function AST node
            source: Source code
            
        Returns:
            True if function looks like a tool
        """
        # Tools typically:
        # 1. Return Dict[str, Any]
        # 2. Have docstrings
        # 3. Don't start with underscore
        # 4. Are not class methods
        
        if node.name.startswith("_"):
            return False
        
        # Check for return type hint
        if node.returns:
            returns_str = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
            if "Dict" in returns_str or "dict" in returns_str.lower():
                return True
        
        # Check for docstring
        if ast.get_docstring(node):
            return True
        
        return False
    
    def register_tool_from_file(self, file_path: Path, function_name: str) -> bool:
        """Register a tool from a file.
        
        Args:
            file_path: Path to Python file
            function_name: Name of function to register
            
        Returns:
            True if registration successful
        """
        try:
            # Import module
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get function
            if not hasattr(module, function_name):
                return False
            
            tool_func = getattr(module, function_name)
            
            # Validate
            validation = self.validator.validate_tool(tool_func, str(file_path))
            
            # Create metadata
            sig = inspect.signature(tool_func)
            parameters = {
                name: {
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "default": param.default if param.default != inspect.Parameter.empty else None,
                    "required": param.default == inspect.Parameter.empty
                }
                for name, param in sig.parameters.items()
            }
            
            metadata = ToolMetadata(
                name=function_name,
                function=tool_func,
                description=tool_func.__doc__ or "No description",
                parameters=parameters,
                return_type=str(sig.return_annotation) if sig.return_annotation != inspect.Parameter.empty else "Any",
                source_file=str(file_path),
                risk_level=validation["risk_level"],
                validated=validation["valid"],
                validation_errors=validation.get("errors", [])
            )
            
            # Register
            self.tools[function_name] = metadata
            
            return True
        except Exception as e:
            print(f"Error registering tool {function_name} from {file_path}: {e}")
            return False
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: Optional[str] = None,
        risk_level: str = "unknown"
    ) -> bool:
        """Register a tool directly.
        
        Args:
            name: Tool name
            function: Tool function
            description: Tool description
            risk_level: Risk level ("green", "yellow", "red")
            
        Returns:
            True if registration successful
        """
        # Validate
        source_file = inspect.getfile(function) if hasattr(function, '__module__') else "unknown"
        validation = self.validator.validate_tool(function, source_file)
        
        # Create metadata
        sig = inspect.signature(function)
        parameters = {
            name: {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }
            for name, param in sig.parameters.items()
        }
        
        metadata = ToolMetadata(
            name=name,
            function=function,
            description=description or function.__doc__ or "No description",
            parameters=parameters,
            return_type=str(sig.return_annotation) if sig.return_annotation != inspect.Parameter.empty else "Any",
            source_file=source_file,
            risk_level=risk_level,
            validated=validation["valid"],
            validation_errors=validation.get("errors", [])
        )
        
        self.tools[name] = metadata
        return True
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolMetadata or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self, risk_level: Optional[str] = None) -> List[str]:
        """List all registered tools.
        
        Args:
            risk_level: Filter by risk level (optional)
            
        Returns:
            List of tool names
        """
        if risk_level:
            return [
                name for name, metadata in self.tools.items()
                if metadata.risk_level == risk_level
            ]
        return list(self.tools.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Dict with tool information
        """
        metadata = self.tools.get(name)
        if not metadata:
            return None
        
        return {
            "name": metadata.name,
            "description": metadata.description,
            "parameters": metadata.parameters,
            "return_type": metadata.return_type,
            "source_file": metadata.source_file,
            "risk_level": metadata.risk_level,
            "validated": metadata.validated,
            "validation_errors": metadata.validation_errors or []
        }


# Global registry instance
_tool_registry = None

def get_tool_registry() -> DynamicToolRegistry:
    """Get or create global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = DynamicToolRegistry()
    return _tool_registry


"""ArchitectAgent - Designs software architecture for features.

This agent analyzes the codebase and creates a detailed architecture plan for implementing features.

Responsibilities:
1. Analyze existing codebase structure
2. Understand current patterns and conventions
3. Design solution architecture
4. Plan database schema changes
5. Design API endpoints
6. Plan frontend components
7. Identify dependencies
8. Assess complexity and risks
9. Output structured implementation plan
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from sub_agents import BaseSubAgent


class ArchitectAgent(BaseSubAgent):
    """Designs software architecture for feature requests."""

    def __init__(self, repo_path: str = "."):
        """Initialize the architect agent.

        Args:
            repo_path: Path to the project repository
        """
        system_prompt = """You are a Senior Software Architect with expertise in full-stack development.

Your role:
1. Analyze existing codebases to understand patterns
2. Design clean, maintainable architectures
3. Plan database schemas (if needed)
4. Design API endpoints following REST/GraphQL best practices
5. Plan frontend component structure
6. Consider scalability, security, and performance
7. Identify potential risks and edge cases
8. Output detailed, structured implementation plans

ANALYSIS PROCESS:
1. Explore project structure (directories, files)
2. Read key files (models, routes, components, configs)
3. Understand tech stack and frameworks
4. Identify existing patterns and conventions
5. Note architectural decisions (monolith vs microservices, state management, etc.)

DESIGN PRINCIPLES:
- Follow existing project conventions
- Prefer composition over inheritance
- Keep components focused and testable
- Design for extensibility
- Consider security (auth, validation, sanitization)
- Plan for error handling
- Design database schema with normalization
- API endpoints should be RESTful and consistent

OUTPUT FORMAT:
Structured JSON with:
- summary: High-level approach
- database_changes: Schema modifications needed
- backend_files: Files to create/modify
- frontend_files: Files to create/modify
- api_endpoints: New endpoints to create
- dependencies: New packages needed
- estimated_complexity: low/medium/high
- risks: Potential issues
- implementation_steps: Ordered steps
"""
        super().__init__("ArchitectAgent", system_prompt)
        self.repo_path = Path(repo_path)

    def execute(self, feature_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze codebase and design architecture for the feature.

        Args:
            feature_request: Natural language description of feature
            context: Optional context (tech stack, constraints, etc.)

        Returns:
            Dictionary with status and architecture plan
        """
        print(f"🏗️  Analyzing codebase at: {self.repo_path}")

        # Step 1: Analyze codebase
        codebase_analysis = self._analyze_codebase()

        print(f"   📂 Project type: {codebase_analysis['project_type']}")
        print(f"   🔧 Tech stack: {', '.join(codebase_analysis['tech_stack'])}")

        # Step 2: Design solution using LLM
        print(f"   🎨 Designing architecture for: {feature_request}")
        architecture_plan = self._design_solution(feature_request, codebase_analysis, context)

        # Step 3: Validate plan
        validation = self._validate_plan(architecture_plan)
        if not validation["valid"]:
            return {
                "status": "error",
                "message": f"Invalid architecture plan: {validation['reason']}",
            }

        # Step 4: Write architecture document
        arch_doc_path = self._write_architecture_doc(feature_request, architecture_plan)

        print(f"   ✅ Architecture plan created: {arch_doc_path}")

        return {
            "status": "success",
            "plan": architecture_plan,
            "codebase_analysis": codebase_analysis,
            "files": [str(arch_doc_path)],
        }

    def _analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the codebase structure and patterns."""
        analysis = {
            "project_type": "unknown",
            "tech_stack": [],
            "backend_framework": None,
            "frontend_framework": None,
            "database": None,
            "key_directories": [],
            "patterns": [],
            "existing_files": {
                "backend": [],
                "frontend": [],
                "tests": [],
                "configs": [],
            },
        }

        # Detect project type and tech stack
        if (self.repo_path / "package.json").exists():
            analysis["project_type"] = "javascript/typescript"
            analysis["tech_stack"].append("Node.js")

            # Check for React/Vue/Angular
            package_json = self._read_json_file("package.json")
            if package_json:
                deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
                if "react" in deps:
                    analysis["frontend_framework"] = "React"
                    analysis["tech_stack"].append("React")
                elif "vue" in deps:
                    analysis["frontend_framework"] = "Vue"
                    analysis["tech_stack"].append("Vue")
                elif "@angular/core" in deps:
                    analysis["frontend_framework"] = "Angular"
                    analysis["tech_stack"].append("Angular")

                # Backend framework
                if "express" in deps:
                    analysis["backend_framework"] = "Express"
                    analysis["tech_stack"].append("Express")
                elif "fastify" in deps:
                    analysis["backend_framework"] = "Fastify"
                    analysis["tech_stack"].append("Fastify")

        if (self.repo_path / "requirements.txt").exists() or (self.repo_path / "pyproject.toml").exists():
            analysis["project_type"] = "python"
            analysis["tech_stack"].append("Python")

            # Check for Django/Flask/FastAPI
            requirements = self._read_requirements()
            if "django" in requirements:
                analysis["backend_framework"] = "Django"
                analysis["tech_stack"].append("Django")
            elif "flask" in requirements:
                analysis["backend_framework"] = "Flask"
                analysis["tech_stack"].append("Flask")
            elif "fastapi" in requirements:
                analysis["backend_framework"] = "FastAPI"
                analysis["tech_stack"].append("FastAPI")

        # Find key directories
        common_dirs = ["src", "lib", "app", "server", "client", "frontend", "backend", "components", "models", "routes", "api"]
        for dir_name in common_dirs:
            dir_path = self.repo_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                analysis["key_directories"].append(dir_name)

                # Categorize files
                self._categorize_files(dir_path, analysis)

        # Detect database
        if (self.repo_path / "prisma").exists():
            analysis["database"] = "Prisma"
            analysis["tech_stack"].append("Prisma")
        elif "django" in analysis["tech_stack"]:
            analysis["database"] = "Django ORM"
        elif "sqlalchemy" in self._read_requirements():
            analysis["database"] = "SQLAlchemy"

        return analysis

    def _categorize_files(self, directory: Path, analysis: Dict[str, Any]):
        """Categorize files in directory."""
        try:
            for file_path in directory.rglob("*"):
                if not file_path.is_file():
                    continue

                rel_path = str(file_path.relative_to(self.repo_path))

                # Backend files
                if file_path.suffix in [".py", ".js", ".ts"] and any(
                    keyword in rel_path.lower() for keyword in ["route", "api", "controller", "model", "service"]
                ):
                    analysis["existing_files"]["backend"].append(rel_path)

                # Frontend files
                elif file_path.suffix in [".jsx", ".tsx", ".vue"] or "component" in rel_path.lower():
                    analysis["existing_files"]["frontend"].append(rel_path)

                # Test files
                elif "test" in rel_path.lower() or file_path.name.startswith("test_"):
                    analysis["existing_files"]["tests"].append(rel_path)

                # Config files
                elif file_path.suffix in [".json", ".yaml", ".yml", ".toml", ".env"]:
                    analysis["existing_files"]["configs"].append(rel_path)

        except Exception as e:
            print(f"   ⚠️  Warning: Could not categorize files in {directory}: {e}")

    def _read_json_file(self, filename: str) -> Optional[Dict]:
        """Read and parse JSON file."""
        try:
            file_path = self.repo_path / filename
            if file_path.exists():
                return json.loads(file_path.read_text())
        except Exception as e:
            print(f"   ⚠️  Warning: Could not read {filename}: {e}")
        return None

    def _read_requirements(self) -> List[str]:
        """Read Python requirements."""
        requirements = []

        # Try requirements.txt
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            try:
                requirements = [
                    line.split("==")[0].split(">=")[0].lower()
                    for line in req_file.read_text().splitlines()
                    if line.strip() and not line.startswith("#")
                ]
            except Exception:
                pass

        # Try pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomli
                data = tomli.loads(pyproject.read_text())
                deps = data.get("project", {}).get("dependencies", [])
                requirements.extend([dep.split("==")[0].split(">=")[0].lower() for dep in deps])
            except Exception:
                pass

        return requirements

    def _design_solution(
        self, feature_request: str, codebase_analysis: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Design the solution architecture using LLM reasoning."""
        # Create prompt for LLM
        prompt = f"""Design architecture for this feature request:

FEATURE REQUEST:
{feature_request}

CODEBASE ANALYSIS:
- Project Type: {codebase_analysis['project_type']}
- Tech Stack: {', '.join(codebase_analysis['tech_stack'])}
- Backend Framework: {codebase_analysis.get('backend_framework', 'None')}
- Frontend Framework: {codebase_analysis.get('frontend_framework', 'None')}
- Database: {codebase_analysis.get('database', 'None')}
- Key Directories: {', '.join(codebase_analysis['key_directories'])}

EXISTING FILES:
- Backend: {len(codebase_analysis['existing_files']['backend'])} files
- Frontend: {len(codebase_analysis['existing_files']['frontend'])} files
- Tests: {len(codebase_analysis['existing_files']['tests'])} files

Please provide a detailed architecture plan in JSON format:
{{
    "summary": "High-level approach description",
    "database_changes": [
        {{"table": "users", "action": "add_column", "column": "oauth_provider", "type": "string"}}
    ],
    "backend_files": [
        {{"path": "api/routes/auth.py", "action": "create", "purpose": "OAuth endpoints"}}
    ],
    "frontend_files": [
        {{"path": "components/LoginButton.tsx", "action": "create", "purpose": "OAuth login UI"}}
    ],
    "api_endpoints": [
        {{"method": "POST", "path": "/api/auth/oauth", "purpose": "Initiate OAuth flow"}}
    ],
    "dependencies": ["oauthlib", "python-jose"],
    "estimated_complexity": "medium",
    "risks": ["OAuth token security", "Session management"],
    "implementation_steps": [
        "1. Add database columns for OAuth",
        "2. Implement OAuth backend endpoints",
        "3. Create frontend OAuth button",
        "4. Add tests"
    ]
}}
"""

        # Use LLM to generate plan (simplified for Phase 1)
        # In production, this would call self.llm with structured output
        # For now, return a sensible default plan

        plan = {
            "summary": f"Implementing: {feature_request}",
            "database_changes": [],
            "backend_files": [],
            "frontend_files": [],
            "api_endpoints": [],
            "dependencies": [],
            "estimated_complexity": "medium",
            "risks": [],
            "implementation_steps": [
                "1. Analyze requirements",
                "2. Implement backend logic",
                "3. Implement frontend UI",
                "4. Add tests",
            ],
        }

        # Add context-specific details
        if codebase_analysis["backend_framework"]:
            plan["backend_files"].append({
                "path": f"api/routes/{self._slugify(feature_request)}.py",
                "action": "create",
                "purpose": f"API endpoints for {feature_request}",
            })

        if codebase_analysis["frontend_framework"] == "React":
            plan["frontend_files"].append({
                "path": f"components/{self._pascalcase(feature_request)}.tsx",
                "action": "create",
                "purpose": f"React component for {feature_request}",
            })

        return plan

    def _validate_plan(self, plan: Dict[str, Any]) -> Dict[str, bool]:
        """Validate the architecture plan."""
        required_fields = ["summary", "estimated_complexity", "implementation_steps"]

        for field in required_fields:
            if field not in plan:
                return {"valid": False, "reason": f"Missing required field: {field}"}

        if plan["estimated_complexity"] not in ["low", "medium", "high"]:
            return {"valid": False, "reason": "Invalid complexity level"}

        return {"valid": True}

    def _write_architecture_doc(self, feature_request: str, plan: Dict[str, Any]) -> Path:
        """Write architecture documentation to file."""
        doc_path = self.repo_path / "ARCHITECTURE.md"

        content = f"""# Architecture Plan

**Feature:** {feature_request}
**Date:** {self._get_timestamp()}
**Complexity:** {plan['estimated_complexity']}

## Summary

{plan['summary']}

## Database Changes

"""
        if plan.get("database_changes"):
            for change in plan["database_changes"]:
                content += f"- **{change.get('table', 'unknown')}**: {change.get('action', 'modify')} - {change.get('column', 'N/A')}\n"
        else:
            content += "No database changes required.\n"

        content += "\n## Backend Files\n\n"
        if plan.get("backend_files"):
            for file in plan["backend_files"]:
                content += f"- **{file['path']}** ({file['action']}): {file['purpose']}\n"
        else:
            content += "No backend files.\n"

        content += "\n## Frontend Files\n\n"
        if plan.get("frontend_files"):
            for file in plan["frontend_files"]:
                content += f"- **{file['path']}** ({file['action']}): {file['purpose']}\n"
        else:
            content += "No frontend files.\n"

        content += "\n## API Endpoints\n\n"
        if plan.get("api_endpoints"):
            for endpoint in plan["api_endpoints"]:
                content += f"- **{endpoint['method']} {endpoint['path']}**: {endpoint['purpose']}\n"
        else:
            content += "No new API endpoints.\n"

        content += "\n## Dependencies\n\n"
        if plan.get("dependencies"):
            for dep in plan["dependencies"]:
                content += f"- {dep}\n"
        else:
            content += "No new dependencies.\n"

        content += "\n## Implementation Steps\n\n"
        for step in plan.get("implementation_steps", []):
            content += f"{step}\n"

        content += "\n## Risks\n\n"
        if plan.get("risks"):
            for risk in plan["risks"]:
                content += f"- {risk}\n"
        else:
            content += "No identified risks.\n"

        doc_path.write_text(content)
        return doc_path

    def _slugify(self, text: str) -> str:
        """Convert text to slug."""
        return text.lower().replace(" ", "_")[:30]

    def _pascalcase(self, text: str) -> str:
        """Convert text to PascalCase."""
        words = text.split()[:3]
        return "".join(word.capitalize() for word in words)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

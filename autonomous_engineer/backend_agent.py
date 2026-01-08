"""BackendAgent - Implements server-side code.

This agent implements backend functionality based on the architecture plan.

Responsibilities:
1. Implement database models
2. Create database migrations
3. Implement API endpoints
4. Add business logic
5. Add error handling and validation
6. Follow existing code patterns
7. Add proper logging
8. Include docstrings and comments
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from sub_agents import BaseSubAgent


class BackendAgent(BaseSubAgent):
    """Implements backend code based on architecture plan."""

    def __init__(self, repo_path: str = "."):
        """Initialize the backend agent.

        Args:
            repo_path: Path to the project repository
        """
        system_prompt = """You are a Senior Backend Engineer with expertise in building robust server-side applications.

Your responsibilities:
1. Implement database models following the architecture plan
2. Create clean, testable API endpoints
3. Add comprehensive error handling
4. Implement proper validation
5. Follow REST/GraphQL best practices
6. Write secure code (prevent SQL injection, XSS, etc.)
7. Add logging for debugging
8. Follow project conventions and patterns
9. Write clear docstrings and comments

CODE QUALITY:
- Keep functions focused (single responsibility)
- Use descriptive variable names
- Add type hints (Python) or TypeScript types
- Handle edge cases
- Validate all inputs
- Use proper HTTP status codes
- Return consistent response formats

SECURITY:
- Sanitize all user inputs
- Use parameterized queries (prevent SQL injection)
- Implement authentication/authorization checks
- Hash passwords (bcrypt/argon2)
- Rate limiting for sensitive endpoints
- CSRF protection
- Input validation

ERROR HANDLING:
- Try/catch blocks for external calls
- Return meaningful error messages
- Log errors with context
- Don't expose sensitive info in errors
- Use custom exceptions

PATTERNS:
- Follow existing project structure
- Use existing libraries/utilities
- Match existing naming conventions
- Follow framework best practices (Django/Flask/FastAPI/Express)
"""
        super().__init__("BackendAgent", system_prompt)
        self.repo_path = Path(repo_path)

    def execute(self, architecture_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implement backend code based on architecture plan.

        Args:
            architecture_plan: Architecture plan from ArchitectAgent
            context: Optional context (framework details, etc.)

        Returns:
            Dictionary with status and files created
        """
        print(f"⚙️  Implementing backend code...")

        files_created = []
        errors = []

        # Get backend files from plan
        backend_files = architecture_plan.get("backend_files", [])

        if not backend_files:
            print(f"   ℹ️  No backend files specified in architecture plan")
            return {
                "status": "success",
                "files_created": [],
                "message": "No backend implementation needed",
            }

        # Implement each file
        for file_spec in backend_files:
            try:
                print(f"   📝 Creating {file_spec['path']}...")
                code = self._generate_code(file_spec, architecture_plan, context)

                file_path = self.repo_path / file_spec["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code)

                files_created.append(file_spec["path"])
                print(f"      ✅ Created {file_spec['path']}")

            except Exception as e:
                error_msg = f"Failed to create {file_spec['path']}: {str(e)}"
                errors.append(error_msg)
                print(f"      ❌ {error_msg}")

        if errors:
            return {
                "status": "error",
                "message": f"Failed to create {len(errors)} files",
                "errors": errors,
                "files_created": files_created,
            }

        return {
            "status": "success",
            "files_created": files_created,
            "message": f"Created {len(files_created)} backend files",
        }

    def _generate_code(
        self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate code for a backend file.

        Args:
            file_spec: File specification from architecture plan
            architecture_plan: Full architecture plan
            context: Optional context

        Returns:
            Generated code as string
        """
        file_path = file_spec["path"]
        purpose = file_spec.get("purpose", "Backend implementation")

        # Determine file type and generate appropriate code
        if "model" in file_path.lower():
            return self._generate_model_code(file_spec, architecture_plan)
        elif "route" in file_path.lower() or "api" in file_path.lower():
            return self._generate_api_code(file_spec, architecture_plan)
        elif "service" in file_path.lower():
            return self._generate_service_code(file_spec, architecture_plan)
        elif "schema" in file_path.lower():
            return self._generate_schema_code(file_spec, architecture_plan)
        else:
            return self._generate_generic_code(file_spec, architecture_plan)

    def _generate_model_code(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate database model code."""
        # Check if Python or JavaScript
        if file_spec["path"].endswith(".py"):
            return self._generate_python_model(file_spec, architecture_plan)
        else:
            return self._generate_js_model(file_spec, architecture_plan)

    def _generate_python_model(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate Python model code (SQLAlchemy/Django)."""
        model_name = self._extract_model_name(file_spec["path"])

        code = f'''"""Database model for {model_name}.

Auto-generated by AutonomousEngineer.
Purpose: {file_spec.get('purpose', 'N/A')}
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class {model_name}(Base):
    """Model for {model_name.lower()} data."""

    __tablename__ = "{model_name.lower()}s"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # TODO: Add specific fields based on requirements

    def __repr__(self):
        return f"<{model_name}(id={{self.id}})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {{
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }}
'''
        return code

    def _generate_js_model(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate JavaScript/TypeScript model code (Prisma/TypeORM)."""
        model_name = self._extract_model_name(file_spec["path"])

        code = f'''/**
 * Database model for {model_name}
 *
 * Auto-generated by AutonomousEngineer
 * Purpose: {file_spec.get('purpose', 'N/A')}
 */

import {{ Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn }} from 'typeorm';

@Entity()
export class {model_name} {{
  @PrimaryGeneratedColumn()
  id: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  // TODO: Add specific fields based on requirements
}}
'''
        return code

    def _generate_api_code(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate API endpoint code."""
        if file_spec["path"].endswith(".py"):
            return self._generate_python_api(file_spec, architecture_plan)
        else:
            return self._generate_js_api(file_spec, architecture_plan)

    def _generate_python_api(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate Python API endpoints (FastAPI/Flask)."""
        route_name = self._extract_route_name(file_spec["path"])

        code = f'''"""API routes for {route_name}.

Auto-generated by AutonomousEngineer.
Purpose: {file_spec.get('purpose', 'N/A')}
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/{route_name}", tags=["{route_name}"])


class {route_name.capitalize()}Create(BaseModel):
    """Request model for creating {route_name}."""
    # TODO: Add fields
    pass


class {route_name.capitalize()}Response(BaseModel):
    """Response model for {route_name}."""
    id: int
    # TODO: Add fields

    class Config:
        from_attributes = True


@router.get("/", response_model=List[{route_name.capitalize()}Response])
async def list_{route_name}():
    """List all {route_name}.

    Returns:
        List of {route_name} objects
    """
    # TODO: Implement list logic
    return []


@router.get("/{{id}}", response_model={route_name.capitalize()}Response)
async def get_{route_name}(id: int):
    """Get a single {route_name} by ID.

    Args:
        id: {route_name.capitalize()} ID

    Returns:
        {route_name.capitalize()} object

    Raises:
        HTTPException: If {route_name} not found
    """
    # TODO: Implement get logic
    raise HTTPException(status_code=404, detail="{route_name.capitalize()} not found")


@router.post("/", response_model={route_name.capitalize()}Response, status_code=201)
async def create_{route_name}(data: {route_name.capitalize()}Create):
    """Create a new {route_name}.

    Args:
        data: {route_name.capitalize()} creation data

    Returns:
        Created {route_name} object
    """
    # TODO: Implement create logic
    pass


@router.put("/{{id}}", response_model={route_name.capitalize()}Response)
async def update_{route_name}(id: int, data: {route_name.capitalize()}Create):
    """Update a {route_name}.

    Args:
        id: {route_name.capitalize()} ID
        data: Updated data

    Returns:
        Updated {route_name} object

    Raises:
        HTTPException: If {route_name} not found
    """
    # TODO: Implement update logic
    raise HTTPException(status_code=404, detail="{route_name.capitalize()} not found")


@router.delete("/{{id}}", status_code=204)
async def delete_{route_name}(id: int):
    """Delete a {route_name}.

    Args:
        id: {route_name.capitalize()} ID

    Raises:
        HTTPException: If {route_name} not found
    """
    # TODO: Implement delete logic
    raise HTTPException(status_code=404, detail="{route_name.capitalize()} not found")
'''
        return code

    def _generate_js_api(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate JavaScript/TypeScript API endpoints (Express)."""
        route_name = self._extract_route_name(file_spec["path"])

        code = f'''/**
 * API routes for {route_name}
 *
 * Auto-generated by AutonomousEngineer
 * Purpose: {file_spec.get('purpose', 'N/A')}
 */

import {{ Router }} from 'express';
import type {{ Request, Response }} from 'express';

const router = Router();

/**
 * List all {route_name}
 */
router.get('/', async (req: Request, res: Response) => {{
  try {{
    // TODO: Implement list logic
    res.json([]);
  }} catch (error) {{
    res.status(500).json({{ error: 'Internal server error' }});
  }}
}});

/**
 * Get a single {route_name} by ID
 */
router.get('/:id', async (req: Request, res: Response) => {{
  try {{
    const {{ id }} = req.params;
    // TODO: Implement get logic
    res.status(404).json({{ error: '{route_name.capitalize()} not found' }});
  }} catch (error) {{
    res.status(500).json({{ error: 'Internal server error' }});
  }}
}});

/**
 * Create a new {route_name}
 */
router.post('/', async (req: Request, res: Response) => {{
  try {{
    const data = req.body;
    // TODO: Implement create logic
    res.status(201).json({{ message: 'Created' }});
  }} catch (error) {{
    res.status(500).json({{ error: 'Internal server error' }});
  }}
}});

/**
 * Update a {route_name}
 */
router.put('/:id', async (req: Request, res: Response) => {{
  try {{
    const {{ id }} = req.params;
    const data = req.body;
    // TODO: Implement update logic
    res.status(404).json({{ error: '{route_name.capitalize()} not found' }});
  }} catch (error) {{
    res.status(500).json({{ error: 'Internal server error' }});
  }}
}});

/**
 * Delete a {route_name}
 */
router.delete('/:id', async (req: Request, res: Response) => {{
  try {{
    const {{ id }} = req.params;
    // TODO: Implement delete logic
    res.status(204).send();
  }} catch (error) {{
    res.status(500).json({{ error: 'Internal server error' }});
  }}
}});

export default router;
'''
        return code

    def _generate_service_code(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate service layer code."""
        service_name = self._extract_service_name(file_spec["path"])

        code = f'''"""Business logic service for {service_name}.

Auto-generated by AutonomousEngineer.
Purpose: {file_spec.get('purpose', 'N/A')}
"""

from typing import List, Optional


class {service_name}Service:
    """Service class for {service_name.lower()} business logic."""

    def __init__(self):
        """Initialize the service."""
        pass

    def process(self, data: dict) -> dict:
        """Process {service_name.lower()} data.

        Args:
            data: Input data

        Returns:
            Processed result

        Raises:
            ValueError: If data is invalid
        """
        # TODO: Implement business logic
        return data

    def validate(self, data: dict) -> bool:
        """Validate {service_name.lower()} data.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement validation logic
        return True
'''
        return code

    def _generate_schema_code(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate schema/validation code."""
        schema_name = self._extract_schema_name(file_spec["path"])

        code = f'''"""Data schemas for {schema_name}.

Auto-generated by AutonomousEngineer.
Purpose: {file_spec.get('purpose', 'N/A')}
"""

from pydantic import BaseModel, validator
from typing import Optional


class {schema_name}Base(BaseModel):
    """Base schema for {schema_name.lower()}."""
    # TODO: Add fields
    pass


class {schema_name}Create({schema_name}Base):
    """Schema for creating {schema_name.lower()}."""
    pass


class {schema_name}Update(BaseModel):
    """Schema for updating {schema_name.lower()}."""
    # TODO: Add optional fields
    pass


class {schema_name}Response({schema_name}Base):
    """Schema for {schema_name.lower()} responses."""
    id: int

    class Config:
        from_attributes = True
'''
        return code

    def _generate_generic_code(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate generic backend code."""
        code = f'''"""Auto-generated backend code.

Purpose: {file_spec.get('purpose', 'N/A')}
File: {file_spec['path']}
"""

# TODO: Implement functionality based on requirements
'''
        return code

    def _extract_model_name(self, path: str) -> str:
        """Extract model name from file path."""
        name = Path(path).stem
        return name.replace("_model", "").replace("_", " ").title().replace(" ", "")

    def _extract_route_name(self, path: str) -> str:
        """Extract route name from file path."""
        name = Path(path).stem
        return name.replace("_routes", "").replace("_route", "").replace("_api", "").replace("_", "")

    def _extract_service_name(self, path: str) -> str:
        """Extract service name from file path."""
        name = Path(path).stem
        return name.replace("_service", "").replace("_", " ").title().replace(" ", "")

    def _extract_schema_name(self, path: str) -> str:
        """Extract schema name from file path."""
        name = Path(path).stem
        return name.replace("_schema", "").replace("_", " ").title().replace(" ", "")

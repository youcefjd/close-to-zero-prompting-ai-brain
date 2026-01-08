"""FrontendAgent - Implements client-side UI code.

This agent implements frontend functionality based on the architecture plan.

Responsibilities:
1. Create React/Vue/Angular components
2. Implement state management
3. Add API integration
4. Style with CSS/Tailwind/styled-components
5. Add form validation
6. Handle loading and error states
7. Ensure accessibility (a11y)
8. Make responsive for mobile
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from sub_agents import BaseSubAgent


class FrontendAgent(BaseSubAgent):
    """Implements frontend code based on architecture plan."""

    def __init__(self, repo_path: str = "."):
        """Initialize the frontend agent.

        Args:
            repo_path: Path to the project repository
        """
        system_prompt = """You are a Senior Frontend Engineer with expertise in modern web frameworks.

Your responsibilities:
1. Build clean, reusable React/Vue/Angular components
2. Implement proper state management (Redux/Context/Vuex/Pinia)
3. Integrate with backend APIs
4. Create responsive, mobile-friendly UIs
5. Ensure accessibility (WCAG 2.1 AA)
6. Handle loading, error, and empty states
7. Write semantic HTML
8. Follow design system/style guide
9. Optimize performance (code splitting, lazy loading)

CODE QUALITY:
- Functional components with hooks (React)
- Composition API (Vue 3)
- Single-file components
- Props validation/TypeScript types
- Meaningful component names
- Keep components focused
- Extract reusable logic to hooks/composables

UI/UX BEST PRACTICES:
- Loading indicators for async operations
- Error messages that are helpful
- Form validation with clear feedback
- Empty states for no data
- Disabled buttons during submission
- Optimistic UI updates
- Keyboard navigation
- Screen reader support

ACCESSIBILITY:
- Semantic HTML elements
- ARIA labels where needed
- Keyboard accessible
- Focus management
- Alt text for images
- Color contrast (WCAG AA)
- Form labels

STYLING:
- Use existing design system
- Responsive breakpoints
- Mobile-first approach
- Consistent spacing/typography
- Dark mode support (if applicable)

STATE MANAGEMENT:
- Local state for UI-only data
- Context/store for shared state
- API cache with React Query/SWR
- Form state with controlled components
- URL state for shareable views
"""
        super().__init__("FrontendAgent", system_prompt)
        self.repo_path = Path(repo_path)

    def execute(self, architecture_plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implement frontend code based on architecture plan.

        Args:
            architecture_plan: Architecture plan from ArchitectAgent
            context: Optional context (framework details, etc.)

        Returns:
            Dictionary with status and files created
        """
        print(f"🎨 Implementing frontend code...")

        files_created = []
        errors = []

        # Get frontend files from plan
        frontend_files = architecture_plan.get("frontend_files", [])

        if not frontend_files:
            print(f"   ℹ️  No frontend files specified in architecture plan")
            return {
                "status": "success",
                "files_created": [],
                "message": "No frontend implementation needed",
            }

        # Implement each file
        for file_spec in frontend_files:
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
            "message": f"Created {len(files_created)} frontend files",
        }

    def _generate_code(
        self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate code for a frontend file.

        Args:
            file_spec: File specification from architecture plan
            architecture_plan: Full architecture plan
            context: Optional context

        Returns:
            Generated code as string
        """
        file_path = file_spec["path"]

        # Determine file type and generate appropriate code
        if file_path.endswith(".tsx") or file_path.endswith(".jsx"):
            return self._generate_react_component(file_spec, architecture_plan)
        elif file_path.endswith(".vue"):
            return self._generate_vue_component(file_spec, architecture_plan)
        elif "hook" in file_path.lower():
            return self._generate_react_hook(file_spec, architecture_plan)
        elif "store" in file_path.lower() or "slice" in file_path.lower():
            return self._generate_state_management(file_spec, architecture_plan)
        else:
            return self._generate_generic_component(file_spec, architecture_plan)

    def _generate_react_component(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate React component code."""
        component_name = self._extract_component_name(file_spec["path"])
        is_typescript = file_spec["path"].endswith(".tsx")

        type_annotation = ": React.FC" if is_typescript else ""
        props_type = f"\n\ninterface {component_name}Props {{\n  // TODO: Add props\n}}\n" if is_typescript else ""

        code = f'''/**
 * {component_name} Component
 *
 * Auto-generated by AutonomousEngineer
 * Purpose: {file_spec.get('purpose', 'N/A')}
 */

import React, {{ useState, useEffect }} from 'react';

{props_type}
export const {component_name}{type_annotation} = () => {{
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {{
    // TODO: Implement data fetching or side effects
  }}, []);

  if (loading) {{
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }}

  if (error) {{
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded" role="alert">
        <p>{{error}}</p>
      </div>
    );
  }}

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{component_name}</h1>

      {{/* TODO: Implement component UI */}}
      <div>
        <p>Component content goes here</p>
      </div>
    </div>
  );
}};

export default {component_name};
'''
        return code

    def _generate_vue_component(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate Vue component code."""
        component_name = self._extract_component_name(file_spec["path"])

        code = f'''<!--
  {component_name} Component

  Auto-generated by AutonomousEngineer
  Purpose: {file_spec.get('purpose', 'N/A')}
-->

<template>
  <div class="container mx-auto p-4">
    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center items-center p-4">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded"
      role="alert"
    >
      <p>{{{{ error }}}}</p>
    </div>

    <!-- Main content -->
    <div v-else>
      <h1 class="text-2xl font-bold mb-4">{component_name}</h1>

      <!-- TODO: Implement component UI -->
      <div>
        <p>Component content goes here</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {{ ref, onMounted }} from 'vue';

// State
const loading = ref(false);
const error = ref<string | null>(null);
const data = ref<any>(null);

// Lifecycle
onMounted(() => {{
  // TODO: Implement data fetching or initialization
}});

// Methods
// TODO: Add component methods
</script>

<style scoped>
/* TODO: Add component-specific styles */
</style>
'''
        return code

    def _generate_react_hook(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate React custom hook code."""
        hook_name = self._extract_hook_name(file_spec["path"])

        code = f'''/**
 * {hook_name} Hook
 *
 * Auto-generated by AutonomousEngineer
 * Purpose: {file_spec.get('purpose', 'N/A')}
 */

import {{ useState, useEffect, useCallback }} from 'react';

interface {hook_name.replace('use', '')}Options {{
  // TODO: Add options
}}

interface {hook_name.replace('use', '')}Result {{
  data: any;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}}

export const {hook_name} = (
  options?: {hook_name.replace('use', '')}Options
): {hook_name.replace('use', '')}Result => {{
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {{
    setLoading(true);
    setError(null);

    try {{
      // TODO: Implement data fetching logic
      const response = await fetch('/api/endpoint');

      if (!response.ok) {{
        throw new Error('Failed to fetch data');
      }}

      const result = await response.json();
      setData(result);
    }} catch (err) {{
      setError(err instanceof Error ? err.message : 'An error occurred');
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  useEffect(() => {{
    fetchData();
  }}, [fetchData]);

  return {{
    data,
    loading,
    error,
    refetch: fetchData,
  }};
}};

export default {hook_name};
'''
        return code

    def _generate_state_management(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate state management code (Redux/Zustand/etc)."""
        store_name = self._extract_store_name(file_spec["path"])

        code = f'''/**
 * {store_name} Store
 *
 * Auto-generated by AutonomousEngineer
 * Purpose: {file_spec.get('purpose', 'N/A')}
 */

import {{ createSlice, PayloadAction }} from '@reduxjs/toolkit';

interface {store_name}State {{
  items: any[];
  loading: boolean;
  error: string | null;
}}

const initialState: {store_name}State = {{
  items: [],
  loading: false,
  error: null,
}};

const {store_name.lower()}Slice = createSlice({{
  name: '{store_name.lower()}',
  initialState,
  reducers: {{
    setLoading: (state, action: PayloadAction<boolean>) => {{
      state.loading = action.payload;
    }},
    setError: (state, action: PayloadAction<string | null>) => {{
      state.error = action.payload;
    }},
    setItems: (state, action: PayloadAction<any[]>) => {{
      state.items = action.payload;
      state.loading = false;
      state.error = null;
    }},
    addItem: (state, action: PayloadAction<any>) => {{
      state.items.push(action.payload);
    }},
    updateItem: (state, action: PayloadAction<{{ id: string; data: any }}>) => {{
      const index = state.items.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {{
        state.items[index] = {{ ...state.items[index], ...action.payload.data }};
      }}
    }},
    removeItem: (state, action: PayloadAction<string>) => {{
      state.items = state.items.filter(item => item.id !== action.payload);
    }},
  }},
}});

export const {{
  setLoading,
  setError,
  setItems,
  addItem,
  updateItem,
  removeItem,
}} = {store_name.lower()}Slice.actions;

export default {store_name.lower()}Slice.reducer;

// Selectors
export const select{store_name}Items = (state: any) => state.{store_name.lower()}.items;
export const select{store_name}Loading = (state: any) => state.{store_name.lower()}.loading;
export const select{store_name}Error = (state: any) => state.{store_name.lower()}.error;
'''
        return code

    def _generate_generic_component(self, file_spec: Dict[str, Any], architecture_plan: Dict[str, Any]) -> str:
        """Generate generic frontend code."""
        code = f'''/**
 * Auto-generated frontend code
 *
 * Purpose: {file_spec.get('purpose', 'N/A')}
 * File: {file_spec['path']}
 */

// TODO: Implement functionality based on requirements

export default {{}};
'''
        return code

    def _extract_component_name(self, path: str) -> str:
        """Extract component name from file path."""
        name = Path(path).stem
        # Remove common suffixes
        name = name.replace('.component', '').replace('.test', '')
        # Convert to PascalCase
        return "".join(word.capitalize() for word in name.split("_"))

    def _extract_hook_name(self, path: str) -> str:
        """Extract hook name from file path."""
        name = Path(path).stem
        # Ensure it starts with 'use'
        if not name.startswith('use'):
            name = 'use' + "".join(word.capitalize() for word in name.split("_"))
        return name

    def _extract_store_name(self, path: str) -> str:
        """Extract store/slice name from file path."""
        name = Path(path).stem
        name = name.replace('_slice', '').replace('_store', '')
        return "".join(word.capitalize() for word in name.split("_"))

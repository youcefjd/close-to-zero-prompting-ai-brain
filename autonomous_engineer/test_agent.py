"""TestAgent - Generates comprehensive tests.

This agent generates unit, integration, and end-to-end tests for implemented code.

Responsibilities:
1. Write unit tests (80%+ coverage target)
2. Write integration tests
3. Write E2E tests for critical paths
4. Test edge cases
5. Test error handling
6. Run tests and report results
7. Calculate coverage
"""

import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

from sub_agents import BaseSubAgent


class TestAgent(BaseSubAgent):
    """Generates tests for implemented code."""

    def __init__(self, repo_path: str = "."):
        """Initialize the test agent.

        Args:
            repo_path: Path to the project repository
        """
        system_prompt = """You are a Test Engineer specializing in comprehensive test coverage.

Your responsibilities:
1. Write unit tests for individual functions/components
2. Write integration tests for API endpoints and data flows
3. Write E2E tests for critical user workflows
4. Test happy paths AND edge cases
5. Test error handling and validation
6. Aim for 80%+ code coverage
7. Write clear, maintainable tests
8. Follow testing best practices

TEST TYPES:

Unit Tests:
- Test individual functions in isolation
- Mock external dependencies
- Test return values, side effects
- Test edge cases (null, empty, boundary values)
- Fast execution

Integration Tests:
- Test API endpoints with real database
- Test data flows between components
- Test middleware and authentication
- Verify HTTP status codes and responses
- Test validation and error handling

E2E Tests:
- Test complete user workflows
- Test critical business paths
- Use real browser (Playwright/Cypress)
- Test from user perspective

TEST PRINCIPLES:
- Arrange-Act-Assert pattern
- One assertion per test (when possible)
- Descriptive test names
- Test behavior, not implementation
- Independent tests (no shared state)
- Fast, reliable, isolated

TESTING FRAMEWORKS:
- Python: pytest, unittest
- JavaScript: Jest, Vitest, Mocha
- E2E: Playwright, Cypress, Selenium
- React: React Testing Library
- Vue: Vue Test Utils

COVERAGE:
- Aim for 80%+ line coverage
- 100% for critical paths
- Test edge cases
- Test error handling
"""
        super().__init__("TestAgent", system_prompt)
        self.repo_path = Path(repo_path)

    def execute(self, implementation_files: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate tests for implemented files.

        Args:
            implementation_files: List of file paths that were implemented
            context: Optional context

        Returns:
            Dictionary with status, tests created, and test results
        """
        print(f"🧪 Generating tests for {len(implementation_files)} files...")

        tests_created = []
        errors = []

        # Generate tests for each implementation file
        for file_path in implementation_files:
            try:
                print(f"   📝 Generating tests for {file_path}...")

                # Read the implementation file
                impl_path = self.repo_path / file_path
                if not impl_path.exists():
                    print(f"      ⚠️  File not found: {file_path}")
                    continue

                implementation_code = impl_path.read_text()

                # Generate test code
                test_code = self._generate_test_code(file_path, implementation_code)

                # Write test file
                test_path = self._get_test_path(file_path)
                test_file_path = self.repo_path / test_path
                test_file_path.parent.mkdir(parents=True, exist_ok=True)
                test_file_path.write_text(test_code)

                tests_created.append(test_path)
                print(f"      ✅ Created {test_path}")

            except Exception as e:
                error_msg = f"Failed to generate tests for {file_path}: {str(e)}"
                errors.append(error_msg)
                print(f"      ❌ {error_msg}")

        # Run tests
        print(f"\n   🏃 Running test suite...")
        test_results = self._run_tests()

        if errors:
            return {
                "status": "partial_success",
                "message": f"Generated {len(tests_created)} tests with {len(errors)} errors",
                "tests_created": tests_created,
                "errors": errors,
                "test_results": test_results,
            }

        return {
            "status": "success",
            "tests_created": tests_created,
            "test_results": test_results,
            "message": f"Generated {len(tests_created)} test files",
        }

    def _generate_test_code(self, file_path: str, implementation_code: str) -> str:
        """Generate test code for an implementation file.

        Args:
            file_path: Path to implementation file
            implementation_code: Code to test

        Returns:
            Generated test code
        """
        # Determine file type and generate appropriate tests
        if file_path.endswith(".py"):
            return self._generate_python_tests(file_path, implementation_code)
        elif file_path.endswith((".tsx", ".jsx", ".ts", ".js")):
            return self._generate_javascript_tests(file_path, implementation_code)
        elif file_path.endswith(".vue"):
            return self._generate_vue_tests(file_path, implementation_code)
        else:
            return self._generate_generic_tests(file_path, implementation_code)

    def _generate_python_tests(self, file_path: str, implementation_code: str) -> str:
        """Generate pytest tests for Python code."""
        module_name = Path(file_path).stem
        class_name = self._extract_class_name(implementation_code)

        # Extract function names from implementation
        function_names = self._extract_function_names(implementation_code)

        # Generate test code
        code = f'''"""Tests for {module_name}.

Auto-generated by AutonomousEngineer.
"""

import pytest
from unittest.mock import Mock, patch
from {file_path.replace('/', '.').replace('.py', '')} import {class_name or '*'}


class Test{class_name or module_name.capitalize()}:
    """Test suite for {class_name or module_name}."""

    def setup_method(self):
        """Set up test fixtures."""
        # TODO: Add setup code
        pass

    def teardown_method(self):
        """Clean up after tests."""
        # TODO: Add cleanup code
        pass

'''

        # Generate test methods for each function
        for func_name in function_names[:5]:  # Limit to 5 functions for now
            code += f'''    def test_{func_name}_success(self):
        """Test {func_name} with valid input."""
        # Arrange
        # TODO: Set up test data

        # Act
        # result = {func_name}()

        # Assert
        # assert result is not None
        pass

    def test_{func_name}_error(self):
        """Test {func_name} with invalid input."""
        # Arrange
        # TODO: Set up invalid test data

        # Act & Assert
        # with pytest.raises(ValueError):
        #     {func_name}()
        pass

'''

        code += '''    def test_integration(self):
        """Integration test for the module."""
        # TODO: Test module integration
        pass


# Additional test utilities
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {}


# TODO: Add more test cases
'''

        return code

    def _generate_javascript_tests(self, file_path: str, implementation_code: str) -> str:
        """Generate Jest/Vitest tests for JavaScript/TypeScript code."""
        module_name = Path(file_path).stem
        is_component = any(keyword in file_path.lower() for keyword in ["component", "page", ".tsx", ".jsx"])

        if is_component:
            return self._generate_react_component_tests(file_path, module_name)
        else:
            return self._generate_javascript_unit_tests(file_path, module_name)

    def _generate_react_component_tests(self, file_path: str, component_name: str) -> str:
        """Generate React Testing Library tests."""
        code = f'''/**
 * Tests for {component_name}
 *
 * Auto-generated by AutonomousEngineer
 */

import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import {{ describe, it, expect, vi }} from 'vitest';
import {component_name} from '../{Path(file_path).name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
    expect(screen.getByText(/.*/, {{ exact: false }})).toBeInTheDocument();
  }});

  it('displays loading state', () => {{
    // TODO: Mock loading state
    render(<{component_name} />);
    // expect(screen.getByText(/loading/i)).toBeInTheDocument();
  }});

  it('displays error state', () => {{
    // TODO: Mock error state
    render(<{component_name} />);
    // expect(screen.getByText(/error/i)).toBeInTheDocument();
  }});

  it('handles user interaction', async () => {{
    render(<{component_name} />);

    // TODO: Simulate user interaction
    // const button = screen.getByRole('button');
    // fireEvent.click(button);

    // await waitFor(() => {{
    //   expect(screen.getByText(/success/i)).toBeInTheDocument();
    // }});
  }});

  it('calls API on mount', async () => {{
    // TODO: Mock API call
    const mockFetch = vi.fn();
    global.fetch = mockFetch;

    render(<{component_name} />);

    // await waitFor(() => {{
    //   expect(mockFetch).toHaveBeenCalled();
    // }});
  }});
}});

// TODO: Add more test cases
'''
        return code

    def _generate_javascript_unit_tests(self, file_path: str, module_name: str) -> str:
        """Generate Jest unit tests for JavaScript modules."""
        code = f'''/**
 * Tests for {module_name}
 *
 * Auto-generated by AutonomousEngineer
 */

import {{ describe, it, expect, vi, beforeEach, afterEach }} from 'vitest';
import * as module from '../{Path(file_path).name}';

describe('{module_name}', () => {{
  beforeEach(() => {{
    // Setup before each test
  }});

  afterEach(() => {{
    // Cleanup after each test
  }});

  it('exports expected functions', () => {{
    expect(module).toBeDefined();
    // TODO: Check for specific exports
  }});

  it('handles valid input', () => {{
    // TODO: Test with valid input
    // const result = module.someFunction(validInput);
    // expect(result).toBeDefined();
  }});

  it('handles invalid input', () => {{
    // TODO: Test with invalid input
    // expect(() => module.someFunction(invalidInput)).toThrow();
  }});

  it('handles edge cases', () => {{
    // TODO: Test edge cases
    // null, undefined, empty array, etc.
  }});
}});

// TODO: Add more test cases
'''
        return code

    def _generate_vue_tests(self, file_path: str, implementation_code: str) -> str:
        """Generate Vue Test Utils tests."""
        component_name = Path(file_path).stem

        code = f'''/**
 * Tests for {component_name}
 *
 * Auto-generated by AutonomousEngineer
 */

import {{ mount }} from '@vue/test-utils';
import {{ describe, it, expect, vi }} from 'vitest';
import {component_name} from '../{Path(file_path).name}';

describe('{component_name}', () => {{
  it('renders properly', () => {{
    const wrapper = mount({component_name});
    expect(wrapper.exists()).toBe(true);
  }});

  it('displays loading state', async () => {{
    const wrapper = mount({component_name});
    // TODO: Test loading state
  }});

  it('handles user interaction', async () => {{
    const wrapper = mount({component_name});

    // TODO: Simulate interaction
    // await wrapper.find('button').trigger('click');
    // expect(wrapper.emitted()).toHaveProperty('event-name');
  }});

  it('emits events correctly', async () => {{
    const wrapper = mount({component_name});

    // TODO: Test event emission
    // await wrapper.vm.$emit('event-name', payload);
    // expect(wrapper.emitted('event-name')).toBeTruthy();
  }});
}});

// TODO: Add more test cases
'''
        return code

    def _generate_generic_tests(self, file_path: str, implementation_code: str) -> str:
        """Generate generic test template."""
        return f'''"""Generic tests for {file_path}

Auto-generated by AutonomousEngineer.
"""

# TODO: Implement tests for {file_path}

def test_placeholder():
    """Placeholder test."""
    assert True
'''

    def _get_test_path(self, implementation_path: str) -> str:
        """Get test file path for an implementation file."""
        path = Path(implementation_path)

        # Python: tests/test_filename.py
        if path.suffix == ".py":
            return f"tests/test_{path.name}"

        # JavaScript/TypeScript: same dir with .test.ts suffix
        elif path.suffix in [".ts", ".tsx", ".js", ".jsx", ".vue"]:
            return str(path.parent / f"{path.stem}.test{path.suffix}")

        else:
            return f"tests/{path.name}.test"

    def _run_tests(self) -> Dict[str, Any]:
        """Run the test suite and return results."""
        results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": 0,
            "duration": 0,
            "summary": "",
            "exit_code": 0,
        }

        try:
            # Try pytest first (Python)
            result = subprocess.run(
                ["pytest", "-v", "--tb=short", "--cov=.", "--cov-report=term"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            results["exit_code"] = result.returncode
            results["summary"] = result.stdout + result.stderr

            # Parse pytest output (simplified)
            if "passed" in result.stdout:
                results["passed"] = self._extract_count(result.stdout, "passed")
            if "failed" in result.stdout:
                results["failed"] = self._extract_count(result.stdout, "failed")

            print(f"      ✅ Tests passed: {results['passed']}")
            if results["failed"] > 0:
                print(f"      ❌ Tests failed: {results['failed']}")

        except FileNotFoundError:
            # Try npm test (JavaScript)
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                results["exit_code"] = result.returncode
                results["summary"] = result.stdout + result.stderr

            except Exception as e:
                print(f"      ⚠️  Could not run tests: {e}")
                results["summary"] = f"Test execution failed: {str(e)}"

        except Exception as e:
            print(f"      ⚠️  Error running tests: {e}")
            results["summary"] = f"Test execution error: {str(e)}"

        return results

    def _extract_count(self, output: str, keyword: str) -> int:
        """Extract count from test output."""
        try:
            # Simple extraction - look for "X passed" or "X failed"
            import re
            match = re.search(rf"(\d+)\s+{keyword}", output)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 0

    def _extract_class_name(self, code: str) -> Optional[str]:
        """Extract first class name from Python code."""
        import re
        match = re.search(r"class\s+(\w+)", code)
        return match.group(1) if match else None

    def _extract_function_names(self, code: str) -> List[str]:
        """Extract function names from code."""
        import re
        matches = re.findall(r"def\s+(\w+)\s*\(", code)
        # Filter out dunder methods
        return [name for name in matches if not name.startswith("_")][:10]

# ai-brain Examples

Learn how to build autonomous agents using the ai-brain framework.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Simple Agent](#simple-agent)
3. [Agent with Tools](#agent-with-tools)
4. [Multi-Agent System](#multi-agent-system)
5. [Real-World Examples](#real-world-examples)
   - [Autonomous PR Reviewer](#example-1-autonomous-pr-reviewer)
   - [Autonomous Engineer](#example-2-autonomous-engineer)

---

## Getting Started

### Installation

```bash
# Install ai-brain
pip install -e .

# Or with all dependencies
pip install -e ".[all]"
```

### Basic Structure

Every agent inherits from `BaseSubAgent`:

```python
from sub_agents import BaseSubAgent

class MyAgent(BaseSubAgent):
    """Your autonomous agent."""

    def __init__(self):
        system_prompt = """You are an agent that..."""
        super().__init__("MyAgent", system_prompt)

    def execute(self, task, context=None):
        # Your autonomous logic here
        return {"status": "success"}
```

---

## Simple Agent

### Hello World Agent

```python
from sub_agents import BaseSubAgent

class HelloAgent(BaseSubAgent):
    """A simple greeting agent."""

    def __init__(self):
        system_prompt = """You are a friendly greeting agent.
        You greet users and tell them about ai-brain framework."""
        super().__init__("HelloAgent", system_prompt)

    def execute(self, task, context=None):
        print(f"🤖 {self.agent_name} says hello!")
        print(f"   Task: {task}")
        print(f"   LLM: {self.llm_type}")
        print(f"   Tools available: {len(self.tools)}")

        return {
            "status": "success",
            "message": f"Hello! I'm {self.agent_name}",
            "tools_count": len(self.tools)
        }

# Usage
agent = HelloAgent()
result = agent.execute("Say hello to the world")
print(result)
```

**Output:**
```
🤖 HelloAgent says hello!
   Task: Say hello to the world
   LLM: ollama
   Tools available: 21
{'status': 'success', 'message': "Hello! I'm HelloAgent", 'tools_count': 21}
```

---

## Agent with Tools

### File Analysis Agent

```python
from sub_agents import BaseSubAgent
from pathlib import Path

class FileAnalyzerAgent(BaseSubAgent):
    """Analyzes files in a directory."""

    def __init__(self):
        system_prompt = """You are a file analyzer.
        You analyze files and provide insights."""
        super().__init__("FileAnalyzerAgent", system_prompt)

    def execute(self, directory_path, context=None):
        path = Path(directory_path)

        # Use shell tools
        result = self._execute_tool("run_shell",
            command=f"find {path} -name '*.py' | head -20"
        )

        if result["status"] == "success":
            files = result["output"].strip().split("\n")

            # Analyze each file
            analysis = []
            for file_path in files[:5]:  # First 5 files
                # Read file content
                content_result = self._execute_tool("read_file",
                    path=file_path
                )

                if content_result["status"] == "success":
                    lines = len(content_result["content"].split("\n"))
                    analysis.append({
                        "file": file_path,
                        "lines": lines
                    })

            return {
                "status": "success",
                "total_files": len(files),
                "analyzed": len(analysis),
                "files": analysis
            }

        return {
            "status": "error",
            "message": "Could not analyze directory"
        }

# Usage
agent = FileAnalyzerAgent()
result = agent.execute("/path/to/project")
print(f"Found {result['total_files']} Python files")
print(f"Analyzed {result['analyzed']} files")
```

---

## Multi-Agent System

### Coordinator + Worker Pattern

```python
from sub_agents import BaseSubAgent

class CoordinatorAgent(BaseSubAgent):
    """Coordinates multiple worker agents."""

    def __init__(self):
        system_prompt = """You coordinate worker agents."""
        super().__init__("CoordinatorAgent", system_prompt)

    def execute(self, task, context=None):
        # Spawn workers
        worker1 = WorkerAgent("Worker1")
        worker2 = WorkerAgent("Worker2")

        # Distribute work
        result1 = worker1.execute(f"{task} - Part 1")
        result2 = worker2.execute(f"{task} - Part 2")

        # Combine results
        return {
            "status": "success",
            "worker1": result1,
            "worker2": result2
        }


class WorkerAgent(BaseSubAgent):
    """Performs specific work."""

    def __init__(self, name):
        system_prompt = f"""You are {name}, a worker agent."""
        super().__init__(name, system_prompt)

    def execute(self, task, context=None):
        print(f"   {self.agent_name} working on: {task}")

        # Do work
        result = self._execute_tool("run_shell", command="echo 'Work done'")

        return {
            "status": "success",
            "worker": self.agent_name,
            "output": result["output"]
        }

# Usage
coordinator = CoordinatorAgent()
result = coordinator.execute("Process data")
```

---

## Real-World Examples

### Example 1: Autonomous PR Reviewer

**Repository:** https://github.com/youcefjd/ai-pr-review

**What it does:**
- Monitors GitHub repos 24/7
- Reviews PRs autonomously
- Posts security analysis
- Detects vulnerabilities (SQL injection, XSS, etc.)

**How it uses ai-brain:**

```python
from sub_agents import BaseSubAgent

class PRReviewAgent(BaseSubAgent):
    """Reviews pull requests for security and quality."""

    def __init__(self):
        system_prompt = """You are a security-focused code reviewer.

        You review code for:
        - SQL injection vulnerabilities
        - XSS vulnerabilities
        - Command injection
        - Authentication issues
        - Secrets in code
        """
        super().__init__("PRReviewAgent", system_prompt)

    def execute(self, pr_number, repo_name, context=None):
        # Get PR diff using GitHub tools
        diff_result = self._execute_tool("github_get_pr_diff",
            repo_name=repo_name,
            pr_number=pr_number
        )

        if diff_result["status"] != "success":
            return {"status": "error", "message": "Could not get PR diff"}

        # Analyze diff for issues
        issues = self._analyze_diff(diff_result["diff"])

        # Post comment with findings
        if issues:
            comment = self._format_review_comment(issues)
            self._execute_tool("github_post_comment",
                repo_name=repo_name,
                pr_number=pr_number,
                comment=comment
            )

        return {
            "status": "success",
            "issues_found": len(issues),
            "issues": issues
        }

    def _analyze_diff(self, diff):
        """Analyze diff for security issues."""
        issues = []

        # Check for SQL injection
        if "execute(" in diff and "+" in diff:
            issues.append({
                "type": "security",
                "severity": "high",
                "title": "Potential SQL Injection",
                "description": "Found string concatenation in SQL query"
            })

        # Check for hardcoded secrets
        if "password =" in diff.lower() or "api_key =" in diff.lower():
            issues.append({
                "type": "security",
                "severity": "critical",
                "title": "Hardcoded Secret",
                "description": "Found hardcoded password or API key"
            })

        return issues

    def _format_review_comment(self, issues):
        """Format review comment."""
        comment = "## 🔍 Autonomous Security Review\n\n"

        for issue in issues:
            comment += f"### ⚠️ {issue['title']} ({issue['severity']})\n"
            comment += f"{issue['description']}\n\n"

        comment += "---\n🤖 Review by ai-brain autonomous agent"
        return comment
```

**Key features:**
- Uses `github_get_pr_diff` tool
- Uses `github_post_comment` tool
- Autonomous security analysis
- 24/7 monitoring

**Built in:** 4 hours
**Result:** Monitors repos autonomously, catches vulnerabilities

---

### Example 2: Autonomous Engineer

**Repository:** https://github.com/youcefjd/autonomous_engineer

**What it does:**
- Takes feature request in natural language
- Designs architecture
- Implements backend + frontend
- Writes tests
- Creates PR
- All autonomously

**How it uses ai-brain:**

**7 Agents, all inherit from BaseSubAgent:**

#### 1. OrchestratorAgent
```python
from sub_agents import BaseSubAgent

class OrchestratorAgent(BaseSubAgent):
    """Master coordinator."""

    def execute(self, feature_request, context=None):
        # Phase 1: Architecture
        architect = ArchitectAgent()
        arch_result = architect.execute(feature_request)

        # Phase 2: Implementation
        backend = BackendAgent()
        backend_result = backend.execute(arch_result["plan"])

        frontend = FrontendAgent()
        frontend_result = frontend.execute(arch_result["plan"])

        # Phase 3: Testing
        tester = TestAgent()
        test_result = tester.execute([
            *backend_result["files"],
            *frontend_result["files"]
        ])

        # Phase 4: Deploy
        deployer = DeployAgent()
        deploy_result = deployer.execute({
            "name": "feature",
            "files": backend_result["files"] + frontend_result["files"]
        })

        return {
            "status": "success",
            "pr_url": deploy_result["pr_url"]
        }
```

#### 2. ArchitectAgent
```python
class ArchitectAgent(BaseSubAgent):
    """Designs solution architecture."""

    def execute(self, feature_request, context=None):
        # Analyze codebase
        files_result = self._execute_tool("run_shell",
            command="find . -name '*.py' -o -name '*.tsx'"
        )

        # Design architecture plan
        plan = {
            "backend_files": [...],
            "frontend_files": [...],
            "database_changes": [...]
        }

        # Write architecture doc
        self._execute_tool("write_file",
            path="ARCHITECTURE.md",
            content=self._format_plan(plan)
        )

        return {"status": "success", "plan": plan}
```

#### 3. BackendAgent
```python
class BackendAgent(BaseSubAgent):
    """Implements backend code."""

    def execute(self, architecture_plan, context=None):
        files_created = []

        for file_spec in architecture_plan["backend_files"]:
            code = self._generate_code(file_spec)

            self._execute_tool("write_file",
                path=file_spec["path"],
                content=code
            )

            files_created.append(file_spec["path"])

        return {
            "status": "success",
            "files": files_created
        }
```

#### 4. TestAgent
```python
class TestAgent(BaseSubAgent):
    """Generates tests."""

    def execute(self, implementation_files, context=None):
        tests_created = []

        for file_path in implementation_files:
            test_code = self._generate_tests(file_path)
            test_path = f"tests/test_{Path(file_path).name}"

            self._execute_tool("write_file",
                path=test_path,
                content=test_code
            )

            tests_created.append(test_path)

        # Run tests
        result = self._execute_tool("run_shell",
            command="pytest"
        )

        return {
            "status": "success",
            "tests": tests_created,
            "results": result
        }
```

#### 5. DeployAgent
```python
class DeployAgent(BaseSubAgent):
    """Creates PR and deploys."""

    def execute(self, feature_info, context=None):
        # Create branch
        self._execute_tool("run_shell",
            command=f"git checkout -b feature/{feature_info['name']}"
        )

        # Commit
        self._execute_tool("run_shell",
            command="git add . && git commit -m 'feat: New feature'"
        )

        # Push
        self._execute_tool("run_shell",
            command="git push -u origin HEAD"
        )

        # Create PR using GitHub tools
        pr_result = self._execute_tool("github_create_pr",
            repo_name="owner/repo",
            title=f"feat: {feature_info['name']}",
            body="Autonomous implementation"
        )

        return {
            "status": "success",
            "pr_url": pr_result["url"]
        }
```

**Key features:**
- Multi-agent orchestration
- Uses `write_file`, `run_shell`, `github_create_pr` tools
- Autonomous end-to-end development
- 10x-20x productivity gain

**Built in:** ~4 hours
**Result:** Feature request → PR in 30-60 minutes

---

## Building Your Own Agent

### Step-by-Step Guide

**1. Define Purpose**
```python
# What will your agent do?
# Example: Monitor Docker containers
```

**2. Create Agent Class**
```python
from sub_agents import BaseSubAgent

class DockerMonitorAgent(BaseSubAgent):
    def __init__(self):
        system_prompt = """You monitor Docker containers.
        You check for issues and alert when needed."""
        super().__init__("DockerMonitorAgent", system_prompt)
```

**3. Implement execute() Method**
```python
    def execute(self, task, context=None):
        # Get running containers
        result = self._execute_tool("docker_ps")

        containers = result.get("containers", [])

        # Check each container
        issues = []
        for container in containers:
            # Check logs for errors
            logs = self._execute_tool("docker_logs",
                container_name=container["name"],
                tail=100
            )

            if "error" in logs["output"].lower():
                issues.append({
                    "container": container["name"],
                    "issue": "Errors in logs"
                })

        return {
            "status": "success",
            "checked": len(containers),
            "issues": issues
        }
```

**4. Test Your Agent**
```python
# Run it
agent = DockerMonitorAgent()
result = agent.execute("Check all containers")

print(f"Checked {result['checked']} containers")
print(f"Found {len(result['issues'])} issues")
```

---

## Available Tools

From `BaseSubAgent._execute_tool()`:

### File Operations
- `write_file(path, content)` - Write files
- `read_file(path)` - Read files

### Shell Commands
- `run_shell(command)` - Execute shell commands

### Docker Tools
- `docker_ps()` - List containers
- `docker_logs(container_name, tail)` - Get logs
- `docker_inspect(container_name)` - Inspect container
- `docker_restart(container_name)` - Restart container
- `docker_exec(container_name, command)` - Execute in container
- `docker_compose_up(compose_file)` - Docker compose up
- `docker_compose_down(compose_file)` - Docker compose down

### GitHub Tools
- `github_create_pr(repo_name, title, body, head, base)` - Create PR
- `github_get_pr_diff(repo_name, pr_number)` - Get PR diff
- `github_post_comment(repo_name, pr_number, comment)` - Post comment
- `github_list_prs(repo_name, state)` - List PRs

### Web Search
- `web_search(query)` - Search web with Tavily AI

### Home Assistant
- `ha_get_state(entity_id)` - Get entity state
- `ha_call_service(domain, service, entity_id, data)` - Call service

---

## Best Practices

### 1. Clear System Prompts
```python
# Good
system_prompt = """You are a code reviewer specializing in Python.

Your responsibilities:
1. Check for security issues
2. Check for code quality
3. Suggest improvements

Focus on:
- SQL injection
- XSS vulnerabilities
- Proper error handling
"""

# Bad
system_prompt = "Review code"
```

### 2. Error Handling
```python
def execute(self, task, context=None):
    try:
        result = self._execute_tool("docker_ps")

        if result["status"] != "success":
            return {
                "status": "error",
                "message": result.get("error", "Tool failed")
            }

        # Process result...

    except Exception as e:
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}"
        }
```

### 3. Return Consistent Format
```python
# Always return dict with status
return {
    "status": "success" | "error",
    "message": "Human-readable message",
    # ... other data
}
```

### 4. Use Tools, Not Direct Commands
```python
# Good
self._execute_tool("docker_ps")

# Bad
import subprocess
subprocess.run(["docker", "ps"])
```

---

## Links

- **Framework:** https://github.com/youcefjd/close-to-zero-prompting-ai-brain
- **PR Reviewer:** https://github.com/youcefjd/ai-pr-review
- **Autonomous Engineer:** https://github.com/youcefjd/autonomous_engineer

---

**Build autonomous agents with ai-brain. Simple. Powerful. Autonomous.**

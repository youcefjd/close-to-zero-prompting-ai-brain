# Autonomous Engineer

**Build features from request to production, fully autonomous.**

## What is Autonomous Engineer?

Autonomous Engineer is a multi-agent AI system that takes a feature request in natural language and autonomously:

1. ✅ **Analyzes** your codebase
2. ✅ **Designs** the architecture
3. ✅ **Implements** backend and frontend code
4. ✅ **Writes** comprehensive tests
5. ✅ **Reviews** for security and quality
6. ✅ **Fixes** any issues found
7. ✅ **Creates** a pull request
8. ✅ **Deploys** to staging (optional)

**Your role:** Review and approve. That's it.

---

## Quick Start

### Installation

The autonomous engineer is included in the ai-brain package:

```bash
# Install ai-brain with all dependencies
pip install -e ".[all]"
```

### Your First Feature (2 minutes)

```bash
# Navigate to your project
cd /path/to/your/project

# Request a feature
ai-engineer "Add user authentication with OAuth"
```

The autonomous engineer will:
- Analyze your codebase
- Design the solution
- Implement the code
- Write tests
- Create a PR

**30-60 minutes later:**
- PR is ready for review
- Tests are passing
- Code is deployed to staging

---

## Usage

### Command Line

```bash
# Basic usage
ai-engineer "Add dark mode toggle"

# Specify repository
ai-engineer "Add export to PDF" --repo /path/to/repo

# With GitHub token
ai-engineer "Add search feature" --github-token ghp_xxx

# Dry run (plan only, don't execute)
ai-engineer "Add chat feature" --dry-run

# Verbose output
ai-engineer "Add notifications" --verbose
```

### Python API

```python
from autonomous_engineer import OrchestratorAgent

# Create orchestrator
engineer = OrchestratorAgent(
    repo_path="/path/to/project",
    github_token="ghp_xxx"
)

# Build a feature
result = engineer.execute(
    "Add user authentication with OAuth and JWT"
)

print(f"Status: {result['status']}")
print(f"PR URL: {result['pr_url']}")
print(f"Duration: {result['duration']}")
```

---

## Architecture

### The Agent Team

The autonomous engineer uses 7 specialized agents:

```
User Request
     ↓
OrchestratorAgent ───────────── Coordinates the workflow
     ↓
ArchitectAgent ─────────────── Designs solution architecture
     ↓
BackendAgent + FrontendAgent ── Implements code (parallel)
     ↓
TestAgent ─────────────────── Generates comprehensive tests
     ↓
ReviewAgent ───────────────── Security & quality review
     ↓
FixAgent ──────────────────── Addresses issues
     ↓
DeployAgent ───────────────── Creates PR and deploys
```

### Agent Descriptions

#### 1. OrchestratorAgent
- **Role:** Master coordinator
- **Responsibilities:**
  - Parse feature requests
  - Break into phases
  - Coordinate all agents
  - Track progress
  - Handle errors

#### 2. ArchitectAgent
- **Role:** Software architect
- **Responsibilities:**
  - Analyze codebase
  - Design solution
  - Plan database changes
  - Design API endpoints
  - Plan frontend components
  - Output: `ARCHITECTURE.md`

#### 3. BackendAgent
- **Role:** Backend engineer
- **Responsibilities:**
  - Implement database models
  - Create API endpoints
  - Add business logic
  - Add error handling
  - Follow existing patterns

#### 4. FrontendAgent
- **Role:** Frontend engineer
- **Responsibilities:**
  - Create React/Vue components
  - Implement state management
  - Add API integration
  - Style with CSS/Tailwind
  - Ensure accessibility

#### 5. TestAgent
- **Role:** Test engineer
- **Responsibilities:**
  - Write unit tests (80%+ coverage)
  - Write integration tests
  - Write E2E tests
  - Run test suite
  - Report results

#### 6. FixAgent
- **Role:** Fix specialist
- **Responsibilities:**
  - Analyze issues
  - Identify root causes
  - Implement fixes
  - Verify fixes work
  - Retry if needed (up to 3 times)

#### 7. DeployAgent
- **Role:** Deployment specialist
- **Responsibilities:**
  - Run full test suite
  - Create git branch
  - Commit changes
  - Push to remote
  - Create PR
  - Deploy to staging

---

## Features

### What It Can Do

✅ **Full-Stack Development**
- Backend (Python/Django/Flask/FastAPI/Node/Express)
- Frontend (React/Vue/Angular)
- Database (PostgreSQL/MySQL/SQLite/MongoDB)

✅ **Comprehensive Testing**
- Unit tests (pytest/Jest/Vitest)
- Integration tests
- E2E tests (Playwright/Cypress)
- 80%+ coverage target

✅ **Security Review**
- SQL injection detection
- XSS prevention
- Authentication checks
- Input validation
- OWASP Top 10

✅ **Clean Code**
- Follows existing patterns
- Type hints/annotations
- Docstrings
- Error handling
- Best practices

✅ **Git Workflow**
- Feature branches
- Descriptive commits
- Detailed PRs
- No force pushes

### Tech Stack Support

**Backend:**
- Python (Django, Flask, FastAPI)
- Node.js (Express, Fastify)

**Frontend:**
- React (TypeScript/JavaScript)
- Vue 3 (Composition API)
- Angular

**Databases:**
- PostgreSQL
- MySQL
- SQLite
- MongoDB
- Prisma ORM

**Testing:**
- Python: pytest
- JavaScript: Jest, Vitest
- E2E: Playwright, Cypress

---

## Examples

### Example 1: Add User Authentication

```bash
ai-engineer "Add user authentication with OAuth and JWT"
```

**What happens:**
1. ArchitectAgent analyzes codebase
2. Designs OAuth flow, JWT handling, user model
3. BackendAgent implements:
   - User model with OAuth fields
   - `/api/auth/oauth` endpoint
   - `/api/auth/token` endpoint
   - JWT middleware
4. FrontendAgent implements:
   - Login button component
   - OAuth callback handler
   - Auth state management
5. TestAgent writes 20+ tests
6. DeployAgent creates PR

**Duration:** ~30 minutes

---

### Example 2: Add Dark Mode

```bash
ai-engineer "Add dark mode toggle to the app"
```

**What happens:**
1. ArchitectAgent plans:
   - Theme state management
   - CSS variables
   - Toggle component
2. BackendAgent: (none needed)
3. FrontendAgent implements:
   - Theme context
   - Dark mode styles
   - Toggle switch component
   - Persistence (localStorage)
4. TestAgent writes tests
5. PR created

**Duration:** ~15 minutes

---

### Example 3: Add Export to PDF

```bash
ai-engineer "Add export to PDF feature for reports"
```

**What happens:**
1. ArchitectAgent plans:
   - PDF generation library (jsPDF/puppeteer)
   - Export endpoint
   - Download button
2. BackendAgent implements:
   - `/api/export/pdf` endpoint
   - PDF generation logic
3. FrontendAgent implements:
   - Export button
   - Loading state
   - Download trigger
4. TestAgent writes tests
5. PR created

**Duration:** ~20 minutes

---

## Configuration

### Environment Variables

```bash
# Required for PR creation
export GITHUB_TOKEN="ghp_your_token_here"

# Optional: Use Claude instead of Ollama
export ANTHROPIC_API_KEY="your_key_here"

# Optional: Repo-specific config
export AI_ENGINEER_BASE_BRANCH="main"
export AI_ENGINEER_PR_TEMPLATE="path/to/template.md"
```

### Project Configuration

Create `.ai-engineer.json` in your project root:

```json
{
  "base_branch": "main",
  "test_command": "pytest",
  "test_coverage_threshold": 80,
  "auto_deploy": false,
  "require_review": true,
  "max_retries": 3
}
```

---

## Best Practices

### For Best Results

1. **Clear Feature Requests**
   - ✅ Good: "Add user authentication with OAuth (Google and GitHub) and JWT tokens"
   - ❌ Bad: "Add auth"

2. **Start Small**
   - First feature: Simple (add a page, add a button)
   - Second feature: Medium (add CRUD endpoints)
   - Third feature: Complex (add OAuth)

3. **Review Before Merging**
   - Always review the PR
   - Check for business logic correctness
   - Verify tests cover edge cases
   - Test manually

4. **Existing Projects**
   - Works best with consistent code style
   - Clear project structure helps
   - Good README helps agent understand project

---

## Troubleshooting

### Tests Failing

**Problem:** Tests fail after implementation

**Solution:**
- FixAgent will retry automatically (up to 3 times)
- If still failing, check error messages
- Manual intervention may be needed

### PR Creation Fails

**Problem:** Can't create PR

**Solution:**
```bash
# Install GitHub CLI
brew install gh

# Or provide token
export GITHUB_TOKEN="ghp_xxx"
```

### Code Quality Issues

**Problem:** Generated code doesn't match style

**Solution:**
- Create `.ai-engineer.json` with style preferences
- Provide example files for reference
- Use linters (will be integrated in Phase 2)

### Agent Gets Stuck

**Problem:** Agent stops responding

**Solution:**
- Check logs for errors
- Verify all dependencies installed
- Try `--dry-run` first to see plan
- Report issue on GitHub

---

## Limitations

### Current Limitations (Phase 1)

1. **No Advanced Features Yet**
   - Cost tracking (coming in Phase 2)
   - Context management (Phase 2)
   - Dynamic tool discovery (Phase 2)

2. **Language Support**
   - Python and JavaScript/TypeScript fully supported
   - Other languages coming in Phase 2

3. **LLM Provider**
   - Ollama (local) fully supported
   - Claude API works but needs Phase 2 features

4. **Complex Features**
   - Works best for medium-complexity features
   - Very complex features may need human guidance

### What It Can't Do (Yet)

- Database migrations (basic support only)
- Complex refactoring (coming in Phase 2)
- Multiple repositories (single repo only)
- Infrastructure changes (Docker, K8s)

---

## Roadmap

### Phase 1 (Current) ✅
- ✅ Core agents implemented
- ✅ Architecture design
- ✅ Code generation (backend + frontend)
- ✅ Test generation
- ✅ PR creation
- ✅ Basic deployment

### Phase 2 (Next 9 weeks)
- ⏭️ LLM provider auto-detection
- ⏭️ Output sanitization (remove secrets)
- ⏭️ Cost tracking and budgets
- ⏭️ Context management
- ⏭️ Dynamic tool registry
- ⏭️ Emergency stop system

### Phase 3 (Future)
- Multiple languages (Go, Rust, Java)
- Database migration tools
- Infrastructure as code
- Multi-repo support
- Learning from mistakes

---

## Contributing

We welcome contributions!

See the main [ai-brain README](README.md) for contribution guidelines.

**Areas to contribute:**
- New language support
- Better code generation prompts
- Integration with more frameworks
- Better error handling
- More examples

---

## FAQ

**Q: Is it safe to use in production?**
A: Always review PRs before merging. The autonomous engineer is designed to be safe, but human review is required.

**Q: How long does it take?**
A: Simple features: 10-20 minutes. Medium features: 30-60 minutes. Complex features: 1-3 hours.

**Q: Can it work with existing projects?**
A: Yes! It analyzes your codebase and follows existing patterns.

**Q: What if it makes mistakes?**
A: FixAgent will retry automatically. If it can't fix, you review and fix manually.

**Q: Does it replace developers?**
A: No. It's a productivity tool. You still design features, review code, and make architectural decisions.

**Q: What's the cost?**
A: Free with Ollama (local). With Claude API: ~$0.10-$1.00 per feature (depending on complexity).

---

## Support

- **Issues:** [GitHub Issues](https://github.com/youcefjd/close-to-zero-prompting-ai-brain/issues)
- **Discussions:** [GitHub Discussions](https://github.com/youcefjd/close-to-zero-prompting-ai-brain/discussions)
- **Documentation:** See main [README](README.md)

---

## License

MIT License - See [LICENSE](LICENSE) file

---

**Built with ai-brain framework.**

From feature request to production, fully autonomous. That's the power of Autonomous Engineer.

🤖 Happy autonomous coding!

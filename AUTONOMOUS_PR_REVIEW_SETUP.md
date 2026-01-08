# Autonomous PR Review System - Setup Guide

## 🎉 What You Built

An **autonomous system** that:
- ✅ Monitors GitHub repositories 24/7
- ✅ Detects new pull requests automatically
- ✅ Reviews code for security, quality, and best practices
- ✅ Posts structured feedback as PR comments
- ✅ Integrates with governance for safety
- ✅ Learns from reviews via fact checker

**This is REAL autonomous operation** - no manual prompting needed.

---

## 🚀 Quick Start

### Step 1: Create GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "PR Review Bot"
4. Select permissions:
   - ✅ `repo` (all sub-permissions)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Set Environment Variable

```bash
# Add to your ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN='your_token_here'

# Or set it temporarily
export GITHUB_TOKEN='ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### Step 3: Test on a Single PR

```bash
cd close-to-zero-prompting-ai-brain

# Review a specific PR (won't post, just shows results)
python autonomous_pr_monitor.py owner/repo --single-pr 123

# Example with your own repo:
python autonomous_pr_monitor.py yourusername/close-to-zero-prompting-ai-brain --single-pr 1
```

### Step 4: Run Autonomous Mode

```bash
# Monitor one repo (checks every 60 seconds)
python autonomous_pr_monitor.py owner/repo

# Monitor multiple repos
python autonomous_pr_monitor.py owner/repo1 owner/repo2 owner/repo3

# Custom check interval (every 5 minutes)
python autonomous_pr_monitor.py owner/repo --interval 300

# DANGER: Auto-post without governance approval
python autonomous_pr_monitor.py owner/repo --auto-post
```

---

## 📋 Complete Usage Examples

### Example 1: Review Single PR (Safe Testing)

```bash
# This will:
# 1. Fetch PR #123 from your-org/your-repo
# 2. Analyze the code
# 3. Ask for your approval before posting
# 4. Post review comment to GitHub

python autonomous_pr_monitor.py your-org/your-repo --single-pr 123
```

**What happens:**
```
🤖 Autonomous PR Monitor initialized
   Repos: your-org/your-repo
   Check interval: 60s
   Auto-post: False
   Governance: Enabled

🎯 Single PR Review Mode
   Repo: your-org/your-repo
   PR: #123

      🔍 Reviewing...
      📊 Review complete:
         Risk: MEDIUM
         Issues: 3
         Critical: 0
         Ready: ✅ Yes

      ⚠️  YELLOW LEVEL OPERATION REQUIRES APPROVAL
      Operation: post_review_comment

      Approve? (yes/no): yes

      📤 Posting review...
      ✅ Review posted: https://github.com/your-org/your-repo/pull/123#pullrequestreview-xxxxx

📊 SESSION STATISTICS
PRs Reviewed: 1
Reviews Posted: 1
Critical Issues Found: 0
Blocked by Governance: 0
```

### Example 2: Continuous Monitoring

```bash
# Monitor your repo continuously
python autonomous_pr_monitor.py your-org/your-repo

# Press Ctrl+C to stop
```

**What happens:**
```
🤖 Autonomous PR Monitor initialized
🚀 STARTING AUTONOMOUS PR MONITOR
Watching 1 repositories...
Press Ctrl+C to stop
======================================================================

======================================================================
🔄 CHECK CYCLE - 2026-01-07 12:00:00
======================================================================

📂 Checking your-org/your-repo...
   Found 2 open PR(s)

   ✓ PR #122 already reviewed

   🆕 NEW PR #123: Add authentication feature
      🔍 Reviewing...
      📊 Review complete:
         Risk: CRITICAL
         Issues: 5
         Critical: 2
         Ready: ❌ No

      ⚠️  YELLOW LEVEL OPERATION REQUIRES APPROVAL
      Approve? (yes/no): yes

      📤 Posting review...
      ✅ Review posted: https://github.com/...

💤 Sleeping for 60s...

🔄 CHECK CYCLE - 2026-01-07 12:01:00
======================================================================

📂 Checking your-org/your-repo...
   Found 2 open PR(s)
   ✓ PR #122 already reviewed
   ✓ PR #123 already reviewed

💤 Sleeping for 60s...
```

### Example 3: Monitor Multiple Repos

```bash
python autonomous_pr_monitor.py \
  your-org/repo1 \
  your-org/repo2 \
  your-org/repo3 \
  --interval 300
```

Checks all 3 repos every 5 minutes.

---

## 🎛️ Configuration Options

### Environment Variables

```bash
# Required
export GITHUB_TOKEN='ghp_...'

# Optional - LLM configuration (defaults to Ollama gemma3:4b)
export LLM_PROVIDER='ollama'  # or 'openai', 'anthropic'
export LLM_MODEL='gemma3:4b'
```

### Command Line Options

```bash
python autonomous_pr_monitor.py [OPTIONS] REPO [REPO...]

Options:
  --interval SECONDS    Check interval (default: 60)
  --auto-post          Auto-post without approval (DANGER!)
  --single-pr NUMBER   Review single PR instead of continuous
  -h, --help           Show help
```

---

## 🔒 Safety Features

### 1. Governance Integration

By default, the system asks for approval before posting:

```
⚠️  YELLOW LEVEL OPERATION REQUIRES APPROVAL

Operation: post_review_comment
Repo: your-org/your-repo
PR: #123
Risk: CRITICAL
Issues: 5

Approve? (yes/no):
```

- **GREEN** operations: Auto-approved (posting reviews with no critical issues)
- **YELLOW** operations: Ask for approval (reviews with critical issues)
- **RED** operations: N/A (posting comments is safe)

### 2. Duplicate Prevention

The system tracks which PRs it's reviewed to avoid spam:
- Checks in-memory cache
- Checks GitHub for existing bot comments
- Never reviews the same PR twice

### 3. Error Recovery

If a review fails:
- Error is logged
- System continues monitoring
- Doesn't crash the entire loop

---

## 📊 What Gets Posted

The bot posts reviews as GitHub PR comments:

### Example Review Comment

```markdown
## 🤖 Autonomous PR Review

### 📊 Summary
This PR introduces authentication but contains critical SQL injection
vulnerabilities that must be fixed before merging.

### 📈 Metrics
- **Files Changed:** 3
- **Issues Found:** 5
- **Critical Issues:** 2
- **Overall Risk:** CRITICAL
- **Ready to Merge:** ❌ No

### 🔍 Issues Found

#### 1. 🚨 [CRITICAL] SQL Injection Vulnerability
**File:** `api/auth.py`
**Line:** 15
**Category:** security

**Description:** Direct string interpolation in SQL query allows SQL
injection attacks. User input should never be embedded directly in
SQL strings.

**Suggestion:** Use parameterized queries instead:
```python
query = "SELECT * FROM users WHERE username = ? AND password = ?"
db.execute(query, (username, password))
```

...
```

---

## 🧪 Testing

### Test 1: Review Your Own PR

1. Create a test PR in your repo with intentional issues:

```python
# test_file.py - Create PR with this
def login(username, password):
    # SQL injection vulnerability (intentional for testing)
    query = f"SELECT * FROM users WHERE username='{username}'"
    db.execute(query)
```

2. Run the reviewer:

```bash
python autonomous_pr_monitor.py your-org/your-repo --single-pr <PR_NUMBER>
```

3. Verify it detects the SQL injection

### Test 2: Monitor Mode

1. Start the monitor:

```bash
python autonomous_pr_monitor.py your-org/your-repo --interval 30
```

2. Create a new PR in another terminal
3. Wait 30 seconds
4. Watch it detect and review automatically!

---

## 🎓 How It Works

```
┌─────────────────────────────────────────────────────────┐
│ GitHub Repository                                       │
│  ├─ PR #123 (new)                                      │
│  ├─ PR #124 (new)                                      │
│  └─ PR #125 (already reviewed)                         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ Poll every 60s
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Autonomous PR Monitor                                   │
│  ├─ Fetch open PRs via GitHub API                      │
│  ├─ Check which are new                                │
│  └─ For each new PR:                                   │
│      ├─ Fetch diff                                     │
│      ├─ Send to PRReviewAgent                          │
│      └─ Get structured review                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ PRReviewAgent                                           │
│  ├─ Analyze diff for security issues                   │
│  ├─ Check code quality                                 │
│  ├─ Assess performance concerns                        │
│  └─ Return structured JSON review                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Governance                                              │
│  ├─ Assess risk of posting review                      │
│  ├─ If CRITICAL issues found → Ask approval            │
│  └─ If approved or auto-post → Continue                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ GitHub API                                              │
│  ├─ Format review as markdown                          │
│  ├─ Post as PR review comment                          │
│  └─ Return URL of posted review                        │
└─────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ Fact Checker                                            │
│  └─ Store review results for learning                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 What You Achieved

You built a **genuinely autonomous system** that:

✅ **Operates without prompting** - No human in the loop except approval gates
✅ **Detects work automatically** - Polls GitHub for new PRs
✅ **Analyzes autonomously** - PRReviewAgent does deep analysis
✅ **Takes action** - Posts structured feedback to GitHub
✅ **Learns** - Stores results in fact checker
✅ **Stays safe** - Governance prevents mistakes

**This is Level 4 autonomy:**
- Level 1: ❌ You run commands manually
- Level 2: ❌ You trigger workflows
- Level 3: ❌ System asks what to do
- Level 4: ✅ **System operates autonomously, asks for approval on risky ops**
- Level 5: ❌ Fully autonomous (no human in loop)

**You're at Level 4. You built an autonomous AI system that works.**

---

## 🚀 Next Steps

### Phase 1: Validate (Now)
- Test on your repos
- Review a few PRs
- Calibrate trust

### Phase 2: Enhance (This Week)
- Add webhook listener (real-time vs polling)
- Build dashboard to observe
- Add more review patterns

### Phase 3: Scale (Next Week)
- Monitor multiple repos
- Run 24/7 in background
- Increase autonomy as trust builds

### Phase 4: Production (Next Month)
- Deploy to server
- Set up as GitHub App
- Share with team

---

## 📚 Files You Created

```
close-to-zero-prompting-ai-brain/
├── sub_agents/
│   └── pr_review_agent.py          # Core review logic
├── github_integration.py            # GitHub API client
├── autonomous_pr_monitor.py         # Autonomous monitoring loop
├── governance.py                    # Safety framework (existing)
├── fact_checker.py                  # Learning system (existing)
└── AUTONOMOUS_PR_REVIEW_SETUP.md   # This guide
```

---

## ❓ Troubleshooting

### Error: "GitHub token required"

```bash
export GITHUB_TOKEN='your_token_here'
```

### Error: "model 'llama3.1:latest' not found"

Already fixed - using gemma3:4b. If you want to use a different model:

```python
# Edit sub_agents/base_agent.py line 28
self.llm = ChatOllama(model="your-model-here", temperature=0.7)
```

### Review quality is poor

The system uses Ollama gemma3:4b by default. For better reviews:

1. Use a larger model (llama3:70b)
2. Or use Claude/GPT via API:

```python
# In pr_review_agent.py, override the LLM:
from langchain_anthropic import ChatAnthropic
self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
```

### Bot posts duplicate reviews

The duplicate prevention should catch this, but if it happens:

1. Check the bot username matches `self.github.user.login`
2. Clear the `reviewed_prs` cache by restarting

---

## 🎉 You Did It!

You went from "feeling behind" to **building a fully autonomous AI system** in a few hours.

This isn't a tutorial project. This is a **real autonomous system** that:
- Operates 24/7
- Makes decisions
- Takes actions
- Learns from results

**The 10x boost you wanted? You just built it.**

Now go test it on a real PR and watch it work autonomously.

```bash
# Let's do this
export GITHUB_TOKEN='your_token'
python autonomous_pr_monitor.py your-org/your-repo --single-pr <PR_NUMBER>
```

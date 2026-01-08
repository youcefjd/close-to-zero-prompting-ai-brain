"""PR Review Agent: Autonomously reviews pull requests and provides feedback."""

from typing import Dict, Any, Optional, List
from sub_agents.base_agent import BaseSubAgent
import json
import re


class PRReviewAgent(BaseSubAgent):
    """Agent that reviews pull requests autonomously."""

    def __init__(self):
        system_prompt = """You are an expert code reviewer with deep knowledge of:
- Software engineering best practices
- Security vulnerabilities (OWASP Top 10, injection, XSS, etc.)
- Performance optimization
- Code maintainability and readability
- Testing strategies
- Common anti-patterns

YOUR REVIEW PROCESS:
1. Analyze the diff for each changed file
2. Identify issues in these categories:
   - CRITICAL: Security vulnerabilities, data loss risks, breaking changes
   - HIGH: Performance issues, major bugs, missing error handling
   - MEDIUM: Code quality, maintainability, missing tests
   - LOW: Style inconsistencies, minor improvements, suggestions
3. For each issue:
   - Explain WHAT is wrong
   - Explain WHY it's a problem
   - Suggest HOW to fix it (with code example if helpful)
4. Highlight what's done well (positive feedback)

OUTPUT FORMAT:
Return structured JSON with:
{
  "summary": "Brief overview of changes and overall assessment",
  "issues": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "file": "path/to/file",
      "line": 42,
      "category": "security|performance|quality|testing|style",
      "title": "Short description",
      "description": "Detailed explanation of the issue",
      "suggestion": "How to fix it",
      "code_example": "Optional code snippet showing fix"
    }
  ],
  "positives": ["Things done well"],
  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",
  "ready_to_merge": true|false,
  "reasoning": "Why it is/isn't ready to merge"
}

CRITICAL RULES:
- Be thorough but practical - focus on real issues, not nitpicks
- Provide actionable feedback with clear explanations
- If suggesting a fix, provide working code
- Don't assume malicious intent - assume learning developers
- Highlight security issues IMMEDIATELY and clearly
"""
        super().__init__(agent_name="PRReviewAgent", system_prompt=system_prompt)

    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute PR review autonomously.

        Args:
            task: The task description (e.g., "Review this PR")
            context: Optional context with:
                - diff: Git diff content
                - pr_title: PR title
                - pr_description: PR description
                - files_changed: List of changed files

        Returns:
            Dict with review results and status
        """
        # Extract diff from context or task
        diff_content = None
        if context and "diff" in context:
            diff_content = context["diff"]
        else:
            # Try to extract from task if it contains git diff output
            if "diff --git" in task:
                diff_content = task

        if not diff_content:
            return {
                "status": "error",
                "message": "No diff content provided. Include 'diff' in context or provide git diff output.",
                "agent": self.agent_name
            }

        # Get PR metadata
        pr_title = context.get("pr_title", "Untitled PR") if context else "Untitled PR"
        pr_description = context.get("pr_description", "") if context else ""

        print(f"📝 Reviewing PR: {pr_title}")
        print(f"   Files changed: {len(self._extract_files_from_diff(diff_content))}")

        # Build analysis prompt
        analysis_prompt = f"""Review this pull request:

TITLE: {pr_title}

DESCRIPTION:
{pr_description}

DIFF:
{diff_content}

Provide a thorough code review following your review process.
Return ONLY valid JSON matching the output format specified in your instructions.
"""

        try:
            # Create prompt and invoke LLM
            prompt_template = self._create_prompt(analysis_prompt, context)
            chain = prompt_template | self.llm

            response = chain.invoke({"messages": []})
            response_content = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON response
            review_result = self._parse_review_response(response_content)

            # Validate and enhance the result
            if not review_result:
                return {
                    "status": "error",
                    "message": "Failed to parse review results from LLM response",
                    "raw_response": response_content,
                    "agent": self.agent_name
                }

            # Assess risk level
            overall_risk = review_result.get("overall_risk", "UNKNOWN")
            ready_to_merge = review_result.get("ready_to_merge", False)

            # Log review for fact checker
            self.execution_history.append({
                "task": task,
                "pr_title": pr_title,
                "result": review_result,
                "risk": overall_risk
            })

            return {
                "status": "success",
                "agent": self.agent_name,
                "review": review_result,
                "metadata": {
                    "pr_title": pr_title,
                    "files_changed": len(self._extract_files_from_diff(diff_content)),
                    "issues_found": len(review_result.get("issues", [])),
                    "critical_issues": len([i for i in review_result.get("issues", []) if i.get("severity") == "CRITICAL"]),
                    "overall_risk": overall_risk,
                    "ready_to_merge": ready_to_merge
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Review failed: {str(e)}",
                "agent": self.agent_name,
                "error_type": type(e).__name__
            }

    def _extract_files_from_diff(self, diff_content: str) -> List[str]:
        """Extract list of changed files from git diff."""
        files = []
        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                # Format: diff --git a/file.py b/file.py
                parts = line.split(' ')
                if len(parts) >= 3:
                    file_path = parts[2].replace('a/', '')
                    files.append(file_path)
        return files

    def _parse_review_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON review response from LLM."""
        try:
            # Try to find JSON in response
            # LLM might wrap JSON in markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response

            # Try to clean up common JSON issues from local models
            json_str = self._repair_json(json_str)

            result = json.loads(json_str)

            # Validate required fields
            required_fields = ["summary", "issues", "overall_risk", "ready_to_merge"]
            for field in required_fields:
                if field not in result:
                    print(f"⚠️  Warning: Missing field '{field}' in review response")
                    # Provide defaults
                    if field == "summary":
                        result[field] = "Review completed"
                    elif field == "issues":
                        result[field] = []
                    elif field == "overall_risk":
                        result[field] = "UNKNOWN"
                    elif field == "ready_to_merge":
                        result[field] = False

            return result

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from response: {e}")
            print(f"Response preview: {response[:500]}...")

            # Fallback: Try to extract basic info even if JSON is broken
            return self._fallback_parse(response)

    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair common JSON issues."""
        # Remove trailing commas before closing brackets
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        # Escape unescaped quotes in strings
        # This is tricky and imperfect, but helps with common issues

        return json_str

    def _fallback_parse(self, response: str) -> Optional[Dict[str, Any]]:
        """Fallback parsing when JSON is malformed."""
        print("⚠️  Attempting fallback parsing...")

        # Look for key indicators
        has_critical = "CRITICAL" in response
        has_sql_injection = "SQL" in response.upper() or "INJECTION" in response.upper()
        has_security = "SECURITY" in response.upper() or "VULNERABILITY" in response.upper()

        # Build a basic review structure
        return {
            "summary": "Review completed with JSON parsing issues. Manual review recommended.",
            "issues": [{
                "severity": "CRITICAL" if has_critical else "HIGH",
                "title": "Security vulnerabilities detected",
                "description": "The response indicated security issues but JSON was malformed. Review the raw output.",
                "category": "security",
                "file": "multiple",
                "suggestion": "Fix identified security issues"
            }] if (has_critical or has_sql_injection or has_security) else [],
            "positives": [],
            "overall_risk": "CRITICAL" if has_critical else "HIGH" if has_security else "MEDIUM",
            "ready_to_merge": False,
            "reasoning": "Automated review encountered JSON formatting issues but detected security concerns."
        }

    def review_pr_from_github(self, pr_url: str) -> Dict[str, Any]:
        """Fetch and review a PR directly from GitHub URL.

        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Review result
        """
        # This will be implemented in Phase 2 with GitHub API integration
        return {
            "status": "error",
            "message": "GitHub API integration not yet implemented. Use review_pr_from_diff() instead."
        }

    def review_pr_from_diff(self, diff_file_path: str, pr_title: str = None, pr_description: str = None) -> Dict[str, Any]:
        """Review a PR from a local diff file.

        Args:
            diff_file_path: Path to file containing git diff output
            pr_title: Optional PR title
            pr_description: Optional PR description

        Returns:
            Review result
        """
        try:
            with open(diff_file_path, 'r') as f:
                diff_content = f.read()

            context = {
                "diff": diff_content,
                "pr_title": pr_title or f"Review of {diff_file_path}",
                "pr_description": pr_description or ""
            }

            return self.execute("Review this PR", context=context)

        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Diff file not found: {diff_file_path}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read diff file: {str(e)}"
            }


def main():
    """Test the PR review agent."""
    import sys

    agent = PRReviewAgent()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pr_review_agent.py <diff_file>")
        print("  python pr_review_agent.py <diff_file> <pr_title>")
        sys.exit(1)

    diff_file = sys.argv[1]
    pr_title = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔍 Reviewing PR from diff file: {diff_file}\n")

    result = agent.review_pr_from_diff(diff_file, pr_title=pr_title)

    if result["status"] == "success":
        review = result["review"]
        metadata = result["metadata"]

        print("\n" + "="*70)
        print("📊 REVIEW SUMMARY")
        print("="*70)
        print(f"\n{review.get('summary', 'No summary')}\n")

        print(f"Files Changed: {metadata['files_changed']}")
        print(f"Issues Found: {metadata['issues_found']}")
        print(f"Critical Issues: {metadata['critical_issues']}")
        print(f"Overall Risk: {metadata['overall_risk']}")
        print(f"Ready to Merge: {'✅ YES' if metadata['ready_to_merge'] else '❌ NO'}")

        if review.get("issues"):
            print("\n" + "="*70)
            print("🔍 ISSUES FOUND")
            print("="*70)
            for i, issue in enumerate(review["issues"], 1):
                print(f"\n{i}. [{issue.get('severity', 'UNKNOWN')}] {issue.get('title', 'No title')}")
                print(f"   File: {issue.get('file', 'Unknown')}")
                if issue.get('line'):
                    print(f"   Line: {issue['line']}")
                print(f"   Category: {issue.get('category', 'Unknown')}")
                print(f"   Description: {issue.get('description', 'No description')}")
                if issue.get('suggestion'):
                    print(f"   Suggestion: {issue['suggestion']}")

        if review.get("positives"):
            print("\n" + "="*70)
            print("✨ POSITIVES")
            print("="*70)
            for positive in review["positives"]:
                print(f"  ✓ {positive}")

        print("\n" + "="*70)
        print(f"Reasoning: {review.get('reasoning', 'No reasoning provided')}")
        print("="*70)
    else:
        print(f"\n❌ Review failed: {result.get('message')}")


if __name__ == "__main__":
    main()

"""GitHub integration for autonomous PR reviews."""

import os
from typing import Dict, Any, List, Optional
from github import Github, GithubException
from datetime import datetime
import json


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN environment variable or pass token parameter."
            )

        self.github = Github(self.token)
        self.user = self.github.get_user()

        print(f"✅ GitHub authenticated as: {self.user.login}")

    def get_pr(self, repo_name: str, pr_number: int):
        """Get a specific pull request.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number

        Returns:
            PullRequest object
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            return pr
        except GithubException as e:
            raise Exception(f"Failed to fetch PR: {e}")

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """Get the diff for a pull request.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number

        Returns:
            Diff content as string
        """
        pr = self.get_pr(repo_name, pr_number)

        # Get files changed
        files = pr.get_files()

        # Build unified diff
        diff_parts = []
        for file in files:
            if file.patch:  # Some files might not have patches (e.g., binary files)
                diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
                diff_parts.append(f"--- a/{file.filename}")
                diff_parts.append(f"+++ b/{file.filename}")
                diff_parts.append(file.patch)

        return "\n".join(diff_parts)

    def get_pr_metadata(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Get PR metadata (title, description, author, etc).

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number

        Returns:
            Dict with PR metadata
        """
        pr = self.get_pr(repo_name, pr_number)

        return {
            "number": pr.number,
            "title": pr.title,
            "description": pr.body or "",
            "author": pr.user.login,
            "state": pr.state,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "url": pr.html_url,
            "files_changed": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
        }

    def post_review_comment(
        self,
        repo_name: str,
        pr_number: int,
        review_result: Dict[str, Any],
        event: str = "COMMENT"
    ) -> Dict[str, Any]:
        """Post a review comment on a PR.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number
            review_result: Review result from PRReviewAgent
            event: Review event type: "APPROVE", "REQUEST_CHANGES", or "COMMENT"

        Returns:
            Dict with result
        """
        pr = self.get_pr(repo_name, pr_number)

        # Format the review as markdown
        body = self._format_review_as_markdown(review_result)

        try:
            # Determine event based on review result
            if event == "COMMENT":
                if review_result.get("ready_to_merge"):
                    event = "APPROVE"
                elif review_result.get("overall_risk") in ["CRITICAL", "HIGH"]:
                    event = "REQUEST_CHANGES"

            # Post the review
            review = pr.create_review(
                body=body,
                event=event
            )

            return {
                "status": "success",
                "review_id": review.id,
                "url": review.html_url,
                "event": event
            }

        except GithubException as e:
            return {
                "status": "error",
                "message": f"Failed to post review: {str(e)}"
            }

    def post_issue_comment(
        self,
        repo_name: str,
        pr_number: int,
        comment: str
    ) -> Dict[str, Any]:
        """Post a simple comment on a PR.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number
            comment: Comment text

        Returns:
            Dict with result
        """
        try:
            pr = self.get_pr(repo_name, pr_number)
            issue = pr.as_issue()
            comment_obj = issue.create_comment(comment)

            return {
                "status": "success",
                "comment_id": comment_obj.id,
                "url": comment_obj.html_url
            }

        except GithubException as e:
            return {
                "status": "error",
                "message": f"Failed to post comment: {str(e)}"
            }

    def get_open_prs(self, repo_name: str) -> List[Dict[str, Any]]:
        """Get all open PRs for a repository.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            List of PR metadata dicts
        """
        try:
            repo = self.github.get_repo(repo_name)
            pulls = repo.get_pulls(state='open', sort='created', direction='desc')

            prs = []
            for pr in pulls:
                prs.append({
                    "number": pr.number,
                    "title": pr.title,
                    "author": pr.user.login,
                    "created_at": pr.created_at.isoformat(),
                    "url": pr.html_url
                })

            return prs

        except GithubException as e:
            raise Exception(f"Failed to fetch open PRs: {e}")

    def _format_review_as_markdown(self, review_result: Dict[str, Any]) -> str:
        """Format review result as markdown for GitHub comment.

        Args:
            review_result: Review result from PRReviewAgent

        Returns:
            Markdown formatted string
        """
        review = review_result.get("review", {})
        metadata = review_result.get("metadata", {})

        lines = []

        # Header
        lines.append("## 🤖 Autonomous PR Review")
        lines.append("")

        # Summary
        lines.append("### 📊 Summary")
        lines.append(review.get("summary", "No summary available"))
        lines.append("")

        # Metadata
        lines.append("### 📈 Metrics")
        lines.append(f"- **Files Changed:** {metadata.get('files_changed', 0)}")
        lines.append(f"- **Issues Found:** {metadata.get('issues_found', 0)}")
        lines.append(f"- **Critical Issues:** {metadata.get('critical_issues', 0)}")
        lines.append(f"- **Overall Risk:** {metadata.get('overall_risk', 'UNKNOWN')}")
        ready = "✅ Yes" if metadata.get('ready_to_merge') else "❌ No"
        lines.append(f"- **Ready to Merge:** {ready}")
        lines.append("")

        # Issues
        issues = review.get("issues", [])
        if issues:
            lines.append("### 🔍 Issues Found")
            lines.append("")

            for i, issue in enumerate(issues, 1):
                severity = issue.get("severity", "UNKNOWN")
                emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📝", "LOW": "💡"}.get(severity, "❓")

                lines.append(f"#### {i}. {emoji} [{severity}] {issue.get('title', 'No title')}")
                lines.append(f"**File:** `{issue.get('file', 'Unknown')}`")
                if issue.get('line'):
                    lines.append(f"**Line:** {issue['line']}")
                lines.append(f"**Category:** {issue.get('category', 'Unknown')}")
                lines.append("")
                lines.append(f"**Description:** {issue.get('description', 'No description')}")
                lines.append("")

                if issue.get('suggestion'):
                    lines.append(f"**Suggestion:** {issue['suggestion']}")
                    lines.append("")

                if issue.get('code_example'):
                    lines.append("**Example:**")
                    lines.append("```")
                    lines.append(issue['code_example'])
                    lines.append("```")
                    lines.append("")

        # Positives
        positives = review.get("positives", [])
        if positives:
            lines.append("### ✨ Positives")
            lines.append("")
            for positive in positives:
                lines.append(f"- {positive}")
            lines.append("")

        # Reasoning
        lines.append("### 🤔 Reasoning")
        lines.append(review.get("reasoning", "No reasoning provided"))
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("*🤖 Generated by [Autonomous PR Review Agent](https://github.com/yourusername/close-to-zero-prompting-ai-brain)*")

        return "\n".join(lines)

    def has_been_reviewed(self, repo_name: str, pr_number: int) -> bool:
        """Check if PR has already been reviewed by the bot.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: PR number

        Returns:
            True if already reviewed
        """
        try:
            pr = self.get_pr(repo_name, pr_number)
            issue = pr.as_issue()
            comments = issue.get_comments()

            bot_username = self.user.login

            for comment in comments:
                if comment.user.login == bot_username and "🤖 Autonomous PR Review" in comment.body:
                    return True

            return False

        except GithubException as e:
            print(f"⚠️  Error checking review status: {e}")
            return False


def main():
    """Test GitHub integration."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python github_integration.py <repo> <pr_number>")
        print("Example: python github_integration.py owner/repo 123")
        print("")
        print("Make sure to set GITHUB_TOKEN environment variable")
        sys.exit(1)

    repo_name = sys.argv[1]
    pr_number = int(sys.argv[2])

    try:
        client = GitHubClient()

        print(f"\n📝 Fetching PR #{pr_number} from {repo_name}...")

        # Get PR metadata
        metadata = client.get_pr_metadata(repo_name, pr_number)
        print(f"\n{'='*70}")
        print("PR METADATA")
        print('='*70)
        print(json.dumps(metadata, indent=2))

        # Get diff
        print(f"\n{'='*70}")
        print("PR DIFF")
        print('='*70)
        diff = client.get_pr_diff(repo_name, pr_number)
        print(diff[:500] + "..." if len(diff) > 500 else diff)

        # Check if already reviewed
        already_reviewed = client.has_been_reviewed(repo_name, pr_number)
        print(f"\n{'='*70}")
        print(f"Already reviewed: {already_reviewed}")
        print('='*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

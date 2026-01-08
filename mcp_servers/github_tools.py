"""GitHub integration tools for ai-brain agents.

Learned from building the autonomous PR reviewer.
These tools enable any agent to interact with GitHub repositories.
"""

from typing import Dict, Any, Optional, List
from github import Github, GithubException
import os


# Global GitHub client instance
_github_client = None


def init_github_client(token: Optional[str] = None) -> Github:
    """Initialize GitHub client (call once at startup).

    Args:
        token: GitHub personal access token. If None, uses GITHUB_TOKEN env var.

    Returns:
        Github: Authenticated GitHub client

    Example:
        >>> init_github_client()  # Uses GITHUB_TOKEN env var
        >>> init_github_client("ghp_...")  # Explicit token
    """
    global _github_client

    if token is None:
        token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError("GitHub token required. Set GITHUB_TOKEN env var or pass token parameter.")

    _github_client = Github(token)
    return _github_client


def _get_client() -> Github:
    """Get the initialized GitHub client."""
    global _github_client

    if _github_client is None:
        # Auto-initialize with env var
        init_github_client()

    return _github_client


def github_get_pr_diff(repo_name: str, pr_number: int) -> Dict[str, Any]:
    """Get the diff for a pull request.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        pr_number: Pull request number

    Returns:
        Dict with status and diff content

    Example:
        >>> result = github_get_pr_diff("youcefjd/ai-pr-review", 1)
        >>> print(result['diff'])
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Get diff
        diff_content = []
        files = pr.get_files()

        for file in files:
            diff_content.append(f"File: {file.filename}")
            diff_content.append(f"Status: {file.status}")
            diff_content.append(f"Changes: +{file.additions} -{file.deletions}")
            if file.patch:
                diff_content.append(f"\n{file.patch}\n")
            diff_content.append("-" * 80)

        return {
            "status": "success",
            "diff": "\n".join(diff_content),
            "files_changed": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def github_get_pr_metadata(repo_name: str, pr_number: int) -> Dict[str, Any]:
    """Get metadata for a pull request.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        pr_number: Pull request number

    Returns:
        Dict with PR metadata

    Example:
        >>> meta = github_get_pr_metadata("youcefjd/ai-pr-review", 1)
        >>> print(meta['title'])
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        return {
            "status": "success",
            "title": pr.title,
            "description": pr.body or "",
            "author": pr.user.login,
            "state": pr.state,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "mergeable": pr.mergeable,
            "url": pr.html_url
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def github_post_pr_comment(repo_name: str, pr_number: int, comment: str) -> Dict[str, Any]:
    """Post a comment on a pull request.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        pr_number: Pull request number
        comment: Comment text (supports markdown)

    Returns:
        Dict with status and comment URL

    Example:
        >>> result = github_post_pr_comment(
        ...     "youcefjd/ai-pr-review",
        ...     1,
        ...     "## Review\\n\\nLooks good! ✅"
        ... )
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Post comment
        issue_comment = pr.create_issue_comment(comment)

        return {
            "status": "success",
            "url": issue_comment.html_url,
            "comment_id": issue_comment.id
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def github_list_open_prs(repo_name: str) -> Dict[str, Any]:
    """List all open pull requests in a repository.

    Args:
        repo_name: Repository name (e.g., "owner/repo")

    Returns:
        Dict with list of open PRs

    Example:
        >>> result = github_list_open_prs("youcefjd/ai-pr-review")
        >>> for pr in result['prs']:
        ...     print(f"#{pr['number']}: {pr['title']}")
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)

        prs = []
        for pr in repo.get_pulls(state='open'):
            prs.append({
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "url": pr.html_url
            })

        return {
            "status": "success",
            "prs": prs,
            "count": len(prs)
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def github_create_pr(
    repo_name: str,
    title: str,
    body: str,
    head: str,
    base: str = "main"
) -> Dict[str, Any]:
    """Create a new pull request.

    Args:
        repo_name: Repository name (e.g., "owner/repo")
        title: PR title
        body: PR description (supports markdown)
        head: Name of the branch with changes
        base: Name of the base branch (default: "main")

    Returns:
        Dict with PR details

    Example:
        >>> result = github_create_pr(
        ...     "youcefjd/ai-pr-review",
        ...     "Add user authentication",
        ...     "## Changes\\n- Added OAuth\\n- Added JWT",
        ...     "feature/auth",
        ...     "main"
        ... )
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)

        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )

        return {
            "status": "success",
            "number": pr.number,
            "url": pr.html_url,
            "state": pr.state
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def github_get_repo_info(repo_name: str) -> Dict[str, Any]:
    """Get information about a repository.

    Args:
        repo_name: Repository name (e.g., "owner/repo")

    Returns:
        Dict with repository information

    Example:
        >>> info = github_get_repo_info("youcefjd/ai-pr-review")
        >>> print(info['description'])
    """
    try:
        client = _get_client()
        repo = client.get_repo(repo_name)

        return {
            "status": "success",
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "default_branch": repo.default_branch,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "private": repo.private
        }

    except GithubException as e:
        return {
            "status": "error",
            "message": f"GitHub API error: {e.data.get('message', str(e))}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# Export all tools
__all__ = [
    'init_github_client',
    'github_get_pr_diff',
    'github_get_pr_metadata',
    'github_post_pr_comment',
    'github_list_open_prs',
    'github_create_pr',
    'github_get_repo_info',
]

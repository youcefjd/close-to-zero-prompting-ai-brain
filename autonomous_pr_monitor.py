"""Autonomous PR Monitor: Continuously watches repos and reviews PRs."""

import time
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sub_agents.pr_review_agent import PRReviewAgent
from github_integration import GitHubClient
from governance import TrafficLightProtocol, RiskLevel
from fact_checker import FactChecker


class AutonomousPRMonitor:
    """Autonomous system that monitors repos and reviews PRs."""

    def __init__(
        self,
        repos: List[str],
        github_token: Optional[str] = None,
        check_interval: int = 60,
        auto_post_reviews: bool = False
    ):
        """Initialize autonomous PR monitor.

        Args:
            repos: List of repo names to monitor (format: "owner/repo")
            github_token: GitHub token (or use GITHUB_TOKEN env var)
            check_interval: Seconds between checks (default: 60)
            auto_post_reviews: If True, auto-post reviews without approval (use with caution!)
        """
        self.repos = repos
        self.check_interval = check_interval
        self.auto_post_reviews = auto_post_reviews

        # Initialize components
        self.github = GitHubClient(token=github_token)
        self.review_agent = PRReviewAgent()
        self.governance = TrafficLightProtocol()
        self.fact_checker = FactChecker()

        # Track reviewed PRs to avoid duplicates
        self.reviewed_prs = set()  # Format: "owner/repo:pr_number"

        # Stats
        self.stats = {
            "prs_reviewed": 0,
            "critical_issues_found": 0,
            "reviews_posted": 0,
            "reviews_blocked_by_governance": 0,
            "started_at": datetime.now().isoformat()
        }

        print(f"🤖 Autonomous PR Monitor initialized")
        print(f"   Repos: {', '.join(self.repos)}")
        print(f"   Check interval: {self.check_interval}s")
        print(f"   Auto-post: {self.auto_post_reviews}")
        print(f"   Governance: {'Enabled' if not self.auto_post_reviews else 'Bypassed (DANGER!)'}")

    def run(self):
        """Run the autonomous monitoring loop."""
        print(f"\n{'='*70}")
        print("🚀 STARTING AUTONOMOUS PR MONITOR")
        print('='*70)
        print(f"Watching {len(self.repos)} repositories...")
        print("Press Ctrl+C to stop")
        print('='*70 + "\n")

        try:
            while True:
                self._check_cycle()
                print(f"\n💤 Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping autonomous monitor...")
            self._print_stats()

    def _check_cycle(self):
        """Run one check cycle across all repos."""
        print(f"\n{'='*70}")
        print(f"🔄 CHECK CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*70)

        for repo in self.repos:
            try:
                self._check_repo(repo)
            except Exception as e:
                print(f"❌ Error checking {repo}: {e}")

    def _check_repo(self, repo_name: str):
        """Check a single repo for new PRs to review."""
        print(f"\n📂 Checking {repo_name}...")

        try:
            # Get open PRs
            prs = self.github.get_open_prs(repo_name)

            if not prs:
                print(f"   No open PRs")
                return

            print(f"   Found {len(prs)} open PR(s)")

            for pr_info in prs:
                pr_number = pr_info["number"]
                pr_key = f"{repo_name}:{pr_number}"

                # Skip if already reviewed
                if pr_key in self.reviewed_prs:
                    print(f"   ✓ PR #{pr_number} already reviewed")
                    continue

                # Check if bot already commented
                if self.github.has_been_reviewed(repo_name, pr_number):
                    print(f"   ✓ PR #{pr_number} already has review comment")
                    self.reviewed_prs.add(pr_key)
                    continue

                # New PR - review it!
                print(f"\n   🆕 NEW PR #{pr_number}: {pr_info['title']}")
                self._review_and_post(repo_name, pr_number)

        except Exception as e:
            print(f"   ❌ Error: {e}")

    def _review_and_post(self, repo_name: str, pr_number: int):
        """Review a PR and post the review."""
        print(f"      🔍 Reviewing...")

        try:
            # Get PR metadata and diff
            metadata = self.github.get_pr_metadata(repo_name, pr_number)
            diff = self.github.get_pr_diff(repo_name, pr_number)

            # Review the PR
            context = {
                "diff": diff,
                "pr_title": metadata["title"],
                "pr_description": metadata["description"]
            }

            review_result = self.review_agent.execute("Review this PR", context=context)

            if review_result["status"] != "success":
                print(f"      ❌ Review failed: {review_result.get('message')}")
                return

            # Track stats
            self.stats["prs_reviewed"] += 1
            critical_issues = review_result["metadata"]["critical_issues"]
            self.stats["critical_issues_found"] += critical_issues

            # Display results
            overall_risk = review_result["metadata"]["overall_risk"]
            ready = review_result["metadata"]["ready_to_merge"]

            print(f"      📊 Review complete:")
            print(f"         Risk: {overall_risk}")
            print(f"         Issues: {review_result['metadata']['issues_found']}")
            print(f"         Critical: {critical_issues}")
            print(f"         Ready: {'✅ Yes' if ready else '❌ No'}")

            # Governance check before posting
            operation = {
                "tool": "post_review_comment",
                "repo": repo_name,
                "pr": pr_number,
                "risk": overall_risk,
                "issues": review_result['metadata']['issues_found']
            }

            risk_level = self._assess_posting_risk(review_result)

            if not self.auto_post_reviews:
                # Ask for approval
                should_post = self.governance.request_approval(operation, risk_level)

                if not should_post:
                    print(f"      ⛔ Governance blocked posting review")
                    self.stats["reviews_blocked_by_governance"] += 1
                    return

            # Post the review
            print(f"      📤 Posting review...")
            post_result = self.github.post_review_comment(
                repo_name,
                pr_number,
                review_result
            )

            if post_result["status"] == "success":
                print(f"      ✅ Review posted: {post_result['url']}")
                self.stats["reviews_posted"] += 1

                # Mark as reviewed
                pr_key = f"{repo_name}:{pr_number}"
                self.reviewed_prs.add(pr_key)

                # Learn from this review
                self.fact_checker.store_fact(
                    f"Reviewed PR #{pr_number} in {repo_name}: {overall_risk} risk, {critical_issues} critical issues",
                    confidence=0.9
                )

            else:
                print(f"      ❌ Failed to post: {post_result.get('message')}")

        except Exception as e:
            print(f"      ❌ Error during review: {e}")
            import traceback
            traceback.print_exc()

    def _assess_posting_risk(self, review_result: Dict[str, Any]) -> RiskLevel:
        """Assess risk of posting a review comment.

        Posting reviews is generally safe (read-only on repo), but we assess
        based on the review content to decide if human should approve.

        Args:
            review_result: Review result from PRReviewAgent

        Returns:
            RiskLevel
        """
        overall_risk = review_result["metadata"]["overall_risk"]

        # Posting is always safe (just a comment), so we use GREEN
        # But if review found critical issues, we want human to verify before posting
        if overall_risk == "CRITICAL":
            return RiskLevel.YELLOW  # Ask for approval
        else:
            return RiskLevel.GREEN  # Auto-post

    def _print_stats(self):
        """Print session statistics."""
        runtime = datetime.now() - datetime.fromisoformat(self.stats["started_at"])

        print(f"\n{'='*70}")
        print("📊 SESSION STATISTICS")
        print('='*70)
        print(f"Runtime: {str(runtime).split('.')[0]}")
        print(f"PRs Reviewed: {self.stats['prs_reviewed']}")
        print(f"Reviews Posted: {self.stats['reviews_posted']}")
        print(f"Critical Issues Found: {self.stats['critical_issues_found']}")
        print(f"Blocked by Governance: {self.stats['reviews_blocked_by_governance']}")
        print('='*70)

    def review_single_pr(self, repo_name: str, pr_number: int):
        """Review a single PR immediately (for testing).

        Args:
            repo_name: Repository name
            pr_number: PR number
        """
        print(f"🎯 Single PR Review Mode")
        print(f"   Repo: {repo_name}")
        print(f"   PR: #{pr_number}\n")

        self._review_and_post(repo_name, pr_number)
        self._print_stats()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous PR Review Monitor")
    parser.add_argument(
        "repos",
        nargs="+",
        help="Repository names to monitor (format: owner/repo)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--auto-post",
        action="store_true",
        help="Auto-post reviews without governance approval (USE WITH CAUTION!)"
    )
    parser.add_argument(
        "--single-pr",
        type=int,
        help="Review a single PR number instead of continuous monitoring"
    )

    args = parser.parse_args()

    if not os.getenv('GITHUB_TOKEN'):
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export GITHUB_TOKEN='your_github_token_here'")
        print("\nCreate a token at: https://github.com/settings/tokens")
        print("Required permissions: repo (all)")
        sys.exit(1)

    # Create monitor
    monitor = AutonomousPRMonitor(
        repos=args.repos,
        check_interval=args.interval,
        auto_post_reviews=args.auto_post
    )

    # Single PR mode or continuous monitoring
    if args.single_pr:
        if len(args.repos) > 1:
            print("❌ Error: --single-pr only works with one repository")
            sys.exit(1)

        monitor.review_single_pr(args.repos[0], args.single_pr)
    else:
        monitor.run()


if __name__ == "__main__":
    main()

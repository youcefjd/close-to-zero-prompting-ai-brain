#!/usr/bin/env python3
"""Quick test - pass token as argument or it will read from environment"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_integration import GitHubClient
from sub_agents.pr_review_agent import PRReviewAgent

def main():
    # Get token from command line or environment
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print("✅ Using token from command line")
    else:
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print("✅ Using token from environment")
        else:
            print("❌ No token provided")
            print()
            print("Usage:")
            print("  python3 quick_test.py YOUR_GITHUB_TOKEN")
            print("  OR")
            print("  export GITHUB_TOKEN='your_token' && python3 quick_test.py")
            sys.exit(1)

    print(f"   Token: {token[:10]}...{token[-4:]}")
    print()

    # Connect to GitHub
    print("🔌 Connecting to GitHub...")
    try:
        client = GitHubClient(token=token)
        print()

        # Check for open PRs
        print("📦 Checking youcefjd/ai-pr-review for PRs...")
        prs = client.get_open_prs("youcefjd/ai-pr-review")

        print(f"   Found {len(prs)} open PR(s)")

        if not prs:
            print()
            print("ℹ️  No open PRs - create one at:")
            print("   https://github.com/youcefjd/ai-pr-review/compare/main...feature/add-authentication")
            return

        # Found PRs - let's review the first one
        pr = prs[0]
        pr_number = pr['number']

        print(f"   PR #{pr_number}: {pr['title']}")
        print()

        # Get the diff and review it
        print(f"🔍 Reviewing PR #{pr_number}...")
        metadata = client.get_pr_metadata("youcefjd/ai-pr-review", pr_number)
        diff = client.get_pr_diff("youcefjd/ai-pr-review", pr_number)

        print(f"   Files changed: {metadata['files_changed']}")
        print(f"   +{metadata['additions']} -{metadata['deletions']}")
        print()

        # Run the autonomous review
        print("🤖 Running autonomous PR review...")
        agent = PRReviewAgent()

        context = {
            "diff": diff,
            "pr_title": metadata["title"],
            "pr_description": metadata["description"]
        }

        result = agent.execute("Review this PR", context=context)

        if result['status'] == 'success':
            review = result['review']
            meta = result['metadata']

            print()
            print("="*70)
            print("📊 REVIEW COMPLETE")
            print("="*70)
            print(review.get('summary', ''))
            print()
            print(f"Issues: {meta['issues_found']} | Critical: {meta['critical_issues']}")
            print(f"Risk: {meta['overall_risk']} | Ready: {'✅ YES' if meta['ready_to_merge'] else '❌ NO'}")

            if review.get('issues'):
                print()
                print("🔍 ISSUES:")
                for i, issue in enumerate(review['issues'][:3], 1):  # Show first 3
                    emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '📝', 'LOW': '💡'}.get(issue.get('severity'), '❓')
                    print(f"  {i}. {emoji} {issue.get('title')}")
                if len(review['issues']) > 3:
                    print(f"  ... and {len(review['issues']) - 3} more")

            print()
            print("="*70)

            # Ask if they want to post it
            print()
            response = input("📤 Post this review to GitHub? (yes/no): ").strip().lower()

            if response == 'yes':
                print()
                print("📤 Posting review to PR...")
                post_result = client.post_review_comment(
                    "youcefjd/ai-pr-review",
                    pr_number,
                    result
                )

                if post_result['status'] == 'success':
                    print(f"✅ Posted! View at: {post_result['url']}")
                    print()
                    print("🎉 AUTONOMOUS PR REVIEW COMPLETE!")
                else:
                    print(f"❌ Failed to post: {post_result.get('message')}")
            else:
                print("⏭️  Skipped posting")
        else:
            print(f"❌ Review failed: {result.get('message')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

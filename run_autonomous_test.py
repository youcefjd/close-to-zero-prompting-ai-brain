#!/usr/bin/env python3
"""Run autonomous PR review test - picks up GITHUB_TOKEN from environment"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_integration import GitHubClient

def main():
    print("🚀 AUTONOMOUS PR REVIEW - LIVE TEST")
    print("="*70)

    # Check token
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not found in environment")
        print()
        print("Please export it:")
        print("  export GITHUB_TOKEN='ghp_your_token_here'")
        sys.exit(1)

    print(f"✅ Token found ({len(token)} chars)")
    print()

    # Test connection
    print("🔌 Testing GitHub connection...")
    try:
        client = GitHubClient(token=token)
        print()

        # Check the test repo
        print("📦 Checking youcefjd/ai-pr-review...")
        try:
            prs = client.get_open_prs("youcefjd/ai-pr-review")
            print(f"   Open PRs: {len(prs)}")

            if prs:
                for pr in prs:
                    print(f"   - PR #{pr['number']}: {pr['title']}")

                print()
                print("🎯 Ready to review!")
                print()
                print("Run autonomous review with:")
                print(f"  python autonomous_pr_monitor.py youcefjd/ai-pr-review --single-pr {prs[0]['number']}")
            else:
                print()
                print("ℹ️  No open PRs found yet")
                print()
                print("To create a test PR:")
                print("1. Go to: https://github.com/youcefjd/ai-pr-review")
                print("2. Click 'Compare & pull request' for feature/add-authentication branch")
                print("3. Create the PR")
                print("4. Run this script again")

        except Exception as e:
            print(f"⚠️  Error checking repo: {e}")

    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        print()
        print("Check your token at: https://github.com/settings/tokens")
        sys.exit(1)

if __name__ == "__main__":
    main()

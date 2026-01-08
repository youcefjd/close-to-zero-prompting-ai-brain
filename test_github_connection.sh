#!/bin/bash
# Test GitHub connection and run autonomous PR review

echo "🔍 Checking GitHub token..."
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set in your terminal"
    echo ""
    echo "Please run:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

echo "✅ Token found (${#GITHUB_TOKEN} characters)"
echo ""

# Test the connection
echo "🔌 Testing GitHub API connection..."
python3 << 'PYTHON_EOF'
import os
from github import Github

token = os.getenv('GITHUB_TOKEN')
try:
    g = Github(token)
    user = g.get_user()
    print(f"✅ Connected as: {user.login}")
    print(f"   Name: {user.name}")
    print(f"   Repos: {user.public_repos}")
    print("")
    print("🎉 GitHub connection works!")
    print("")

    # Check the test repo
    print("📦 Checking test repo...")
    try:
        repo = g.get_repo("youcefjd/ai-pr-review")
        print(f"✅ Found repo: {repo.full_name}")

        # Get branches
        branches = [b.name for b in repo.get_branches()]
        print(f"   Branches: {', '.join(branches)}")

        if 'feature/add-authentication' in branches:
            print("")
            print("🎯 Ready to test autonomous PR review!")
            print("")
            print("To create a PR and test, you can either:")
            print("1. Create PR manually on GitHub")
            print("2. Or run this to create it via API:")
            print("   python3 create_test_pr.py")

    except Exception as e:
        print(f"⚠️  Repo check: {e}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("")
    print("Check your token at: https://github.com/settings/tokens")
    exit(1)
PYTHON_EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next: Create PR and test autonomous review"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

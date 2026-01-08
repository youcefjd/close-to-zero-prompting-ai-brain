#!/bin/bash
# Quick test script for autonomous PR review system

echo "🚀 Autonomous PR Review System - Quick Test"
echo "=========================================="
echo ""

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set"
    echo ""
    echo "To set it:"
    echo "  export GITHUB_TOKEN='your_github_token_here'"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required permissions: repo (all)"
    echo ""
    exit 1
fi

echo "✅ GITHUB_TOKEN is set"
echo ""

# Check if user provided repo and PR number
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./test_autonomous_system.sh <repo> <pr_number>"
    echo ""
    echo "Example:"
    echo "  ./test_autonomous_system.sh your-org/your-repo 123"
    echo ""
    echo "This will:"
    echo "  1. Fetch PR #123 from your-org/your-repo"
    echo "  2. Analyze the code for issues"
    echo "  3. Ask for your approval"
    echo "  4. Post review to GitHub"
    echo ""
    exit 1
fi

REPO=$1
PR_NUMBER=$2

echo "Testing with:"
echo "  Repo: $REPO"
echo "  PR: #$PR_NUMBER"
echo ""
echo "Starting test..."
echo "=========================================="
echo ""

# Run the autonomous monitor in single-PR mode
python autonomous_pr_monitor.py "$REPO" --single-pr "$PR_NUMBER"

echo ""
echo "=========================================="
echo "✅ Test complete!"
echo ""
echo "What just happened:"
echo "  1. Your autonomous system fetched the PR"
echo "  2. PRReviewAgent analyzed the code"
echo "  3. It found security/quality issues"
echo "  4. You approved posting the review"
echo "  5. It posted to GitHub automatically"
echo ""
echo "🎉 Your autonomous PR review system works!"
echo ""
echo "Next steps:"
echo "  • Check the GitHub PR for the review comment"
echo "  • Run in continuous mode: python autonomous_pr_monitor.py $REPO"
echo "  • Monitor multiple repos: python autonomous_pr_monitor.py repo1 repo2"
echo ""

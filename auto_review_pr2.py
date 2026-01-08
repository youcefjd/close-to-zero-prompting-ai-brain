#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/youcef/close-to-zero-prompting-ai-brain/close-to-zero-prompting-ai-brain')

from github import Github
from github_integration import GitHubClient
from sub_agents.pr_review_agent import PRReviewAgent

token = sys.argv[1] if len(sys.argv) > 1 else None

print("🧪 BLIND TEST - Agent must detect issues WITHOUT hints!")
print("="*70)
print()

# Create PR
print("📝 Creating PR #2...")
g = Github(token)
repo = g.get_repo("youcefjd/ai-pr-review")

pr = repo.create_pull(
    title="Add user dashboard, admin panel, and search features",
    body="Implements new features: user dashboard, admin panel, and search. Adds essential functionality for users.",
    head="feature/user-dashboard",
    base="main"
)

print(f"✅ PR #{pr.number} created: {pr.html_url}")
print()

# Review it
print("🤖 Autonomous review starting...")
client = GitHubClient(token=token)
agent = PRReviewAgent()

metadata = client.get_pr_metadata("youcefjd/ai-pr-review", pr.number)
diff = client.get_pr_diff("youcefjd/ai-pr-review", pr.number)

result = agent.execute("Review this PR", context={
    "diff": diff,
    "pr_title": metadata["title"],
    "pr_description": metadata["description"]
})

if result['status'] == 'success':
    meta = result['metadata']
    review = result['review']

    print(f"✅ Found {meta['issues_found']} issues, {meta['critical_issues']} CRITICAL")

    if review.get('issues'):
        critical = [i for i in review['issues'] if i.get('severity') == 'CRITICAL']
        if critical:
            print(f"\n🚨 CRITICAL ISSUES (no hints given!):")
            for i, issue in enumerate(critical, 1):
                print(f"   {i}. {issue.get('title')}")

    # Post automatically
    print(f"\n📤 Posting to GitHub...")
    post_result = client.post_review_comment("youcefjd/ai-pr-review", pr.number, result)

    if post_result['status'] == 'success':
        print(f"✅ POSTED: {post_result['url']}")
        print(f"\n🎯 Agent detected {meta['critical_issues']} critical issues WITHOUT any hints!")
        print(f"   View review: https://github.com/youcefjd/ai-pr-review/pull/{pr.number}")

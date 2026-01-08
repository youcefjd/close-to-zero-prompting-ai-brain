#!/usr/bin/env python3
"""Test script for PR Review Agent."""

import sys
sys.path.insert(0, '/Users/youcef/close-to-zero-prompting-ai-brain/close-to-zero-prompting-ai-brain')

from sub_agents.pr_review_agent import PRReviewAgent


def main():
    print("🚀 Testing Autonomous PR Review Agent\n")
    print("="*70)

    agent = PRReviewAgent()

    # Test with the sample diff
    diff_file = "test_pr.diff"
    pr_title = "Add authentication and data processing"

    print(f"📝 Reviewing: {pr_title}")
    print(f"📄 Diff file: {diff_file}\n")

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
                severity_emoji = {
                    "CRITICAL": "🚨",
                    "HIGH": "⚠️",
                    "MEDIUM": "📝",
                    "LOW": "💡"
                }.get(issue.get('severity', 'UNKNOWN'), "❓")

                print(f"\n{i}. {severity_emoji} [{issue.get('severity', 'UNKNOWN')}] {issue.get('title', 'No title')}")
                print(f"   📁 File: {issue.get('file', 'Unknown')}")
                if issue.get('line'):
                    print(f"   📍 Line: {issue['line']}")
                print(f"   🏷️  Category: {issue.get('category', 'Unknown')}")
                print(f"   📖 Description: {issue.get('description', 'No description')}")
                if issue.get('suggestion'):
                    print(f"   💡 Suggestion: {issue['suggestion']}")
                if issue.get('code_example'):
                    print(f"   💻 Code Example:\n{issue['code_example']}")

        if review.get("positives"):
            print("\n" + "="*70)
            print("✨ POSITIVES")
            print("="*70)
            for positive in review["positives"]:
                print(f"  ✓ {positive}")

        print("\n" + "="*70)
        print("🤔 REASONING")
        print("="*70)
        print(f"{review.get('reasoning', 'No reasoning provided')}")
        print("="*70)

        # Test that it detected the SQL injection
        found_sql_injection = any(
            'sql' in issue.get('title', '').lower() or 'injection' in issue.get('description', '').lower()
            for issue in review.get('issues', [])
        )

        if found_sql_injection:
            print("\n✅ SUCCESS: Agent correctly detected SQL injection vulnerabilities!")
        else:
            print("\n⚠️  WARNING: Agent may have missed SQL injection vulnerabilities")

    else:
        print(f"\n❌ Review failed: {result.get('message')}")
        if 'raw_response' in result:
            print(f"\nRaw response: {result['raw_response'][:500]}...")

    print("\n" + "="*70)
    print("✅ Test Complete!")
    print("="*70)


if __name__ == "__main__":
    main()

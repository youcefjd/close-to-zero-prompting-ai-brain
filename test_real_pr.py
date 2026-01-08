#!/usr/bin/env python3
"""Test PR Review Agent on REAL code - the PR we just created."""

import sys
sys.path.insert(0, '/Users/youcef/close-to-zero-prompting-ai-brain/close-to-zero-prompting-ai-brain')

from sub_agents.pr_review_agent import PRReviewAgent


def main():
    print("🚀 REAL PR REVIEW TEST")
    print("="*70)
    print("Reviewing the PRReviewAgent we just built (meta!)")
    print("="*70 + "\n")

    agent = PRReviewAgent()

    # Review the actual PR we just created
    result = agent.review_pr_from_diff(
        "real_pr.diff",
        pr_title="Add autonomous PR review agent",
        pr_description="Implements PRReviewAgent that can autonomously review pull requests, detect security issues, and provide structured feedback."
    )

    if result["status"] == "success":
        review = result["review"]
        metadata = result["metadata"]

        print("="*70)
        print("📊 REVIEW SUMMARY")
        print("="*70)
        print(f"\n{review.get('summary', 'No summary')}\n")

        print(f"📁 Files Changed: {metadata['files_changed']}")
        print(f"🔍 Issues Found: {metadata['issues_found']}")
        print(f"🚨 Critical Issues: {metadata['critical_issues']}")
        print(f"⚠️  Overall Risk: {metadata['overall_risk']}")
        print(f"{'✅ Ready to Merge' if metadata['ready_to_merge'] else '❌ NOT Ready to Merge'}")

        if review.get("issues"):
            print("\n" + "="*70)
            print("🔍 ISSUES")
            print("="*70)
            for i, issue in enumerate(review["issues"], 1):
                emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📝", "LOW": "💡"}.get(issue.get('severity'), "❓")
                print(f"\n{i}. {emoji} [{issue.get('severity')}] {issue.get('title')}")
                print(f"   📁 {issue.get('file')} (line {issue.get('line', 'N/A')})")
                print(f"   📖 {issue.get('description')}")
                if issue.get('suggestion'):
                    print(f"   💡 {issue['suggestion']}")

        if review.get("positives"):
            print("\n" + "="*70)
            print("✨ POSITIVES")
            print("="*70)
            for pos in review["positives"]:
                print(f"  ✓ {pos}")

        print("\n" + "="*70)
        print("🤔 REASONING")
        print("="*70)
        print(review.get('reasoning', 'No reasoning'))
        print("="*70)

        # Analysis
        print("\n" + "="*70)
        print("📈 META-ANALYSIS")
        print("="*70)
        print(f"✅ Agent successfully reviewed {metadata['files_changed']} files")
        print(f"✅ Provided structured feedback with {metadata['issues_found']} issues")
        print(f"✅ Assessment: {metadata['overall_risk']} risk")

        if metadata['ready_to_merge']:
            print("\n🎉 The agent thinks our code is ready to merge!")
        else:
            print(f"\n⚠️  Agent suggests improvements before merging")

    else:
        print(f"❌ Review failed: {result.get('message')}")

    print("\n" + "="*70)
    print("✅ REAL PR TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

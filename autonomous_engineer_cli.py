#!/usr/bin/env python3
"""Autonomous Engineer CLI - Build features from request to production.

Usage:
    ai-engineer "Add user authentication with OAuth"
    ai-engineer "Add dark mode to the app"
    ai-engineer "Add export to PDF feature"

The autonomous engineer will:
1. Analyze your codebase
2. Design the architecture
3. Implement backend and frontend
4. Write comprehensive tests
5. Review for security
6. Create a pull request

All autonomously!
"""

import sys
import argparse
from pathlib import Path

from autonomous_engineer.orchestrator_agent import OrchestratorAgent


def main():
    """Main entry point for the autonomous engineer CLI."""
    parser = argparse.ArgumentParser(
        description="Autonomous Engineer - Build features from request to production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-engineer "Add user authentication with OAuth"
  ai-engineer "Add dark mode toggle to settings"
  ai-engineer "Add export to PDF feature"

The autonomous engineer will autonomously:
  • Design architecture
  • Implement backend & frontend
  • Write comprehensive tests
  • Review for security
  • Create pull request

All you do is review and approve!
        """,
    )

    parser.add_argument(
        "feature_request",
        type=str,
        help="Natural language description of the feature to build",
    )

    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        default=".",
        help="Path to the project repository (default: current directory)",
    )

    parser.add_argument(
        "--github-token",
        "-t",
        type=str,
        help="GitHub token for PR creation (default: from GITHUB_TOKEN env var)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only, don't execute (shows what would be done)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Validate repository path
    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"❌ Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    if not (repo_path / ".git").exists():
        print(f"⚠️  Warning: {repo_path} is not a git repository")
        print(f"   The autonomous engineer works best with git repositories.")
        response = input("   Continue anyway? [y/N] ")
        if response.lower() != "y":
            sys.exit(0)

    # Print welcome message
    print("\n" + "=" * 70)
    print("  🤖 AUTONOMOUS ENGINEER")
    print("  From feature request to production, fully autonomous")
    print("=" * 70)
    print(f"\n📋 Feature Request: {args.feature_request}")
    print(f"📁 Repository: {repo_path}")

    if args.dry_run:
        print(f"🔍 Mode: DRY RUN (planning only)")
    else:
        print(f"🚀 Mode: FULL EXECUTION")

    print("=" * 70 + "\n")

    # Create orchestrator
    orchestrator = OrchestratorAgent(
        repo_path=str(repo_path),
        github_token=args.github_token,
    )

    # Execute
    try:
        result = orchestrator.execute(
            feature_request=args.feature_request,
            context={
                "dry_run": args.dry_run,
                "verbose": args.verbose,
            },
        )

        # Print results
        print("\n" + "=" * 70)
        if result["status"] == "success":
            print("✅ SUCCESS!")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   Duration: {result.get('duration', 'unknown')}")
            print(f"   Phases completed: {len(result.get('phases', {}))}")

            if "pr_url" in result and result["pr_url"]:
                print(f"\n🔗 Pull Request: {result['pr_url']}")
                print(f"   PR #{result.get('pr_number', 'N/A')}")

            print(f"\n✅ Feature implementation complete!")
            print(f"   Review the PR and approve when ready.")

        elif result["status"] == "error":
            print("❌ ERROR")
            print("=" * 70)
            print(f"\n{result.get('message', 'Unknown error')}")

            if "failed_phase" in result:
                print(f"\nFailed at phase: {result['failed_phase']}")

            if "completed_phases" in result:
                print(f"Completed phases: {', '.join(result['completed_phases'])}")

            sys.exit(1)

        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   Changes may be incomplete")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

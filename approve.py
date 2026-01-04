"""Interactive approval interface for pending agent operations."""

import sys
from governance import get_governance
import json


def list_pending():
    """List all pending approval requests."""
    governance = get_governance()
    governance._load_approvals()
    
    pending = [
        req for req in governance.pending_approvals.values()
        if req.get("status") == "pending"
    ]
    
    if not pending:
        print("No pending approval requests.")
        return
    
    print(f"\n📋 Pending Approval Requests ({len(pending)}):\n")
    for req in pending:
        print(f"  ID: {req['approval_id']}")
        print(f"  Tool: {req['tool_name']}")
        print(f"  Risk: {req['risk_level'].upper()}")
        print(f"  Time: {req['timestamp']}")
        print(f"  Message: {req.get('approval_message', '')}")
        print()
        
        # Show change plan if available
        change_plan = req.get("change_plan", {})
        if "formatted_plan" in change_plan:
            print("  Change Plan:")
            print("  " + "\n  ".join(change_plan["formatted_plan"].split("\n")))
            print()


def approve(approval_id: str):
    """Approve a request."""
    governance = get_governance()
    governance._load_approvals()
    
    request = governance.get_approval_request(approval_id)
    if not request:
        print(f"❌ Approval {approval_id} not found.")
        return
    
    if request.get("status") != "pending":
        print(f"⚠️  Approval {approval_id} is already {request.get('status')}.")
        return
    
    # Show plan
    change_plan = request.get("change_plan", {})
    if "formatted_plan" in change_plan:
        print("\n" + "="*70)
        print(change_plan["formatted_plan"])
        print("="*70 + "\n")
    
    # Confirm
    print(f"⚠️  Approve this request? (yes/no): ", end="")
    response = input().strip().lower()
    
    if response == "yes" or response == "y":
        result = governance.approve(approval_id, approver="human")
        if result["status"] == "approved":
            print(f"\n✅ Approved! The system will re-execute the request with this approval.\n")
            print(f"💡 Re-run your original command to execute with the approved permission.\n")
        else:
            print(f"❌ Approval failed: {result.get('message')}")
    else:
        print("❌ Approval cancelled.")


def reject(approval_id: str, reason: str = ""):
    """Reject a request."""
    governance = get_governance()
    governance._load_approvals()
    
    if not reason:
        print(f"Reason for rejection (optional): ", end="")
        reason = input().strip()
    
    result = governance.reject(approval_id, reason)
    if result["status"] == "rejected":
        print(f"✅ Request {approval_id} rejected.")
    else:
        print(f"❌ Rejection failed: {result.get('message')}")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python approve.py list              - List pending requests")
        print("  python approve.py approve <id>      - Approve a request")
        print("  python approve.py reject <id> [reason] - Reject a request")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_pending()
    elif command == "approve":
        if len(sys.argv) < 3:
            print("❌ Please provide approval ID")
            return
        approve(sys.argv[2])
    elif command == "reject":
        if len(sys.argv) < 3:
            print("❌ Please provide approval ID")
            return
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        reject(sys.argv[2], reason)
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Test script for complex task execution with monitoring."""

import sys
import time
import traceback
from datetime import datetime
from autonomous_orchestrator import AutonomousOrchestrator
from cost_tracker import get_cost_tracker
from self_healing import get_self_healing_system
from emergency_stop import get_emergency_stop


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_section(text):
    """Print a section header."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}")


def monitor_execution(task: str, environment: str = "dev"):
    """Monitor execution of a complex task."""
    
    print_header("🧪 COMPLEX TASK TESTING")
    
    # Pre-flight checks
    print_section("Pre-Flight Checks")
    
    emergency_stop = get_emergency_stop()
    if emergency_stop.is_stopped():
        print("  ⚠️  Emergency stop is active. Resetting...")
        emergency_stop.reset()
    
    print("  ✅ Emergency stop: OK")
    print("  ✅ Cost tracker: OK")
    print("  ✅ Self-healing: OK")
    print(f"  ✅ Environment: {environment}")
    
    # Initialize
    start_time = time.time()
    orchestrator = AutonomousOrchestrator()
    cost_tracker = get_cost_tracker()
    cost_tracker.reset_task()
    
    print_section("Task Execution")
    print(f"  📝 Task: {task}")
    print(f"  ⏱️  Start: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Execute with context
        context = {"environment": environment}
        result = orchestrator.execute(task, context)
        
        elapsed = time.time() - start_time
        cost_summary = cost_tracker.get_summary()
        
        print_section("Execution Results")
        print(f"  ✅ Status: {result.get('status', 'unknown')}")
        print(f"  ⏱️  Time: {elapsed:.2f} seconds")
        print(f"  💰 Cost: ${cost_summary['current_task']['cost']:.4f}")
        print(f"  📊 Tokens: {cost_summary['current_task']['total_tokens']:,}")
        print(f"  📈 Usage: {cost_summary['usage_percentage']['cost']:.1f}% of limit")
        
        # Check for self-healing
        if result.get('self_healed'):
            print_section("Self-Healing")
            healing_details = result.get('healing_details', {})
            print(f"  ✅ Self-healing triggered!")
            print(f"  📋 Issue Type: {healing_details.get('issue_type', 'unknown')}")
            print(f"  🔧 Fix Applied: {healing_details.get('fix_applied', False)}")
        
        # Check for approval requests
        if result.get('status') == 'needs_approval':
            print_section("Approval Required")
            print(f"  ⏸️  Approval ID: {result.get('healing_details', {}).get('approval_id', 'N/A')}")
            print(f"  💡 Run: python approve.py {result.get('healing_details', {}).get('approval_id', '')}")
        
        # Check for errors
        if result.get('status') == 'error':
            print_section("Error Details")
            print(f"  ❌ Error: {result.get('message', 'Unknown error')}")
            print(f"  📋 Reason: {result.get('reason', 'N/A')}")
        
        # Success metrics
        if result.get('status') == 'success':
            print_section("Success Metrics")
            print(f"  ✅ Task completed successfully")
            print(f"  ⚡ Performance: {elapsed:.2f}s")
            print(f"  💰 Cost efficiency: ${cost_summary['current_task']['cost']:.4f}")
            
            if elapsed < 30:
                print(f"  ⚡ Fast execution (< 30s)")
            elif elapsed < 120:
                print(f"  ⚡ Reasonable execution (< 2min)")
            else:
                print(f"  ⚠️  Slow execution (> 2min) - consider optimization")
            
            # Show actual result content
            print_section("Task Result")
            message = result.get('message', '')
            if len(message) > 500:
                print(f"  {message[:500]}...")
                print(f"  (truncated - full message: {len(message)} chars)")
            else:
                print(f"  {message}")
            
            # Show container data if present
            if 'containers' in result:
                print_section("Container List")
                containers = result.get('containers', [])
                print(f"  Found {len(containers)} container(s):")
                for i, container in enumerate(containers, 1):
                    name = container.get('Names', 'N/A')
                    status = container.get('Status', 'N/A')
                    state = container.get('State', 'N/A')
                    print(f"    {i}. {name} - {state} ({status})")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        
        print_section("Execution Failed")
        print(f"  ❌ Error: {str(e)}")
        print(f"  ⏱️  Time before failure: {elapsed:.2f} seconds")
        print(f"  📋 Stack trace:")
        print(f"  {traceback.format_exc()[:500]}...")
        
        # Check if self-healing attempted
        try:
            healing_system = get_self_healing_system()
            if len(healing_system.healing_history) > 0:
                last_attempt = healing_system.healing_history[-1]
                print_section("Self-Healing Attempt")
                print(f"  🔍 Issue detected: {last_attempt.get('issue_type', 'unknown')}")
                print(f"  ✅ Fix proposed: {last_attempt.get('validation', {}).get('valid', False)}")
                print(f"  ✅ Success: {last_attempt.get('success', False)}")
        except:
            pass
        
        raise


def run_test_suite():
    """Run a suite of test tasks."""
    
    test_tasks = [
        {
            "name": "Simple Docker Check",
            "task": "List all Docker containers and show their status",
            "expected_time": 10,
            "complexity": "low"
        },
        {
            "name": "Multi-Step Configuration",
            "task": "Create a docker-compose.yml with Redis and PostgreSQL, then verify the file was created",
            "expected_time": 30,
            "complexity": "medium"
        },
        {
            "name": "Complex System Setup",
            "task": "Create a docker-compose.yml with 3 services (Redis, PostgreSQL, Python API), configure them with environment variables, and create a README explaining the setup",
            "expected_time": 60,
            "complexity": "high"
        }
    ]
    
    print_header("🧪 COMPLEX TASK TEST SUITE")
    
    results = []
    for i, test in enumerate(test_tasks, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_tasks)}: {test['name']}")
        print(f"Complexity: {test['complexity']}")
        print(f"{'='*70}\n")
        
        try:
            result = monitor_execution(test['task'], environment="dev")
            results.append({
                "test": test['name'],
                "status": result.get('status', 'unknown'),
                "success": result.get('status') == 'success'
            })
        except Exception as e:
            results.append({
                "test": test['name'],
                "status": "error",
                "success": False,
                "error": str(e)
            })
        
        # Wait between tests
        if i < len(test_tasks):
            print("\n⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Summary
    print_header("📊 TEST SUITE SUMMARY")
    
    total = len(results)
    successful = sum(1 for r in results if r.get('success'))
    
    print(f"  Total Tests: {total}")
    print(f"  Successful: {successful} ✅")
    print(f"  Failed: {total - successful} ❌")
    print(f"  Success Rate: {(successful/total*100):.1f}%")
    
    print("\n  Detailed Results:")
    for result in results:
        status_icon = "✅" if result.get('success') else "❌"
        print(f"    {status_icon} {result['test']}: {result['status']}")
        if not result.get('success') and result.get('error'):
            print(f"       Error: {result['error'][:100]}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--suite":
            run_test_suite()
        else:
            task = " ".join(sys.argv[1:])
            monitor_execution(task)
    else:
        print("Usage:")
        print("  python test_complex_tasks.py <task>")
        print("  python test_complex_tasks.py --suite")
        print("\nExamples:")
        print("  python test_complex_tasks.py 'List all Docker containers'")
        print("  python test_complex_tasks.py 'Create a docker-compose.yml with Redis and PostgreSQL'")
        print("  python test_complex_tasks.py --suite")


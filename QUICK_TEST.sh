#!/bin/bash
# Quick test script for Zero Prompting AI Brain

echo "🧠 Zero Prompting AI Brain - Quick Test"
echo "========================================"
echo ""

# Test 1: Simple Docker check
echo "Test 1: Docker Container List"
echo "-----------------------------"
python autonomous_orchestrator.py "List all running Docker containers"
echo ""
echo "Press Enter to continue..."
read

# Test 2: File creation
echo "Test 2: File Creation"
echo "---------------------"
python autonomous_orchestrator.py "Create a test.txt file with the content 'Hello from AI Brain'"
echo ""
echo "Press Enter to continue..."
read

# Test 3: Consultation
echo "Test 3: Consultation Task"
echo "-------------------------"
python autonomous_orchestrator.py "Compare Docker Compose vs Kubernetes for a small application"
echo ""
echo "Press Enter to continue..."
read

# Test 4: Complex task
echo "Test 4: Multi-Step Task"
echo "-----------------------"
python autonomous_orchestrator.py "Check if Docker is running, list all containers, and create a summary file called docker_status.txt"
echo ""
echo "Press Enter to continue..."
read

# Test 5: Emergency stop
echo "Test 5: Emergency Stop (will start a long task, then stop it)"
echo "-------------------------------------------------------------"
echo "Starting long task in background..."
python autonomous_orchestrator.py "List all containers, show detailed logs, then analyze each one" &
TASK_PID=$!
sleep 2
echo "Activating emergency stop..."
python stop.py stop "Test emergency stop"
sleep 1
python stop.py status
python stop.py reset
echo ""
echo "All tests complete!"


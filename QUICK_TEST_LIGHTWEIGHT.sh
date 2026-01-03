#!/bin/bash

# Quick Lightweight Test for AI Brain
# Tests: Design Consultant, Governance, System Building
# Resource-friendly: No heavy containers, minimal dependencies

echo "🧠 AI Brain - Lightweight Test"
echo "=============================="
echo ""
echo "This test will:"
echo "  1. Test design consultant (Q&A, options)"
echo "  2. Test governance enforcement"
echo "  3. Build a simple system (lightweight)"
echo ""
echo "Press Enter to start..."
read

# Test 1: Simple monitoring/logging system (lightweight)
echo ""
echo "📋 TEST 1: Simple Log Monitoring System"
echo "========================================"
echo ""
python autonomous_orchestrator.py "Build a simple log monitoring system that watches a log file and alerts on errors - keep it lightweight for a small laptop"

echo ""
echo "Press Enter for next test..."
read

# Test 2: Configuration management tool
echo ""
echo "📋 TEST 2: Configuration Management Tool"
echo "========================================"
echo ""
python autonomous_orchestrator.py "Build a simple configuration management tool that can read, validate, and update YAML config files safely"

echo ""
echo "Press Enter for next test..."
read

# Test 3: Simple API health checker
echo ""
echo "📋 TEST 3: API Health Checker"
echo "============================="
echo ""
python autonomous_orchestrator.py "Build a lightweight API health checker that monitors endpoints and reports status - no heavy dependencies"

echo ""
echo "✅ All tests complete!"
echo ""
echo "Check the results above to verify:"
echo "  - Design consultant asked questions"
echo "  - Options were presented"
echo "  - Governance was enforced"
echo "  - System was built"


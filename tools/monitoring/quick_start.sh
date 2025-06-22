#!/bin/bash

# Quick Start Investigation Script
# Simplified interface for running the complete investigation

set -e

REPO_PATH="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$REPO_PATH/tools/monitoring"

echo "🕵️ Empty File Investigation - Quick Start"
echo "Repository: $REPO_PATH"
echo "Timestamp: $(date)"
echo ""

# Function to display menu
show_menu() {
    echo "🔍 Investigation Options:"
    echo "1. Collect current evidence"
    echo "2. Start monitoring for recreation"
    echo "3. Run restoration test (requires monitoring)"
    echo "4. Stop monitoring and analyze results"
    echo "5. Complete investigation (automated)"
    echo "6. Show investigation status"
    echo "7. Exit"
    echo ""
}

# Function to check if monitoring is running
check_monitoring() {
    if pgrep -f "master_monitor.sh" > /dev/null; then
        echo "✅ Monitoring is currently ACTIVE"
        return 0
    else
        echo "❌ Monitoring is currently INACTIVE"
        return 1
    fi
}

# Function to collect evidence
collect_evidence() {
    echo "📊 Collecting current evidence..."
    "$REPO_PATH/forensics/collect_evidence.sh"
    echo ""
}

# Function to start monitoring
start_monitoring() {
    if check_monitoring; then
        echo "Monitoring already running. Use option 4 to stop first."
        return 1
    fi
    
    echo "🚀 Starting comprehensive monitoring..."
    "$SCRIPT_DIR/master_monitor.sh" &
    echo "Monitoring started in background"
    echo "Wait 10 seconds for initialization..."
    sleep 10
    echo "✅ Monitoring is now active"
    echo ""
}

# Function to run restoration test
run_restoration_test() {
    if ! check_monitoring; then
        echo "❌ Monitoring must be active first. Use option 2."
        return 1
    fi
    
    echo "🧪 Running restoration test..."
    "$SCRIPT_DIR/restoration_test.sh"
    echo ""
}

# Function to stop monitoring
stop_monitoring() {
    if ! check_monitoring; then
        echo "No monitoring to stop."
        return 1
    fi
    
    echo "🛑 Stopping monitoring and collecting evidence..."
    "$SCRIPT_DIR/stop_monitoring.sh"
    echo ""
}

# Function to run complete investigation
complete_investigation() {
    echo "🔬 Starting complete automated investigation..."
    echo ""
    
    # Step 1: Collect initial evidence
    echo "Step 1: Collecting initial evidence..."
    collect_evidence
    
    # Step 2: Start monitoring
    echo "Step 2: Starting monitoring..."
    start_monitoring
    
    # Step 3: Run restoration test
    echo "Step 3: Running restoration test..."
    sleep 2
    run_restoration_test
    
    # Step 4: Wait for results
    echo "Step 4: Waiting for results..."
    sleep 30
    
    # Step 5: Stop and analyze
    echo "Step 5: Stopping monitoring and analyzing..."
    stop_monitoring
    
    echo "🎯 Complete investigation finished!"
    echo "Review the evidence files for results."
    echo ""
}

# Function to show status
show_status() {
    echo "📊 Investigation Status:"
    echo ""
    
    # Check monitoring
    check_monitoring
    echo ""
    
    # Check empty files
    EMPTY_COUNT=$(find "$REPO_PATH" -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
    echo "Empty files currently: $EMPTY_COUNT"
    
    if [[ $EMPTY_COUNT -gt 0 ]]; then
        echo "🚨 Empty files detected:"
        find "$REPO_PATH" -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | head -5
    fi
    echo ""
    
    # Check evidence directories
    EVIDENCE_DIRS=$(find "$REPO_PATH" -name "evidence_*" -type d 2>/dev/null | wc -l)
    echo "Evidence directories: $EVIDENCE_DIRS"
    
    if [[ $EVIDENCE_DIRS -gt 0 ]]; then
        echo "Latest evidence:"
        find "$REPO_PATH" -name "evidence_*" -type d 2>/dev/null | sort | tail -1
    fi
    echo ""
}

# Main menu loop
while true; do
    show_menu
    read -p "Select option (1-7): " choice
    echo ""
    
    case $choice in
        1)
            collect_evidence
            ;;
        2)
            start_monitoring
            ;;
        3)
            run_restoration_test
            ;;
        4)
            stop_monitoring
            ;;
        5)
            complete_investigation
            ;;
        6)
            show_status
            ;;
        7)
            echo "👋 Investigation interface closed"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-7."
            echo ""
            ;;
    esac
    
    read -p "Press Enter to continue..."
    echo ""
done
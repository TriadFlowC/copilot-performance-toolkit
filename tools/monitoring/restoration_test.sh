#!/bin/bash

# Git Restoration Test Script
# Automated script to trigger empty file recreation while monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_PATH="$(git rev-parse --show-toplevel)"

echo "🧪 Git Restoration Test for Empty File Investigation"
echo "Repository: $REPO_PATH"
echo "Timestamp: $(date)"
echo ""

# Check if monitoring is already running
if pgrep -f "master_monitor.sh" > /dev/null; then
    echo "✅ Monitoring detected as already running"
else
    echo "❌ No monitoring detected. Please start monitoring first:"
    echo "   cd $SCRIPT_DIR"
    echo "   ./master_monitor.sh"
    echo ""
    read -p "Start monitoring now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting monitoring..."
        "$SCRIPT_DIR/master_monitor.sh" &
        MONITOR_PID=$!
        echo "Monitoring started with PID: $MONITOR_PID"
        echo "Waiting 10 seconds for monitoring to initialize..."
        sleep 10
    else
        echo "Please start monitoring manually and then run this script again."
        exit 1
    fi
fi

echo "🔍 Current repository state:"
cd "$REPO_PATH"
git status --short

echo ""
echo "📊 Current empty file count:"
CURRENT_EMPTY=$(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
echo "Empty files: $CURRENT_EMPTY"

if [[ $CURRENT_EMPTY -gt 0 ]]; then
    echo "🚨 Empty files already exist. Listing them:"
    find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 "
    echo ""
fi

echo "🎯 TARGET FILES FOR RESTORATION TEST:"
TARGET_FILES=(
    "docs/theoretical-analysis/copilot_context_theory.md"
    "docs/theoretical-analysis/copilot_deep_theory.md"
    "tools/test.py"
    "tools/workspace_analyzer_enhanced.py"
    "tools/compare_folders.py"
)

echo "Files to be restored (if they exist):"
for file in "${TARGET_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file (exists)"
    else
        echo "  ❌ $file (not found)"
    fi
done

echo ""
echo "⚠️  CRITICAL MOMENT: Git Restoration Test"
echo "This will trigger file restoration and potentially recreate empty files."
echo "Monitoring systems should capture the recreation event."
echo ""

read -p "Proceed with restoration test? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test cancelled."
    exit 0
fi

echo "🔄 Creating safety backup..."
git stash push -m "Before empty file restoration test - $(date)"

echo ""
echo "🚨 EXECUTING RESTORATION TEST..."
echo "Timestamp: $(date)"

# Method 1: Restore specific files from HEAD
echo "Method 1: Restoring files from HEAD..."
for file in "${TARGET_FILES[@]}"; do
    if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
        echo "  Restoring: $file"
        git checkout HEAD -- "$file" 2>/dev/null || echo "  Failed to restore: $file"
    fi
done

echo "Waiting 15 seconds for potential file recreation..."
sleep 15

echo ""
echo "📊 Checking for empty files after restoration..."
NEW_EMPTY=$(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
echo "Empty files now: $NEW_EMPTY"

if [[ $NEW_EMPTY -gt $CURRENT_EMPTY ]]; then
    echo "🚨 NEW EMPTY FILES DETECTED!"
    echo "Empty files created during test:"
    find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 "
    echo ""
    echo "🎯 RECREATION EVENT CAPTURED!"
    echo "Check monitoring logs for the culprit process."
else
    echo "No new empty files detected from Method 1."
fi

echo ""
echo "Method 2: Clean untracked files..."
# This might trigger recreation if the process is monitoring for missing files
git clean -n -f "*.md" "*.py" 2>/dev/null | head -5

echo "Waiting 15 seconds for potential file recreation..."
sleep 15

echo ""
echo "📊 Final empty file check..."
FINAL_EMPTY=$(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
echo "Final empty files: $FINAL_EMPTY"

if [[ $FINAL_EMPTY -gt $CURRENT_EMPTY ]]; then
    echo "🚨 EMPTY FILE RECREATION CONFIRMED!"
    echo "Net new empty files: $((FINAL_EMPTY - CURRENT_EMPTY))"
    echo ""
    echo "📋 Investigation Results:"
    echo "  - Original empty files: $CURRENT_EMPTY"
    echo "  - After Method 1: $NEW_EMPTY"
    echo "  - Final count: $FINAL_EMPTY"
    echo "  - Recreation detected: YES"
    echo ""
    echo "🔍 Check the monitoring evidence for:"
    echo "  - Process IDs that created the files"
    echo "  - Extension activities during recreation"
    echo "  - File system events and timestamps"
    echo "  - Memory usage patterns"
    echo ""
    echo "🛑 Recommendation: Stop monitoring to analyze evidence"
    echo "   Run: $SCRIPT_DIR/stop_monitoring.sh"
else
    echo "No recreation detected in this test run."
    echo "This could mean:"
    echo "  - The trigger conditions weren't met"
    echo "  - The process isn't currently active"
    echo "  - Different restoration method needed"
fi

echo ""
echo "🏁 Restoration test complete"
echo "Timestamp: $(date)"
echo ""
echo "📊 Test Summary:"
echo "  - Test started: $(date)"
echo "  - Repository: $REPO_PATH"
echo "  - Initial empty files: $CURRENT_EMPTY"
echo "  - Final empty files: $FINAL_EMPTY"
echo "  - Recreation detected: $([[ $FINAL_EMPTY -gt $CURRENT_EMPTY ]] && echo "YES" || echo "NO")"
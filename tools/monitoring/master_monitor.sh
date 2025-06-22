#!/bin/bash

# Master Monitor Script for Empty File Investigation
# This orchestrates all monitoring scripts for the Git restoration test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVIDENCE_DIR="${SCRIPT_DIR}/evidence_$(date +%Y%m%d_%H%M%S)"
REPO_PATH="${REPO_PATH:-$(git rev-parse --show-toplevel)}"

echo "🕵️ Starting Master Monitor for Empty File Investigation"
echo "Evidence Directory: $EVIDENCE_DIR"
echo "Repository Path: $REPO_PATH"
echo "Timestamp: $(date)"

# Create evidence directory
mkdir -p "$EVIDENCE_DIR"

# Create monitoring log
MASTER_LOG="${EVIDENCE_DIR}/master_monitor.log"
echo "=== Master Monitor Started ===" > "$MASTER_LOG"
echo "Timestamp: $(date)" >> "$MASTER_LOG"
echo "Repository: $REPO_PATH" >> "$MASTER_LOG"
echo "Evidence Directory: $EVIDENCE_DIR" >> "$MASTER_LOG"
echo "" >> "$MASTER_LOG"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping all monitoring processes..."
    echo "=== Master Monitor Cleanup Started ===" >> "$MASTER_LOG"
    echo "Timestamp: $(date)" >> "$MASTER_LOG"
    
    # Kill all background monitoring processes
    if [[ -f "${EVIDENCE_DIR}/monitor_pids.txt" ]]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "Stopping process $pid" >> "$MASTER_LOG"
                kill "$pid" 2>/dev/null || true
            fi
        done < "${EVIDENCE_DIR}/monitor_pids.txt"
    fi
    
    echo "=== Master Monitor Cleanup Complete ===" >> "$MASTER_LOG"
    echo "Evidence collected in: $EVIDENCE_DIR"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Store PIDs for cleanup
PID_FILE="${EVIDENCE_DIR}/monitor_pids.txt"
touch "$PID_FILE"

echo "🔍 Starting file system monitor..."
"$SCRIPT_DIR/file_creation_monitor.sh" "$REPO_PATH" "$EVIDENCE_DIR" &
echo $! >> "$PID_FILE"
echo "File creation monitor PID: $!" >> "$MASTER_LOG"

echo "📊 Starting process activity monitor..."
"$SCRIPT_DIR/process_activity_monitor.sh" "$EVIDENCE_DIR" &
echo $! >> "$PID_FILE"
echo "Process activity monitor PID: $!" >> "$MASTER_LOG"

echo "🔌 Starting extension activity tracker..."
"$SCRIPT_DIR/extension_activity_tracker.sh" "$EVIDENCE_DIR" &
echo $! >> "$PID_FILE"
echo "Extension activity tracker PID: $!" >> "$MASTER_LOG"

echo "📸 Capturing initial Git state..."
"$SCRIPT_DIR/git_state_capture.sh" "$REPO_PATH" "$EVIDENCE_DIR" "before"

echo ""
echo "🚀 All monitoring systems active!"
echo "📁 Evidence being collected in: $EVIDENCE_DIR"
echo ""
echo "🔬 READY FOR GIT RESTORATION TEST"
echo "Run the following command in another terminal to trigger recreation:"
echo "cd $REPO_PATH"
echo "git checkout HEAD -- copilot_context_theory.md test.py workspace_analyzer_enhanced.py compare_folders.py"
echo ""
echo "Press Ctrl+C to stop monitoring and collect evidence..."

# Wait for user to stop monitoring
while true; do
    sleep 5
    
    # Check if empty files were created
    EMPTY_FILES=$(find "$REPO_PATH" -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
    if [[ $EMPTY_FILES -gt 0 ]]; then
        echo "🚨 EMPTY FILES DETECTED! Count: $EMPTY_FILES" | tee -a "$MASTER_LOG"
        echo "Timestamp: $(date)" >> "$MASTER_LOG"
        
        # Capture immediate post-creation state
        echo "📸 Capturing post-creation Git state..."
        "$SCRIPT_DIR/git_state_capture.sh" "$REPO_PATH" "$EVIDENCE_DIR" "after_creation"
        
        echo "🎯 Recreation event captured! Monitoring will continue for 30 more seconds..."
        sleep 30
        break
    fi
done

echo "🏁 Monitoring complete. Evidence package ready for analysis."
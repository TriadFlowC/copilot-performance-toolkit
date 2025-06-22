#!/bin/bash

# Process Activity Monitor for VS Code and Related Processes
# Tracks VS Code process activities and memory usage patterns

EVIDENCE_DIR="$1"

if [[ -z "$EVIDENCE_DIR" ]]; then
    echo "Usage: $0 <evidence_dir>"
    exit 1
fi

LOG_FILE="${EVIDENCE_DIR}/process_activity_monitor.log"
MEMORY_LOG="${EVIDENCE_DIR}/memory_usage.log"

echo "📊 Starting VS Code process activity monitor..."
echo "Evidence Directory: $EVIDENCE_DIR"
echo "Timestamp: $(date)"

# Initialize log files
echo "=== Process Activity Monitor Started ===" > "$LOG_FILE"
echo "Timestamp: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "=== Memory Usage Monitor Started ===" > "$MEMORY_LOG"
echo "Timestamp: $(date)" >> "$MEMORY_LOG"
echo "" >> "$MEMORY_LOG"

# Track empty files state
LAST_EMPTY_FILES="${EVIDENCE_DIR}/last_empty_files.txt"
touch "$LAST_EMPTY_FILES"

while true; do
    CURRENT_TIME=$(date)
    
    # Log VS Code processes every 30 seconds
    echo "[$CURRENT_TIME] VS Code Processes:" >> "$LOG_FILE"
    
    # Get VS Code related processes
    VSCODE_PROCESSES=$(ps aux | grep -E "(code|copilot|vscode)" | grep -v grep)
    
    if [[ -n "$VSCODE_PROCESSES" ]]; then
        echo "$VSCODE_PROCESSES" >> "$LOG_FILE"
        
        # Extract memory usage for key processes
        echo "[$CURRENT_TIME] Memory Usage Summary:" >> "$MEMORY_LOG"
        echo "$VSCODE_PROCESSES" | while read -r line; do
            # Extract memory percentage and process info
            MEM_PERCENT=$(echo "$line" | awk '{print $4}')
            PROCESS_NAME=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
            echo "  $MEM_PERCENT% - $PROCESS_NAME" >> "$MEMORY_LOG"
        done
        echo "" >> "$MEMORY_LOG"
    else
        echo "No VS Code processes found" >> "$LOG_FILE"
        echo "[$CURRENT_TIME] No VS Code processes found" >> "$MEMORY_LOG"
    fi
    
    echo "---" >> "$LOG_FILE"
    
    # Check for new empty files every 10 seconds
    REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
    CURRENT_EMPTY_FILES="${EVIDENCE_DIR}/current_empty_files.txt"
    
    find "$REPO_PATH" -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " > "$CURRENT_EMPTY_FILES" 2>/dev/null || touch "$CURRENT_EMPTY_FILES"
    
    if ! cmp -s "$CURRENT_EMPTY_FILES" "$LAST_EMPTY_FILES" 2>/dev/null; then
        echo "🚨 [$CURRENT_TIME] NEW EMPTY FILES DETECTED!" >> "$LOG_FILE"
        echo "Previous empty files:" >> "$LOG_FILE"
        cat "$LAST_EMPTY_FILES" >> "$LOG_FILE" 2>/dev/null || echo "None" >> "$LOG_FILE"
        echo "Current empty files:" >> "$LOG_FILE"
        cat "$CURRENT_EMPTY_FILES" >> "$LOG_FILE"
        echo "Difference:" >> "$LOG_FILE"
        diff "$LAST_EMPTY_FILES" "$CURRENT_EMPTY_FILES" >> "$LOG_FILE" 2>/dev/null || echo "Files differ" >> "$LOG_FILE"
        
        # Capture detailed process state at time of empty file detection
        echo "Process state at empty file detection:" >> "$LOG_FILE"
        ps aux | grep -E "(code|copilot|vscode)" | grep -v grep >> "$LOG_FILE"
        
        # Check what processes have the empty files open
        echo "Processes with empty files open:" >> "$LOG_FILE"
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                FILE_PATH=$(echo "$line" | awk '{print $2}')
                if [[ -f "$FILE_PATH" ]]; then
                    echo "Checking $FILE_PATH:" >> "$LOG_FILE"
                    lsof "$FILE_PATH" 2>/dev/null >> "$LOG_FILE" || echo "  No processes have file open" >> "$LOG_FILE"
                fi
            fi
        done < "$CURRENT_EMPTY_FILES"
        
        echo "=== End Empty File Detection Event ===" >> "$LOG_FILE"
        
        # Update last known state
        cp "$CURRENT_EMPTY_FILES" "$LAST_EMPTY_FILES"
    fi
    
    sleep 10
done
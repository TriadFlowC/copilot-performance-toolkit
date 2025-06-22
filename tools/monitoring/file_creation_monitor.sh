#!/bin/bash

# Real-time File System Monitor for Empty File Creation
# Monitors file creation events and identifies empty files

REPO_PATH="$1"
EVIDENCE_DIR="$2"

if [[ -z "$REPO_PATH" || -z "$EVIDENCE_DIR" ]]; then
    echo "Usage: $0 <repo_path> <evidence_dir>"
    exit 1
fi

LOG_FILE="${EVIDENCE_DIR}/file_creation_monitor.log"

echo "🔍 Starting file system monitor for empty file creation..."
echo "Monitoring: $REPO_PATH"
echo "Timestamp: $(date)"
echo "Log file: $LOG_FILE"

# Initialize log file
echo "=== File Creation Monitor Started ===" > "$LOG_FILE"
echo "Timestamp: $(date)" >> "$LOG_FILE"
echo "Monitoring Path: $REPO_PATH" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Function to check if fswatch is available
check_fswatch() {
    if command -v fswatch >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to monitor using fswatch (macOS)
monitor_with_fswatch() {
    echo "Using fswatch for file system monitoring" >> "$LOG_FILE"
    
    fswatch -0 "$REPO_PATH" | while read -d "" event; do
        if [[ "$event" =~ \.(md|py)$ ]]; then
            echo "[$(date)] FILE EVENT: $event" | tee -a "$LOG_FILE"
            
            # Check if file exists and is empty
            if [[ -f "$event" ]] && [[ ! -s "$event" ]]; then
                echo "🚨 EMPTY FILE CREATED: $event" | tee -a "$LOG_FILE"
                echo "Process list at time of creation:" >> "$LOG_FILE"
                ps aux | grep -E "(code|copilot|vscode)" | head -10 >> "$LOG_FILE"
                echo "Files open by processes:" >> "$LOG_FILE"
                lsof "$event" 2>/dev/null >> "$LOG_FILE" || echo "No processes have file open yet" >> "$LOG_FILE"
                echo "File details:" >> "$LOG_FILE"
                stat "$event" >> "$LOG_FILE" 2>/dev/null || true
                echo "---" >> "$LOG_FILE"
                
                # Also log to main evidence file
                echo "[$(date)] EMPTY FILE ALERT: $event" >> "${EVIDENCE_DIR}/empty_file_alerts.log"
            fi
        fi
    done
}

# Function to monitor using polling (Linux/fallback)
monitor_with_polling() {
    echo "Using polling for file system monitoring" >> "$LOG_FILE"
    
    # Create baseline file list
    BASELINE_FILE="${EVIDENCE_DIR}/baseline_files.txt"
    find "$REPO_PATH" -name "*.md" -o -name "*.py" > "$BASELINE_FILE"
    
    while true; do
        # Check for new files
        CURRENT_FILES="${EVIDENCE_DIR}/current_files.txt"
        find "$REPO_PATH" -name "*.md" -o -name "*.py" > "$CURRENT_FILES"
        
        # Find new files
        NEW_FILES=$(comm -13 <(sort "$BASELINE_FILE") <(sort "$CURRENT_FILES"))
        
        if [[ -n "$NEW_FILES" ]]; then
            echo "[$(date)] NEW FILES DETECTED:" | tee -a "$LOG_FILE"
            echo "$NEW_FILES" | tee -a "$LOG_FILE"
            
            # Check each new file for emptiness
            while IFS= read -r file; do
                if [[ -f "$file" ]] && [[ ! -s "$file" ]]; then
                    echo "🚨 NEW EMPTY FILE: $file" | tee -a "$LOG_FILE"
                    echo "Process list at time of detection:" >> "$LOG_FILE"
                    ps aux | grep -E "(code|copilot|vscode)" | head -10 >> "$LOG_FILE"
                    echo "Files open by processes:" >> "$LOG_FILE"
                    lsof "$file" 2>/dev/null >> "$LOG_FILE" || echo "No processes have file open yet" >> "$LOG_FILE"
                    echo "File details:" >> "$LOG_FILE"
                    stat "$file" >> "$LOG_FILE" 2>/dev/null || true
                    echo "---" >> "$LOG_FILE"
                    
                    # Also log to main evidence file
                    echo "[$(date)] EMPTY FILE ALERT: $file" >> "${EVIDENCE_DIR}/empty_file_alerts.log"
                fi
            done <<< "$NEW_FILES"
            
            # Update baseline
            cp "$CURRENT_FILES" "$BASELINE_FILE"
        fi
        
        # Also check existing files for changes to empty
        while IFS= read -r file; do
            if [[ -f "$file" ]] && [[ ! -s "$file" ]]; then
                # Check if this file was previously non-empty
                if ! grep -q "EMPTY FILE ALERT: $file" "${EVIDENCE_DIR}/empty_file_alerts.log" 2>/dev/null; then
                    echo "🚨 FILE BECAME EMPTY: $file" | tee -a "$LOG_FILE"
                    echo "[$(date)] FILE BECAME EMPTY: $file" >> "${EVIDENCE_DIR}/empty_file_alerts.log"
                fi
            fi
        done < "$CURRENT_FILES"
        
        sleep 2
    done
}

# Start monitoring
if check_fswatch; then
    monitor_with_fswatch
else
    echo "fswatch not available, falling back to polling method"
    monitor_with_polling
fi
#!/bin/bash

# VS Code Extension Activity Tracker
# Monitors VS Code extension logs and activities

EVIDENCE_DIR="$1"

if [[ -z "$EVIDENCE_DIR" ]]; then
    echo "Usage: $0 <evidence_dir>"
    exit 1
fi

LOG_FILE="${EVIDENCE_DIR}/extension_activity_tracker.log"

echo "🔌 Starting VS Code extension activity tracker..."
echo "Evidence Directory: $EVIDENCE_DIR"
echo "Timestamp: $(date)"

# Initialize log file
echo "=== Extension Activity Tracker Started ===" > "$LOG_FILE"
echo "Timestamp: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Function to monitor VS Code logs
monitor_vscode_logs() {
    # Common VS Code log locations
    VSCODE_LOGS_DIRS=(
        "$HOME/Library/Application Support/Code/logs"
        "$HOME/.config/Code/logs"
        "$HOME/AppData/Roaming/Code/logs"
    )
    
    for log_dir in "${VSCODE_LOGS_DIRS[@]}"; do
        if [[ -d "$log_dir" ]]; then
            echo "Found VS Code logs directory: $log_dir" >> "$LOG_FILE"
            
            # Find the most recent log directory
            LATEST_LOG_DIR=$(find "$log_dir" -type d -name "2*" | sort | tail -1)
            
            if [[ -d "$LATEST_LOG_DIR" ]]; then
                echo "Monitoring latest log directory: $LATEST_LOG_DIR" >> "$LOG_FILE"
                
                # Monitor main.log if it exists
                MAIN_LOG="$LATEST_LOG_DIR/main.log"
                if [[ -f "$MAIN_LOG" ]]; then
                    echo "Monitoring main.log: $MAIN_LOG" >> "$LOG_FILE"
                    tail -f "$MAIN_LOG" 2>/dev/null | while read -r line; do
                        if [[ "$line" =~ (copilot|file|create|write|workspace|github) ]]; then
                            echo "[$(date)] VS Code Main Log: $line" >> "$LOG_FILE"
                        fi
                    done &
                fi
                
                # Monitor extension host logs
                find "$LATEST_LOG_DIR" -name "*extensionHost*" -type f | while read -r ext_log; do
                    echo "Monitoring extension host log: $ext_log" >> "$LOG_FILE"
                    tail -f "$ext_log" 2>/dev/null | while read -r line; do
                        if [[ "$line" =~ (copilot|file|create|write|workspace|github) ]]; then
                            echo "[$(date)] Extension Host Log: $line" >> "$LOG_FILE"
                        fi
                    done &
                done
            fi
            break
        fi
    done
}

# Function to monitor system logs for VS Code
monitor_system_logs() {
    # Monitor system logs for VS Code activity (macOS)
    if command -v log >/dev/null 2>&1; then
        echo "Starting macOS system log monitoring" >> "$LOG_FILE"
        log stream --predicate 'processImagePath contains "Code"' --info 2>/dev/null | while read -r line; do
            if [[ "$line" =~ (file|create|write|workspace|copilot) ]]; then
                echo "[$(date)] System Log: $line" >> "$LOG_FILE"
            fi
        done &
    fi
    
    # Monitor system logs for VS Code activity (Linux)
    if command -v journalctl >/dev/null 2>&1; then
        echo "Starting Linux system log monitoring" >> "$LOG_FILE"
        journalctl -f -u code 2>/dev/null | while read -r line; do
            if [[ "$line" =~ (file|create|write|workspace|copilot) ]]; then
                echo "[$(date)] System Log: $line" >> "$LOG_FILE"
            fi
        done &
    fi
}

# Function to monitor Copilot specific activities
monitor_copilot_activity() {
    echo "Starting Copilot activity monitoring" >> "$LOG_FILE"
    
    # Monitor Copilot cache/config directories
    COPILOT_DIRS=(
        "$HOME/.config/github-copilot"
        "$HOME/Library/Application Support/github-copilot"
        "$HOME/.vscode/extensions/github.copilot*"
    )
    
    for copilot_dir in "${COPILOT_DIRS[@]}"; do
        if [[ -d "$copilot_dir" ]]; then
            echo "Monitoring Copilot directory: $copilot_dir" >> "$LOG_FILE"
            
            # Monitor for file changes in Copilot directories
            if command -v fswatch >/dev/null 2>&1; then
                fswatch -0 "$copilot_dir" 2>/dev/null | while read -d "" event; do
                    echo "[$(date)] Copilot Activity: $event" >> "$LOG_FILE"
                done &
            fi
        fi
    done
}

# Function to monitor process creation
monitor_process_creation() {
    echo "Starting process creation monitoring" >> "$LOG_FILE"
    
    while true; do
        # Check for new VS Code processes
        CURRENT_PROCESSES=$(pgrep -f "code" 2>/dev/null | sort)
        
        if [[ -f "${EVIDENCE_DIR}/last_processes.txt" ]]; then
            NEW_PROCESSES=$(comm -13 "${EVIDENCE_DIR}/last_processes.txt" <(echo "$CURRENT_PROCESSES"))
            
            if [[ -n "$NEW_PROCESSES" ]]; then
                echo "[$(date)] NEW VS CODE PROCESSES DETECTED:" >> "$LOG_FILE"
                echo "$NEW_PROCESSES" | while read -r pid; do
                    if [[ -n "$pid" ]]; then
                        PROCESS_INFO=$(ps -p "$pid" -o pid,ppid,cmd 2>/dev/null)
                        echo "  PID $pid: $PROCESS_INFO" >> "$LOG_FILE"
                    fi
                done
            fi
        fi
        
        echo "$CURRENT_PROCESSES" > "${EVIDENCE_DIR}/last_processes.txt"
        sleep 5
    done &
}

# Start all monitoring functions
echo "Starting VS Code log monitoring..." >> "$LOG_FILE"
monitor_vscode_logs

echo "Starting system log monitoring..." >> "$LOG_FILE"
monitor_system_logs

echo "Starting Copilot activity monitoring..." >> "$LOG_FILE"
monitor_copilot_activity

echo "Starting process creation monitoring..." >> "$LOG_FILE"
monitor_process_creation

echo "All extension monitoring started" >> "$LOG_FILE"

# Keep the script running
while true; do
    sleep 60
    echo "[$(date)] Extension activity tracker heartbeat" >> "$LOG_FILE"
done
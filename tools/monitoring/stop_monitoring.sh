#!/bin/bash

# Stop Monitoring Script
# Cleanly stops all monitoring processes and packages evidence

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 Stopping all monitoring processes..."

# Find all evidence directories from today
EVIDENCE_DIRS=$(find "$SCRIPT_DIR" -name "evidence_*" -type d -newermt "$(date '+%Y-%m-%d')" 2>/dev/null)

if [[ -z "$EVIDENCE_DIRS" ]]; then
    echo "No active evidence directories found"
    exit 1
fi

# Stop processes for each evidence directory
echo "$EVIDENCE_DIRS" | while read -r evidence_dir; do
    if [[ -d "$evidence_dir" ]]; then
        echo "Processing evidence directory: $evidence_dir"
        
        PID_FILE="$evidence_dir/monitor_pids.txt"
        if [[ -f "$PID_FILE" ]]; then
            echo "Stopping monitoring processes..."
            while read -r pid; do
                if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                    echo "  Stopping process $pid"
                    kill "$pid" 2>/dev/null || true
                    sleep 1
                    # Force kill if still running
                    if kill -0 "$pid" 2>/dev/null; then
                        echo "  Force stopping process $pid"
                        kill -9 "$pid" 2>/dev/null || true
                    fi
                fi
            done < "$PID_FILE"
        fi
        
        # Create final evidence package
        echo "Creating evidence package..."
        PACKAGE_NAME="evidence_package_$(date +%Y%m%d_%H%M%S).tar.gz"
        
        cd "$(dirname "$evidence_dir")" || continue
        tar -czf "$PACKAGE_NAME" "$(basename "$evidence_dir")"
        
        echo "Evidence package created: $(pwd)/$PACKAGE_NAME"
        
        # Create analysis summary
        SUMMARY_FILE="$evidence_dir/investigation_summary.txt"
        {
            echo "=== Empty File Investigation Summary ==="
            echo "Timestamp: $(date)"
            echo "Evidence Directory: $evidence_dir"
            echo ""
            
            echo "=== Monitoring Duration ==="
            if [[ -f "$evidence_dir/master_monitor.log" ]]; then
                START_TIME=$(head -3 "$evidence_dir/master_monitor.log" | grep "Timestamp:" | head -1)
                echo "Start: $START_TIME"
            fi
            echo "End: $(date)"
            echo ""
            
            echo "=== Files Generated ==="
            ls -la "$evidence_dir"
            echo ""
            
            echo "=== Empty File Alerts ==="
            if [[ -f "$evidence_dir/empty_file_alerts.log" ]]; then
                cat "$evidence_dir/empty_file_alerts.log"
            else
                echo "No empty file alerts recorded"
            fi
            echo ""
            
            echo "=== Process Activity Summary ==="
            if [[ -f "$evidence_dir/process_activity_monitor.log" ]]; then
                grep "EMPTY FILES DETECTED" "$evidence_dir/process_activity_monitor.log" | tail -5
            else
                echo "No process activity recorded"
            fi
            echo ""
            
            echo "=== Extension Activity Summary ==="
            if [[ -f "$evidence_dir/extension_activity_tracker.log" ]]; then
                grep -i "copilot" "$evidence_dir/extension_activity_tracker.log" | tail -5
            else
                echo "No extension activity recorded"
            fi
            echo ""
            
        } > "$SUMMARY_FILE"
        
        echo "Investigation summary created: $SUMMARY_FILE"
        echo ""
        echo "📊 EVIDENCE COLLECTION COMPLETE"
        echo "📁 Evidence Directory: $evidence_dir"
        echo "📦 Evidence Package: $(pwd)/$PACKAGE_NAME"
        echo "📋 Summary Report: $SUMMARY_FILE"
        echo ""
    fi
done

echo "🏁 All monitoring stopped and evidence packaged"
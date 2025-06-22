#!/bin/bash

# Forensic Evidence Collector
# Collects comprehensive evidence about the current state of empty files

set -e

REPO_PATH="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
FORENSICS_DIR="$REPO_PATH/forensics"
EVIDENCE_DIR="$FORENSICS_DIR/evidence_$(date +%Y%m%d_%H%M%S)"

echo "🕵️ Forensic Evidence Collector for Empty File Investigation"
echo "Repository: $REPO_PATH"
echo "Evidence Directory: $EVIDENCE_DIR"
echo "Timestamp: $(date)"

# Create forensics directory structure
mkdir -p "$EVIDENCE_DIR"
mkdir -p "$FORENSICS_DIR/analysis"

cd "$REPO_PATH"

echo ""
echo "📊 Collecting forensic evidence..."

# 1. File System Forensics
echo "🔍 Collecting file system forensics..."
OUTPUT_FILE="$EVIDENCE_DIR/file_forensics.txt"
{
    echo "=== File System Forensics ==="
    echo "Timestamp: $(date)"
    echo "Repository: $REPO_PATH"
    echo ""
    
    echo "=== All .md and .py files with detailed stat output ==="
    find . -name "*.md" -o -name "*.py" | while read -r file; do
        if [[ -f "$file" ]]; then
            echo "--- File: $file ---"
            stat "$file" 2>/dev/null || ls -la "$file"
            if [[ ! -s "$file" ]]; then
                echo "🚨 EMPTY FILE DETECTED: $file"
            fi
            echo ""
        fi
    done
    
} > "$OUTPUT_FILE"
echo "File forensics saved to: $OUTPUT_FILE"

# 2. Empty Files List
echo "🔍 Identifying all empty files..."
EMPTY_FILES_OUTPUT="$EVIDENCE_DIR/all_empty_files.txt"
{
    echo "=== All Empty Files in Project ==="
    echo "Timestamp: $(date)"
    echo ""
    
    find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " || echo "No empty files found"
    
} > "$EMPTY_FILES_OUTPUT"
echo "Empty files list saved to: $EMPTY_FILES_OUTPUT"

# 3. Process Analysis
echo "🔍 Analyzing running processes..."
PROCESSES_OUTPUT="$EVIDENCE_DIR/running_processes.txt"
{
    echo "=== Running Processes Analysis ==="
    echo "Timestamp: $(date)"
    echo ""
    
    echo "=== All VS Code and related processes ==="
    ps aux | grep -E "(code|copilot|vscode)" | grep -v grep || echo "No VS Code processes found"
    echo ""
    
    echo "=== Process tree ==="
    pstree 2>/dev/null || echo "pstree not available"
    echo ""
    
    echo "=== Memory usage by VS Code processes ==="
    ps aux | grep -E "(code|copilot|vscode)" | grep -v grep | awk '{print $4 "% " $11}' | sort -nr || echo "No memory usage data"
    
} > "$PROCESSES_OUTPUT"
echo "Process analysis saved to: $PROCESSES_OUTPUT"

# 4. Open Files Analysis
echo "🔍 Checking which processes have files open..."
OPEN_FILES_OUTPUT="$EVIDENCE_DIR/open_files.txt"
{
    echo "=== Open Files Analysis ==="
    echo "Timestamp: $(date)"
    echo ""
    
    echo "=== Processes with .md or .py files open ==="
    find . -name "*.md" -o -name "*.py" | head -20 | while read -r file; do
        if [[ -f "$file" ]]; then
            echo "--- Checking: $file ---"
            lsof "$file" 2>/dev/null || echo "No processes have $file open"
            echo ""
        fi
    done
    
} > "$OPEN_FILES_OUTPUT"
echo "Open files analysis saved to: $OPEN_FILES_OUTPUT"

# 5. System Logs
echo "🔍 Collecting recent system logs..."
SYSTEM_LOGS_OUTPUT="$EVIDENCE_DIR/system_logs.txt"
{
    echo "=== System Logs (Last 2 Hours) ==="
    echo "Timestamp: $(date)"
    echo ""
    
    # macOS logs
    if command -v log >/dev/null 2>&1; then
        echo "=== macOS Console Logs (VS Code related) ==="
        log show --predicate 'processImagePath contains "Code"' --info --last 2h 2>/dev/null | head -50 || echo "No macOS logs available"
        echo ""
    fi
    
    # Linux logs
    if command -v journalctl >/dev/null 2>&1; then
        echo "=== Linux System Logs (Last 2 hours) ==="
        journalctl --since "2 hours ago" | grep -i code | head -50 || echo "No Linux logs available"
        echo ""
    fi
    
    # General system information
    echo "=== System Information ==="
    uname -a
    echo ""
    
    echo "=== Disk Usage ==="
    df -h . || echo "Unable to get disk usage"
    echo ""
    
} > "$SYSTEM_LOGS_OUTPUT"
echo "System logs saved to: $SYSTEM_LOGS_OUTPUT"

# 6. Git Context
echo "🔍 Capturing Git context..."
GIT_STATUS_OUTPUT="$EVIDENCE_DIR/git_status.txt"
{
    echo "=== Git Status Analysis ==="
    echo "Timestamp: $(date)"
    echo ""
    
    echo "=== Current Git Status ==="
    git status
    echo ""
    
    echo "=== Recent Git History ==="
    git log --oneline -10
    echo ""
    
    echo "=== Git Configuration ==="
    git config --list --local
    echo ""
    
} > "$GIT_STATUS_OUTPUT"
echo "Git context saved to: $GIT_STATUS_OUTPUT"

# 7. Environment Information
echo "🔍 Collecting environment information..."
ENV_INFO_OUTPUT="$EVIDENCE_DIR/investigation_metadata.txt"
{
    echo "=== Investigation Metadata ==="
    echo "Timestamp: $(date)"
    echo "Investigator: Forensic Evidence Collector"
    echo "Repository: $REPO_PATH"
    echo "Evidence Directory: $EVIDENCE_DIR"
    echo ""
    
    echo "=== Environment Information ==="
    echo "Operating System: $(uname -s)"
    echo "Kernel Version: $(uname -r)"
    echo "Architecture: $(uname -m)"
    echo ""
    
    echo "=== VS Code Information ==="
    if command -v code >/dev/null 2>&1; then
        code --version 2>/dev/null || echo "VS Code version unavailable"
    else
        echo "VS Code command not found in PATH"
    fi
    echo ""
    
    echo "=== Shell Information ==="
    echo "Shell: $SHELL"
    echo "User: $USER"
    echo "Home: $HOME"
    echo ""
    
    echo "=== Investigation Scope ==="
    echo "Total .md files: $(find . -name "*.md" | wc -l)"
    echo "Total .py files: $(find . -name "*.py" | wc -l)"
    echo "Total empty files: $(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)"
    echo ""
    
} > "$ENV_INFO_OUTPUT"
echo "Environment information saved to: $ENV_INFO_OUTPUT"

# 8. Create investigation summary
echo "🔍 Creating investigation summary..."
SUMMARY_OUTPUT="$EVIDENCE_DIR/investigation_summary.txt"
{
    echo "=== Forensic Investigation Summary ==="
    echo "Generated: $(date)"
    echo "Repository: $REPO_PATH"
    echo ""
    
    echo "=== Key Findings ==="
    EMPTY_COUNT=$(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
    echo "Empty files detected: $EMPTY_COUNT"
    
    if [[ $EMPTY_COUNT -gt 0 ]]; then
        echo "🚨 EMPTY FILES FOUND:"
        find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | head -10
        echo ""
        
        echo "🔍 IDENTICAL TIMESTAMPS CHECK:"
        find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | while read -r line; do
            FILE=$(echo "$line" | awk '{print $2}')
            if [[ -f "$FILE" ]]; then
                stat -c "%y %n" "$FILE" 2>/dev/null || stat -f "%Sm %N" "$FILE" 2>/dev/null || echo "Cannot get timestamp for $FILE"
            fi
        done
    fi
    echo ""
    
    echo "=== VS Code Processes ==="
    VSCODE_PROCS=$(ps aux | grep -E "(code|copilot|vscode)" | grep -v grep | wc -l)
    echo "VS Code processes running: $VSCODE_PROCS"
    
    if [[ $VSCODE_PROCS -gt 0 ]]; then
        echo "Active VS Code processes:"
        ps aux | grep -E "(code|copilot|vscode)" | grep -v grep | head -5
    fi
    echo ""
    
    echo "=== Evidence Files Generated ==="
    ls -la "$EVIDENCE_DIR"
    echo ""
    
    echo "=== Next Steps ==="
    echo "1. Analyze file timestamps in file_forensics.txt"
    echo "2. Check process activity in running_processes.txt"
    echo "3. Review open files in open_files.txt"
    echo "4. If no empty files exist, set up monitoring for recreation"
    echo "5. If empty files exist, prepare for restoration test"
    echo ""
    
} > "$SUMMARY_OUTPUT"
echo "Investigation summary saved to: $SUMMARY_OUTPUT"

echo ""
echo "🎯 FORENSIC EVIDENCE COLLECTION COMPLETE"
echo ""
echo "📁 Evidence Directory: $EVIDENCE_DIR"
echo "📋 Summary Report: $SUMMARY_OUTPUT"
echo ""
echo "📊 Key Findings:"
EMPTY_COUNT=$(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)
echo "  - Empty files detected: $EMPTY_COUNT"
VSCODE_PROCS=$(ps aux | grep -E "(code|copilot|vscode)" | grep -v grep | wc -l)
echo "  - VS Code processes: $VSCODE_PROCS"
echo "  - Evidence files: $(ls "$EVIDENCE_DIR" | wc -l)"
echo ""

if [[ $EMPTY_COUNT -gt 0 ]]; then
    echo "🚨 EMPTY FILES DETECTED - Ready for analysis!"
    echo "🔬 Next step: Analyze evidence files to identify patterns"
    echo "🧪 Consider running restoration test to capture recreation"
else
    echo "✅ NO EMPTY FILES CURRENTLY - Ready for monitoring!"
    echo "🔬 Next step: Set up monitoring and trigger restoration test"
fi

echo ""
echo "🛠️  Available Tools:"
echo "  - Monitoring: $REPO_PATH/tools/monitoring/master_monitor.sh"
echo "  - Restoration Test: $REPO_PATH/tools/monitoring/restoration_test.sh"
echo "  - Stop Monitoring: $REPO_PATH/tools/monitoring/stop_monitoring.sh"
#!/bin/bash

# Git State Capture Script
# Captures complete git state before/after recreation events

REPO_PATH="$1"
EVIDENCE_DIR="$2"
SUFFIX="$3"

if [[ -z "$REPO_PATH" || -z "$EVIDENCE_DIR" || -z "$SUFFIX" ]]; then
    echo "Usage: $0 <repo_path> <evidence_dir> <suffix>"
    exit 1
fi

cd "$REPO_PATH" || exit 1

OUTPUT_FILE="${EVIDENCE_DIR}/git_state_${SUFFIX}.txt"

echo "📸 Capturing Git state: $SUFFIX"
echo "Repository: $REPO_PATH"
echo "Output: $OUTPUT_FILE"

# Capture comprehensive git state
{
    echo "=== Git State Capture: $SUFFIX ==="
    echo "Timestamp: $(date)"
    echo "Repository Path: $REPO_PATH"
    echo ""
    
    echo "=== Git Status ==="
    git status --porcelain
    echo ""
    
    echo "=== Git Status (Verbose) ==="
    git status
    echo ""
    
    echo "=== Git Log (Last 10 commits) ==="
    git log --oneline -10
    echo ""
    
    echo "=== Git Branch Information ==="
    git branch -v
    echo ""
    
    echo "=== Git Remote Information ==="
    git remote -v
    echo ""
    
    echo "=== File Timestamps and Sizes ==="
    find . -name "*.md" -o -name "*.py" | head -30 | while read -r file; do
        if [[ -f "$file" ]]; then
            stat "$file" 2>/dev/null || ls -la "$file"
        fi
    done
    echo ""
    
    echo "=== Empty Files Detection ==="
    find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " || echo "No empty files found"
    echo ""
    
    echo "=== Git Diff (Staged) ==="
    git diff --cached --name-only
    echo ""
    
    echo "=== Git Diff (Unstaged) ==="
    git diff --name-only
    echo ""
    
    echo "=== Git Diff HEAD ==="
    git diff HEAD --name-only
    echo ""
    
    echo "=== Working Directory File Count ==="
    find . -name "*.md" -o -name "*.py" | wc -l
    echo ""
    
    echo "=== Recently Modified Files (Last 10 minutes) ==="
    find . -name "*.md" -o -name "*.py" -newermt "$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || \
    find . -name "*.md" -o -name "*.py" -newer /tmp/10min_ago 2>/dev/null || \
    echo "Unable to determine recently modified files"
    echo ""
    
    echo "=== Git Index Status ==="
    git ls-files --stage | head -20
    echo ""
    
    echo "=== Git Configuration ==="
    git config --list --local
    echo ""
    
    echo "=== Directory Structure ==="
    find . -type d -name ".git" -prune -o -type d -print | head -20
    echo ""
    
    echo "=== File Permissions ==="
    find . -name "*.md" -o -name "*.py" | head -20 | xargs ls -la
    echo ""
    
} > "$OUTPUT_FILE"

echo "Git state captured successfully: $OUTPUT_FILE"

# Also create a summary file for quick reference
SUMMARY_FILE="${EVIDENCE_DIR}/git_summary_${SUFFIX}.txt"
{
    echo "=== Git State Summary: $SUFFIX ==="
    echo "Timestamp: $(date)"
    echo "Repository: $REPO_PATH"
    echo ""
    
    echo "Modified files:"
    git status --porcelain | head -10
    echo ""
    
    echo "Empty files:"
    find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | head -10 || echo "None"
    echo ""
    
    echo "Total .md files: $(find . -name "*.md" | wc -l)"
    echo "Total .py files: $(find . -name "*.py" | wc -l)"
    echo "Total empty files: $(find . -name "*.md" -o -name "*.py" | xargs wc -l 2>/dev/null | grep " 0 " | wc -l)"
    
} > "$SUMMARY_FILE"

echo "Git summary created: $SUMMARY_FILE"
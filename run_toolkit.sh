#!/bin/bash

echo "🛠️  Copilot Performance Toolkit"
echo "================================"
echo ""
echo "Available tools:"
echo "1. Memory Monitor          - python3 tools/test.py"
echo "2. Workspace Analyzer      - python3 tools/workspace_analyzer_enhanced.py"
echo "3. Folder Comparator       - python3 tools/compare_folders.py"
echo ""
echo "Quick commands:"
echo "  Monitor memory:          ./run_toolkit.sh monitor"
echo "  Analyze workspace:       ./run_toolkit.sh analyze [path]"
echo "  Compare folders:         ./run_toolkit.sh compare [path1] [path2]"
echo ""

case "$1" in
    monitor)
        echo "🔍 Starting memory monitor..."
        python3 tools/test.py --copilot-focused
        ;;
    analyze)
        path=${2:-.}
        echo "📊 Analyzing workspace: $path"
        python3 tools/workspace_analyzer_enhanced.py "$path"
        ;;
    compare)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Usage: ./run_toolkit.sh compare <folder1> <folder2>"
            exit 1
        fi
        echo "🔍 Comparing folders..."
        python3 tools/compare_folders.py "$2" "$3"
        ;;
    *)
        echo "For detailed usage, see README.md or individual tool help:"
        echo "  python3 tools/test.py --help"
        echo "  python3 tools/workspace_analyzer_enhanced.py --help"
        ;;
esac

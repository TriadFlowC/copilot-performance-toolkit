#!/usr/bin/env python3
"""
Demo script showing how to use the workspace analyzer
"""

import subprocess
import sys
from pathlib import Path

def run_demo():
    print("🎯 Workspace Analyzer Demo")
    print("=" * 50)
    
    # Show help
    print("📚 Available options:")
    result = subprocess.run([sys.executable, 'workspace_analyzer_enhanced.py', '--help'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    print("\n" + "=" * 50)
    print("📋 Usage Examples:")
    print("=" * 50)
    
    examples = [
        ("Analyze current directory:", 
         "python workspace_analyzer_enhanced.py"),
        
        ("Analyze specific repository:", 
         "python workspace_analyzer_enhanced.py /path/to/your/large/repo"),
        
        ("Dry run (analysis only, no files):", 
         "python workspace_analyzer_enhanced.py /path/to/repo --dry-run"),
        
        ("Custom file limits:", 
         "python workspace_analyzer_enhanced.py . --max-files 1000"),
        
        ("Lower risk threshold (more workspaces):", 
         "python workspace_analyzer_enhanced.py . --risk-threshold 30"),
        
        ("Custom output directory:", 
         "python workspace_analyzer_enhanced.py . --output-dir my_workspaces"),
        
        ("Verbose output:", 
         "python workspace_analyzer_enhanced.py . --verbose"),
    ]
    
    for description, command in examples:
        print(f"\n📌 {description}")
        print(f"   {command}")
    
    print("\n" + "=" * 50)
    print("🚀 Quick Start Guide:")
    print("=" * 50)
    
    print("""
1. 📂 Navigate to your large repository:
   cd /path/to/your/large/repo

2. 🔍 Run a dry-run analysis first:
   python /path/to/workspace_analyzer_enhanced.py . --dry-run

3. 📊 Review the analysis results and file counts

4. 💾 Generate workspace files:
   python /path/to/workspace_analyzer_enhanced.py .

5. 🧪 Test a workspace:
   code workspaces/workspace_1_*.code-workspace

6. 📈 Monitor memory usage:
   python /path/to/test.py --copilot-focused

7. 🎯 Compare before/after performance
""")
    
    print("\n💡 Pro Tips:")
    print("-" * 30)
    tips = [
        "Start with --dry-run to see what would be created",
        "Use --max-files 1000 for very large repositories",
        "Lower --risk-threshold creates more, smaller workspaces",
        "Each workspace gets optimized Copilot settings automatically",
        "Test the highest-risk workspaces first (🔥 icons)",
        "Use the memory monitoring script to validate improvements"
    ]
    
    for tip in tips:
        print(f"• {tip}")

if __name__ == "__main__":
    run_demo()

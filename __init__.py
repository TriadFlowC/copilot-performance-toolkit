"""
Copilot Performance Toolkit

A comprehensive toolkit for analyzing, understanding, and optimizing GitHub Copilot 
performance in large codebases.

This package provides:
- Memory monitoring tools for VS Code and Copilot
- Workspace boundary analysis and optimization
- Theoretical foundations for AI code assistant scaling
- Practical implementation guides and examples
"""

__version__ = "1.0.0"
__author__ = "Copilot Performance Research Team"

# Import main classes for easy access
try:
    from .tools.workspace_analyzer_enhanced import WorkspaceBoundaryAnalyzer
except ImportError:
    # Handle case where tools are in different directory structure
    pass

# Package metadata
__all__ = [
    "WorkspaceBoundaryAnalyzer",
]

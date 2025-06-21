#!/usr/bin/env python3
"""
Simple folder comparison script
Compares two folders recursively and lists different files
Respects .gitignore files to exclude ignored files
"""

import os
import sys
from pathlib import Path
import hashlib
import fnmatch

def load_gitignore_patterns(folder_path):
    """Load gitignore patterns from .gitignore files"""
    patterns = []
    folder_path = Path(folder_path)
    
    # Common patterns that are typically ignored
    default_patterns = [
        '__pycache__/',
        '*.pyc',
        '.DS_Store',
        '.git/',
        'node_modules/',
        '.env',
        '*.log',
        'dist/',
        'build/',
        '.vscode/',
        '.idea/',
        '*.tmp',
        '*.temp'
    ]
    patterns.extend(default_patterns)
    
    # Look for .gitignore files
    gitignore_path = folder_path / '.gitignore'
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except:
            pass
    
    return patterns

def is_ignored(file_path, patterns):
    """Check if a file should be ignored based on gitignore patterns"""
    file_path = str(file_path)
    
    for pattern in patterns:
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            if '/' in file_path:
                parts = file_path.split('/')
                if pattern in parts:
                    return True
        
        # Handle glob patterns
        if fnmatch.fnmatch(file_path, pattern):
            return True
        
        # Handle patterns with path separators
        if '/' in pattern:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        else:
            # Check if pattern matches any part of the path
            parts = file_path.split('/')
            if pattern in parts or any(fnmatch.fnmatch(part, pattern) for part in parts):
                return True
    
    return False

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def get_folder_files(folder_path):
    """Get all files in folder with their relative paths and hashes"""
    folder_path = Path(folder_path)
    files = {}
    
    # Load gitignore patterns for this folder
    patterns = load_gitignore_patterns(folder_path)
    
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(folder_path)
            
            # Skip ignored files
            if is_ignored(rel_path, patterns):
                continue
                
            file_hash = get_file_hash(file_path)
            files[str(rel_path)] = file_hash
    
    return files

def compare_folders(folder1, folder2):
    """Compare two folders and return differences"""
    print(f"Comparing:")
    print(f"  Folder 1: {folder1}")
    print(f"  Folder 2: {folder2}")
    print("-" * 50)
    
    files1 = get_folder_files(folder1)
    files2 = get_folder_files(folder2)
    
    all_files = set(files1.keys()) | set(files2.keys())
    
    only_in_1 = []
    only_in_2 = []
    different = []
    
    for file_path in sorted(all_files):
        if file_path in files1 and file_path in files2:
            # File exists in both, check if content is different
            if files1[file_path] != files2[file_path]:
                different.append(file_path)
        elif file_path in files1:
            only_in_1.append(file_path)
        else:
            only_in_2.append(file_path)
    
    # Print results
    if only_in_1:
        print(f"Only in {Path(folder1).name}:")
        for file_path in only_in_1:
            print(f"  {file_path}")
        print()
    
    if only_in_2:
        print(f"Only in {Path(folder2).name}:")
        for file_path in only_in_2:
            print(f"  {file_path}")
        print()
    
    if different:
        print("Different content:")
        for file_path in different:
            print(f"  {file_path}")
        print()
    
    if not (only_in_1 or only_in_2 or different):
        print("✅ Folders are identical")
    else:
        total_diffs = len(only_in_1) + len(only_in_2) + len(different)
        print(f"📊 Summary: {total_diffs} differences found")

def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_folders.py <folder1> <folder2>")
        sys.exit(1)
    
    folder1 = sys.argv[1]
    folder2 = sys.argv[2]
    
    # Validate folders exist
    if not os.path.isdir(folder1):
        print(f"Error: '{folder1}' is not a directory")
        sys.exit(1)
    
    if not os.path.isdir(folder2):
        print(f"Error: '{folder2}' is not a directory")
        sys.exit(1)
    
    compare_folders(folder1, folder2)

if __name__ == "__main__":
    main()

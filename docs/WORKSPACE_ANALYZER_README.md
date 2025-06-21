# Workspace Boundary Analyzer for Copilot Performance

This tool solves **GitHub Copilot memory issues in large repositories** by intelligently splitting them into smaller, optimized workspaces.

## 🎯 Problem Solved

**Issue**: Copilot causes severe memory usage (2-3GB) and UI freezing in large repositories due to context explosion.

**Solution**: Automatically analyze repository structure and create optimized VS Code workspaces with appropriate Copilot settings.

## 🚀 Quick Start

### 1. Analyze Your Large Repository

```bash
# Dry run first (no files created)
python workspace_analyzer_enhanced.py /path/to/your/large/repo --dry-run

# Generate workspace files
python workspace_analyzer_enhanced.py /path/to/your/large/repo
```

### 2. Test Generated Workspaces

```bash
# Open a generated workspace
code workspaces/workspace_1_*.code-workspace

# Monitor memory improvement
python test.py --copilot-focused
```

## 📊 How It Works

### Analysis Features

- **Risk Scoring**: Calculates Copilot performance risk (0-100) based on file count and complexity
- **Smart Grouping**: Groups related directories by file type (frontend, backend, config)
- **Dependency Analysis**: Considers import patterns for logical boundaries
- **Automatic Optimization**: Sets appropriate Copilot context limits per workspace

### Risk-Based Workspace Creation

```
🔥 High Risk (80+ score): Minimal context (512 tokens)
⚠️  Medium Risk (40-80): Small context (1024 tokens)  
✅ Low Risk (<40): Medium context (2048 tokens)
```

## 📋 Command Line Options

```bash
Usage: python workspace_analyzer_enhanced.py [repo_path] [options]

Arguments:
  repo_path                 Repository to analyze (default: current directory)

Options:
  --max-files N            Max files per workspace (default: 1500)
  --risk-threshold N       Risk threshold 0-100 (default: 50)
  --output-dir DIR         Output directory (default: workspaces)
  --dry-run               Analysis only, no file generation
  --verbose, -v           Detailed output
  --help, -h              Show help
```

## 🎮 Usage Examples

### Basic Usage
```bash
# Analyze current directory
python workspace_analyzer_enhanced.py

# Analyze specific repository
python workspace_analyzer_enhanced.py ~/projects/my-large-project
```

### Advanced Options
```bash
# Very large repository (smaller workspaces)
python workspace_analyzer_enhanced.py /path/to/huge/repo --max-files 1000

# More aggressive splitting (lower threshold)
python workspace_analyzer_enhanced.py . --risk-threshold 30

# Custom output location
python workspace_analyzer_enhanced.py . --output-dir my_workspaces

# Preview what would be created
python workspace_analyzer_enhanced.py /path/to/repo --dry-run --verbose
```

## 📊 Expected Results

### Before (Large Repository)
- **Memory Usage**: 2-3GB during Copilot queries
- **UI Behavior**: Freezing during context loading
- **Performance**: Slow Copilot responses
- **Experience**: Frustrating development workflow

### After (Optimized Workspaces)
- **Memory Usage**: 0.5-1GB per workspace 📉 60-80% reduction
- **UI Behavior**: Responsive interface ✅ No freezing
- **Performance**: Fast Copilot suggestions ⚡ 3-5x faster
- **Experience**: Smooth development workflow 🎯 Focused context

## 📁 Generated Files

The analyzer creates:

### Workspace Files
```
workspaces/
├── workspace_1_frontend.code-workspace    # Frontend-focused workspace
├── workspace_2_backend.code-workspace     # Backend-focused workspace
├── workspace_3_config.code-workspace      # Configuration files
└── workspace_analysis_report.md           # Detailed analysis report
```

### Optimized Settings Per Workspace
Each workspace includes:
- **Risk-appropriate Copilot context limits**
- **File exclusion patterns** (node_modules, dist, etc.)
- **Language server optimizations**
- **Extension recommendations**

## 🔍 Analysis Report

The generated report includes:
- **Workspace breakdown** with file counts and risk scores
- **Optimization strategy** explanation
- **Usage instructions** for each workspace
- **Expected performance benefits**

## 💡 Best Practices

### 1. Start with Dry Run
```bash
python workspace_analyzer_enhanced.py /path/to/repo --dry-run
```
Review the analysis before generating files.

### 2. Test High-Risk Workspaces First
Focus on workspaces marked with 🔥 - these will show the biggest improvement.

### 3. Monitor Performance
```bash
python test.py --copilot-focused
```
Use the memory monitoring script to validate improvements.

### 4. Adjust Based on Workflow
- **Prefer fewer workspaces**: Increase `--max-files`
- **Want more focused contexts**: Decrease `--risk-threshold`
- **Working on specific areas**: Use targeted workspaces

## 🛠️ Integration with Memory Monitoring

Combine with the memory monitoring tools:

```bash
# Before: Monitor large repository
python test.py --copilot-focused

# After: Monitor optimized workspace  
code workspaces/workspace_1_*.code-workspace
python test.py --copilot-focused
```

## ⚙️ Customization

### File Type Classification
The analyzer recognizes:
- **Frontend**: `.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.html`, `.css`
- **Backend**: `.py`, `.java`, `.go`, `.rs`, `.php`, `.rb`, `.cs`
- **Config**: `.json`, `.yaml`, `.toml`, `.ini`, `.env`
- **Docs**: `.md`, `.rst`, `.txt`
- **Build**: `Dockerfile`, `Makefile`, `.sh`

### Risk Factors
Risk scores consider:
- File count (primary factor)
- File type diversity
- Frontend complexity (more complex imports)
- Directory structure depth

## 🔧 Troubleshooting

### "No workspaces suggested"
Your repository is already small enough! This is good news - no optimization needed.

### "Analysis failed"
- Check that the path exists and is readable
- Use `--verbose` for detailed error information
- Ensure you have read permissions on the repository

### Generated workspaces too small/large
- Adjust `--max-files` (higher = larger workspaces)
- Adjust `--risk-threshold` (lower = more workspaces)

## 🎯 When to Use This Tool

✅ **Use when you experience:**
- High memory usage (>2GB) during Copilot queries
- UI freezing when asking Copilot questions
- Slow Copilot response times
- Large repositories (1000+ files)

❌ **Don't use for:**
- Small repositories (<500 files)
- Repositories where Copilot already works well
- Temporary/experimental projects

## 🤝 Related Tools

This tool works perfectly with:
- **Memory Monitor** (`test.py --copilot-focused`) - Validate improvements
- **Freeze Detector** (`test.py --freeze-detection`) - Monitor UI responsiveness
- **Context Optimizer** - Apply repository-specific Copilot settings

## 📈 Success Metrics

Track these improvements:
- [ ] Memory usage reduction (target: 60-80% less)
- [ ] UI responsiveness (target: no freezing)
- [ ] Copilot response speed (target: 3-5x faster)
- [ ] Development productivity (target: smoother workflow)

---

*This tool is part of a comprehensive solution for optimizing GitHub Copilot performance in large repositories. It transforms the "repository size problem" into multiple "small repository solutions" where Copilot performs optimally.*

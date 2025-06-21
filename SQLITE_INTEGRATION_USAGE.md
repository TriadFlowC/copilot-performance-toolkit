# SQLite Integration for Memory Monitor

The VS Code Memory Monitor now supports optional SQLite database tracking for persistent storage of monitoring runs and measurements.

## Overview

- **Optional**: Database tracking is **disabled by default** - existing workflow unchanged
- **CLI-controlled**: Enable via `--db-track` flag, customize database path with `--db-path`
- **Foundation phase**: Focused on core functionality, no integration with other tools yet
- **Utilities included**: Query, export, backup, and cleanup commands

## Getting Started

### Basic Usage

```bash
# Normal usage (no database tracking)
python tools/test.py --snapshot

# With database tracking enabled
python tools/test.py --db-track --snapshot

# Custom database path
python tools/test.py --db-track --db-path mydata.db --snapshot
```

### Continuous Monitoring with Database

```bash
# Monitor for 5 minutes with 10-second intervals
python tools/test.py --db-track --copilot-analysis

# Repository analysis with database tracking
python tools/test.py --db-track --repo-analysis
```

## Database Utilities

The `db_utils.py` tool provides utilities for working with the monitoring database:

### View Database Statistics

```bash
python tools/db_utils.py stats
python tools/db_utils.py --db-path custom.db stats
```

### List Monitoring Runs

```bash
# List all runs
python tools/db_utils.py list

# List last 10 runs
python tools/db_utils.py list --limit 10

# Filter by mode
python tools/db_utils.py list --mode snapshot

# Filter by date range
python tools/db_utils.py list --start-date 2024-01-01 --end-date 2024-01-31
```

### View Detailed Run Information

```bash
# Show detailed information for run ID 5
python tools/db_utils.py show --run-id 5

# Show summary only (no individual measurements)
python tools/db_utils.py show --run-id 5 --summary-only
```

### Export Data

```bash
# Export all data to JSON
python tools/db_utils.py export --output all_data.json

# Export specific run
python tools/db_utils.py export --run-id 5 --output run5.json

# Export by mode
python tools/db_utils.py export --mode snapshot --output snapshots.json

# Export last 20 runs
python tools/db_utils.py export --limit 20 --output recent.json
```

### Backup Database

```bash
# Create backup with timestamp
python tools/db_utils.py backup

# Custom backup path
python tools/db_utils.py backup --backup-path backup_20240101.db
```

### Cleanup Old Data

```bash
# Keep only last 30 days of data
python tools/db_utils.py cleanup --days 30

# Skip confirmation prompt
python tools/db_utils.py cleanup --days 30 --force
```

## Database Schema

### Tables

#### monitoring_runs
- `id`: Primary key
- `start_time`: When monitoring started
- `end_time`: When monitoring completed
- `mode`: Type of monitoring (snapshot, continuous_monitoring, etc.)
- `interval_seconds`: Measurement interval
- `duration_seconds`: Total monitoring duration
- `total_measurements`: Number of measurements taken
- `command_line_args`: Original command line
- `status`: Run status (running, completed, interrupted, etc.)
- `notes`: Additional notes

#### memory_measurements
- `id`: Primary key
- `run_id`: Foreign key to monitoring_runs
- `timestamp`: When measurement was taken
- `process_count`: Number of VS Code processes found
- `total_rss_bytes`: Total RAM usage (bytes)
- `total_vms_bytes`: Total virtual memory usage (bytes)
- `process_data`: JSON data with detailed process information
- `measurement_index`: Sequence number within run
- `notes`: Additional notes

## Examples

### Example 1: Memory Snapshot with Database

```bash
# Take snapshot and store in database
python tools/test.py --db-track --snapshot

# View the result
python tools/db_utils.py list
python tools/db_utils.py show --run-id 1
```

### Example 2: Continuous Monitoring Analysis

```bash
# Monitor for 2 minutes with database tracking
python tools/test.py --db-track 10 120

# Export the data for analysis
python tools/db_utils.py export --output monitoring_session.json

# View statistics
python tools/db_utils.py stats
```

### Example 3: Historical Analysis

```bash
# Run multiple monitoring sessions over time
python tools/test.py --db-track --copilot-analysis
# ... (repeat at different times) ...

# List all runs to see trends
python tools/db_utils.py list

# Export all data for external analysis
python tools/db_utils.py export --output complete_history.json
```

## Integration Points

The database integration is added to these monitoring modes:

- **Snapshot mode** (`--snapshot`): Single measurement stored as run with 1 measurement
- **Continuous monitoring**: All measurements during monitoring session stored
- **Repository analysis** (`--repo-analysis`): Analysis results and any continuous monitoring
- **Copilot analysis** (`--copilot-analysis`): Hypothesis testing measurements

## Default Behavior

- **No impact on existing usage**: All existing commands work exactly the same
- **Console output preserved**: Database tracking doesn't change console output
- **Optional**: Database features only active when `--db-track` is specified
- **Performance**: Minimal overhead when database tracking is disabled

## File Locations

- **Default database**: `performance.db` in current directory
- **Custom database**: Specify with `--db-path PATH`
- **Backup files**: `performance.db.backup_YYYYMMDD_HHMMSS` by default
- **Export files**: `memory_monitor_export_YYYYMMDD_HHMMSS.json` by default

## Troubleshooting

### Database Not Found

If you get a "database not found" error:
```bash
# Create a new database (will be created automatically on first use)
python tools/test.py --db-track --snapshot
```

### Large Database Files

If database gets large:
```bash
# Check size
python tools/db_utils.py stats

# Clean up old data (keep last 30 days)
python tools/db_utils.py cleanup --days 30

# Create backup before cleanup
python tools/db_utils.py backup
```

### Export Format

JSON exports contain:
- Database statistics
- Complete run information
- All measurements with process details
- Timestamps in ISO format

This format can be imported into analysis tools like Excel, R, Python pandas, etc.

## Future Enhancements

This foundation implementation enables future features:
- Integration with other toolkit tools
- Advanced analytics and trending
- Automated baseline establishment
- Alert thresholds
- Team workspace comparison

The database schema is designed to support these future enhancements while maintaining backward compatibility.
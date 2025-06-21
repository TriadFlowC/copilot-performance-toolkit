#!/usr/bin/env python3
"""
Database utility commands for VS Code Memory Monitor
Provides CLI utilities for querying, exporting, backup, and cleanup
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add tools directory to path for import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import MemoryMonitorDB


def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if bytes_value is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def format_duration(seconds):
    """Convert seconds to human readable duration"""
    if seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def cmd_list_runs(db: MemoryMonitorDB, args):
    """List monitoring runs"""
    runs = db.get_monitoring_runs(
        limit=args.limit,
        mode=args.mode,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if not runs:
        print("No monitoring runs found.")
        return
    
    print(f"\n📊 Found {len(runs)} monitoring run(s):")
    print("=" * 120)
    print(f"{'ID':<4} {'Start Time':<19} {'Mode':<20} {'Duration':<10} {'Measurements':<12} {'Status':<10}")
    print("=" * 120)
    
    for run in runs:
        start_time = run['start_time'][:19] if run['start_time'] else "N/A"
        duration = "N/A"
        if run['duration_seconds']:
            duration = format_duration(run['duration_seconds'])
        
        print(f"{run['id']:<4} {start_time:<19} {run['mode']:<20} "
              f"{duration:<10} {run['total_measurements']:<12} {run['status']:<10}")
    
    print("=" * 120)


def cmd_show_run(db: MemoryMonitorDB, args):
    """Show detailed information about a specific run"""
    if not args.run_id:
        print("❌ Run ID is required")
        return
    
    # Get run info
    runs = db.get_monitoring_runs()
    run = next((r for r in runs if r['id'] == args.run_id), None)
    
    if not run:
        print(f"❌ Run with ID {args.run_id} not found")
        return
    
    # Get measurements
    measurements = db.get_measurements_for_run(args.run_id)
    
    print(f"\n🔍 Monitoring Run Details (ID: {run['id']})")
    print("=" * 80)
    print(f"Mode: {run['mode']}")
    print(f"Start Time: {run['start_time']}")
    print(f"End Time: {run['end_time'] or 'N/A'}")
    print(f"Status: {run['status']}")
    print(f"Duration: {format_duration(run['duration_seconds'])}")
    print(f"Interval: {run['interval_seconds']}s" if run['interval_seconds'] else "N/A")
    print(f"Total Measurements: {len(measurements)}")
    
    if run['command_line_args']:
        print(f"Command Line Args: {run['command_line_args']}")
    
    if run['notes']:
        print(f"Notes: {run['notes']}")
    
    if measurements and not args.summary_only:
        print(f"\n📈 Memory Measurements:")
        print("-" * 80)
        print(f"{'#':<4} {'Time':<8} {'Processes':<10} {'Total RAM':<12} {'Virtual':<12}")
        print("-" * 80)
        
        # Show first 10 and last 10 measurements if more than 20 total
        if len(measurements) > 20:
            display_measurements = measurements[:10] + measurements[-10:]
            show_ellipsis = True
        else:
            display_measurements = measurements
            show_ellipsis = False
        
        for i, measurement in enumerate(display_measurements):
            if show_ellipsis and i == 10:
                print("... (measurements truncated) ...")
                continue
                
            timestamp = measurement['timestamp']
            time_part = timestamp[11:19] if len(timestamp) > 11 else timestamp
            
            print(f"{measurement['measurement_index'] or i+1:<4} {time_part:<8} "
                  f"{measurement['process_count']:<10} "
                  f"{format_bytes(measurement['total_rss_bytes']):<12} "
                  f"{format_bytes(measurement['total_vms_bytes']):<12}")
        
        print("-" * 80)
        
        # Show memory trend
        if len(measurements) > 1:
            first_rss = measurements[0]['total_rss_bytes']
            last_rss = measurements[-1]['total_rss_bytes']
            change = last_rss - first_rss
            change_percent = (change / first_rss * 100) if first_rss > 0 else 0
            
            print(f"\n📊 Memory Trend:")
            print(f"   Initial RAM: {format_bytes(first_rss)}")
            print(f"   Final RAM: {format_bytes(last_rss)}")
            print(f"   Change: {format_bytes(change)} ({change_percent:+.1f}%)")


def cmd_export_data(db: MemoryMonitorDB, args):
    """Export data to JSON"""
    try:
        output_file = db.export_to_json(
            output_file=args.output,
            run_id=args.run_id,
            mode=args.mode,
            limit=args.limit
        )
        print(f"✅ Data exported to: {output_file}")
        
        # Show basic stats about exported data
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        total_runs = len(data['runs'])
        total_measurements = sum(len(run.get('measurements', [])) for run in data['runs'])
        
        print(f"📊 Export Summary:")
        print(f"   Runs exported: {total_runs}")
        print(f"   Total measurements: {total_measurements}")
        print(f"   File size: {format_bytes(os.path.getsize(output_file))}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


def cmd_backup_db(db: MemoryMonitorDB, args):
    """Create database backup"""
    try:
        backup_path = db.backup_database(args.backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        
        # Show backup file size
        backup_size = os.path.getsize(backup_path)
        print(f"📊 Backup size: {format_bytes(backup_size)}")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")


def cmd_cleanup_data(db: MemoryMonitorDB, args):
    """Cleanup old data"""
    if not args.days:
        print("❌ Number of days to keep is required")
        return
    
    if args.days < 1:
        print("❌ Days must be a positive number")
        return
    
    print(f"⚠️  This will permanently delete data older than {args.days} days.")
    if not args.force:
        response = input("Continue? (y/N): ").lower()
        if response not in ['y', 'yes']:
            print("Cleanup cancelled.")
            return
    
    try:
        deleted_runs = db.cleanup_old_data(args.days)
        if deleted_runs > 0:
            print(f"✅ Cleaned up {deleted_runs} old monitoring run(s)")
        else:
            print("✅ No old data found to clean up")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def cmd_stats(db: MemoryMonitorDB, args):
    """Show database statistics"""
    try:
        stats = db.get_database_stats()
        
        print(f"\n📊 Database Statistics")
        print("=" * 50)
        print(f"Database Path: {stats['database_path']}")
        print(f"Database Size: {format_bytes(stats['database_size_bytes'])}")
        print(f"Total Runs: {stats['total_runs']}")
        print(f"Total Measurements: {stats['total_measurements']}")
        
        if stats['earliest_run'] and stats['latest_run']:
            print(f"Date Range: {stats['earliest_run'][:10]} to {stats['latest_run'][:10]}")
        
        # Show mode breakdown
        runs = db.get_monitoring_runs()
        if runs:
            mode_counts = {}
            for run in runs:
                mode = run['mode']
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            print(f"\n📈 Runs by Mode:")
            for mode, count in sorted(mode_counts.items()):
                print(f"   {mode}: {count}")
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")


def main():
    """Main CLI interface for database utilities"""
    parser = argparse.ArgumentParser(
        description="Database utilities for VS Code Memory Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db_utils.py list                          # List all runs
  python db_utils.py list --mode snapshot --limit 10
  python db_utils.py show --run-id 5               # Show detailed run info
  python db_utils.py export --output data.json    # Export all data
  python db_utils.py export --run-id 5 --output run5.json
  python db_utils.py backup --backup-path backup.db
  python db_utils.py cleanup --days 30            # Keep only last 30 days
  python db_utils.py stats                        # Show database statistics
        """
    )
    
    parser.add_argument('--db-path', default='performance.db',
                       help='Path to SQLite database file (default: performance.db)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List runs command
    list_parser = subparsers.add_parser('list', help='List monitoring runs')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    list_parser.add_argument('--mode', help='Filter by monitoring mode')
    list_parser.add_argument('--start-date', help='Filter by start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='Filter by end date (YYYY-MM-DD)')
    list_parser.set_defaults(func=cmd_list_runs)
    
    # Show run command
    show_parser = subparsers.add_parser('show', help='Show detailed run information')
    show_parser.add_argument('--run-id', type=int, required=True, help='Run ID to show')
    show_parser.add_argument('--summary-only', action='store_true', 
                            help='Show only summary, not individual measurements')
    show_parser.set_defaults(func=cmd_show_run)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to JSON')
    export_parser.add_argument('--output', help='Output file path')
    export_parser.add_argument('--run-id', type=int, help='Export specific run only')
    export_parser.add_argument('--mode', help='Export runs of specific mode only')
    export_parser.add_argument('--limit', type=int, help='Limit number of runs to export')
    export_parser.set_defaults(func=cmd_export_data)
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--backup-path', help='Backup file path')
    backup_parser.set_defaults(func=cmd_backup_db)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, required=True,
                               help='Number of days of data to keep')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='Skip confirmation prompt')
    cleanup_parser.set_defaults(func=cmd_cleanup_data)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database
    try:
        db = MemoryMonitorDB(args.db_path)
        args.func(db, args)
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
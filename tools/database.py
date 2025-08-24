#!/usr/bin/env python3
"""
Database operations module for VS Code Memory Monitor
Provides SQLite-based persistent storage for monitoring runs and measurements
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


class MemoryMonitorDB:
    """Database manager for memory monitoring data"""
    
    def __init__(self, db_path: str = "performance.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create monitoring_runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    mode TEXT NOT NULL,
                    interval_seconds INTEGER,
                    duration_seconds INTEGER,
                    total_measurements INTEGER DEFAULT 0,
                    command_line_args TEXT,
                    status TEXT DEFAULT 'running',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create memory_measurements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    process_count INTEGER,
                    total_rss_bytes INTEGER,
                    total_vms_bytes INTEGER,
                    process_data TEXT,
                    measurement_index INTEGER,
                    notes TEXT,
                    FOREIGN KEY (run_id) REFERENCES monitoring_runs (id)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_monitoring_runs_start_time 
                ON monitoring_runs (start_time)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memory_measurements_run_id 
                ON memory_measurements (run_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memory_measurements_timestamp 
                ON memory_measurements (timestamp)
            ''')
            
            conn.commit()
    
    def start_monitoring_run(self, mode: str, interval_seconds: int = None, 
                           duration_seconds: int = None, command_line_args: str = None,
                           notes: str = None) -> int:
        """Start a new monitoring run and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO monitoring_runs 
                (start_time, mode, interval_seconds, duration_seconds, command_line_args, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), mode, interval_seconds, duration_seconds, command_line_args, notes))
            
            run_id = cursor.lastrowid
            conn.commit()
            return run_id
    
    def end_monitoring_run(self, run_id: int, total_measurements: int = 0, 
                          status: str = 'completed', notes: str = None):
        """Mark a monitoring run as completed and update statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE monitoring_runs 
                SET end_time = ?, total_measurements = ?, status = ?, notes = ?
                WHERE id = ?
            ''', (datetime.now(), total_measurements, status, notes, run_id))
            conn.commit()
    
    def add_measurement(self, run_id: int, timestamp: datetime, process_count: int,
                       total_rss_bytes: int, total_vms_bytes: int, 
                       process_data: List[Dict], measurement_index: int = None,
                       notes: str = None):
        """Add a memory measurement to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert process data to JSON for storage
            process_data_json = json.dumps(process_data, default=str)
            
            cursor.execute('''
                INSERT INTO memory_measurements 
                (run_id, timestamp, process_count, total_rss_bytes, total_vms_bytes, 
                 process_data, measurement_index, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (run_id, timestamp, process_count, total_rss_bytes, total_vms_bytes,
                  process_data_json, measurement_index, notes))
            conn.commit()
    
    def get_monitoring_runs(self, limit: int = None, mode: str = None, 
                           start_date: str = None, end_date: str = None) -> List[Dict]:
        """Retrieve monitoring runs with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            query = "SELECT * FROM monitoring_runs WHERE 1=1"
            params = []
            
            if mode:
                query += " AND mode = ?"
                params.append(mode)
            
            if start_date:
                query += " AND start_time >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND start_time <= ?"
                params.append(end_date)
            
            query += " ORDER BY start_time DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_measurements_for_run(self, run_id: int) -> List[Dict]:
        """Get all measurements for a specific monitoring run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM memory_measurements 
                WHERE run_id = ? 
                ORDER BY timestamp
            ''', (run_id,))
            
            measurements = []
            for row in cursor.fetchall():
                measurement = dict(row)
                # Parse process data back from JSON
                if measurement['process_data']:
                    measurement['process_data'] = json.loads(measurement['process_data'])
                measurements.append(measurement)
            
            return measurements
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get run count
            cursor.execute("SELECT COUNT(*) FROM monitoring_runs")
            run_count = cursor.fetchone()[0]
            
            # Get measurement count
            cursor.execute("SELECT COUNT(*) FROM memory_measurements")
            measurement_count = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Get date range
            cursor.execute("SELECT MIN(start_time), MAX(start_time) FROM monitoring_runs")
            date_range = cursor.fetchone()
            
            return {
                'database_path': self.db_path,
                'database_size_bytes': db_size,
                'total_runs': run_count,
                'total_measurements': measurement_count,
                'earliest_run': date_range[0],
                'latest_run': date_range[1]
            }
    
    def export_to_json(self, output_file: str = None, run_id: int = None, 
                      mode: str = None, limit: int = None) -> str:
        """Export database data to JSON format"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"memory_monitor_export_{timestamp}.json"
        
        # Get runs based on criteria
        if run_id:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM monitoring_runs WHERE id = ?", (run_id,))
                runs = [dict(row) for row in cursor.fetchall()]
        else:
            runs = self.get_monitoring_runs(limit=limit, mode=mode)
        
        # Get measurements for each run
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'database_stats': self.get_database_stats(),
            'runs': []
        }
        
        for run in runs:
            run_data = dict(run)
            run_data['measurements'] = self.get_measurements_for_run(run['id'])
            export_data['runs'].append(run_data)
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_file
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Remove data older than specified days"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get runs to delete
            cursor.execute('''
                SELECT id FROM monitoring_runs 
                WHERE start_time < ?
            ''', (cutoff_date,))
            old_run_ids = [row[0] for row in cursor.fetchall()]
            
            if not old_run_ids:
                return 0
            
            # Delete measurements for old runs
            placeholders = ','.join('?' * len(old_run_ids))
            cursor.execute(f'''
                DELETE FROM memory_measurements 
                WHERE run_id IN ({placeholders})
            ''', old_run_ids)
            
            # Delete old runs
            cursor.execute(f'''
                DELETE FROM monitoring_runs 
                WHERE id IN ({placeholders})
            ''', old_run_ids)
            
            conn.commit()
            return len(old_run_ids)
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a backup of the database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        # Use SQLite backup API for safe backup
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        return backup_path
    
    def close(self):
        """Close database connection (placeholder for consistency)"""
        # SQLite connections are automatically closed when exiting context managers
        pass
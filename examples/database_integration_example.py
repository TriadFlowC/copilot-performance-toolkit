#!/usr/bin/env python3
"""
Database Schema and Data Access Layer for Copilot Performance Toolkit
Example implementation for SQLite integration assessment
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class PerformanceDatabase:
    """
    Simple data access layer for performance monitoring data
    Demonstrates SQLite integration approach for the toolkit
    """
    
    def __init__(self, db_path: str = "copilot_performance.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            # Monitoring runs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date DATETIME NOT NULL,
                    tool_name TEXT NOT NULL,
                    parameters TEXT,  -- JSON string of parameters
                    duration_seconds INTEGER,
                    repository_path TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Memory measurements table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    process_id INTEGER NOT NULL,
                    process_name TEXT NOT NULL,
                    process_type TEXT NOT NULL,
                    memory_rss_mb REAL NOT NULL,
                    memory_growth_mb REAL DEFAULT 0,
                    cpu_percent REAL DEFAULT 0,
                    open_files INTEGER DEFAULT 0,
                    threads INTEGER DEFAULT 0,
                    is_copilot_related BOOLEAN DEFAULT FALSE,
                    is_extension_host BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (run_id) REFERENCES monitoring_runs (id)
                )
            ''')
            
            # Repository analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS repository_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    analysis_date DATETIME NOT NULL,
                    repository_path TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    total_size_mb REAL NOT NULL,
                    git_commits INTEGER,
                    git_tracked_files INTEGER,
                    analysis_results TEXT,  -- JSON string of full results
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES monitoring_runs (id)
                )
            ''')
            
            # Directory analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS directory_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_analysis_id INTEGER NOT NULL,
                    directory_path TEXT NOT NULL,
                    file_count INTEGER NOT NULL,
                    risk_score INTEGER NOT NULL,
                    size_mb REAL NOT NULL,
                    primary_file_types TEXT,  -- JSON array
                    copilot_settings TEXT,    -- JSON object
                    FOREIGN KEY (repository_analysis_id) REFERENCES repository_analysis (id)
                )
            ''')
            
            # Workspace recommendations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workspace_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_analysis_id INTEGER NOT NULL,
                    workspace_name TEXT NOT NULL,
                    workspace_path TEXT NOT NULL,
                    file_count INTEGER NOT NULL,
                    risk_score INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    recommendation_type TEXT NOT NULL,
                    implemented BOOLEAN DEFAULT FALSE,
                    feedback_score INTEGER,  -- 1-5 rating if provided
                    feedback_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (repository_analysis_id) REFERENCES repository_analysis (id)
                )
            ''')
            
            # Comparison operations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comparison_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    comparison_date DATETIME NOT NULL,
                    folder1_path TEXT NOT NULL,
                    folder2_path TEXT NOT NULL,
                    differences_found INTEGER NOT NULL,
                    comparison_results TEXT,  -- JSON string of results
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES monitoring_runs (id)
                )
            ''')
            
            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_run_timestamp ON memory_measurements(run_id, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memory_process_type ON memory_measurements(process_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_runs_date ON monitoring_runs(run_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_repo ON repository_analysis(repository_path)')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def start_monitoring_run(self, tool_name: str, parameters: Dict[str, Any] = None, 
                           repository_path: str = None, notes: str = None) -> int:
        """Start a new monitoring run and return the run ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO monitoring_runs (run_date, tool_name, parameters, repository_path, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                tool_name,
                json.dumps(parameters) if parameters else None,
                repository_path,
                notes
            ))
            conn.commit()
            return cursor.lastrowid
    
    def finish_monitoring_run(self, run_id: int, duration_seconds: int):
        """Update monitoring run with completion information"""
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE monitoring_runs 
                SET duration_seconds = ? 
                WHERE id = ?
            ''', (duration_seconds, run_id))
            conn.commit()
    
    def record_memory_measurement(self, run_id: int, measurement_data: Dict[str, Any]):
        """Record a memory measurement"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO memory_measurements (
                    run_id, timestamp, process_id, process_name, process_type,
                    memory_rss_mb, memory_growth_mb, cpu_percent, open_files, threads,
                    is_copilot_related, is_extension_host
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id,
                measurement_data.get('timestamp', datetime.now()),
                measurement_data['process_id'],
                measurement_data['process_name'],
                measurement_data['process_type'],
                measurement_data['memory_rss_mb'],
                measurement_data.get('memory_growth_mb', 0),
                measurement_data.get('cpu_percent', 0),
                measurement_data.get('open_files', 0),
                measurement_data.get('threads', 0),
                measurement_data.get('is_copilot_related', False),
                measurement_data.get('is_extension_host', False)
            ))
            conn.commit()
    
    def record_repository_analysis(self, run_id: int, analysis_data: Dict[str, Any]) -> int:
        """Record repository analysis results"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO repository_analysis (
                    run_id, analysis_date, repository_path, total_files, total_size_mb,
                    git_commits, git_tracked_files, analysis_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_id,
                datetime.now(),
                analysis_data['repository_path'],
                analysis_data['total_files'],
                analysis_data.get('total_size_mb', 0),
                analysis_data.get('git_commits'),
                analysis_data.get('git_tracked_files'),
                json.dumps(analysis_data.get('full_results', {}))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_memory_trends(self, run_id: int, process_type: str = None) -> List[Dict]:
        """Get memory usage trends for a specific run"""
        with self.get_connection() as conn:
            query = '''
                SELECT timestamp, process_type, memory_rss_mb, memory_growth_mb
                FROM memory_measurements 
                WHERE run_id = ?
            '''
            params = [run_id]
            
            if process_type:
                query += ' AND process_type = ?'
                params.append(process_type)
            
            query += ' ORDER BY timestamp'
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_runs(self, tool_name: str = None, limit: int = 10) -> List[Dict]:
        """Get recent monitoring runs"""
        with self.get_connection() as conn:
            query = '''
                SELECT id, run_date, tool_name, parameters, duration_seconds, repository_path, notes
                FROM monitoring_runs
            '''
            params = []
            
            if tool_name:
                query += ' WHERE tool_name = ?'
                params.append(tool_name)
            
            query += ' ORDER BY run_date DESC LIMIT ?'
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_summary(self, repository_path: str = None) -> Dict[str, Any]:
        """Get performance summary statistics"""
        with self.get_connection() as conn:
            # Get run counts
            run_query = 'SELECT COUNT(*) as total_runs FROM monitoring_runs'
            run_params = []
            
            if repository_path:
                run_query += ' WHERE repository_path = ?'
                run_params.append(repository_path)
            
            total_runs = conn.execute(run_query, run_params).fetchone()['total_runs']
            
            # Get memory statistics
            memory_query = '''
                SELECT 
                    AVG(memory_rss_mb) as avg_memory,
                    MAX(memory_rss_mb) as peak_memory,
                    COUNT(*) as measurement_count
                FROM memory_measurements mm
                JOIN monitoring_runs mr ON mm.run_id = mr.id
            '''
            memory_params = []
            
            if repository_path:
                memory_query += ' WHERE mr.repository_path = ?'
                memory_params.append(repository_path)
            
            memory_stats = dict(conn.execute(memory_query, memory_params).fetchone())
            
            return {
                'total_runs': total_runs,
                'memory_statistics': memory_stats,
                'repository_path': repository_path
            }

    def export_data(self, output_path: str, run_id: int = None):
        """Export data to JSON file for analysis or sharing"""
        with self.get_connection() as conn:
            export_data = {}
            
            # Export runs
            run_query = 'SELECT * FROM monitoring_runs'
            run_params = []
            if run_id:
                run_query += ' WHERE id = ?'
                run_params.append(run_id)
            
            runs = [dict(row) for row in conn.execute(run_query, run_params)]
            export_data['runs'] = runs
            
            # Export related data for each run
            for run in runs:
                run_id_key = run['id']
                
                # Memory measurements
                memory_data = [dict(row) for row in conn.execute(
                    'SELECT * FROM memory_measurements WHERE run_id = ?', [run_id_key]
                )]
                export_data[f'memory_run_{run_id_key}'] = memory_data
                
                # Repository analysis
                analysis_data = [dict(row) for row in conn.execute(
                    'SELECT * FROM repository_analysis WHERE run_id = ?', [run_id_key]
                )]
                export_data[f'analysis_run_{run_id_key}'] = analysis_data
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)


def example_usage():
    """Example of how the database would be used in practice"""
    
    # Initialize database
    db = PerformanceDatabase("example_performance.db")
    
    # Start a monitoring run
    run_id = db.start_monitoring_run(
        tool_name="test.py",
        parameters={"mode": "copilot-focused", "interval": 5},
        repository_path="/path/to/large/repo",
        notes="Testing memory patterns with new Copilot features"
    )
    
    # Record some sample measurements
    sample_measurements = [
        {
            'process_id': 1234,
            'process_name': 'Code Helper',
            'process_type': 'Extension Host',
            'memory_rss_mb': 145.2,
            'memory_growth_mb': 12.5,
            'cpu_percent': 15.3,
            'is_copilot_related': True,
            'is_extension_host': True
        },
        {
            'process_id': 1235,
            'process_name': 'TypeScript Language Server',
            'process_type': 'Language Server',
            'memory_rss_mb': 89.7,
            'memory_growth_mb': 5.2,
            'cpu_percent': 8.1,
            'is_copilot_related': False,
            'is_extension_host': False
        }
    ]
    
    for measurement in sample_measurements:
        db.record_memory_measurement(run_id, measurement)
    
    # Finish the run
    db.finish_monitoring_run(run_id, duration_seconds=300)
    
    # Query the data
    trends = db.get_memory_trends(run_id, process_type='Extension Host')
    recent_runs = db.get_recent_runs(tool_name="test.py")
    summary = db.get_performance_summary()
    
    print(f"Recorded {len(trends)} measurements")
    print(f"Found {len(recent_runs)} recent runs")
    print(f"Summary: {summary}")
    
    # Export data
    db.export_data("performance_export.json", run_id=run_id)
    print("Data exported to performance_export.json")


if __name__ == "__main__":
    example_usage()
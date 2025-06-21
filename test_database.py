#!/usr/bin/env python3
"""
Basic tests for SQLite integration in memory monitor
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from database import MemoryMonitorDB


class TestMemoryMonitorDB(unittest.TestCase):
    """Test cases for MemoryMonitorDB"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db = MemoryMonitorDB(self.test_db_path)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database tables are created correctly"""
        stats = self.db.get_database_stats()
        self.assertEqual(stats['total_runs'], 0)
        self.assertEqual(stats['total_measurements'], 0)
        self.assertTrue(os.path.exists(self.test_db_path))
    
    def test_monitoring_run_lifecycle(self):
        """Test creating and completing a monitoring run"""
        # Start a run
        run_id = self.db.start_monitoring_run(
            mode='test_mode',
            interval_seconds=10,
            duration_seconds=60,
            command_line_args='test command',
            notes='Test run'
        )
        self.assertIsInstance(run_id, int)
        self.assertGreater(run_id, 0)
        
        # Check run exists
        runs = self.db.get_monitoring_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['mode'], 'test_mode')
        self.assertEqual(runs[0]['status'], 'running')
        
        # End the run
        self.db.end_monitoring_run(run_id, 5, 'completed', 'Test completed')
        
        # Verify run was updated
        runs = self.db.get_monitoring_runs()
        self.assertEqual(runs[0]['status'], 'completed')
        self.assertEqual(runs[0]['total_measurements'], 5)
    
    def test_add_measurements(self):
        """Test adding measurements to a run"""
        # Create a run
        run_id = self.db.start_monitoring_run('test_mode')
        
        # Add measurements
        test_processes = [
            {'pid': 1234, 'name': 'Code Helper', 'rss': 100000000, 'vms': 200000000}
        ]
        
        timestamp = datetime.now()
        self.db.add_measurement(
            run_id=run_id,
            timestamp=timestamp,
            process_count=1,
            total_rss_bytes=100000000,
            total_vms_bytes=200000000,
            process_data=test_processes,
            measurement_index=1,
            notes='Test measurement'
        )
        
        # Verify measurement was added
        measurements = self.db.get_measurements_for_run(run_id)
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0]['process_count'], 1)
        self.assertEqual(measurements[0]['total_rss_bytes'], 100000000)
        self.assertEqual(len(measurements[0]['process_data']), 1)
    
    def test_export_functionality(self):
        """Test JSON export functionality"""
        # Create test data
        run_id = self.db.start_monitoring_run('export_test')
        test_processes = [{'pid': 1234, 'name': 'Test Process', 'rss': 50000000}]
        self.db.add_measurement(
            run_id=run_id,
            timestamp=datetime.now(),
            process_count=1,
            total_rss_bytes=50000000,
            total_vms_bytes=100000000,
            process_data=test_processes
        )
        self.db.end_monitoring_run(run_id, 1, 'completed')
        
        # Export data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            result_file = self.db.export_to_json(export_file)
            self.assertEqual(result_file, export_file)
            self.assertTrue(os.path.exists(export_file))
            
            # Verify export contains data
            import json
            with open(export_file, 'r') as f:
                data = json.load(f)
            
            self.assertEqual(len(data['runs']), 1)
            self.assertEqual(data['runs'][0]['mode'], 'export_test')
            self.assertEqual(len(data['runs'][0]['measurements']), 1)
            
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)
    
    def test_backup_functionality(self):
        """Test database backup functionality"""
        # Create test data
        run_id = self.db.start_monitoring_run('backup_test')
        self.db.end_monitoring_run(run_id, 0, 'completed')
        
        # Create backup
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            backup_path = f.name
        
        try:
            result_path = self.db.backup_database(backup_path)
            self.assertEqual(result_path, backup_path)
            self.assertTrue(os.path.exists(backup_path))
            
            # Verify backup contains data
            backup_db = MemoryMonitorDB(backup_path)
            runs = backup_db.get_monitoring_runs()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]['mode'], 'backup_test')
            
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)
    
    def test_cleanup_functionality(self):
        """Test data cleanup functionality"""
        # Create old test data (simulated by direct database manipulation)
        import sqlite3
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            # Insert old run (45 days ago)
            old_date = datetime(2024, 1, 1)
            cursor.execute('''
                INSERT INTO monitoring_runs (start_time, mode, status)
                VALUES (?, 'old_test', 'completed')
            ''', (old_date,))
            old_run_id = cursor.lastrowid
            
            # Insert recent run
            recent_date = datetime.now()
            cursor.execute('''
                INSERT INTO monitoring_runs (start_time, mode, status)
                VALUES (?, 'recent_test', 'completed')
            ''', (recent_date,))
            conn.commit()
        
        # Verify we have 2 runs
        runs = self.db.get_monitoring_runs()
        self.assertEqual(len(runs), 2)
        
        # Cleanup old data (keep last 30 days)
        deleted_count = self.db.cleanup_old_data(days_to_keep=30)
        self.assertEqual(deleted_count, 1)
        
        # Verify only recent run remains
        runs = self.db.get_monitoring_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['mode'], 'recent_test')


if __name__ == '__main__':
    unittest.main()
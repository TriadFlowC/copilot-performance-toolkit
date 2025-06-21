#!/usr/bin/env python3
"""
VS Code Memory Usage Monitor
A script to monitor memory usage of VS Code processes on macOS
"""

import psutil
import time
import sys
import os
import argparse
from datetime import datetime

# Database integration (optional)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import MemoryMonitorDB
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

def get_vscode_processes():
    """Find all VS Code related processes with detailed info"""
    vscode_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'cmdline', 'create_time']):
        try:
            proc_info = proc.info
            proc_name = proc_info['name'].lower()
            
            # Look for VS Code related processes
            if any(keyword in proc_name for keyword in [
                'code', 'electron', 'visual studio code'
            ]):
                # Additional check to make sure it's actually VS Code
                try:
                    cmdline = proc.cmdline()
                    if any('visual studio code' in arg.lower() or 
                          'vscode' in arg.lower() or
                          'code' in arg.lower() for arg in cmdline):
                        
                        # Determine process type based on command line arguments
                        process_type = determine_process_type(cmdline, proc_name)
                        
                        vscode_processes.append({
                            'process': proc,
                            'type': process_type,
                            'name': proc_info['name'],
                            'cmdline': cmdline
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return vscode_processes

def determine_process_type(cmdline, proc_name):
    """Determine the type of VS Code process based on command line arguments"""
    cmdline_str = ' '.join(cmdline).lower()
    
    if '--type=renderer' in cmdline_str:
        if '--webview' in cmdline_str:
            return 'Webview (Extensions/UI)'
        elif 'extensionhost' in cmdline_str:
            return 'Extension Host'
        else:
            return 'Window/Editor'
    elif '--type=gpu-process' in cmdline_str:
        return 'GPU Process'
    elif '--type=utility' in cmdline_str:
        return 'Utility Process'
    elif '--type=zygote' in cmdline_str:
        return 'Zygote Process'
    elif 'extensionhost' in cmdline_str:
        return 'Extension Host'
    elif '--shared-process' in cmdline_str:
        return 'Shared Process'
    elif 'crashreporter' in proc_name.lower():
        return 'Crash Reporter'
    elif any(lang in cmdline_str for lang in ['typescript', 'javascript', 'python', 'node', 'language-server']):
        return 'Language Server'
    elif proc_name.lower() == 'code' and '--' not in cmdline_str:
        return 'Main Process'
    elif any(git_term in cmdline_str for git_term in ['git', 'scm', 'source-control']):
        return 'Git/SCM Process'
    else:
        return 'Other/Unknown'

def detect_copilot_related_processes(process_data):
    """Detect processes that might be related to Copilot functionality"""
    copilot_processes = []
    git_processes = []
    extension_hosts = []
    
    for proc_data in process_data:
        cmdline_str = ' '.join(proc_data['cmdline']).lower()
        proc_type = proc_data['type']
        
        # Check for Copilot-related processes
        if any(copilot_term in cmdline_str for copilot_term in [
            'copilot', 'github.copilot', 'ms-vscode.copilot', 'github-copilot'
        ]):
            copilot_processes.append(proc_data)
        
        # Check for Git-related processes
        if any(git_term in cmdline_str for git_term in [
            'git', 'scm', 'source-control', 'diff', 'merge'
        ]) or 'Git/SCM' in proc_type:
            git_processes.append(proc_data)
        
        # Extension hosts (likely to run Copilot)
        if 'Extension Host' in proc_type:
            extension_hosts.append(proc_data)
    
    return {
        'copilot': copilot_processes,
        'git': git_processes,
        'extension_hosts': extension_hosts
    }

def analyze_copilot_git_hypothesis(process_data):
    """Analyze memory usage patterns to test Copilot + Git interaction hypothesis"""
    print("\n🔍 COPILOT + GIT MEMORY INTERACTION ANALYSIS")
    print("=" * 80)
    
    # Detect relevant processes
    special_processes = detect_copilot_related_processes(process_data)
    
    # Collect detailed process information with focus on hypothesis
    processes_with_memory = []
    total_memory = 0
    
    for proc_data in process_data:
        try:
            proc = proc_data['process']
            memory_info = proc.memory_info()
            cpu_percent = proc.cpu_percent()
            
            rss = memory_info.rss
            vms = memory_info.vms
            total_memory += rss
            
            # Get additional process info
            try:
                open_files = len(proc.open_files())
                threads = proc.num_threads()
                create_time = proc.create_time()
                uptime = time.time() - create_time
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = threads = uptime = 0
            
            # Analyze command line for hypothesis-relevant info
            cmdline_analysis = analyze_cmdline_for_hypothesis(proc_data['cmdline'])
            
            processes_with_memory.append({
                'pid': proc.pid,
                'type': proc_data['type'],
                'name': proc_data['name'],
                'rss': rss,
                'vms': vms,
                'cpu': cpu_percent,
                'open_files': open_files,
                'threads': threads,
                'uptime': uptime,
                'cmdline': proc_data['cmdline'],
                'analysis': cmdline_analysis,
                'is_copilot_related': proc_data in special_processes['copilot'],
                'is_git_related': proc_data in special_processes['git'],
                'is_extension_host': proc_data in special_processes['extension_hosts']
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
    
    print(f"📊 Total VS Code Memory Usage: {format_bytes(total_memory)}")
    print(f"🔢 Total Processes: {len(processes_with_memory)}")
    
    # Analyze hypothesis-specific patterns
    print("\n🧪 HYPOTHESIS TESTING RESULTS:")
    print("-" * 80)
    
    # H1: Extension Host Analysis (Copilot UI)
    extension_hosts = [p for p in processes_with_memory if p['is_extension_host']]
    if extension_hosts:
        total_ext_memory = sum(p['rss'] for p in extension_hosts)
        avg_ext_memory = total_ext_memory / len(extension_hosts)
        print(f"📈 H3 - Extension Host Analysis:")
        print(f"   • Extension Host processes: {len(extension_hosts)}")
        print(f"   • Total Extension Host memory: {format_bytes(total_ext_memory)}")
        print(f"   • Average per Extension Host: {format_bytes(avg_ext_memory)}")
        
        # Check for high memory extension hosts
        high_memory_ext = [p for p in extension_hosts if p['rss'] > 200 * 1024 * 1024]
        if high_memory_ext:
            print(f"   ⚠️  High memory Extension Hosts detected: {len(high_memory_ext)}")
            for ext in high_memory_ext:
                print(f"      - PID {ext['pid']}: {format_bytes(ext['rss'])}")
        else:
            print(f"   ✅ Extension Host memory usage appears normal")
    
    # H2: Git Process Analysis
    git_processes = [p for p in processes_with_memory if p['is_git_related']]
    if git_processes:
        total_git_memory = sum(p['rss'] for p in git_processes)
        print(f"\n📈 H2 - Git Integration Analysis:")
        print(f"   • Git-related processes: {len(git_processes)}")
        print(f"   • Total Git process memory: {format_bytes(total_git_memory)}")
        
        # Check for memory growth patterns
        git_with_high_uptime = [p for p in git_processes if p['uptime'] > 3600]  # 1 hour
        if git_with_high_uptime:
            print(f"   ⚠️  Long-running Git processes: {len(git_with_high_uptime)}")
    else:
        print(f"\n📈 H2 - Git Integration Analysis:")
        print(f"   • No specific Git processes detected")
    
    # H4: File Handle Analysis
    total_files = sum(p['open_files'] for p in processes_with_memory)
    high_file_processes = [p for p in processes_with_memory if p['open_files'] > 50]
    
    print(f"\n📈 H4 - File Watcher Analysis:")
    print(f"   • Total open file handles: {total_files}")
    print(f"   • Processes with >50 file handles: {len(high_file_processes)}")
    
    if total_files > 500:
        print(f"   ⚠️  High file handle usage detected")
        print(f"   • This could indicate file watcher overload from rapid changes")
    else:
        print(f"   ✅ File handle usage appears normal")
    
    # H5: Language Server Analysis
    language_servers = [p for p in processes_with_memory if 'Language Server' in p['type']]
    if language_servers:
        total_ls_memory = sum(p['rss'] for p in language_servers)
        high_cpu_ls = [p for p in language_servers if p['cpu'] > 10]
        
        print(f"\n📈 H5 - Language Server Analysis:")
        print(f"   • Language Server processes: {len(language_servers)}")
        print(f"   • Total Language Server memory: {format_bytes(total_ls_memory)}")
        print(f"   • High CPU Language Servers: {len(high_cpu_ls)}")
        
        if high_cpu_ls:
            print(f"   ⚠️  Language servers showing high CPU usage")
            print(f"   • This could indicate continuous re-parsing of modified code")
    
    # Detailed process breakdown for hypothesis
    print(f"\n🔍 DETAILED PROCESS BREAKDOWN (Top 10 by Memory):")
    print("-" * 120)
    print(f"{'#':>2} {'PID':>6} {'RAM':>10} {'CPU':>5} {'Files':>5} {'Uptime':>8} {'Hypothesis Flags':<20} {'Type':<20}")
    print("-" * 120)
    
    for i, proc in enumerate(processes_with_memory[:10], 1):
        flags = []
        if proc['is_copilot_related']:
            flags.append('COPILOT')
        if proc['is_git_related']:
            flags.append('GIT')
        if proc['is_extension_host']:
            flags.append('EXT-HOST')
        if proc['open_files'] > 50:
            flags.append('HIGH-FILES')
        if proc['cpu'] > 10:
            flags.append('HIGH-CPU')
        
        flags_str = ','.join(flags) if flags else '-'
        uptime_str = f"{proc['uptime']/3600:.1f}h" if proc['uptime'] > 0 else "N/A"
        
        memory_mb = proc['rss'] / (1024 * 1024)
        indicator = "🔥" if memory_mb > 200 else "⚠️" if memory_mb > 100 else "📊"
        
        print(f"{indicator} {i:2d} {proc['pid']:6d} "
              f"{format_bytes(proc['rss']):>10s} "
              f"{proc['cpu']:4.1f}% "
              f"{proc['open_files']:4d} "
              f"{uptime_str:>8s} "
              f"{flags_str:<20s} "
              f"{proc['type']:<20s}")
    
    return processes_with_memory

def analyze_cmdline_for_hypothesis(cmdline):
    """Analyze command line arguments for hypothesis-relevant information"""
    cmdline_str = ' '.join(cmdline).lower()
    analysis = {
        'has_git_terms': any(term in cmdline_str for term in ['git', 'scm', 'diff', 'merge']),
        'has_copilot_terms': any(term in cmdline_str for term in ['copilot', 'github.copilot']),
        'has_extension_terms': any(term in cmdline_str for term in ['extension', 'ext-host']),
        'has_language_server': any(term in cmdline_str for term in ['language-server', 'typescript', 'javascript']),
        'has_file_watcher': any(term in cmdline_str for term in ['watcher', 'file-watcher', 'chokidar'])
    }
    return analysis

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def monitor_memory_with_hypothesis(interval=15, duration=600, focus="4"):
    """Monitor VS Code memory usage with focus on Copilot+Git hypothesis"""
    focus_names = {
        "1": "Extension Hosts (Copilot UI)",
        "2": "Git Processes",
        "3": "Language Servers", 
        "4": "All Hypothesis-Relevant Processes"
    }
    
    print(f"🔍 Monitoring {focus_names.get(focus, 'All Processes')}...")
    print(f"📊 Checking every {interval} seconds for {duration} seconds")
    print("=" * 120)
    
    start_time = time.time()
    measurements = []
    baseline_memory = {}
    
    try:
        measurement_count = 0
        while time.time() - start_time < duration:
            measurement_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            process_data = get_vscode_processes()
            
            if not process_data:
                print(f"[{timestamp}] ❌ No VS Code processes found")
                time.sleep(interval)
                continue
            
            # Analyze processes for hypothesis
            special_processes = detect_copilot_related_processes(process_data)
            
            # Filter processes based on focus
            if focus == "1":  # Extension Hosts
                target_processes = [p for p in process_data if 'Extension Host' in p['type']]
            elif focus == "2":  # Git processes
                target_processes = special_processes['git']
            elif focus == "3":  # Language Servers
                target_processes = [p for p in process_data if 'Language Server' in p['type']]
            else:  # All hypothesis-relevant
                target_processes = process_data
            
            if not target_processes:
                print(f"[{timestamp}] ❌ No target processes found for focus area")
                time.sleep(interval)
                continue
            
            # Collect detailed information
            processes_with_memory = []
            total_memory = 0
            
            for proc_data in target_processes:
                try:
                    proc = proc_data['process']
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()
                    
                    rss = memory_info.rss
                    total_memory += rss
                    
                    # Get additional info
                    try:
                        open_files = len(proc.open_files())
                        threads = proc.num_threads()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        open_files = threads = 0
                    
                    # Calculate memory growth since baseline
                    memory_growth = 0
                    growth_percentage = 0
                    if proc.pid in baseline_memory:
                        memory_growth = rss - baseline_memory[proc.pid]
                        growth_percentage = (memory_growth / baseline_memory[proc.pid]) * 100 if baseline_memory[proc.pid] > 0 else 0
                    else:
                        baseline_memory[proc.pid] = rss
                    
                    processes_with_memory.append({
                        'pid': proc.pid,
                        'type': proc_data['type'],
                        'rss': rss,
                        'cpu': cpu_percent,
                        'open_files': open_files,
                        'threads': threads,
                        'memory_growth': memory_growth,
                        'growth_percentage': growth_percentage,
                        'is_copilot_related': proc_data in special_processes['copilot'],
                        'is_git_related': proc_data in special_processes['git'],
                        'is_extension_host': proc_data in special_processes['extension_hosts']
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
            
            print(f"\n[{timestamp}] 📈 Measurement #{measurement_count} - {focus_names.get(focus, 'All Processes')}")
            print("-" * 120)
            print(f"{'#':>2} {'PID':>6} {'RAM':>10} {'Growth':>8} {'%':>6} {'CPU':>5} {'Files':>5} {'Flags':<15} {'Type':<20}")
            print("-" * 120)
            
            for i, proc in enumerate(processes_with_memory[:8], 1):  # Top 8
                flags = []
                if proc['is_copilot_related']:
                    flags.append('COP')
                if proc['is_git_related']:
                    flags.append('GIT')
                if proc['is_extension_host']:
                    flags.append('EXT')
                
                flags_str = ','.join(flags) if flags else '-'
                
                # Highlight concerning patterns
                memory_mb = proc['rss'] / (1024 * 1024)
                growth_indicator = "📈" if proc['growth_percentage'] > 10 else "🔥" if memory_mb > 200 else "📊"
                
                print(f"{growth_indicator} {i:2d} {proc['pid']:6d} "
                      f"{format_bytes(proc['rss']):>10s} "
                      f"{format_bytes(proc['memory_growth']):>8s} "
                      f"{proc['growth_percentage']:5.1f}% "
                      f"{proc['cpu']:4.1f}% "
                      f"{proc['open_files']:4d} "
                      f"{flags_str:<15s} "
                      f"{proc['type']:<20s}")
            
            print("-" * 120)
            print(f"📊 TOTALS: Processes: {len(processes_with_memory)} | Total RAM: {format_bytes(total_memory)}")
            
            # Hypothesis-specific alerts
            high_growth_processes = [p for p in processes_with_memory if p['growth_percentage'] > 20]
            if high_growth_processes:
                print(f"⚠️  HIGH MEMORY GROWTH DETECTED:")
                for proc in high_growth_processes[:3]:
                    print(f"   PID {proc['pid']}: {proc['growth_percentage']:.1f}% growth ({format_bytes(proc['memory_growth'])})")
            
            # Store measurement
            measurements.append({
                'timestamp': timestamp,
                'measurement_count': measurement_count,
                'total_memory': total_memory,
                'process_count': len(processes_with_memory),
                'processes': processes_with_memory.copy(),
                'high_growth_count': len(high_growth_processes)
            })
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Hypothesis monitoring stopped by user")
    
    # Analyze results for hypothesis validation
    if measurements:
        print("\n" + "=" * 120)
        print("🧪 HYPOTHESIS VALIDATION RESULTS")
        print("=" * 120)
        
        # Memory growth analysis
        total_measurements = len(measurements)
        memory_trend = [m['total_memory'] for m in measurements]
        
        if len(memory_trend) > 2:
            initial_memory = memory_trend[0]
            final_memory = memory_trend[-1]
            memory_change = final_memory - initial_memory
            memory_change_percent = (memory_change / initial_memory) * 100 if initial_memory > 0 else 0
            
            print(f"📈 MEMORY TREND ANALYSIS:")
            print(f"   Initial memory: {format_bytes(initial_memory)}")
            print(f"   Final memory: {format_bytes(final_memory)}")
            print(f"   Total change: {format_bytes(memory_change)} ({memory_change_percent:+.1f}%)")
            
            # Determine if hypothesis is supported
            if memory_change_percent > 15:
                print(f"   🔥 HYPOTHESIS SUPPORTED: Significant memory growth detected")
            elif memory_change_percent > 5:
                print(f"   ⚠️  HYPOTHESIS PARTIALLY SUPPORTED: Moderate memory growth")
            else:
                print(f"   ✅ HYPOTHESIS NOT SUPPORTED: Memory usage stable")
        
        # Growth pattern analysis
        high_growth_measurements = [m for m in measurements if m['high_growth_count'] > 0]
        if high_growth_measurements:
            print(f"\n📊 GROWTH PATTERN ANALYSIS:")
            print(f"   Measurements with high growth: {len(high_growth_measurements)}/{total_measurements}")
            print(f"   This suggests memory growth is occurring during monitoring")
        
        # Process-specific analysis
        all_processes = {}
        for measurement in measurements:
            for proc in measurement['processes']:
                pid = proc['pid']
                if pid not in all_processes:
                    all_processes[pid] = []
                all_processes[pid].append(proc['rss'])
        
        problematic_processes = []
        for pid, memory_history in all_processes.items():
            if len(memory_history) > 2:
                growth = memory_history[-1] - memory_history[0]
                growth_percent = (growth / memory_history[0]) * 100 if memory_history[0] > 0 else 0
                if growth_percent > 20:
                    problematic_processes.append((pid, growth_percent, growth))
        
        if problematic_processes:
            print(f"\n🎯 PROBLEMATIC PROCESSES IDENTIFIED:")
            for pid, growth_percent, growth in sorted(problematic_processes, key=lambda x: x[1], reverse=True)[:5]:
                print(f"   PID {pid}: {growth_percent:.1f}% growth ({format_bytes(growth)})")
        
        return measurements

def monitor_memory(interval=5, duration=60, db=None):
    """Monitor VS Code memory usage with detailed process breakdown"""
    print(f"🔍 Monitoring VS Code memory usage...")
    print(f"📊 Checking every {interval} seconds for {duration} seconds")
    print("=" * 100)
    
    # Start database run if enabled
    run_id = None
    if db:
        run_id = db.start_monitoring_run(
            mode='continuous_monitoring',
            interval_seconds=interval,
            duration_seconds=duration,
            command_line_args=' '.join(sys.argv),
            notes='Continuous memory monitoring'
        )
    
    start_time = time.time()
    measurements = []
    measurement_count = 0
    
    try:
        while time.time() - start_time < duration:
            measurement_count += 1
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%H:%M:%S")
            process_data = get_vscode_processes()
            
            if not process_data:
                print(f"[{timestamp_str}] ❌ No VS Code processes found")
                time.sleep(interval)
                continue
            
            total_memory = 0
            total_vms = 0
            total_cpu = 0
            process_count = len(process_data)
            
            # Sort processes by memory usage (highest first)
            processes_with_memory = []
            
            for proc_data in process_data:
                try:
                    proc = proc_data['process']
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()
                    
                    rss = memory_info.rss  # Resident Set Size (physical memory)
                    vms = memory_info.vms  # Virtual Memory Size
                    
                    total_memory += rss
                    total_vms += vms
                    total_cpu += cpu_percent
                    
                    processes_with_memory.append({
                        'pid': proc.pid,
                        'type': proc_data['type'],
                        'name': proc_data['name'],
                        'rss': rss,
                        'vms': vms,
                        'cpu': cpu_percent
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Save to database if enabled
            if db and run_id:
                db.add_measurement(
                    run_id=run_id,
                    timestamp=timestamp,
                    process_count=len(processes_with_memory),
                    total_rss_bytes=total_memory,
                    total_vms_bytes=total_vms,
                    process_data=processes_with_memory,
                    measurement_index=measurement_count,
                    notes=f'Measurement {measurement_count}'
                )
            
            # Sort by memory usage (RSS) descending
            processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
            
            print(f"\n[{timestamp_str}] 📈 Found {process_count} VS Code process(es) - Sorted by Memory Usage:")
            print("-" * 100)
            print(f"{'#':>2} {'PID':>6} {'RAM':>12} {'Virtual':>12} {'CPU':>6} {'Process Type':<25}")
            print("-" * 100)
            
            for i, proc_info in enumerate(processes_with_memory, 1):
                # Highlight high memory processes
                memory_indicator = "🔥" if proc_info['rss'] > 200 * 1024 * 1024 else "📊"  # 200MB threshold
                
                print(f"{memory_indicator} {i:2d} {proc_info['pid']:6d} "
                      f"{format_bytes(proc_info['rss']):>12s} "
                      f"{format_bytes(proc_info['vms']):>12s} "
                      f"{proc_info['cpu']:5.1f}% "
                      f"{proc_info['type']:<25}")
            
            print("-" * 100)
            print(f"📊 TOTALS: RAM: {format_bytes(total_memory):>12s} | "
                  f"CPU: {total_cpu:5.1f}% | "
                  f"Processes: {process_count}")
            
            # Show top memory consumers
            if processes_with_memory:
                top_3 = processes_with_memory[:3]
                print(f"\n🏆 TOP MEMORY CONSUMERS:")
                for i, proc in enumerate(top_3, 1):
                    percentage = (proc['rss'] / total_memory) * 100
                    print(f"  {i}. {proc['type']:<25} - {format_bytes(proc['rss']):>10s} ({percentage:.1f}%)")
            
            # Store measurement for summary
            measurements.append({
                'timestamp': timestamp,
                'total_memory': total_memory,
                'total_cpu': total_cpu,
                'process_count': process_count,
                'processes': processes_with_memory.copy()
            })
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
        if db and run_id:
            db.end_monitoring_run(run_id, measurement_count, 'interrupted', 'Monitoring stopped by user')
    
    # End database run if successful
    if db and run_id:
        db.end_monitoring_run(run_id, measurement_count, 'completed', 'Monitoring completed successfully')
        print(f"💾 Data saved to database (Run ID: {run_id}, {measurement_count} measurements)")
    
    # Print detailed summary
    if measurements:
        print("\n" + "=" * 100)
        print("📋 DETAILED SUMMARY")
        print("=" * 100)
        
        total_measurements = len(measurements)
        avg_memory = sum(m['total_memory'] for m in measurements) / total_measurements
        max_memory = max(m['total_memory'] for m in measurements)
        min_memory = min(m['total_memory'] for m in measurements)
        
        avg_cpu = sum(m['total_cpu'] for m in measurements) / total_measurements
        max_cpu = max(m['total_cpu'] for m in measurements)
        
        avg_processes = sum(m['process_count'] for m in measurements) / total_measurements
        
        print(f"📊 Memory Usage:")
        print(f"   Average: {format_bytes(avg_memory)}")
        print(f"   Maximum: {format_bytes(max_memory)}")
        print(f"   Minimum: {format_bytes(min_memory)}")
        print(f"\n🔥 CPU Usage:")
        print(f"   Average: {avg_cpu:.1f}%")
        print(f"   Maximum: {max_cpu:.1f}%")
        print(f"\n⚙️  Process Count:")
        print(f"   Average: {avg_processes:.1f}")
        print(f"\n📈 Total Measurements: {total_measurements}")
        
        # Analyze process types over time
        process_type_stats = {}
        for measurement in measurements:
            for proc in measurement['processes']:
                proc_type = proc['type']
                if proc_type not in process_type_stats:
                    process_type_stats[proc_type] = {'total_memory': 0, 'count': 0, 'max_memory': 0}
                
                process_type_stats[proc_type]['total_memory'] += proc['rss']
                process_type_stats[proc_type]['count'] += 1
                process_type_stats[proc_type]['max_memory'] = max(
                    process_type_stats[proc_type]['max_memory'], 
                    proc['rss']
                )
        
        print(f"\n🔍 PROCESS TYPE ANALYSIS:")
        print("-" * 80)
        print(f"{'Process Type':<25} {'Avg Memory':>12} {'Max Memory':>12} {'Occurrences':>12}")
        print("-" * 80)
        
        # Sort by average memory usage
        sorted_types = sorted(process_type_stats.items(), 
                            key=lambda x: x[1]['total_memory'] / x[1]['count'], 
                            reverse=True)
        
        for proc_type, stats in sorted_types:
            avg_mem = stats['total_memory'] / stats['count']
            max_mem = stats['max_memory']
            count = stats['count']
            
            indicator = "🔥" if avg_mem > 200 * 1024 * 1024 else "📊"
            print(f"{indicator} {proc_type:<23} "
                  f"{format_bytes(avg_mem):>12s} "
                  f"{format_bytes(max_mem):>12s} "
                  f"{count:>12d}")
        
        # Memory usage recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        high_memory_types = [t for t, s in sorted_types 
                           if s['total_memory'] / s['count'] > 200 * 1024 * 1024]
        
        if high_memory_types:
            print("   High memory usage detected in:")
            for proc_type in high_memory_types[:3]:
                print(f"   • {proc_type}")
            print("   Consider:")
            print("   - Closing unused editor tabs")
            print("   - Disabling unnecessary extensions")
            print("   - Restarting VS Code periodically")
            print("   - Using workspace-specific extension profiles")
        else:
            print("   ✅ Memory usage appears normal for your setup")

def analyze_repo_memory_usage(process_data):
    """Analyze memory usage specifically for large repository scenarios"""
    print("🔍 ANALYZING MEMORY USAGE FOR LARGE REPOSITORY")
    print("=" * 80)
    
    # Collect detailed process information
    processes_with_memory = []
    total_memory = 0
    
    for proc_data in process_data:
        try:
            proc = proc_data['process']
            memory_info = proc.memory_info()
            cpu_percent = proc.cpu_percent()
            
            rss = memory_info.rss
            vms = memory_info.vms
            total_memory += rss
            
            # Try to get additional info
            try:
                open_files = len(proc.open_files())
                connections = len(proc.connections())
                threads = proc.num_threads()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = connections = threads = 0
            
            processes_with_memory.append({
                'pid': proc.pid,
                'type': proc_data['type'],
                'name': proc_data['name'],
                'rss': rss,
                'vms': vms,
                'cpu': cpu_percent,
                'open_files': open_files,
                'connections': connections,
                'threads': threads,
                'cmdline': proc_data['cmdline']
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
    
    print(f"📊 Total VS Code Memory Usage: {format_bytes(total_memory)}")
    print(f"🔢 Total Processes: {len(processes_with_memory)}")
    print()
    
    # Show top memory consumers with detailed info
    print("🏆 TOP MEMORY CONSUMERS:")
    print("-" * 120)
    print(f"{'#':>2} {'PID':>6} {'RAM':>10} {'Threads':>8} {'Files':>6} {'Conn':>5} {'Process Type':<25} {'Details'}")
    print("-" * 120)
    
    for i, proc in enumerate(processes_with_memory[:10], 1):  # Top 10
        memory_mb = proc['rss'] / (1024 * 1024)
        indicator = "🔥" if memory_mb > 200 else "⚠️" if memory_mb > 100 else "📊"
        
        # Extract useful details from command line
        details = extract_process_details(proc['cmdline'], proc['type'])
        
        print(f"{indicator} {i:2d} {proc['pid']:6d} "
              f"{format_bytes(proc['rss']):>10s} "
              f"{proc['threads']:7d} "
              f"{proc['open_files']:5d} "
              f"{proc['connections']:4d} "
              f"{proc['type']:<25} "
              f"{details}")
    
    print("-" * 120)
    
    # Memory usage by process type
    print("\n📈 MEMORY BREAKDOWN BY PROCESS TYPE:")
    type_stats = {}
    for proc in processes_with_memory:
        proc_type = proc['type']
        if proc_type not in type_stats:
            type_stats[proc_type] = {
                'memory': 0, 'count': 0, 'max_memory': 0, 
                'total_threads': 0, 'total_files': 0
            }
        
        type_stats[proc_type]['memory'] += proc['rss']
        type_stats[proc_type]['count'] += 1
        type_stats[proc_type]['max_memory'] = max(type_stats[proc_type]['max_memory'], proc['rss'])
        type_stats[proc_type]['total_threads'] += proc['threads']
        type_stats[proc_type]['total_files'] += proc['open_files']
    
    print("-" * 100)
    print(f"{'Process Type':<25} {'Total':>10} {'Avg':>10} {'Max':>10} {'Count':>5} {'Threads':>8} {'Files':>6}")
    print("-" * 100)
    
    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]['memory'], reverse=True)
    for proc_type, stats in sorted_types:
        avg_memory = stats['memory'] / stats['count']
        percentage = (stats['memory'] / total_memory) * 100
        
        indicator = "🔥" if percentage > 25 else "⚠️" if percentage > 10 else "📊"
        
        print(f"{indicator} {proc_type:<23} "
              f"{format_bytes(stats['memory']):>10s} "
              f"{format_bytes(avg_memory):>10s} "
              f"{format_bytes(stats['max_memory']):>10s} "
              f"{stats['count']:4d} "
              f"{stats['total_threads']:7d} "
              f"{stats['total_files']:5d}")
    
    print("-" * 100)
    
    # Large repository specific analysis
    print("\n🔍 LARGE REPOSITORY ANALYSIS:")
    
    # Check for signs of large repository issues
    window_processes = [p for p in processes_with_memory if 'Window' in p['type']]
    extension_processes = [p for p in processes_with_memory if 'Extension' in p['type']]
    language_servers = [p for p in processes_with_memory if 'Language Server' in p['type']]
    
    issues_found = []
    recommendations = []
    
    # Check for high memory window processes
    high_memory_windows = [p for p in window_processes if p['rss'] > 500 * 1024 * 1024]  # 500MB
    if high_memory_windows:
        issues_found.append(f"High memory window processes: {len(high_memory_windows)}")
        recommendations.extend([
            "Close unused editor tabs",
            "Split large files across multiple windows",
            "Consider using VS Code's 'workbench.editor.limit.enabled' setting"
        ])
    
    # Check for many extension processes
    if len(extension_processes) > 5:
        issues_found.append(f"Many extension processes: {len(extension_processes)}")
        recommendations.extend([
            "Review installed extensions and disable unused ones",
            "Use workspace-specific extension profiles",
            "Consider lightweight alternatives to heavy extensions"
        ])
    
    # Check total memory usage
    total_gb = total_memory / (1024 * 1024 * 1024)
    if total_gb > 2:
        issues_found.append(f"High total memory usage: {total_gb:.1f}GB")
        recommendations.extend([
            "Restart VS Code periodically",
            "Close and reopen the workspace",
            "Consider increasing system RAM"
        ])
    
    # Check for high file handle usage
    total_files = sum(p['open_files'] for p in processes_with_memory)
    if total_files > 1000:
        issues_found.append(f"High file handle usage: {total_files}")
        recommendations.extend([
            "Check for file watcher issues",
            "Review files.watcherExclude settings",
            "Consider excluding build/node_modules directories"
        ])
    
    if issues_found:
        print("⚠️  ISSUES DETECTED:")
        for issue in issues_found:
            print(f"   • {issue}")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in set(recommendations):  # Remove duplicates
            print(f"   • {rec}")
    else:
        print("✅ No major issues detected with current memory usage")
    
    print(f"\n📋 VS Code Settings to Consider for Large Repositories:")
    print('   • "files.watcherExclude": {"**/node_modules/**": true}')
    print('   • "search.exclude": {"**/node_modules": true, "**/dist": true}')
    print('   • "typescript.disableAutomaticTypeAcquisition": true')
    print('   • "workbench.editor.limit.enabled": true')
    print('   • "workbench.editor.limit.value": 10')

def extract_process_details(cmdline, proc_type):
    """Extract meaningful details from command line arguments"""
    cmdline_str = ' '.join(cmdline)
    
    if 'Window' in proc_type:
        # Try to find workspace or file info
        for arg in cmdline:
            if arg.startswith('/') and ('workspace' in arg or 'project' in arg or len(arg) > 50):
                return f"Workspace: ...{arg[-30:]}"
        return "Main editor window"
    
    elif 'Extension' in proc_type:
        # Look for extension identifiers
        for arg in cmdline:
            if '.' in arg and len(arg) > 5 and len(arg) < 50:
                if any(ext in arg for ext in ['vscode', 'ms-', 'redhat', 'github']):
                    return f"Extension: {arg}"
        return "Extension host"
    
    elif 'Language Server' in proc_type:
        # Look for language server info
        for arg in cmdline:
            if any(lang in arg.lower() for lang in ['typescript', 'python', 'javascript', 'java', 'go']):
                return f"Language: {arg}"
        return "Language server"
    
    return "Standard process"

def monitor_freeze_patterns(interval=5, duration=600):
    """Monitor memory patterns associated with UI freezing during Copilot usage"""
    print(f"🧊 Monitoring UI Freeze Patterns...")
    print(f"📊 Checking every {interval} seconds for {duration} seconds")
    print("🎯 Focus: Memory oscillations, CPU spikes, and process behavior during freezes")
    print("=" * 120)
    
    start_time = time.time()
    measurements = []
    freeze_events = []
    
    # Track baseline for anomaly detection
    baseline_memory = {}
    
    try:
        measurement_count = 0
        while time.time() - start_time < duration:
            measurement_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            process_data = get_vscode_processes()
            
            if not process_data:
                print(f"[{timestamp}] ❌ No VS Code processes found")
                time.sleep(interval)
                continue
            
            # Collect process data with focus on key processes
            current_processes = {}
            total_memory = 0
            high_cpu_processes = []
            memory_spikes = []
            
            for proc_data in process_data:
                try:
                    proc = proc_data['process']
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()
                    
                    rss = memory_info.rss
                    total_memory += rss
                    
                    proc_info = {
                        'pid': proc.pid,
                        'type': proc_data['type'],
                        'rss': rss,
                        'cpu': cpu_percent,
                        'timestamp': timestamp
                    }
                    
                    current_processes[proc.pid] = proc_info
                    
                    # Detect high CPU (potential freeze indicators)
                    if cpu_percent > 50:
                        high_cpu_processes.append(proc_info)
                    
                    # Detect memory spikes compared to baseline
                    if proc.pid in baseline_memory:
                        baseline_rss = baseline_memory[proc.pid]['rss']
                        if rss > baseline_rss * 1.5:  # 50% increase
                            memory_spikes.append({
                                'pid': proc.pid,
                                'type': proc_data['type'],
                                'baseline': baseline_rss,
                                'current': rss,
                                'increase_pct': ((rss - baseline_rss) / baseline_rss) * 100
                            })
                    else:
                        # Establish baseline
                        baseline_memory[proc.pid] = {'rss': rss, 'type': proc_data['type']}
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort processes by memory for display
            sorted_processes = sorted(current_processes.values(), key=lambda x: x['rss'], reverse=True)
            
            # Detect potential freeze conditions
            freeze_indicators = []
            if high_cpu_processes:
                freeze_indicators.append(f"HIGH-CPU: {len(high_cpu_processes)} processes")
            if memory_spikes:
                freeze_indicators.append(f"MEM-SPIKE: {len(memory_spikes)} processes")
            if total_memory > 3 * 1024 * 1024 * 1024:  # 3GB threshold
                freeze_indicators.append("HIGH-TOTAL-MEM")
            
            # Display current state
            status_icon = "🔥" if freeze_indicators else "📊"
            print(f"\n[{timestamp}] {status_icon} Measurement #{measurement_count} - Total RAM: {format_bytes(total_memory)}")
            
            if freeze_indicators:
                print(f"⚠️  FREEZE INDICATORS: {', '.join(freeze_indicators)}")
                freeze_events.append({
                    'timestamp': timestamp,
                    'measurement': measurement_count,
                    'indicators': freeze_indicators,
                    'total_memory': total_memory,
                    'high_cpu_procs': high_cpu_processes.copy(),
                    'memory_spikes': memory_spikes.copy()
                })
            
            print("-" * 120)
            print(f"{'#':>2} {'PID':>6} {'RAM':>12} {'CPU':>6} {'Type':<25} {'Status'}")
            print("-" * 120)
            
            for i, proc in enumerate(sorted_processes[:8], 1):  # Top 8 processes
                # Determine status indicators
                status_parts = []
                if proc['cpu'] > 50:
                    status_parts.append("HIGH-CPU")
                if proc['pid'] in [spike['pid'] for spike in memory_spikes]:
                    spike = next(s for s in memory_spikes if s['pid'] == proc['pid'])
                    status_parts.append(f"SPIKE+{spike['increase_pct']:.0f}%")
                
                status = " | ".join(status_parts) if status_parts else "-"
                cpu_icon = "🔥" if proc['cpu'] > 50 else "📊"
                
                print(f"{cpu_icon} {i:2d} {proc['pid']:6d} "
                      f"{format_bytes(proc['rss']):>12s} "
                      f"{proc['cpu']:5.1f}% "
                      f"{proc['type']:<25} "
                      f"{status}")
            
            # Show memory spikes detail
            if memory_spikes:
                print(f"\n🚨 MEMORY SPIKES DETECTED:")
                for spike in memory_spikes:
                    print(f"   PID {spike['pid']} ({spike['type']}): "
                          f"{format_bytes(spike['baseline'])} → {format_bytes(spike['current'])} "
                          f"(+{spike['increase_pct']:.1f}%)")
            
            # Store measurement
            measurements.append({
                'timestamp': timestamp,
                'measurement': measurement_count,
                'total_memory': total_memory,
                'process_count': len(current_processes),
                'freeze_indicators': freeze_indicators.copy(),
                'processes': current_processes.copy()
            })
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Freeze pattern monitoring stopped by user")
    
    # Analysis and summary
    if measurements:
        print("\n" + "=" * 120)
        print("🧊 FREEZE PATTERN ANALYSIS")
        print("=" * 120)
        
        total_measurements = len(measurements)
        freeze_measurement_count = len(freeze_events)
        
        print(f"📊 SUMMARY:")
        print(f"   Total measurements: {total_measurements}")
        print(f"   Freeze events detected: {freeze_measurement_count}")
        print(f"   Freeze frequency: {(freeze_measurement_count/total_measurements)*100:.1f}%")
        
        if freeze_events:
            print(f"\n🚨 FREEZE EVENT ANALYSIS:")
            
            # Group freeze indicators
            indicator_counts = {}
            for event in freeze_events:
                for indicator in event['indicators']:
                    indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
            
            print(f"   Most common freeze indicators:")
            for indicator, count in sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {indicator}: {count} times ({(count/freeze_measurement_count)*100:.1f}%)")
            
            # Memory pattern during freezes
            freeze_memories = [event['total_memory'] for event in freeze_events]
            avg_freeze_memory = sum(freeze_memories) / len(freeze_memories)
            max_freeze_memory = max(freeze_memories)
            
            all_memories = [m['total_memory'] for m in measurements]
            avg_normal_memory = sum(all_memories) / len(all_memories)
            
            print(f"\n📈 MEMORY PATTERNS:")
            print(f"   Average memory during freezes: {format_bytes(avg_freeze_memory)}")
            print(f"   Maximum memory during freeze: {format_bytes(max_freeze_memory)}")
            print(f"   Average memory overall: {format_bytes(avg_normal_memory)}")
            print(f"   Memory increase during freezes: {((avg_freeze_memory/avg_normal_memory-1)*100):+.1f}%")
        
        # Process behavior analysis
        print(f"\n🔍 PROCESS BEHAVIOR PATTERNS:")
        process_freeze_involvement = {}
        
        for event in freeze_events:
            # Count high CPU processes
            for proc in event['high_cpu_procs']:
                pid = proc['pid']
                proc_type = proc['type']
                key = f"{proc_type} (PID {pid})"
                process_freeze_involvement[key] = process_freeze_involvement.get(key, 0) + 1
            
            # Count memory spike processes
            for spike in event['memory_spikes']:
                pid = spike['pid']
                proc_type = spike['type']
                key = f"{proc_type} (PID {pid})"
                process_freeze_involvement[key] = process_freeze_involvement.get(key, 0) + 1
        
        if process_freeze_involvement:
            print(f"   Processes most involved in freeze events:")
            sorted_involvement = sorted(process_freeze_involvement.items(), 
                                      key=lambda x: x[1], reverse=True)
            for proc_info, count in sorted_involvement[:5]:
                print(f"   • {proc_info}: {count} freeze events")
        
        # Recommendations based on findings
        print(f"\n💡 FREEZE PATTERN RECOMMENDATIONS:")
        
        if freeze_measurement_count > total_measurements * 0.3:  # >30% freeze events
            print("   ⚠️  HIGH FREEZE FREQUENCY DETECTED")
            print("   • Consider reducing Copilot usage intensity")
            print("   • Try smaller context windows for Copilot queries")
            print("   • Monitor during specific Copilot operations")
        
        if 'HIGH-TOTAL-MEM' in indicator_counts:
            print("   ⚠️  MEMORY PRESSURE CAUSING FREEZES")
            print("   • Consider increasing system RAM")
            print("   • Close other applications during intensive Copilot use")
            print("   • Monitor for memory leaks in extensions")
        
        if any('HIGH-CPU' in indicator for indicator in indicator_counts):
            print("   ⚠️  CPU SATURATION DURING FREEZES")
            print("   • Copilot queries may be computationally intensive")
            print("   • Consider limiting concurrent language servers")
            print("   • Monitor specific language server configurations")
        
        print(f"\n🎯 NEXT STEPS:")
        print("   1. Run this monitoring during different Copilot usage patterns")
        print("   2. Compare freeze patterns with/without Git operations")
        print("   3. Test with different repository sizes")
        print("   4. Experiment with Copilot settings adjustments")

def run_git_isolation_test():
    """Run comprehensive Git isolation testing"""
    import os
    import shutil
    from pathlib import Path
    
    print("🔬 STARTING GIT ISOLATION TEST")
    print("=" * 80)
    
    # Find Git repositories in current directory and subdirectories
    current_dir = os.getcwd()
    print(f"📂 Scanning for Git repositories in: {current_dir}")
    
    git_repos = []
    for root, dirs, files in os.walk(current_dir):
        if '.git' in dirs:
            git_repos.append(root)
            dirs.remove('.git')  # Don't recurse into .git directories
    
    if not git_repos:
        print("❌ No Git repositories found in current directory")
        print("   Make sure you're running this in a directory with a .git folder")
        return
    
    print(f"📊 Found {len(git_repos)} Git repository(ies):")
    for i, repo in enumerate(git_repos, 1):
        rel_path = os.path.relpath(repo, current_dir)
        print(f"   {i}. {rel_path if rel_path != '.' else 'Current directory'}")
    
    # Phase 1: Test WITH Git
    print(f"\n" + "=" * 80)
    print("📈 PHASE 1: BASELINE WITH GIT INTEGRATION")
    print("=" * 80)
    print("Testing memory patterns with Git integration enabled...")
    print("Use Copilot normally and note any UI freezing behavior.\n")
    
    input("Press Enter when ready to start baseline monitoring...")
    
    print("🔄 Starting baseline monitoring (with Git)...")
    print("   (Press Ctrl+C when you've experienced the freezing behavior)")
    
    try:
        baseline_results = monitor_git_isolation_phase(
            phase_name="WITH_GIT",
            duration=300,  # 5 minutes
            interval=10
        )
    except KeyboardInterrupt:
        print("\n⏸️  Baseline monitoring stopped by user")
        baseline_results = {"stopped_early": True}
    
    # Phase 2: Disable Git
    print(f"\n" + "=" * 80)
    print("🚫 PHASE 2: DISABLING GIT INTEGRATION")
    print("=" * 80)
    
    print("We'll now temporarily disable Git integration. Choose method:")
    print("1. Move .git folders (safest, completely removes Git)")
    print("2. Disable Git in VS Code settings (keeps .git, disables integration)")
    print("3. Skip Git removal (manual testing)")
    
    while True:
        choice = input("\nSelect method (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3")
    
    git_disabled = False
    backup_info = []
    
    if choice == '1':
        print(f"\n📦 Moving .git folders to temporary backup...")
        for repo in git_repos:
            git_path = os.path.join(repo, '.git')
            backup_path = os.path.join(repo, '.git_backup_isolation_test')
            
            try:
                if os.path.exists(git_path):
                    shutil.move(git_path, backup_path)
                    backup_info.append((repo, git_path, backup_path))
                    rel_repo = os.path.relpath(repo, current_dir)
                    print(f"   ✅ Moved: {rel_repo}/.git → {rel_repo}/.git_backup_isolation_test")
            except Exception as e:
                print(f"   ❌ Error moving {git_path}: {e}")
        
        git_disabled = True
        print(f"\n⚠️  Git integration disabled. You should restart VS Code for full effect.")
        
    elif choice == '2':
        print(f"\n⚙️  To disable Git in VS Code settings, add this to your settings.json:")
        print('   "git.enabled": false,')
        print('   "git.autorefresh": false,')
        print('   "git.decorations.enabled": false')
        print(f"\nAfter changing settings, restart VS Code.")
        git_disabled = True
        
    elif choice == '3':
        print(f"\n⏭️  Skipping automatic Git removal.")
        print("   You can manually disable Git or test with current setup.")
    
    if git_disabled or choice == '3':
        print(f"\n📋 Next steps:")
        print("1. Restart VS Code if you haven't already")
        print("2. Open your large repository")
        print("3. Try the same Copilot operations that caused freezing")
        print("4. Come back here to continue monitoring\n")
        
        input("Press Enter when VS Code is restarted and ready for testing...")
        
        # Phase 3: Test WITHOUT Git
        print(f"\n" + "=" * 80)
        print("📉 PHASE 3: TESTING WITHOUT GIT INTEGRATION")
        print("=" * 80)
        print("Testing memory patterns WITHOUT Git integration...")
        print("Try the same Copilot operations and compare behavior.\n")
        
        input("Press Enter when ready to start no-Git monitoring...")
        
        print("🔄 Starting no-Git monitoring...")
        print("   (Press Ctrl+C when you've tested equivalent operations)")
        
        try:
            no_git_results = monitor_git_isolation_phase(
                phase_name="WITHOUT_GIT",
                duration=300,  # 5 minutes
                interval=10
            )
        except KeyboardInterrupt:
            print("\n⏸️  No-Git monitoring stopped by user")
            no_git_results = {"stopped_early": True}
        
        # Compare results
        print(f"\n" + "=" * 80)
        print("📊 COMPARISON ANALYSIS")
        print("=" * 80)
        
        compare_git_isolation_results(baseline_results, no_git_results)
    
    # Phase 4: Restore Git
    if backup_info:
        print(f"\n" + "=" * 80)
        print("🔄 RESTORING GIT INTEGRATION")
        print("=" * 80)
        
        restore = input("❓ Restore Git folders now? (Y/n): ").lower()
        if restore != 'n':
            print(f"\n📦 Restoring .git folders...")
            for repo, original_path, backup_path in backup_info:
                try:
                    if os.path.exists(backup_path):
                        shutil.move(backup_path, original_path)
                        rel_repo = os.path.relpath(repo, current_dir)
                        print(f"   ✅ Restored: {rel_repo}/.git")
                except Exception as e:
                    print(f"   ❌ Error restoring {backup_path}: {e}")
            
            print(f"\n✅ Git integration restored. Restart VS Code to re-enable Git features.")
        else:
            print(f"\n⚠️  Git folders left as backups. To restore manually:")
            for repo, original_path, backup_path in backup_info:
                rel_repo = os.path.relpath(repo, current_dir)
                print(f"   mv '{backup_path}' '{original_path}'")

def monitor_git_isolation_phase(phase_name, duration=300, interval=10):
    """Monitor memory during a specific phase of Git isolation testing"""
    print(f"🔍 Monitoring Phase: {phase_name}")
    print(f"📊 Duration: {duration}s, Interval: {interval}s")
    print("=" * 60)
    
    start_time = time.time()
    measurements = []
    
    while time.time() - start_time < duration:
        timestamp = datetime.now().strftime("%H:%M:%S")
        process_data = get_vscode_processes()
        
        if not process_data:
            print(f"[{timestamp}] ❌ No VS Code processes found")
            time.sleep(interval)
            continue
        
        # Collect key metrics
        total_memory = 0
        git_processes = 0
        window_memory = 0
        language_server_memory = 0
        
        process_breakdown = []
        
        for proc_data in process_data:
            try:
                proc = proc_data['process']
                memory_info = proc.memory_info()
                rss = memory_info.rss
                total_memory += rss
                
                proc_type = proc_data['type']
                if 'git' in proc_type.lower() or any('git' in arg.lower() for arg in proc_data.get('cmdline', [])):
                    git_processes += 1
                
                if 'Window' in proc_type:
                    window_memory += rss
                elif 'Language Server' in proc_type:
                    language_server_memory += rss
                
                process_breakdown.append({
                    'type': proc_type,
                    'memory': rss,
                    'pid': proc.pid
                })
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory for display
        process_breakdown.sort(key=lambda x: x['memory'], reverse=True)
        
        print(f"[{timestamp}] Total: {format_bytes(total_memory)} | "
              f"Window: {format_bytes(window_memory)} | "
              f"LangSrv: {format_bytes(language_server_memory)} | "
              f"Git Procs: {git_processes}")
        
        # Show top 3 processes
        for i, proc in enumerate(process_breakdown[:3], 1):
            print(f"   {i}. {proc['type']}: {format_bytes(proc['memory'])}")
        
        measurements.append({
            'timestamp': timestamp,
            'total_memory': total_memory,
            'window_memory': window_memory,
            'language_server_memory': language_server_memory,
            'git_processes': git_processes,
            'process_breakdown': process_breakdown.copy()
        })
        
        time.sleep(interval)
    
    return {
        'phase': phase_name,
        'measurements': measurements,
        'duration': duration,
        'interval': interval
    }

def compare_git_isolation_results(baseline_results, no_git_results):
    """Compare results from Git isolation testing"""
    
    if baseline_results.get('stopped_early') and no_git_results.get('stopped_early'):
        print("⚠️  Both phases stopped early - limited comparison available")
        return
    
    if baseline_results.get('stopped_early'):
        print("⚠️  Baseline phase stopped early - limited comparison")
        baseline_measurements = []
    else:
        baseline_measurements = baseline_results.get('measurements', [])
    
    if no_git_results.get('stopped_early'):
        print("⚠️  No-Git phase stopped early - limited comparison")
        no_git_measurements = []
    else:
        no_git_measurements = no_git_results.get('measurements', [])
    
    if not baseline_measurements and not no_git_measurements:
        print("❌ No measurement data available for comparison")
        return
    
    print("📊 GIT ISOLATION TEST RESULTS")
    print("=" * 60)
    
    # Memory comparison
    if baseline_measurements and no_git_measurements:
        baseline_avg = sum(m['total_memory'] for m in baseline_measurements) / len(baseline_measurements)
        baseline_max = max(m['total_memory'] for m in baseline_measurements)
        baseline_window_avg = sum(m['window_memory'] for m in baseline_measurements) / len(baseline_measurements)
        
        no_git_avg = sum(m['total_memory'] for m in no_git_measurements) / len(no_git_measurements)
        no_git_max = max(m['total_memory'] for m in no_git_measurements)
        no_git_window_avg = sum(m['window_memory'] for m in no_git_measurements) / len(no_git_measurements)
        
        print(f"📈 MEMORY COMPARISON:")
        print(f"                    WITH Git    WITHOUT Git    Difference")
        print(f"   Average Total:   {format_bytes(baseline_avg):>10s}  {format_bytes(no_git_avg):>10s}  {((no_git_avg/baseline_avg-1)*100):+6.1f}%")
        print(f"   Maximum Total:   {format_bytes(baseline_max):>10s}  {format_bytes(no_git_max):>10s}  {((no_git_max/baseline_max-1)*100):+6.1f}%")
        print(f"   Window Process:  {format_bytes(baseline_window_avg):>10s}  {format_bytes(no_git_window_avg):>10s}  {((no_git_window_avg/baseline_window_avg-1)*100):+6.1f}%")
        
        # Determine results
        memory_reduction = (baseline_avg - no_git_avg) / baseline_avg
        
        print(f"\n🎯 RESULTS INTERPRETATION:")
        
        if memory_reduction > 0.2:  # 20% reduction
            print("✅ SIGNIFICANT IMPROVEMENT: Git removal reduced memory usage by >20%")
            print("   → Git integration was a major contributor to memory issues")
            print("   → Consider optimizing Git settings or using external Git")
        elif memory_reduction > 0.1:  # 10% reduction
            print("⚠️  MODERATE IMPROVEMENT: Git removal reduced memory usage by 10-20%")
            print("   → Git integration contributes to memory issues but isn't the only cause")
            print("   → Investigate other factors like Copilot context size")
        elif abs(memory_reduction) < 0.1:  # Less than 10% change
            print("❌ NO SIGNIFICANT CHANGE: Memory usage similar with/without Git")
            print("   → Git integration is NOT the primary cause of memory issues")
            print("   → Focus on Copilot settings, language servers, or VS Code configuration")
        else:  # Memory increased without Git
            print("🤔 UNEXPECTED RESULT: Memory usage increased without Git")
            print("   → This suggests Git integration was actually helping manage memory")
            print("   → Other processes may be compensating for missing Git functionality")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if memory_reduction > 0.1:
            print("   • Optimize Git integration settings:")
            print('     - "git.autorefresh": false')
            print('     - "files.watcherExclude": {"**/.git/**": true}')
            print("   • Consider using Git from command line for large repos")
            print("   • Experiment with Git-related VS Code extensions")
        else:
            print("   • Git is not the bottleneck - focus on:")
            print("   • Copilot context size and query patterns")
            print("   • Language server configurations")
            print("   • VS Code memory settings and limits")
            print("   • System RAM and performance optimization")
    
    else:
        print("📊 Partial data available - manual observation needed")
        print("   Compare your experience:")
        print("   • Did UI freezing improve without Git?")
        print("   • Were Copilot operations more responsive?")
        print("   • Did memory usage feel more stable?")

def analyze_copilot_focused_memory(process_data):
    """Analyze memory usage with focus on Copilot after ruling out Git"""
    print("\n🤖 COPILOT-FOCUSED MEMORY ANALYSIS (Post-Git Isolation)")
    print("=" * 80)
    print("Git has been ruled out as primary cause. Focusing on Copilot-specific issues.")
    
    # Collect detailed process information
    processes_with_memory = []
    total_memory = 0
    
    # Detect Copilot and extension-related processes
    extension_hosts = []
    language_servers = []
    window_processes = []
    
    for proc_data in process_data:
        try:
            proc = proc_data['process']
            memory_info = proc.memory_info()
            cpu_percent = proc.cpu_percent()
            
            rss = memory_info.rss
            vms = memory_info.vms
            total_memory += rss
            
            # Get additional process info
            try:
                open_files = len(proc.open_files())
                threads = proc.num_threads()
                create_time = proc.create_time()
                uptime = time.time() - create_time
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = threads = uptime = 0
            
            proc_info = {
                'pid': proc.pid,
                'type': proc_data['type'],
                'name': proc_data['name'],
                'rss': rss,
                'vms': vms,
                'cpu': cpu_percent,
                'open_files': open_files,
                'threads': threads,
                'uptime': uptime,
                'cmdline': proc_data['cmdline']
            }
            
            processes_with_memory.append(proc_info)
            
            # Categorize for Copilot analysis
            if 'Extension Host' in proc_data['type']:
                extension_hosts.append(proc_info)
            elif 'Language Server' in proc_data['type']:
                language_servers.append(proc_info)
            elif 'Window' in proc_data['type']:
                window_processes.append(proc_info)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
    
    print(f"📊 Total VS Code Memory Usage: {format_bytes(total_memory)}")
    print(f"🔢 Total Processes: {len(processes_with_memory)}")
    
    # Extension Host Analysis (Primary Copilot suspects)
    print(f"\n🎯 EXTENSION HOST ANALYSIS (Primary Copilot Processes):")
    print("-" * 80)
    
    if extension_hosts:
        total_ext_memory = sum(p['rss'] for p in extension_hosts)
        ext_percentage = (total_ext_memory / total_memory) * 100
        
        print(f"📈 Extension Hosts Summary:")
        print(f"   • Count: {len(extension_hosts)}")
        print(f"   • Total Memory: {format_bytes(total_ext_memory)} ({ext_percentage:.1f}% of total)")
        print(f"   • Average per Extension Host: {format_bytes(total_ext_memory / len(extension_hosts))}")
        
        # Check for problematic extension hosts
        high_memory_exts = [p for p in extension_hosts if p['rss'] > 100 * 1024 * 1024]  # 100MB
        if high_memory_exts:
            print(f"\n⚠️  HIGH MEMORY EXTENSION HOSTS:")
            for ext in high_memory_exts:
                uptime_str = f"{ext['uptime']/3600:.1f}h" if ext['uptime'] > 0 else "N/A"
                print(f"   • PID {ext['pid']}: {format_bytes(ext['rss'])} "
                      f"(CPU: {ext['cpu']:.1f}%, Uptime: {uptime_str})")
        else:
            print(f"   ✅ Extension Host memory usage appears normal")
    else:
        print(f"   ❌ No Extension Host processes found")
    
    # Language Server Analysis
    print(f"\n🔍 LANGUAGE SERVER ANALYSIS:")
    print("-" * 80)
    
    if language_servers:
        total_ls_memory = sum(p['rss'] for p in language_servers)
        ls_percentage = (total_ls_memory / total_memory) * 100
        
        print(f"📈 Language Servers Summary:")
        print(f"   • Count: {len(language_servers)}")
        print(f"   • Total Memory: {format_bytes(total_ls_memory)} ({ls_percentage:.1f}% of total)")
        
        # Check for high CPU language servers (sign of overwork)
        high_cpu_ls = [p for p in language_servers if p['cpu'] > 5]
        if high_cpu_ls:
            print(f"\n⚠️  HIGH CPU LANGUAGE SERVERS:")
            for ls in high_cpu_ls:
                print(f"   • PID {ls['pid']}: {format_bytes(ls['rss'])} "
                      f"(CPU: {ls['cpu']:.1f}%)")
        
        # Check for language servers with many open files
        high_file_ls = [p for p in language_servers if p['open_files'] > 100]
        if high_file_ls:
            print(f"\n📁 LANGUAGE SERVERS WITH MANY OPEN FILES:")
            for ls in high_file_ls:
                print(f"   • PID {ls['pid']}: {ls['open_files']} files, {format_bytes(ls['rss'])}")
    else:
        print(f"   ❌ No Language Server processes found")
    
    # Window Process Analysis
    print(f"\n🪟 WINDOW/EDITOR PROCESS ANALYSIS:")
    print("-" * 80)
    
    if window_processes:
        total_window_memory = sum(p['rss'] for p in window_processes)
        window_percentage = (total_window_memory / total_memory) * 100
        
        print(f"📈 Window Processes Summary:")
        print(f"   • Count: {len(window_processes)}")
        print(f"   • Total Memory: {format_bytes(total_window_memory)} ({window_percentage:.1f}% of total)")
        
        # Check for very high memory window processes
        huge_windows = [p for p in window_processes if p['rss'] > 500 * 1024 * 1024]  # 500MB
        if huge_windows:
            print(f"\n🔥 EXTREMELY HIGH MEMORY WINDOW PROCESSES:")
            for win in huge_windows:
                print(f"   • PID {win['pid']}: {format_bytes(win['rss'])}")
                print(f"     This likely indicates excessive context loading for Copilot")
    
    # Top memory consumers with Copilot focus
    print(f"\n🏆 TOP MEMORY CONSUMERS (Copilot Perspective):")
    print("-" * 100)
    print(f"{'#':>2} {'PID':>6} {'RAM':>10} {'CPU':>5} {'Files':>5} {'Threads':>7} {'Copilot Relevance':<20} {'Type':<20}")
    print("-" * 100)
    
    for i, proc in enumerate(processes_with_memory[:8], 1):
        # Determine Copilot relevance
        relevance = "Unknown"
        if 'Extension Host' in proc['type']:
            relevance = "HIGH (Copilot runs here)"
        elif 'Window' in proc['type']:
            relevance = "HIGH (Context loading)"
        elif 'Language Server' in proc['type']:
            relevance = "MEDIUM (Code analysis)"
        elif 'GPU Process' in proc['type']:
            relevance = "LOW (Graphics only)"
        
        memory_mb = proc['rss'] / (1024 * 1024)
        indicator = "🔥" if memory_mb > 200 else "⚠️" if memory_mb > 100 else "📊"
        
        print(f"{indicator} {i:2d} {proc['pid']:6d} "
              f"{format_bytes(proc['rss']):>10s} "
              f"{proc['cpu']:4.1f}% "
              f"{proc['open_files']:4d} "
              f"{proc['threads']:6d} "
              f"{relevance:<20s} "
              f"{proc['type']:<20s}")
    
    # Copilot-specific recommendations
    print(f"\n💡 COPILOT-SPECIFIC RECOMMENDATIONS:")
    
    total_gb = total_memory / (1024 * 1024 * 1024)
    if total_gb > 2:
        print("   🔥 HIGH TOTAL MEMORY USAGE DETECTED")
        print("   • Primary suspect: Copilot context size in large repository")
        print("   • Try reducing Copilot context scope")
        print("   • Consider workspace-specific Copilot settings")
    
    if extension_hosts and any(p['rss'] > 200 * 1024 * 1024 for p in extension_hosts):
        print("   ⚠️  HIGH EXTENSION HOST MEMORY")
        print("   • Copilot extension may be accumulating context")
        print("   • Try restarting Extension Host: Ctrl+Shift+P → 'Developer: Restart Extension Host'")
    
    if language_servers and any(p['cpu'] > 10 for p in language_servers):
        print("   ⚠️  LANGUAGE SERVERS OVERLOADED")
        print("   • Large repository causing continuous analysis")
        print("   • Consider excluding directories from language server scanning")
    
    print(f"\n🎯 NEXT TESTING STEPS:")
    print("   1. Test with smaller Copilot queries")
    print("   2. Try disabling Copilot temporarily")
    print("   3. Monitor during specific Copilot operations")
    print("   4. Test with reduced VS Code workspace scope")

def monitor_copilot_processes(focus="extension_hosts", duration=300, interval=10):
    """Monitor processes with focus on Copilot-specific behavior"""
    focus_descriptions = {
        "extension_hosts": "Extension Host processes (where Copilot runs)",
        "query_testing": "Memory behavior during Copilot queries",
        "settings_testing": "Comparison with different Copilot settings"
    }
    
    print(f"🤖 COPILOT-FOCUSED MONITORING")
    print(f"🎯 Focus: {focus_descriptions.get(focus, 'General Copilot monitoring')}")
    print(f"📊 Duration: {duration}s, Interval: {interval}s")
    
    if focus == "query_testing":
        print("\n📋 QUERY TESTING INSTRUCTIONS:")
        print("1. Start with small, simple Copilot queries")
        print("2. Gradually increase query complexity")
        print("3. Note when memory spikes occur")
        print("4. Try different types of queries (chat vs autocomplete)")
    
    elif focus == "settings_testing":
        print("\n📋 SETTINGS TESTING INSTRUCTIONS:")
        print("1. Test current settings first")
        print("2. Try reduced context settings")
        print("3. Test with Copilot disabled")
        print("4. Compare memory usage patterns")
    
    print("=" * 100)
    
    start_time = time.time()
    measurements = []
    baseline_memory = {}
    
    try:
        measurement_count = 0
        while time.time() - start_time < duration:
            measurement_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            process_data = get_vscode_processes()
            
            if not process_data:
                print(f"[{timestamp}] ❌ No VS Code processes found")
                time.sleep(interval)
                continue
            
                       
            # Filter processes based on focus
            if focus == "extension_hosts":
                target_processes = [p for p in process_data if 'Extension Host' in p['type']]
            else:
                target_processes = process_data
            
            if not target_processes:
                print(f"[{timestamp}] ❌ No target processes found")
                time.sleep(interval)
                continue
            
            # Analyze current memory state
            current_memory = {}
            total_memory = 0
            copilot_relevant_memory = 0
            
            for proc_data in target_processes:
                try:
                    proc = proc_data['process']
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()
                    
                    rss = memory_info.rss
                    total_memory += rss
                    
                    # Focus on Copilot-relevant processes
                    if any(keyword in proc_data['type'] for keyword in ['Extension Host', 'Window', 'Language Server']):
                        copilot_relevant_memory += rss
                    
                    # Calculate growth since baseline
                    growth = 0
                    growth_pct = 0
                    if proc.pid in baseline_memory:
                        growth = rss - baseline_memory[proc.pid]
                        growth_pct = (growth / baseline_memory[proc.pid]) * 100 if baseline_memory[proc.pid] > 0 else 0
                    else:
                        baseline_memory[proc.pid] = rss
                    
                    current_memory[proc.pid] = {
                        'type': proc_data['type'],
                        'rss': rss,
                        'cpu': cpu_percent,
                        'growth': growth,
                        'growth_pct': growth_pct
                    }
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Display results
            print(f"\n[{timestamp}] 🤖 Measurement #{measurement_count}")
            print(f"Total Memory: {format_bytes(total_memory)} | "
                  f"Copilot-Relevant: {format_bytes(copilot_relevant_memory)} | "
                  f"Processes: {len(current_memory)}")
            
            # Show top processes with growth information
            sorted_processes = sorted(current_memory.items(), 
                                    key=lambda x: x[1]['rss'], reverse=True)
            
            if sorted_processes:
                print("-" * 90)
                print(f"{'PID':>6} {'RAM':>10} {'Growth':>8} {'%':>6} {'CPU':>5} {'Type':<20}")
                print("-" * 90)
                
                for pid, info in sorted_processes[:5]:  # Top 5
                    growth_indicator = "📈" if info['growth_pct'] > 10 else "🔥" if info['rss'] > 200*1024*1024 else "📊"
                    
                    print(f"{growth_indicator} {pid:6d} "
                          f"{format_bytes(info['rss']):>10s} "
                          f"{format_bytes(info['growth']):>8s} "
                          f"{info['growth_pct']:5.1f}% "
                          f"{info['cpu']:4.1f}% "
                          f"{info['type']:<20s}")
            
            # Check for concerning patterns
            high_growth = [pid for pid, info in current_memory.items() if info['growth_pct'] > 20]
            if high_growth:
                print(f"⚠️  HIGH GROWTH DETECTED: {len(high_growth)} process(es)")
            
            # Store measurement
            measurements.append({
                'timestamp': timestamp,
                'measurement': measurement_count,
                'total_memory': total_memory,
                'copilot_relevant_memory': copilot_relevant_memory,
                'process_count': len(current_memory),
                'high_growth_count': len(high_growth)
            })
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Copilot monitoring stopped by user")
    
    # Analysis
    if measurements:
        print("\n" + "=" * 100)
        print("🤖 COPILOT MONITORING ANALYSIS")
        print("=" * 100)
        
        initial_memory = measurements[0]['total_memory']
        final_memory = measurements[-1]['total_memory']
        memory_change = final_memory - initial_memory
        memory_change_pct = (memory_change / initial_memory) * 100 if initial_memory > 0 else 0
        
        print(f"📈 MEMORY TREND:")
        print(f"   Initial: {format_bytes(initial_memory)}")
        print(f"   Final: {format_bytes(final_memory)}")
        print(f"   Change: {format_bytes(memory_change)} ({memory_change_pct:+.1f}%)")
        
        avg_copilot_memory = sum(m['copilot_relevant_memory'] for m in measurements) / len(measurements)
        copilot_percentage = (avg_copilot_memory / (sum(m['total_memory'] for m in measurements) / len(measurements))) * 100
        
        print(f"\n🎯 COPILOT-RELEVANT PROCESSES:")
        print(f"   Average Copilot-relevant memory: {format_bytes(avg_copilot_memory)}")
        print(f"   Percentage of total: {copilot_percentage:.1f}%")
        
        # Growth events
        high_growth_events = sum(m['high_growth_count'] for m in measurements)
        if high_growth_events > 0:
            print(f"\n⚠️  GROWTH EVENTS: {high_growth_events} detected during monitoring")
            print("   This suggests active memory accumulation")
        
        print(f"\n💡 COPILOT OPTIMIZATION RECOMMENDATIONS:")
        
        if memory_change_pct > 10:
            print("   🔥 MEMORY GROWTH DETECTED")
            print("   • Copilot appears to accumulate memory over time")
            print("   • Try restarting Extension Host periodically")
            print("   • Consider reducing Copilot context settings")
        
        if copilot_percentage > 60:
            print("   ⚠️  COPILOT PROCESSES DOMINATE MEMORY")
            print("   • Extension Hosts and related processes use majority of memory")
            print("   • Focus optimization efforts on Copilot settings")
        
        if high_growth_events > len(measurements) * 0.2:
            print("   🚨 FREQUENT MEMORY SPIKES")
            print("   • Memory growth events happening frequently")
            print("   • Investigate specific Copilot operations causing spikes")

def parse_arguments():
    """Parse command line arguments with database support"""
    parser = argparse.ArgumentParser(
        description="VS Code Memory Monitor with optional database tracking",
        add_help=False  # We'll handle help manually for backward compatibility
    )
    
    # Database options
    parser.add_argument('--db-track', action='store_true',
                       help='Enable database tracking (default: disabled)')
    parser.add_argument('--db-path', default='performance.db',
                       help='SQLite database path (default: performance.db)')
    
    # Check if we're using the new argument style or legacy style
    if any(arg.startswith('--db-') for arg in sys.argv):
        # New style with explicit database arguments
        known_args, unknown_args = parser.parse_known_args()
        
        # Parse remaining arguments manually for backward compatibility
        legacy_args = []
        mode = None
        
        for arg in unknown_args:
            if arg in ['-h', '--help', '--snapshot', '--repo-analysis', '--copilot-analysis',
                      '--freeze-detection', '--git-isolation', '--copilot-focused',
                      '--copilot-context-test', '--copilot-optimization']:
                mode = arg
            else:
                try:
                    # Try to parse as integer (interval/duration)
                    int(arg)
                    legacy_args.append(arg)
                except ValueError:
                    # Unknown argument
                    pass
        
        return known_args, mode, legacy_args
    else:
        # Legacy style - no database arguments
        return argparse.Namespace(db_track=False, db_path='performance.db'), None, sys.argv[1:]


def main():
    """Main function with command line argument handling and database support"""
    # Parse arguments
    db_args, mode, legacy_args = parse_arguments()
    
    # Initialize database if requested
    db = None
    if db_args.db_track:
        if not DATABASE_AVAILABLE:
            print("❌ Database functionality not available (missing database.py)")
            print("   Running in console-only mode...")
        else:
            try:
                db = MemoryMonitorDB(db_args.db_path)
                print(f"📊 Database tracking enabled: {db_args.db_path}")
            except Exception as e:
                print(f"❌ Database initialization failed: {e}")
                print("   Running in console-only mode...")
                db = None
    
    # Handle legacy argument style
    if mode or legacy_args:
        if mode:
            sys.argv = ['test.py', mode] + legacy_args
        else:
            sys.argv = ['test.py'] + legacy_args
    
    # Continue with original main logic but pass db parameter
    return main_with_db(db)


def main_with_db(db=None):
    """Original main function with database integration"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("VS Code Memory Monitor")
            print("Usage: python test.py [options] [interval] [duration]")
            print("Options:")
            print("  -h, --help: show this help")
            print("  -s, --snapshot: take a single detailed snapshot")
            print("  -r, --repo-analysis: analyze memory usage for large repository")
            print("  -c, --copilot-analysis: analyze Copilot + Git memory hypothesis")
            print("  -f, --freeze-detection: monitor UI freeze patterns")
            print("  -g, --git-isolation: test memory patterns with/without Git integration")
            print("  --copilot-focused: continuous monitoring focused on Copilot processes")
            print("  --copilot-context-test: test impact of Copilot context size on memory")
            print("  --copilot-optimization: generate Copilot optimization recommendations")
            print("  --db-track: enable database tracking (stores data in SQLite)")
            print("  --db-path PATH: specify database file path (default: performance.db)")
            print("  interval: seconds between checks (default: 5)")
            print("  duration: total monitoring time in seconds (default: 60)")
            print("\nExamples:")
            print("  python test.py --snapshot")
            print("  python test.py --repo-analysis")
            print("  python test.py --copilot-analysis")
            print("  python test.py --freeze-detection")
            print("  python test.py --git-isolation")
            print("  python test.py --copilot-focused")
            print("  python test.py --copilot-context-test")
            print("  python test.py --copilot-optimization")
            print("  python test.py --db-track --snapshot")
            print("  python test.py --db-track --db-path mydata.db --copilot-analysis")
            print("  python test.py 3 30    # Monitor for 30s with 3s intervals")
            return
        elif sys.argv[1] == '--copilot-focused':
            # Copilot-focused continuous monitoring
            print("🤖 COPILOT-FOCUSED MONITORING MODE")
            print("=" * 60)
            print("This mode continuously monitors VS Code with focus on")
            print("Copilot-related processes and Extension Host memory.\n")
            
            print("📋 What this monitors:")
            print("• Extension Host processes (where Copilot runs)")
            print("• Language Server processes")
            print("• Copilot-specific processes")
            print("• Main VS Code processes")
            print("• Memory growth patterns\n")
            
            response = input("❓ Start Copilot-focused monitoring? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Starting Copilot-focused monitoring...")
                print("   (Press Ctrl+C to stop)")
                time.sleep(1)
                monitor_copilot_processes(focus="extension_hosts", duration=300, interval=10, db=db)
            
            return
        elif sys.argv[1] == '--copilot-context-test':
            # Test Copilot context impact on memory
            print("🧪 COPILOT CONTEXT IMPACT TESTING")
            print("=" * 60)
            print("This mode tests the hypothesis that Copilot context size")
            print("directly impacts Extension Host memory usage.\n")
            
            print("📋 Testing Protocol:")
            print("1. Measure baseline memory with current settings")
            print("2. You'll use Copilot heavily (suggestions, chat, etc.)")
            print("3. Measure memory during heavy Copilot usage")
            print("4. Calculate impact and provide recommendations\n")
            
            response = input("❓ Start Copilot context impact test? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Starting Copilot context impact test...")
                time.sleep(1)
                test_copilot_context_impact()
            
            return
        elif sys.argv[1] == '--copilot-optimization':
            # Generate Copilot optimization recommendations
            print("🎯 COPILOT OPTIMIZATION REPORT")
            print("=" * 60)
            print("This mode analyzes your current VS Code + Copilot setup")
            print("and provides specific optimization recommendations.\n")
            
            response = input("❓ Generate Copilot optimization report? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Generating optimization report...")
                time.sleep(1)
                generate_copilot_optimization_report()
            
            return
        elif sys.argv[1] in ['-g', '--git-isolation']:
            # Git isolation testing mode
            print("🔬 GIT ISOLATION TESTING MODE")
            print("=" * 80)
            print("This mode tests whether Git integration is the primary cause")
            print("of memory issues during Copilot usage in large repositories.\n")
            
            print("📋 TESTING PROTOCOL:")
            print("1. First, we'll monitor WITH Git integration (baseline)")
            print("2. Then, we'll help you temporarily disable Git")
            print("3. Finally, we'll monitor WITHOUT Git integration")
            print("4. Compare results to isolate Git's impact\n")
            
            print("⚠️  SAFETY NOTES:")
            print("• Git folder will be temporarily moved, not deleted")
            print("• Easy restoration with simple command")
            print("• No risk of data loss\n")
            
            response = input("❓ Start Git isolation testing? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Starting Git isolation testing...")
                run_git_isolation_test()
            
            return
        elif sys.argv[1] in ['-f', '--freeze-detection']:
            # UI Freeze detection mode
            print("🧊 UI FREEZE DETECTION MODE")
            print("=" * 80)
            print("This mode monitors for memory patterns associated with UI freezing")
            print("during Copilot interactions in large repositories.\n")
            
            print("📋 Instructions:")
            print("1. Start this monitoring")
            print("2. Use Copilot normally in your large repository")
            print("3. When UI freezes occur, note the timestamp")
            print("4. Let monitoring run through freeze events")
            print("5. Review correlation patterns\n")
            
            response = input("❓ Start freeze detection monitoring? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Starting freeze detection monitoring...")
                print("   (Press Ctrl+C to stop)")
                time.sleep(1)
                monitor_freeze_patterns(interval=5, duration=600)  # 10 minutes with 5s intervals
            
            return
        elif sys.argv[1] in ['-c', '--copilot-analysis']:
            # Copilot + Git hypothesis analysis
            print("🧪 COPILOT + GIT MEMORY HYPOTHESIS TESTING")
            print("=" * 80)
            print("This mode tests specific hypotheses about Copilot and Git")
            print("interactions causing memory issues in large repositories.\n")
            
            # Take initial snapshot
            print("📸 Taking initial snapshot for hypothesis testing...")
            process_data = get_vscode_processes()
            
            if not process_data:
                print("❌ No VS Code processes found")
                print("Make sure VS Code is running with Copilot enabled.")
                return
            
            # Run hypothesis analysis
            processes_with_memory = analyze_copilot_git_hypothesis(process_data)
            
            # Offer targeted monitoring
            print(f"\n🔄 TARGETED MONITORING OPTIONS:")
            print("1. Monitor Extension Hosts (Copilot UI hypothesis)")
            print("2. Monitor Git processes (Git integration hypothesis)")
            print("3. Monitor Language Servers (re-parsing hypothesis)")
            print("4. Monitor all processes with hypothesis flags")
            print("5. Skip continuous monitoring")
            
            choice = input("\nSelect monitoring option (1-5): ").strip()
            
            if choice in ['1', '2', '3', '4']:
                print(f"\n🔄 Starting targeted monitoring...")
                print("   (Press Ctrl+C to stop)")
                time.sleep(1)
                monitor_memory_with_hypothesis(interval=15, duration=600, focus=choice)  # 10 minutes
            
            return
        elif sys.argv[1] in ['-r', '--repo-analysis']:
            # Repository-specific analysis
            print("🔍 LARGE REPOSITORY MEMORY ANALYSIS")
            print("=" * 80)
            print("This mode provides detailed analysis for VS Code memory usage")
            print("when working with large repositories.\n")
            
            # Take initial snapshot
            print("📸 Taking initial snapshot...")
            process_data = get_vscode_processes()
            
            if not process_data:
                print("❌ No VS Code processes found")
                print("Make sure VS Code is running with your large repository open.")
                return
            
            # Analyze current state
            analyze_repo_memory_usage(process_data)
            
            # Offer continuous monitoring
            response = input("\n❓ Would you like to start continuous monitoring? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 Starting continuous monitoring...")
                print("   (Press Ctrl+C to stop)")
                time.sleep(1)
                monitor_memory(interval=10, duration=300, db=db)  # 5 minutes with 10s intervals
            
            return
        elif sys.argv[1] in ['-s', '--snapshot']:
            # Single snapshot mode with detailed breakdown
            print("📸 Taking a detailed memory snapshot...")
            
            # Start database run if enabled
            run_id = None
            if db:
                run_id = db.start_monitoring_run(
                    mode='snapshot',
                    command_line_args=' '.join(sys.argv),
                    notes='Single memory snapshot'
                )
            
            process_data = get_vscode_processes()
            
            if not process_data:
                print("❌ No VS Code processes found")
                if db and run_id:
                    db.end_monitoring_run(run_id, 0, 'no_processes', 'No VS Code processes found')
                return
            
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            total_memory = 0
            total_vms = 0
            
            # Collect and sort process information
            processes_with_memory = []
            for proc_data in process_data:
                try:
                    proc = proc_data['process']
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()
                    rss = memory_info.rss
                    vms = memory_info.vms
                    total_memory += rss
                    total_vms += vms
                    
                    processes_with_memory.append({
                        'pid': proc.pid,
                        'type': proc_data['type'],
                        'name': proc_data['name'],
                        'rss': rss,
                        'vms': vms,
                        'cpu': cpu_percent
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Save to database if enabled
            if db and run_id:
                db.add_measurement(
                    run_id=run_id,
                    timestamp=timestamp,
                    process_count=len(processes_with_memory),
                    total_rss_bytes=total_memory,
                    total_vms_bytes=total_vms,
                    process_data=processes_with_memory,
                    measurement_index=1,
                    notes='Memory snapshot'
                )
                db.end_monitoring_run(run_id, 1, 'completed', 'Snapshot completed successfully')
            
            # Sort by memory usage
            processes_with_memory.sort(key=lambda x: x['rss'], reverse=True)
            
            print(f"\n[{timestamp_str}] Found {len(processes_with_memory)} VS Code process(es):")
            print("=" * 100)
            print(f"{'#':>2} {'PID':>6} {'RAM':>12} {'Virtual':>12} {'CPU':>6} {'Process Type':<25}")
            print("=" * 100)
            
            for i, proc_info in enumerate(processes_with_memory, 1):
                memory_indicator = "🔥" if proc_info['rss'] > 200 * 1024 * 1024 else "📊"
                
                print(f"{memory_indicator} {i:2d} {proc_info['pid']:6d} "
                      f"{format_bytes(proc_info['rss']):>12s} "
                      f"{format_bytes(proc_info['vms']):>12s} "
                      f"{proc_info['cpu']:5.1f}% "
                      f"{proc_info['type']:<25}")
            
            print("=" * 100)
            print(f"📊 TOTAL RAM: {format_bytes(total_memory)}")
            
            if db and run_id:
                print(f"💾 Data saved to database (Run ID: {run_id})")
            
            return
            
            print("=" * 100)
            print(f"📊 TOTAL RAM: {format_bytes(total_memory)}")
            
            # Show breakdown by process type
            type_breakdown = {}
            for proc in processes_with_memory:
                proc_type = proc['type']
                if proc_type not in type_breakdown:
                    type_breakdown[proc_type] = {'memory': 0, 'count': 0}
                type_breakdown[proc_type]['memory'] += proc['rss']
                type_breakdown[proc_type]['count'] += 1
            
            print(f"\n🔍 BREAKDOWN BY PROCESS TYPE:")
            print("-" * 60)
            sorted_breakdown = sorted(type_breakdown.items(), key=lambda x: x[1]['memory'], reverse=True)
            
            for proc_type, stats in sorted_breakdown:
                percentage = (stats['memory'] / total_memory) * 100
                indicator = "🔥" if percentage > 20 else "📊"
                print(f"{indicator} {proc_type:<25} "
                      f"{format_bytes(stats['memory']):>10s} "
                      f"({percentage:4.1f}%) "
                      f"[{stats['count']} process{'es' if stats['count'] > 1 else ''}]")
            
            # Recommendations for high memory usage
            high_memory_total = sum(proc['rss'] for proc in processes_with_memory 
                                  if proc['rss'] > 200 * 1024 * 1024)
            
            if high_memory_total > 0:
                print(f"\n⚠️  HIGH MEMORY USAGE DETECTED:")
                print(f"   Total high-memory processes: {format_bytes(high_memory_total)}")
                print(f"   Recommendations:")
                print(f"   • Close unused tabs and windows")
                print(f"   • Disable heavy extensions temporarily")
                print(f"   • Consider restarting VS Code")
                print(f"   • Check for memory leaks in extensions")
            
            return
    
    # Parse interval and duration from command line
    interval = 5
    duration = 60
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid interval value. Using default: 5 seconds")
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid duration value. Using default: 60 seconds")
    
    monitor_memory(interval, duration, db)

if __name__ == "__main__":
    main()
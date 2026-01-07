"""
Resource Optimizer
Optimizes system resources for the HAC platform
"""

import psutil
import os
import sys
import platform
import time
from datetime import datetime
import json

class ResourceOptimizer:
    def __init__(self):
        self.system_info = {}
        self.optimizations_applied = []
        self.log_file = "optimization_log.json"
        
    def get_system_info(self):
        """Get detailed system information"""
        self.system_info = {
            "timestamp": datetime.now().isoformat(),
            "os": platform.system(),
            "os_version": platform.version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_physical_count": psutil.cpu_count(logical=False),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_ram_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "ram_percent_used": psutil.virtual_memory().percent,
            "disk_usage": {},
            "processes_running": len(psutil.pids()),
            "python_version": platform.python_version()
        }
        
        # Get disk information
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.system_info["disk_usage"][partition.mountpoint] = {
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent
                }
            except:
                continue
        
        return self.system_info
    
    def optimize_memory(self):
        """Optimize memory usage"""
        optimizations = []
        
        # Clear Python's internal caches
        import gc
        collected = gc.collect()
        optimizations.append(f"Garbage collection freed {collected} objects")
        
        # Suggest closing memory-intensive processes
        memory_hogs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if proc.info['memory_percent'] > 5.0:  # Using more than 5% memory
                    memory_hogs.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_percent': round(proc.info['memory_percent'], 2)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if memory_hogs:
            memory_hogs.sort(key=lambda x: x['memory_percent'], reverse=True)
            optimizations.append(f"Top memory hogs: {[f'{h['name']}({h['memory_percent']}%)' for h in memory_hogs[:3]]}")
        
        return optimizations
    
    def optimize_cpu(self):
        """Optimize CPU usage"""
        optimizations = []
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            optimizations.append(f"High CPU usage detected: {cpu_percent}%")
            
            # Find CPU-intensive processes
            cpu_hogs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc.cpu_percent(interval=0.1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            time.sleep(0.5)
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    if cpu > 10.0:  # Using more than 10% CPU
                        cpu_hogs.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': round(cpu, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if cpu_hogs:
                cpu_hogs.sort(key=lambda x: x['cpu_percent'], reverse=True)
                optimizations.append(f"Top CPU hogs: {[f'{h['name']}({h['cpu_percent']}%)' for h in cpu_hogs[:3]]}")
        
        return optimizations
    
    def optimize_disk(self):
        """Optimize disk usage"""
        optimizations = []
        
        for mountpoint, usage in self.system_info.get("disk_usage", {}).items():
            if usage["percent_used"] > 85:
                optimizations.append(f"Disk {mountpoint} is {usage['percent_used']}% full. Consider cleaning up.")
            
            # Check for large files in temp directories
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                '/tmp' if platform.system() != 'Windows' else '',
                'C:\\Windows\\Temp' if platform.system() == 'Windows' else ''
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        temp_size = 0
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    temp_size += os.path.getsize(os.path.join(root, file))
                                except:
                                    continue
                        
                        temp_size_gb = round(temp_size / (1024**3), 2)
                        if temp_size_gb > 1.0:
                            optimizations.append(f"Temp directory {temp_dir} has {temp_size_gb}GB of data")
                    except:
                        continue
        
        return optimizations
    
    def optimize_network(self):
        """Optimize network connections"""
        optimizations = []
        
        # Check network connections
        connections = psutil.net_connections()
        established = [conn for conn in connections if conn.status == 'ESTABLISHED']
        
        optimizations.append(f"Active network connections: {len(established)}")
        
        # Check for potentially problematic connections
        suspicious_ports = [8080, 3000, 5000, 8000, 9000]  # Common dev ports
        for conn in established:
            if conn.laddr.port in suspicious_ports and conn.raddr:
                optimizations.append(f"Development service running on port {conn.laddr.port}")
        
        return optimizations
    
    def optimize_python_runtime(self):
        """Optimize Python runtime environment"""
        optimizations = []
        
        # Check Python memory usage
        current_process = psutil.Process()
        memory_info = current_process.memory_info()
        memory_mb = round(memory_info.rss / (1024**2), 2)
        
        optimizations.append(f"Python process using {memory_mb}MB RAM")
        
        if memory_mb > 500:  # If using more than 500MB
            optimizations.append("Python process using high memory. Consider optimizing imports.")
        
        # Check for memory leaks
        import gc
        gc.set_debug(gc.DEBUG_SAVEALL)
        
        return optimizations
    
    def generate_recommendations(self):
        """Generate optimization recommendations"""
        recommendations = []
        
        # Memory recommendations
        if self.system_info.get("ram_percent_used", 0) > 80:
            recommendations.append({
                "category": "Memory",
                "priority": "High",
                "action": "Close unused applications to free up RAM",
                "details": f"RAM usage is at {self.system_info.get('ram_percent_used')}%"
            })
        
        # CPU recommendations
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            recommendations.append({
                "category": "CPU",
                "priority": "High",
                "action": "Reduce CPU-intensive tasks or processes",
                "details": f"CPU usage is at {cpu_percent}%"
            })
        
        # Disk recommendations
        for mountpoint, usage in self.system_info.get("disk_usage", {}).items():
            if usage["percent_used"] > 90:
                recommendations.append({
                    "category": "Disk",
                    "priority": "High",
                    "action": f"Clean up disk {mountpoint}",
                    "details": f"Disk is {usage['percent_used']}% full"
                })
        
        # General recommendations
        if len(psutil.pids()) > 150:
            recommendations.append({
                "category": "System",
                "priority": "Medium",
                "action": "Reduce number of running processes",
                "details": f"{len(psutil.pids())} processes running"
            })
        
        return recommendations
    
    def run_optimization(self, full_scan=True):
        """Run complete optimization"""
        print("=" * 60)
        print("RESOURCE OPTIMIZER")
        print("=" * 60)
        
        # Get system info
        print("\n📊 SYSTEM INFORMATION:")
        print("-" * 40)
        self.get_system_info()
        
        print(f"OS: {self.system_info['os']} {self.system_info['os_version']}")
        print(f"CPU: {self.system_info['cpu_count']} logical cores")
        print(f"RAM: {self.system_info['available_ram_gb']}GB available of {self.system_info['total_ram_gb']}GB ({self.system_info['ram_percent_used']}% used)")
        print(f"Python: {self.system_info['python_version']}")
        
        if full_scan:
            # Run optimizations
            print("\n⚡ RUNNING OPTIMIZATIONS:")
            print("-" * 40)
            
            # Memory optimization
            mem_opt = self.optimize_memory()
            if mem_opt:
                print("🧠 Memory Optimizations:")
                for opt in mem_opt:
                    print(f"  • {opt}")
                    self.optimizations_applied.append(opt)
            
            # CPU optimization
            cpu_opt = self.optimize_cpu()
            if cpu_opt:
                print("\n⚡ CPU Optimizations:")
                for opt in cpu_opt:
                    print(f"  • {opt}")
                    self.optimizations_applied.append(opt)
            
            # Disk optimization
            disk_opt = self.optimize_disk()
            if disk_opt:
                print("\n💾 Disk Optimizations:")
                for opt in disk_opt:
                    print(f"  • {opt}")
                    self.optimizations_applied.append(opt)
            
            # Network optimization
            net_opt = self.optimize_network()
            if net_opt:
                print("\n🌐 Network Optimizations:")
                for opt in net_opt:
                    print(f"  • {opt}")
                    self.optimizations_applied.append(opt)
            
            # Python runtime optimization
            py_opt = self.optimize_python_runtime()
            if py_opt:
                print("\n🐍 Python Runtime Optimizations:")
                for opt in py_opt:
                    print(f"  • {opt}")
                    self.optimizations_applied.append(opt)
        
        # Generate recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        recommendations = self.generate_recommendations()
        
        if not recommendations:
            print("✅ System is running optimally!")
        else:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. [{rec['priority'].upper()}] {rec['category']}:")
                print(f"   Action: {rec['action']}")
                print(f"   Reason: {rec['details']}")
        
        # Save log
        self.save_log()
        
        print("\n" + "=" * 60)
        print(f"Optimization completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return self.optimizations_applied
    
    def save_log(self):
        """Save optimization log to file"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.system_info,
            "optimizations_applied": self.optimizations_applied,
            "recommendations": self.generate_recommendations()
        }
        
        try:
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except:
            pass
    
    def quick_scan(self):
        """Perform a quick system scan"""
        return self.run_optimization(full_scan=False)
    
    def monitor_resources(self, interval=5, duration=60):
        """Monitor resources for a period"""
        print(f"\n📈 Monitoring resources for {duration} seconds...")
        print("-" * 40)
        
        end_time = time.time() + duration
        samples = []
        
        while time.time() < end_time:
            sample = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "ram_percent": psutil.virtual_memory().percent,
                "available_ram_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            }
            samples.append(sample)
            
            print(f"[{sample['time']}] CPU: {sample['cpu_percent']}% | RAM: {sample['ram_percent']}% | Available: {sample['available_ram_gb']}GB")
            time.sleep(interval)
        
        # Analyze samples
        avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
        avg_ram = sum(s["ram_percent"] for s in samples) / len(samples)
        
        print("\n📊 MONITORING SUMMARY:")
        print(f"Average CPU Usage: {avg_cpu:.1f}%")
        print(f"Average RAM Usage: {avg_ram:.1f}%")
        
        if avg_cpu > 70:
            print("⚠️  High average CPU usage detected")
        if avg_ram > 80:
            print("⚠️  High average RAM usage detected")


def main():
    """Main function"""
    optimizer = ResourceOptimizer()
    
    print("Resource Optimizer - Choose an option:")
    print("1. Full Optimization Scan")
    print("2. Quick System Scan")
    print("3. Monitor Resources")
    print("4. System Information Only")
    print("5. Exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            optimizer.run_optimization(full_scan=True)
        elif choice == "2":
            optimizer.quick_scan()
        elif choice == "3":
            try:
                duration = int(input("Monitor duration (seconds, default 60): ") or "60")
                interval = int(input("Sample interval (seconds, default 5): ") or "5")
                optimizer.monitor_resources(interval=interval, duration=duration)
            except ValueError:
                print("Invalid input. Using defaults.")
                optimizer.monitor_resources()
        elif choice == "4":
            optimizer.get_system_info()
            print("\nSystem Information:")
            for key, value in optimizer.system_info.items():
                if key != "disk_usage":
                    print(f"{key.replace('_', ' ').title()}: {value}")
            print("\nDisk Usage:")
            for mount, usage in optimizer.system_info.get("disk_usage", {}).items():
                print(f"  {mount}: {usage['percent_used']}% used")
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Running full optimization...")
            optimizer.run_optimization()
            
    except KeyboardInterrupt:
        print("\n\nOptimization interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have required permissions and psutil is installed.")
        print("Install psutil with: pip install psutil")


if __name__ == "__main__":
    # Check if psutil is installed
    try:
        import psutil
        main()
    except ImportError:
        print("❌ psutil library is not installed!")
        print("Install it using: pip install psutil")
        response = input("Do you want to install it now? (y/n): ")
        if response.lower() == 'y':
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("✅ psutil installed successfully!")
            print("Restarting optimizer...")
            main()
        else:
            print("Please install psutil manually and try again.")
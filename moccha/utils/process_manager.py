"""Process management utilities."""

import os
import psutil
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ProcessManager:
    """Utility class for managing processes."""
    
    @staticmethod
    def find_process_by_name(name: str) -> Optional[psutil.Process]:
        """Find a process by its name."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None
    
    @staticmethod
    def find_processes_by_cmdline(keyword: str) -> List[psutil.Process]:
        """Find processes by command line keyword."""
        processes = []
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                if proc.info['cmdline'] and any(keyword in ' '.join(proc.info['cmdline']) for keyword in [keyword]):
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
    
    @staticmethod
    def kill_process_by_name(name: str) -> bool:
        """Kill a process by its name."""
        proc = ProcessManager.find_process_by_name(name)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=10)
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return False
        return False
    
    @staticmethod
    def kill_processes_by_cmdline(keyword: str) -> bool:
        """Kill processes by command line keyword."""
        processes = ProcessManager.find_processes_by_cmdline(keyword)
        success = True
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    success = False
        return success
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if a process is running by PID."""
        try:
            proc = psutil.Process(pid)
            return proc.is_running()
        except psutil.NoSuchProcess:
            return False
    
    @staticmethod
    def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
        """Get process information by PID."""
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cmdline": proc.cmdline(),
                "status": proc.status(),
                "create_time": proc.create_time(),
                "memory_info": proc.memory_info()._asdict(),
                "cpu_percent": proc.cpu_percent()
            }
        except psutil.NoSuchProcess:
            return None
    
    @staticmethod
    def get_process_children(pid: int) -> List[int]:
        """Get child processes by PID."""
        try:
            proc = psutil.Process(pid)
            return [child.pid for child in proc.children()]
        except psutil.NoSuchProcess:
            return []
    
    @staticmethod
    def kill_process_tree(pid: int) -> bool:
        """Kill a process and all its children."""
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait a bit for graceful termination
            gone, alive = psutil.wait_procs(children, timeout=3)
            
            # Force kill any remaining children
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                proc.kill()
            
            return True
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            return False
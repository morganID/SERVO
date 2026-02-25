"""Modul utilitas sistem."""

import os
import sys
import io
import uuid
import json
import shutil
import psutil
import signal
import traceback
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from functools import wraps


def get_system_info():
    """Dapatkan informasi sistem."""
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage('/')
    gpu = None
    try:
        r = subprocess.run(
            ['nvidia-smi',
             '--query-gpu=name,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            p = r.stdout.strip().split(', ')
            gpu = {
                "name": p[0],
                "mem_used_mb": int(p[1]),
                "mem_total_mb": int(p[2]),
                "util_pct": int(p[3]),
            }
    except:
        pass

    return {
        "cpu_pct": psutil.cpu_percent(interval=0.5),
        "cpu_count": psutil.cpu_count(),
        "ram_total_gb": round(mem.total / 1e9, 2),
        "ram_used_gb": round(mem.used / 1e9, 2),
        "ram_pct": mem.percent,
        "disk_total_gb": round(disk.total / 1e9, 2),
        "disk_free_gb": round(disk.free / 1e9, 2),
        "gpu": gpu,
    }


def execute_code(code: str, vars: dict) -> dict:
    """Eksekusi kode Python."""
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    result = {"output": "", "error": "", "variables": {}, "success": False}

    try:
        sys.stdout, sys.stderr = out_buf, err_buf
        ns = dict(vars)
        exec(code, {"__builtins__": __builtins__}, ns)

        for k, v in ns.items():
            if not k.startswith('_') and not callable(v):
                try:
                    json.dumps(v)
                    result["variables"][k] = v
                except (TypeError, ValueError):
                    result["variables"][k] = f"<{type(v).__name__}>"

        result["output"] = out_buf.getvalue()
        result["success"] = True
    except:
        result["error"] = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = old_out, old_err

    return result


def run_shell_command(cmd: str, workspace: str, timeout: int = 120) -> dict:
    """Jalankan perintah shell."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout,
            cwd=workspace
        )
        return {
            "stdout": r.stdout,
            "stderr": r.stderr,
            "code": r.returncode,
            "success": r.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def install_package(package: str) -> dict:
    """Install package menggunakan pip."""
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package],
            capture_output=True, text=True, timeout=300
        )
        return {
            "package": package,
            "success": r.returncode == 0,
            "output": r.stdout[-2000:],
            "error": r.stderr[-2000:],
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def async_execute(code: str, vars: dict):
    """Eksekusi kode secara async."""
    tid = str(uuid.uuid4())[:12]
    result = {"status": "running", "created": datetime.now().isoformat()}

    def run(t, c):
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            exec(c, {"__builtins__": __builtins__}, dict(vars))
            result["result"] = buf.getvalue()
            result["status"] = "done"
        except:
            result["error"] = traceback.format_exc()
            result["status"] = "failed"
        finally:
            sys.stdout = old
            result["finished"] = datetime.now().isoformat()

    threading.Thread(target=run, args=(tid, code), daemon=True).start()
    return tid, result
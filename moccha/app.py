"""Flask API Server - semua endpoint."""

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

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS


def create_app(api_key, workspace="/content"):
    """Factory: bikin Flask app."""

    app = Flask(__name__)
    CORS(app)

    # State disimpan di app.config
    app.config['API_KEY'] = api_key
    app.config['WORKSPACE'] = workspace
    app.config['START_TIME'] = datetime.now()
    app.config['VARS'] = {}        # persistent variables
    app.config['HISTORY'] = []     # execution history
    app.config['TASKS'] = {}       # async tasks

    # ── Auth decorator ────────────────────────────────────
    def require_key(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.headers.get('X-API-Key', '')
            if key != app.config['API_KEY']:
                return jsonify({"error": "Invalid API key"}), 401
            return f(*args, **kwargs)
        return decorated

    def add_history(typ, inp, out, ok):
        h = app.config['HISTORY']
        h.append({
            "id": str(uuid.uuid4())[:8],
            "type": typ,
            "time": datetime.now().isoformat(),
            "input": str(inp)[:500],
            "success": ok,
        })
        if len(h) > 200:
            app.config['HISTORY'] = h[-200:]

    # ── Routes ────────────────────────────────────────────

    @app.route('/')
    def home():
        return jsonify({
            "service": "moccha",
            "version": "2.0.0",
            "status": "running",
            "uptime": str(datetime.now() - app.config['START_TIME']),
        })

    @app.route('/ping')
    def ping():
        return jsonify({"pong": True})

    @app.route('/status')
    @require_key
    def status():
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

        return jsonify({
            "uptime": str(datetime.now() - app.config['START_TIME']),
            "cpu_pct": psutil.cpu_percent(interval=0.5),
            "cpu_count": psutil.cpu_count(),
            "ram_total_gb": round(mem.total / 1e9, 2),
            "ram_used_gb": round(mem.used / 1e9, 2),
            "ram_pct": mem.percent,
            "disk_total_gb": round(disk.total / 1e9, 2),
            "disk_free_gb": round(disk.free / 1e9, 2),
            "gpu": gpu,
            "executions": len(app.config['HISTORY']),
            "variables": len(app.config['VARS']),
        })

    @app.route('/execute', methods=['POST'])
    @require_key
    def execute():
        data = request.json or {}
        code = data.get('code', '')
        if not code.strip():
            return jsonify({"error": "No code"}), 400

        out_buf = io.StringIO()
        err_buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        result = {"output": "", "error": "", "variables": {}, "success": False}

        try:
            sys.stdout, sys.stderr = out_buf, err_buf
            ns = dict(app.config['VARS'])
            exec(code, {"__builtins__": __builtins__}, ns)

            for k, v in ns.items():
                if not k.startswith('_') and not callable(v):
                    app.config['VARS'][k] = v
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

        add_history("execute", code, result["output"], result["success"])
        return jsonify(result)

    @app.route('/shell', methods=['POST'])
    @require_key
    def shell():
        data = request.json or {}
        cmd = data.get('command', '')
        timeout = min(data.get('timeout', 120), 600)
        if not cmd.strip():
            return jsonify({"error": "No command"}), 400

        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout,
                cwd=app.config['WORKSPACE']
            )
            res = {
                "stdout": r.stdout,
                "stderr": r.stderr,
                "code": r.returncode,
                "success": r.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            res = {"error": "Timeout", "success": False}
        except Exception as e:
            res = {"error": str(e), "success": False}

        add_history("shell", cmd, res.get("stdout"), res.get("success", False))
        return jsonify(res)

    @app.route('/install', methods=['POST'])
    @require_key
    def install():
        pkg = (request.json or {}).get('package', '')
        if not pkg:
            return jsonify({"error": "No package"}), 400
        try:
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pkg],
                capture_output=True, text=True, timeout=300
            )
            return jsonify({
                "package": pkg,
                "success": r.returncode == 0,
                "output": r.stdout[-2000:],
                "error": r.stderr[-2000:],
            })
        except Exception as e:
            return jsonify({"error": str(e), "success": False})

    @app.route('/files')
    @require_key
    def files():
        path = request.args.get('path', app.config['WORKSPACE'])
        try:
            items = []
            for entry in Path(path).iterdir():
                st = entry.stat()
                items.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size": st.st_size,
                    "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
                })
            items.sort(key=lambda x: (x["type"] == "file", x["name"]))
            return jsonify({"path": path, "items": items})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/upload', methods=['POST'])
    @require_key
    def upload():
        if 'file' not in request.files:
            return jsonify({"error": "No file"}), 400
        f = request.files['file']
        dest = request.form.get('path', app.config['WORKSPACE'])
        os.makedirs(dest, exist_ok=True)
        fpath = os.path.join(dest, f.filename)
        f.save(fpath)
        return jsonify({
            "filename": f.filename,
            "path": fpath,
            "size": os.path.getsize(fpath),
            "success": True,
        })

    @app.route('/download/<path:filepath>')
    @require_key
    def download(filepath):
        full = os.path.join(app.config['WORKSPACE'], filepath)
        if not os.path.isfile(full):
            full = filepath
        if os.path.isfile(full):
            return send_file(full, as_attachment=True)
        return jsonify({"error": "Not found"}), 404

    @app.route('/async-execute', methods=['POST'])
    @require_key
    def async_exec():
        code = (request.json or {}).get('code', '')
        tid = str(uuid.uuid4())[:12]
        app.config['TASKS'][tid] = {"status": "running", "created": datetime.now().isoformat()}

        def run(t, c):
            buf = io.StringIO()
            old = sys.stdout
            try:
                sys.stdout = buf
                exec(c, {"__builtins__": __builtins__}, dict(app.config['VARS']))
                app.config['TASKS'][t]["result"] = buf.getvalue()
                app.config['TASKS'][t]["status"] = "done"
            except:
                app.config['TASKS'][t]["error"] = traceback.format_exc()
                app.config['TASKS'][t]["status"] = "failed"
            finally:
                sys.stdout = old
                app.config['TASKS'][t]["finished"] = datetime.now().isoformat()

        threading.Thread(target=run, args=(tid, code), daemon=True).start()
        return jsonify({"task_id": tid, "status": "running"})

    @app.route('/task/<tid>')
    @require_key
    def get_task(tid):
        t = app.config['TASKS'].get(tid)
        return jsonify(t) if t else (jsonify({"error": "Not found"}), 404)

    @app.route('/variables')
    @require_key
    def variables():
        safe = {}
        for k, v in app.config['VARS'].items():
            try:
                json.dumps(v)
                safe[k] = v
            except:
                safe[k] = f"<{type(v).__name__}>"
        return jsonify(safe)

    @app.route('/variables/<name>', methods=['DELETE'])
    @require_key
    def del_var(name):
        if name in app.config['VARS']:
            del app.config['VARS'][name]
            return jsonify({"deleted": name})
        return jsonify({"error": "Not found"}), 404

    @app.route('/history')
    @require_key
    def history():
        n = int(request.args.get('limit', 20))
        return jsonify(app.config['HISTORY'][-n:])

    return app
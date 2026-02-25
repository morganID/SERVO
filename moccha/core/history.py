"""Modul history dan variables."""

import json
import uuid
from datetime import datetime


def add_history(history: list, typ: str, inp, out, ok: bool):
    """Tambahkan ke history."""
    h = history
    h.append({
        "id": str(uuid.uuid4())[:8],
        "type": typ,
        "time": datetime.now().isoformat(),
        "input": str(inp)[:500],
        "success": ok,
    })
    if len(h) > 200:
        history[:] = h[-200:]


def get_safe_variables(vars: dict) -> dict:
    """Dapatkan variables yang aman untuk JSON."""
    safe = {}
    for k, v in vars.items():
        try:
            json.dumps(v)
            safe[k] = v
        except Exception:
            safe[k] = f"<{type(v).__name__}>"
    return safe
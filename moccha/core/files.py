"""Modul utilitas file."""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


def list_files(path: str):
    """List file dan directory."""
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
        return {"path": path, "items": items}
    except Exception as e:
        return {"error": str(e)}


def upload_file(file, dest: str):
    """Upload file."""
    os.makedirs(dest, exist_ok=True)
    fpath = os.path.join(dest, file.filename)
    file.save(fpath)
    return {
        "filename": file.filename,
        "path": fpath,
        "size": os.path.getsize(fpath),
        "success": True,
    }


def download_file(filepath: str):
    """Download file."""
    full = os.path.join(filepath)
    if os.path.isfile(full):
        return full
    return None


def delete_file(filepath: str):
    """Delete file."""
    try:
        os.remove(filepath)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
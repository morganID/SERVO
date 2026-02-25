"""Konfigurasi aplikasi."""

import os
from pathlib import Path
from datetime import datetime


class Config:
    """Kelas konfigurasi."""

    def __init__(self, api_key: str, workspace: str = "/content"):
        self.api_key = api_key
        self.workspace = Path(workspace)
        self.start_time = datetime.now()
        self.vars = {}
        self.history = []
        self.tasks = {}

    def to_dict(self):
        """Konversi ke dictionary."""
        return {
            "api_key": self.api_key,
            "workspace": str(self.workspace),
            "start_time": self.start_time.isoformat(),
            "vars": self.vars,
            "history": self.history,
            "tasks": self.tasks,
        }
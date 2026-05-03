# swt_dearpygui/utils/export_compat.py
# -*- coding: utf-8 -*-
"""Excel 导出适配层"""

import os
from datetime import datetime


class ExportCompat:
    @staticmethod
    def get_default_dir() -> str:
        try:
            import json
            config_file = os.path.join(os.path.dirname(__file__), "..", "swt_config.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return config.get("export_dir", os.path.expanduser("~"))
        except Exception:
            pass
        return os.path.expanduser("~")

    @staticmethod
    def generate_filename(prefix: str, ext: str = "xlsx") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}.{ext}"

    @staticmethod
    def ensure_dir(filepath: str) -> str:
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        return filepath

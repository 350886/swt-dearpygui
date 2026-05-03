# swt_dearpygui/theme.py
# -*- coding: utf-8 -*-
"""明暗主题系统，通过 token 管理所有样式"""

import json
import os

LIGHT_THEME = {
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F5F5F5",
    "bg_tertiary": "#E8E8E8",
    "bg_sidebar": "#2C3E50",
    "text_primary": "#1A1A1A",
    "text_secondary": "#666666",
    "text_accent": "#3498DB",
    "border": "#DDDDDD",
    "accent": "#3498DB",
    "accent_hover": "#2980B9",
    "success": "#27AE60",
    "warning": "#F39C12",
    "error": "#E74C3C",
    "row_even": "#FFFFFF",
    "row_odd": "#F9F9F9",
    "row_selected": "#EBF5FB",
    "title_bar": "#2C3E50",
    "title_bar_text": "#FFFFFF",
}

DARK_THEME = {
    "bg_primary": "#1E1E1E",
    "bg_secondary": "#252526",
    "bg_tertiary": "#2D2D2D",
    "bg_sidebar": "#171717",
    "text_primary": "#D4D4D4",
    "text_secondary": "#808080",
    "text_accent": "#5DA0D0",
    "border": "#3E3E42",
    "accent": "#5DA0D0",
    "accent_hover": "#4A90C0",
    "success": "#4CAF50",
    "warning": "#FFB74D",
    "error": "#EF5350",
    "row_even": "#1E1E1E",
    "row_odd": "#252526",
    "row_selected": "#263845",
    "title_bar": "#171717",
    "title_bar_text": "#D4D4D4",
}


class ThemeManager:
    _current = "light"
    _config_file = None

    @classmethod
    def get_current_theme(cls) -> str:
        return cls._current

    @classmethod
    def get_token(cls, key: str) -> str:
        theme = LIGHT_THEME if cls._current == "light" else DARK_THEME
        return theme.get(key, "#000000")

    @classmethod
    def set_theme(cls, theme_name: str, config_file: str = None):
        if theme_name not in ("light", "dark"):
            raise ValueError(f"Unknown theme: {theme_name}")
        cls._current = theme_name
        cls._config_file = config_file
        if config_file:
            cls._persist(config_file)

    @classmethod
    def load_from_config(cls, config_file: str) -> str:
        cls._config_file = config_file
        if not os.path.exists(config_file):
            return "light"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            theme = config.get("theme", "light")
            if theme in ("light", "dark"):
                cls._current = theme
        except Exception:
            pass
        return cls._current

    @classmethod
    def _persist(cls, config_file: str):
        if not os.path.exists(config_file):
            return
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            config["theme"] = cls._current
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

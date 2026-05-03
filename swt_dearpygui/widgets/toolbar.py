# swt_dearpygui/widgets/toolbar.py
# -*- coding: utf-8 -*-
"""工具栏组件"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class Toolbar:
    def __init__(self, parent_tag: str):
        self._parent_tag = parent_tag
        self._actions = []
        self._container_tag = f"toolbar_{id(self)}"

    def add_action(self, label: str, callback=None, hotkey: str = None):
        self._actions.append((label, callback, hotkey))
        return self

    def build(self):
        with dpg.group(parent=self._parent_tag):
            hotkey_str = "Ctrl+S" if any(h for _, _, h in self._actions if h) else None
            with dpg.hotkey(keybind=hotkey_str):
                pass
            for label, callback, _ in self._actions:
                dpg.add_button(
                    label=label,
                    width=80,
                    height=28,
                    callback=callback,
                    color=ThemeManager.get_token("accent"),
                    hover_color=ThemeManager.get_token("accent_hover"),
                )
        return self

    @property
    def container_tag(self):
        return self._container_tag

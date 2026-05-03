# swt_dearpygui/widgets/search_bar.py
# -*- coding: utf-8 -*-
"""搜索栏组件"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class SearchBar:
    def __init__(self, placeholder: str = "搜索...", width: int = 300, callback=None):
        self._tag = f"search_{id(self)}"
        self._placeholder = placeholder
        self._width = width
        self._callback = callback
        self._container_tag = None

    def build(self, parent: str = None):
        self._container_tag = parent
        with dpg.group(parent=parent):
            dpg.add_input_text(
                tag=self._tag,
                placeholder=self._placeholder,
                width=self._width,
                callback=self._on_change,
                hint_color=ThemeManager.get_token("text_secondary"),
            )

    def _on_change(self, sender, data):
        if self._callback:
            self._callback(data)

    def get_value(self) -> str:
        if self._container_tag and dpg.does_item_exist(self._tag):
            return dpg.get_value(self._tag)
        return ""

    def set_value(self, value: str):
        if self._container_tag and dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, value)

    def clear(self):
        if self._container_tag and dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, "")

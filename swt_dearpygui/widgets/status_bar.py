# swt_dearpygui/widgets/status_bar.py
# -*- coding: utf-8 -*-
"""状态栏组件"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class StatusBar:
    def __init__(self):
        self._tag = f"statusbar_{id(self)}"

    def build(self, parent: str = None):
        dpg.add_input_text(
            tag=self._tag,
            default_value="就绪",
            width=-1,
            height=24,
            readonly=True,
            color=ThemeManager.get_token("text_secondary"),
            hint_color=ThemeManager.get_token("text_secondary"),
            parent=parent,
        )

    def set_message(self, msg: str):
        if dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, msg)

    def set_color(self, color_token: str):
        if dpg.does_item_exist(self._tag):
            hex_color = ThemeManager.get_token(color_token).lstrip("#")
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            dpg.configure_item(self._tag, color=(r, g, b, 1.0))

    @property
    def tag(self):
        return self._tag

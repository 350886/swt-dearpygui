# swt_dearpygui/widgets/sidebar.py
# -*- coding: utf-8 -*-
"""侧边栏导航组件"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class Sidebar:
    def __init__(self):
        self._categories = []
        self._on_select = None
        self._current_page = None

    def add_category(self, title: str, items: list):
        """items: list of (page_name, display_name)"""
        self._categories.append((title, items))
        return self

    def build(self, parent_tag: str = None):
        sidebar_bg = ThemeManager.get_token("bg_sidebar")
        r, g, b = self._hex_to_rgb(sidebar_bg)

        with dpg.child_window(tag="sidebar_container", width=200, height=-1, parent=parent_tag):
            dpg.add_text("SWT 货运管理", color=(1, 1, 1, 1), parent="sidebar_container")
            dpg.add_separator(parent="sidebar_container")

            for cat_title, items in self._categories:
                dpg.add_text(f"  {cat_title}", color=(0.7, 0.7, 0.7, 1), parent="sidebar_container")
                for page_name, display_name in items:
                    tag = f"nav_{page_name}"
                    dpg.add_button(
                        label=display_name,
                        width=-1,
                        height=28,
                        tag=tag,
                        callback=self._make_callback(page_name),
                        color=(r, g, b, 1),
                        hover_color=(r * 1.1, g * 1.1, b * 1.1, 1),
                        pressed_color=(r * 0.8, g * 0.8, b * 0.8, 1),
                        parent="sidebar_container",
                    )
                dpg.add_separator(parent="sidebar_container")

    def _make_callback(self, page_name: str):
        def callback(sender, data):
            if self._on_select:
                self._on_select(page_name)
        return callback

    def on_select(self, callback):
        self._on_select = callback
        return self

    def set_current_page(self, page_name: str):
        self._current_page = page_name

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)

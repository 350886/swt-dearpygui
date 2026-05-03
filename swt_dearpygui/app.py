# swt_dearpygui/app.py
# -*- coding: utf-8 -*-
"""DearPyGUI 应用主循环"""

import dearpygui.dearpygui as dpg
from .theme import ThemeManager


class SWTApp:
    def __init__(self, config_file: str = None):
        self._config_file = config_file
        self._pages = {}
        self._current_page = None
        self._status_bar_tag = None
        self._container_tag = None

    def register_page(self, name: str, page):
        self._pages[name] = page

    def set_status(self, msg: str):
        if self._status_bar_tag and dpg.does_item_exist(self._status_bar_tag):
            dpg.set_value(self._status_bar_tag, msg)

    def show_error(self, msg: str):
        error_color = ThemeManager.get_token("error")
        r, g, b = self._hex_to_rgb(error_color)
        if self._status_bar_tag and dpg.does_item_exist(self._status_bar_tag):
            dpg.configure_item(self._status_bar_tag, default_value=f"错误: {msg}", color=(r, g, b, 1.0))

    def navigate_to(self, page_name: str):
        if self._current_page and self._current_page in self._pages:
            pass
        self._current_page = page_name
        if page_name in self._pages:
            self._pages[page_name].build()
        self.set_status(f"页面: {page_name}")

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)

    def run(self):
        dpg.create_context()
        dpg.create_viewport(title="SWT 货运管理系统", width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

# swt_dearpygui/widgets/modal_dialog.py
# -*- coding: utf-8 -*-
"""模态对话框组件"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class ModalDialog:
    def __init__(self, title: str, size: tuple = (400, 300)):
        self._title = title
        self._width, self._height = size
        self._tag = f"modal_{id(self)}"
        self._child_tag = f"modal_child_{id(self)}"

    def show(self):
        with dpg.window(
            tag=self._tag,
            label=self._title,
            modal=True,
            popup=self._tag,
            width=self._width,
            height=self._height,
            no_resize=True,
            no_move=False,
        ):
            with dpg.child_window(tag=self._child_tag, width=self._width - 40, height=self._height - 80):
                pass

    def hide(self):
        if dpg.does_item_exist(self._tag):
            dpg.hide_item(self._tag)

    def get_child_tag(self) -> str:
        return self._child_tag

    @property
    def tag(self):
        return self._tag

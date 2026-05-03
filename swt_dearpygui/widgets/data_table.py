# swt_dearpygui/widgets/data_table.py
# -*- coding: utf-8 -*-
"""数据表格组件，支持分页和主题色"""

import dearpygui.dearpygui as dpg
from ..theme import ThemeManager


class DataTable:
    def __init__(self, columns: list, page_size: int = 30):
        self._columns = columns
        self._page_size = page_size
        self._data = []
        self._page = 0
        self._tag = f"datatable_{id(self)}"
        self._col_tags = {}
        self._row_tags = []
        self._selected_rows = []
        self._build_columns()

    def _build_columns(self):
        for i, col in enumerate(self._columns):
            tag = f"col_{i}_{id(self)}"
            self._col_tags[col] = tag

    def build(self, parent: str = None, width: float = 400, height: float = 300):
        self._parent = parent
        with dpg.table(tag=self._tag, parent=parent, width=width, height=height,
            auto_resize_columns=True,
            resizable=True,
            no_hosted_header=False,
            reorderable=True,
            sortable=False,
            no_sort_header=True,
            border_inner_width=1,
            border_color=(0.2, 0.2, 0.2, 1),
            row_background_color=(0.95, 0.95, 0.95, 1),
        ):
            for col in self._columns:
                dpg.add_table_column(parent=self._tag, label=col, tag=self._col_tags[col])

    def set_data(self, data: list):
        """data: list of list, each inner list is a row"""
        self._data = data
        self._page = 0
        self._refresh_page()

    def _refresh_page(self):
        for tag in self._row_tags:
            try:
                dpg.delete_item(tag, children_only=True)
            except Exception:
                pass
        self._row_tags.clear()

        start = self._page * self._page_size
        end = min(start + self._page_size, len(self._data))
        page_data = self._data[start:end]

        for row_idx, row in enumerate(page_data):
            row_tag = f"row_{self._page}_{row_idx}_{id(self)}"
            self._row_tags.append(row_tag)
            with dpg.table_row(parent=self._tag, tag=row_tag):
                for col_idx, val in enumerate(row):
                    bg_token = "row_even" if (start + row_idx) % 2 == 0 else "row_odd"
                    bg = ThemeManager.get_token(bg_token)
                    r, g, b = self._hex_to_rgb(bg)
                    dpg.add_text(str(val), parent=self._tag, color=(r, g, b, 1.0))

    def _hex_to_rgb(self, hex_color: str):
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)

    def get_selected_rows(self) -> list:
        return self._selected_rows

    def clear(self):
        self._data.clear()
        self._page = 0
        self._row_tags.clear()
        try:
            for tag in self._col_tags:
                dpg.delete_item(tag)
        except Exception:
            pass

    def set_page(self, page: int):
        self._page = max(0, page)
        self._refresh_page()

    def get_page_count(self) -> int:
        return max(0, (len(self._data) + self._page_size - 1) // self._page_size)

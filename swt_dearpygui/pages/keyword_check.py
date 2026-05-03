# swt_dearpygui/pages/keyword_check.py
# -*- coding: utf-8 -*-
"""关键词检测页面"""

import dearpygui.dearpygui as dpg
from .base_page import BasePage
from ..widgets.data_table import DataTable
from ..widgets.search_bar import SearchBar
from ..widgets.modal_dialog import ModalDialog
from ..widgets.toolbar import Toolbar
from ..utils.db_compat import DBCompat
from ..theme import ThemeManager


class KeywordCheckPage(BasePage):
    name = "keyword_check"

    def __init__(self, app, db: DBCompat):
        super().__init__(app)
        self.db = db

    def build(self):
        with dpg.group(parent=self._get_container()):
            dpg.add_text("关键词检测", color=ThemeManager.get_token("text_primary"))

        toolbar = Toolbar(self._get_container())
        toolbar.add_action("搜索", callback=self._on_search)
        toolbar.add_action("新增规则", callback=self._on_add_rule)
        toolbar.add_action("删除规则", callback=self._on_delete_rule)
        toolbar.add_action("刷新", callback=self._on_refresh)
        toolbar.build()

        self._search_bar = SearchBar("输入关键词搜索发票...", width=400)
        self._search_bar.build()

        self._data_table = DataTable(
            columns=["发票代码", "发票号码", "日期", "客户代码", "始发地", "目的地", "匹配关键词"],
            page_size=50,
        )
        self._data_table.build(self._get_container(), width=-1, height=450)

    def _get_container(self) -> str:
        return "page_content"

    def _on_search(self, sender, data):
        try:
            keyword = self._search_bar.get_value()
            if not keyword:
                self.app.set_status("请输入关键词")
                return
            sql = """SELECT im.INVOICECODE, im.INVNUMBER, im.INVDATE, im.CUSTCODE, im.DEST, im.SHIP
                     FROM INVOICE_MASTER im
                     WHERE im.INVOICECODE LIKE %s OR im.INVNUMBER LIKE %s OR im.CUSTCODE LIKE %s
                     ORDER BY im.INVDATE DESC LIMIT 1000"""
            params = (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
            results = self.db.query(sql, params)
            rows = [[str(r.get(c, "")) for c in ["INVOICECODE", "INVNUMBER", "INVDATE", "CUSTCODE", "DEST", "SHIP"]] for r in results]
            self._data_table.set_data(rows)
            self.app.set_status(f"找到 {len(rows)} 条记录")
        except Exception as e:
            self.app.show_error(f"搜索失败: {e}")

    def _on_refresh(self, sender, data):
        self._on_search(sender, data)

    def _on_add_rule(self, sender, data):
        dialog = ModalDialog("新增关键词规则", size=(400, 250))
        dpg.add_text("关键词: ", parent=dialog.get_child_tag())
        dpg.add_input_text(tag="dlg_keyword", placeholder="输入关键词", parent=dialog.get_child_tag(), width=300)
        dpg.add_text("动作: ", parent=dialog.get_child_tag())
        with dpg.combo(label="", tag="dlg_action", parent=dialog.get_child_tag(), width=300):
            dpg.add_item_label("标记")
            dpg.add_item_label("拦截")
            dpg.add_item_label("提醒")
        dpg.add_button(label="确认", parent=dialog.get_child_tag(),
                       callback=lambda s, d, dd=dialog: (self._confirm_add_rule(), dd.hide()))

    def _confirm_add_rule(self):
        try:
            keyword = dpg.get_value("dlg_keyword")
            action = dpg.get_value("dlg_action")
            self.db.execute("INSERT INTO keyword_rules (keyword, action) VALUES (%s, %s)", (keyword, action))
            self.app.set_status("规则已添加")
        except Exception as e:
            self.app.show_error(f"添加失败: {e}")

    def _on_delete_rule(self, sender, data):
        self.app.set_status("请选择要删除的规则")

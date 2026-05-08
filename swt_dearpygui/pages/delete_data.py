# swt_dearpygui/pages/delete_data.py
# -*- coding: utf-8 -*-
"""删除数据页面 — 搜索并删除 CON_DETAIL 记录"""

import dearpygui.dearpygui as dpg
from .base_page import BasePage
from ..theme import ThemeManager


class DeleteDataPage(BasePage):
    name = "delete_data"

    def __init__(self, app):
        super().__init__(app)
        self._rows = []
        self._selected_row = None  # dict of selected row

    def build(self):
        if not dpg.does_item_exist(self._get_container()):
            return
        self._rows = []
        self._selected_row = None
        self._selected_key = None
        with dpg.child_window(parent=self._get_container(), autosize_x=True, autosize_y=True):
            dpg.add_text("删除数据", color=ThemeManager.get_color("text_primary"))
            dpg.add_spacer(height=10)
            self._build_search_card()
            dpg.add_spacer(height=8)
            self._build_table_card()

    def _get_container(self) -> str:
        return "page_content"

    # ── 搜索卡片 ──────────────────────────────────

    def _build_search_card(self):
        with dpg.collapsing_header(label="搜索 CON_DETAIL 记录", default_open=True):
            dpg.add_text("搜索 CON_DETAIL 记录，选中后删除（仅允许删除 NN >= 2 的记录）",
                         color=ThemeManager.get_color("text_secondary"), wrap=800)
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="del_keyword", hint="INVOICECODE", width=180,
                                   on_enter=True, callback=self._do_search)
                dpg.add_button(label="搜索", callback=self._do_search, width=60)
                dpg.add_button(label="清空", callback=self._do_clear, width=60)
                dpg.add_button(label="加载全部", callback=self._do_load_all, width=80)
            dpg.add_text(
                "字段: INVOICECODE(發票號) | NN | CONCODE(櫃號) | DRIVER(司機編號) | "
                "SIZE(櫃尺碼) | DRIVERCODE(香港車牌) | TAKENO(提貨號碼) | DRIVERCOMM(司機運費)",
                color=ThemeManager.get_color("text_secondary"), wrap=800)
            dpg.add_text(tag="del_status", default_value="输入發票號搜索或点击加载全部",
                         color=ThemeManager.get_color("text_secondary"))

    # ── 结果表格卡片 ──────────────────────────────

    def _build_table_card(self):
        with dpg.collapsing_header(label="查询结果", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="删除选中记录", callback=self._request_delete, width=130)
                dpg.add_button(label="刷新", callback=self._do_search, width=60)
            dpg.add_text(tag="del_count", default_value="共 0 条记录",
                         color=ThemeManager.get_color("text_secondary"))
            dpg.add_spacer(height=4)
            with dpg.child_window(height=400, border=True):
                with dpg.table(tag="del_table", header_row=True,
                               borders_innerH=True, borders_outerH=True,
                               policy=dpg.mvTable_SizingFixedFit,
                               height=-1):
                    cols = ("INVOICECODE", "NN", "CONCODE", "DRIVER", "SIZE",
                            "DRIVERCODE", "TAKENO", "DRIVERCOMM")
                    labels = {
                        "INVOICECODE": "發票號", "NN": "NN", "CONCODE": "櫃號",
                        "DRIVER": "司機編號", "SIZE": "櫃尺碼", "DRIVERCODE": "香港車牌",
                        "TAKENO": "提貨號碼", "DRIVERCOMM": "司機運費",
                    }
                    for col in cols:
                        dpg.add_table_column(label=labels.get(col, col),
                                            init_width_or_weight=105)

    # ── 数据操作 ──────────────────────────────────

    def _do_search(self, sender=None, app_data=None, user_data=None):
        keyword = (dpg.get_value("del_keyword") or "").strip()
        if not keyword:
            self._do_load_all()
            return
        self._selected_row = None
        self._set_status("del_status", "搜索中...", "warning")
        try:
            cols = "INVOICECODE, NN, CONCODE, DRIVER, SIZE, DRIVERCODE, TAKENO, DRIVERCOMM"
            self._rows = self.app.db.query(
                f"SELECT {cols} FROM CON_DETAIL WHERE INVOICECODE LIKE %s ORDER BY INVOICECODE",
                (f"%{keyword}%",)
            )
            self._refresh_table()
            self._set_status("del_status", f"共 {len(self._rows)} 条记录", "success")
        except Exception as e:
            self._set_status("del_status", f"搜索失败: {e}", "error")

    def _do_load_all(self, sender=None, app_data=None, user_data=None):
        self._selected_row = None
        self._set_status("del_status", "加载中...", "warning")
        try:
            cols = "INVOICECODE, NN, CONCODE, DRIVER, SIZE, DRIVERCODE, TAKENO, DRIVERCOMM"
            self._rows = self.app.db.query(
                f"SELECT {cols} FROM CON_DETAIL ORDER BY INVOICECODE LIMIT 500"
            )
            self._refresh_table()
            self._set_status("del_status", f"共 {len(self._rows)} 条记录", "success")
        except Exception as e:
            self._set_status("del_status", f"加载失败: {e}", "error")

    def _do_clear(self, sender=None, app_data=None, user_data=None):
        dpg.set_value("del_keyword", "")
        self._rows = []
        self._selected_row = None
        self._clear_table_rows()
        dpg.set_value("del_count", "共 0 条记录")
        self._set_status("del_status", "输入發票號搜索或点击加载全部", "info")

    def _refresh_table(self):
        """清除旧行并重新填充表格"""
        self._clear_table_rows()
        cols = ("INVOICECODE", "NN", "CONCODE", "DRIVER", "SIZE",
                "DRIVERCODE", "TAKENO", "DRIVERCOMM")
        if not dpg.does_item_exist("del_table"):
            return
        selected_key = None
        if self._selected_row:
            selected_key = (
                str(self._selected_row.get("INVOICECODE", "")),
                str(self._selected_row.get("CONCODE", ""))
            )
        for row in self._rows:
            with dpg.table_row(parent="del_table"):
                row_key = (str(row.get("INVOICECODE", "")), str(row.get("CONCODE", "")))
                is_selected = (selected_key is not None and row_key == selected_key)
                for col in cols:
                    val = row.get(col)
                    dpg.add_selectable(
                        label=str(val) if val is not None else "",
                        span_columns=False,
                        default_value=is_selected,
                        callback=self._on_row_select,
                        user_data=row)
        dpg.set_value("del_count", f"共 {len(self._rows)} 条记录")

    def _clear_table_rows(self):
        if not dpg.does_item_exist("del_table"):
            return
        for child in dpg.get_item_children("del_table", slot=1):
            dpg.delete_item(child)

    def _on_row_select(self, sender, app_data, user_data):
        self._selected_row = user_data
        self._refresh_table()  # 重绘以高亮选中行

    # ── 删除确认 ──────────────────────────────────

    def _request_delete(self, sender=None, app_data=None, user_data=None):
        if self._selected_row is None:
            self._set_status("del_status", "请先在表格中选中一条记录", "warning")
            return
        row = self._selected_row
        nn_val = row.get("NN", 0)
        try:
            nn = int(nn_val)
        except (ValueError, TypeError):
            nn = 0
        if nn < 2:
            self._set_status("del_status", f"只能删除 NN >= 2 的记录，当前 NN={nn}", "warning")
            return

        invoice_code = str(row.get("INVOICECODE", ""))
        con_code = str(row.get("CONCODE", ""))
        self._show_delete_popup(invoice_code, con_code)

    def _show_delete_popup(self, invoice_code, con_code):
        if dpg.does_item_exist("del_confirm_popup"):
            dpg.delete_item("del_confirm_popup")
        with dpg.window(label="确认删除", modal=True, tag="del_confirm_popup",
                        width=430, height=250, no_resize=True, no_collapse=True):
            dpg.add_text("⚠ 此操作不可撤销！请输入發票號确认删除",
                         color=ThemeManager.get_color("error"))
            dpg.add_spacer(height=5)
            dpg.add_text(f"發票號: {invoice_code}\n櫃    號: {con_code}")
            dpg.add_spacer(height=8)
            dpg.add_text("请输入發票號（输入匹配后按钮启用）:",
                         color=ThemeManager.get_color("text_secondary"))
            dpg.add_input_text(tag="del_confirm_input", width=380, hint="输入發票號")
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="确认删除", callback=self._do_delete,
                               user_data=(invoice_code, con_code), width=100)
                dpg.add_button(label="取消",
                               callback=lambda: dpg.delete_item("del_confirm_popup"),
                               width=60)

    def _do_delete(self, sender, app_data, user_data):
        invoice_code, con_code = user_data
        confirm = (dpg.get_value("del_confirm_input") or "").strip()
        if confirm != invoice_code:
            self._set_status("del_status", "输入的發票號不匹配", "error")
            return
        if dpg.does_item_exist("del_confirm_popup"):
            dpg.delete_item("del_confirm_popup")
        try:
            affected = self.app.db.execute(
                "DELETE FROM CON_DETAIL WHERE INVOICECODE = %s AND CONCODE = %s AND NN >= 2",
                (invoice_code, con_code)
            )
            self._selected_row = None
            self._set_status("del_status",
                f"已删除 {affected} 条记录 (發票號: {invoice_code}, 櫃號: {con_code})", "success")
            # 刷新列表
            self._do_search()
        except Exception as e:
            self._set_status("del_status", f"删除失败: {e}", "error")

    # ── 辅助方法 ──────────────────────────────────

    def _set_status(self, tag: str, msg: str, level: str):
        if not dpg.does_item_exist(tag):
            return
        dpg.set_value(tag, msg)
        dpg.configure_item(tag, color=ThemeManager.get_color(level))

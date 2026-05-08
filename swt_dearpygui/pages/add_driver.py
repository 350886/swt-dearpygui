# swt_dearpygui/pages/add_driver.py
# -*- coding: utf-8 -*-
"""增加司机页面 — 写入 DRIVER_MASTER / VEHICLE_MASTER / DRIVER_CP"""

import dearpygui.dearpygui as dpg
from .base_page import BasePage
from ..theme import ThemeManager


class AddDriverPage(BasePage):
    name = "add_driver"

    def __init__(self, app):
        super().__init__(app)
        self._edit_code = None
        self._driver_rows = []

    def build(self):
        if not dpg.does_item_exist(self._get_container()):
            return
        self._edit_code = None
        self._driver_rows = []
        with dpg.child_window(parent=self._get_container(), autosize_x=True, autosize_y=True):
            dpg.add_text("增加司机", color=ThemeManager.get_color("text_primary"))
            dpg.add_spacer(height=10)
            self._build_form_card()
            dpg.add_spacer(height=8)
            self._build_list_card()
            # 首次构建后加载列表
            self._load_driver_list()

    def _get_container(self) -> str:
        return "page_content"

    # ── 表单卡片 ──────────────────────────────────

    def _build_form_card(self):
        with dpg.collapsing_header(label="司机信息", default_open=True):
            dpg.add_text("提交后同时写入 DRIVER_MASTER / VEHICLE_MASTER / DRIVER_CP 三张表",
                         color=ThemeManager.get_color("text_secondary"), wrap=800)
            dpg.add_text(tag="adv_mode", default_value="📝 新增司机",
                         color=ThemeManager.get_color("accent"))
            dpg.add_spacer(height=5)

            dpg.add_input_text(tag="adv_driver_code", label="司機編號", width=250)
            dpg.add_input_text(tag="adv_driver_name", label="司機姓名", width=250)
            dpg.add_input_text(tag="adv_hk_plate", label="香港車牌", width=250)
            dpg.add_input_text(tag="adv_sz_plate", label="大陸車牌", width=250)

            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                dpg.add_button(label="提交", callback=self._do_submit, width=80)
                dpg.add_button(label="清空", callback=self._do_clear, width=60)
                dpg.add_button(label="取消编辑", callback=self._do_cancel_edit, width=80)
                dpg.add_button(label="删除司机", callback=self._request_delete, width=80)
            dpg.add_text(tag="adv_status", default_value="",
                         color=ThemeManager.get_color("text_secondary"))

    # ── 司机列表卡片 ──────────────────────────────

    def _build_list_card(self):
        with dpg.collapsing_header(label="司机信息列表（点击行可编辑）", default_open=True):
            dpg.add_text(tag="adv_list_count", default_value="共 0 条",
                         color=ThemeManager.get_color("text_secondary"))
            dpg.add_spacer(height=4)
            with dpg.child_window(height=280, border=True):
                with dpg.table(tag="adv_table", header_row=True,
                               borders_innerH=True, borders_outerH=True,
                               policy=dpg.mvTable_SizingFixedFit,
                               height=-1):
                    cols = ("CUSTCODE", "NAME", "HKCP", "SZCP")
                    labels = {"CUSTCODE": "司機編號", "NAME": "司機姓名",
                              "HKCP": "香港車牌", "SZCP": "大陸車牌"}
                    for col in cols:
                        dpg.add_table_column(label=labels[col],
                                            init_width_or_weight=115)

    # ── 司机列表数据 ──────────────────────────────

    def _load_driver_list(self):
        try:
            self._driver_rows = self.app.db.query(
                "SELECT CUSTCODE, NAME, HKCP, SZCP FROM DRIVER_CP ORDER BY CUSTCODE"
            )
            self._refresh_driver_table(self._driver_rows)
        except Exception as e:
            if dpg.does_item_exist("adv_list_count"):
                dpg.set_value("adv_list_count", "加载失败")

    def _refresh_driver_table(self, rows):
        if not dpg.does_item_exist("adv_table"):
            return
        for child in dpg.get_item_children("adv_table", slot=1):
            dpg.delete_item(child)
        cols = ("CUSTCODE", "NAME", "HKCP", "SZCP")
        for row in rows:
            with dpg.table_row(parent="adv_table"):
                is_selected = (
                    self._edit_code is not None
                    and str(row.get("CUSTCODE", "")) == str(self._edit_code)
                )
                for col in cols:
                    val = row.get(col)
                    dpg.add_selectable(
                        label=str(val) if val is not None else "",
                        span_columns=False,
                        default_value=is_selected,
                        callback=self._on_row_select,
                        user_data=row)
        dpg.set_value("adv_list_count", f"共 {len(rows)} 条")

    def _on_row_select(self, sender, app_data, user_data):
        row = user_data
        dpg.set_value("adv_driver_code", str(row.get("CUSTCODE", "") or ""))
        dpg.set_value("adv_driver_name", str(row.get("NAME", "") or ""))
        dpg.set_value("adv_hk_plate", str(row.get("HKCP", "") or ""))
        dpg.set_value("adv_sz_plate", str(row.get("SZCP", "") or ""))
        self._edit_code = row.get("CUSTCODE", "")
        dpg.set_value("adv_mode", "✏️ 编辑司机")
        dpg.configure_item("adv_mode", color=ThemeManager.get_color("warning"))
        self._set_status("adv_status", "", "info")
        self._refresh_driver_table(self._driver_rows)  # 重绘以高亮选中行

    # ── 表单操作 ──────────────────────────────────

    def _do_clear(self, sender=None, app_data=None, user_data=None):
        for tag in ("adv_driver_code", "adv_driver_name", "adv_hk_plate", "adv_sz_plate"):
            dpg.set_value(tag, "")
        dpg.set_value("adv_mode", "📝 新增司机")
        dpg.configure_item("adv_mode", color=ThemeManager.get_color("accent"))
        self._edit_code = None
        self._set_status("adv_status", "", "info")

    def _do_cancel_edit(self, sender=None, app_data=None, user_data=None):
        self._do_clear()

    def _do_submit(self, sender=None, app_data=None, user_data=None):
        driver_code = (dpg.get_value("adv_driver_code") or "").strip()
        driver_name = (dpg.get_value("adv_driver_name") or "").strip()
        hk_plate = (dpg.get_value("adv_hk_plate") or "").strip()
        sz_plate = (dpg.get_value("adv_sz_plate") or "").strip()

        if not driver_code:
            self._set_status("adv_status", "请输入司機編號", "warning"); return
        if not driver_name:
            self._set_status("adv_status", "请输入司機姓名", "warning"); return
        if not hk_plate:
            self._set_status("adv_status", "请输入香港車牌", "warning"); return

        db = self.app.db
        try:
            # 新增模式：检查重复
            if not self._edit_code:
                existing = db.query(
                    "SELECT CUSTCODE, NAME, HKCP, SZCP FROM DRIVER_CP WHERE CUSTCODE = %s",
                    (driver_code,)
                )
                if existing:
                    row = existing[0]
                    dpg.set_value("adv_driver_code", str(row.get("CUSTCODE", "") or ""))
                    dpg.set_value("adv_driver_name", str(row.get("NAME", "") or ""))
                    dpg.set_value("adv_hk_plate", str(row.get("HKCP", "") or ""))
                    dpg.set_value("adv_sz_plate", str(row.get("SZCP", "") or ""))
                    self._edit_code = driver_code
                    dpg.set_value("adv_mode", "✏️ 编辑司机")
                    dpg.configure_item("adv_mode", color=ThemeManager.get_color("warning"))
                    self._set_status("adv_status",
                        f"⚠ 司機編號 {driver_code} 已存在，已加载其信息，请修改后提交", "warning")
                    return

            # 香港車牌去重
            edit_code = self._edit_code
            while True:
                if edit_code:
                    rows = db.query(
                        "SELECT HKCP FROM DRIVER_CP WHERE HKCP = %s AND CUSTCODE != %s",
                        (hk_plate, edit_code))
                else:
                    rows = db.query(
                        "SELECT HKCP FROM DRIVER_CP WHERE HKCP = %s", (hk_plate,))
                if not rows:
                    break
                hk_plate += "*"
            dpg.set_value("adv_hk_plate", hk_plate)

            # 三表写入
            db.execute(
                "INSERT INTO DRIVER_MASTER (DRIVERCODE, NAME) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE NAME = VALUES(NAME)",
                (driver_code, driver_name))
            db.execute(
                "INSERT INTO VEHICLE_MASTER (VEHICLECODE, DRIVER) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE DRIVER = VALUES(DRIVER)",
                (hk_plate, driver_code))
            db.execute(
                "INSERT INTO DRIVER_CP (CUSTCODE, NAME, HKCP, SZCP) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE NAME = VALUES(NAME), HKCP = VALUES(HKCP), SZCP = VALUES(SZCP)",
                (driver_code, driver_name, hk_plate, sz_plate))

            action = "更新" if self._edit_code else "添加"
            self._set_status("adv_status",
                f"✅ 司机 {driver_name}（{driver_code}）{action}成功", "success")
            self._do_clear()
            self._load_driver_list()
        except Exception as e:
            action = "更新" if self._edit_code else "添加"
            self._set_status("adv_status", f"❌ {action}失败: {e}", "error")

    # ── 删除司机 ──────────────────────────────────

    def _request_delete(self, sender=None, app_data=None, user_data=None):
        driver_code = (dpg.get_value("adv_driver_code") or "").strip()
        if not driver_code:
            self._set_status("adv_status",
                "请先在表单中输入要删除的司機編號，或从列表中点击选择", "warning")
            return
        self._show_delete_popup(driver_code)

    def _show_delete_popup(self, driver_code):
        if dpg.does_item_exist("adv_del_popup"):
            dpg.delete_item("adv_del_popup")
        with dpg.window(label="确认删除司机", modal=True, tag="adv_del_popup",
                        width=430, height=250, no_resize=True, no_collapse=True):
            dpg.add_text(
                "⚠ 此操作将删除该司机在 DRIVER_MASTER / VEHICLE_MASTER / DRIVER_CP 中的所有记录！",
                color=ThemeManager.get_color("error"), wrap=380)
            dpg.add_spacer(height=5)
            dpg.add_text(f"司機編號: {driver_code}")
            dpg.add_spacer(height=8)
            dpg.add_text("请输入司機編號确认删除（输入匹配后按钮启用）:",
                         color=ThemeManager.get_color("text_secondary"))
            dpg.add_input_text(tag="adv_del_confirm_input", width=380, hint="输入司機編號")
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="确认删除", callback=self._do_delete,
                               user_data=driver_code, width=100)
                dpg.add_button(label="取消",
                               callback=lambda: dpg.delete_item("adv_del_popup"),
                               width=60)

    def _do_delete(self, sender, app_data, user_data):
        driver_code = user_data
        confirm = (dpg.get_value("adv_del_confirm_input") or "").strip()
        if confirm != driver_code:
            self._set_status("adv_status", "输入的司機編號不匹配", "error")
            return
        if dpg.does_item_exist("adv_del_popup"):
            dpg.delete_item("adv_del_popup")
        try:
            db = self.app.db
            db.execute("DELETE FROM DRIVER_MASTER WHERE DRIVERCODE = %s", (driver_code,))
            db.execute("DELETE FROM VEHICLE_MASTER WHERE DRIVER = %s", (driver_code,))
            db.execute("DELETE FROM DRIVER_CP WHERE CUSTCODE = %s", (driver_code,))
            self._set_status("adv_status",
                f"✅ 司机 {driver_code} 已从三表中删除", "success")
            self._do_clear()
            self._load_driver_list()
        except Exception as e:
            self._set_status("adv_status", f"❌ 删除失败: {e}", "error")

    # ── 辅助方法 ──────────────────────────────────

    def _set_status(self, tag: str, msg: str, level: str):
        if not dpg.does_item_exist(tag):
            return
        dpg.set_value(tag, msg)
        dpg.configure_item(tag, color=ThemeManager.get_color(level))

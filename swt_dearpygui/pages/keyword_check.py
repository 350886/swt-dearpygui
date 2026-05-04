# swt_dearpygui/pages/keyword_check.py
# -*- coding: utf-8 -*-
"""关键词检测页面 — 月度检查 + misc_name_rules CRUD"""

import os
import re
from datetime import datetime
import dearpygui.dearpygui as dpg
from .base_page import BasePage
from ..theme import ThemeManager


class KeywordCheckPage(BasePage):
    name = "keyword_check"

    _columns = ["ID", "排序", "匹配类型", "关键字", "替换值"]

    def __init__(self, app):
        super().__init__(app)
        self._rules = []
        self._selected_id = None
        self._first_load_done = False

    def build(self):
        if not dpg.does_item_exist(self._get_container()):
            return
        with dpg.child_window(parent=self._get_container(), autosize_x=True, autosize_y=True):
            dpg.add_text("关键词检测", color=ThemeManager.get_color("text_primary"))
            dpg.add_separator()
            dpg.add_spacer(height=6)
            self._build_check_card()
            dpg.add_spacer(height=8)
            self._build_rules_card()

    def _get_container(self) -> str:
        return "page_content"

    # ── 月度检查卡片 ────────────────────────────────

    def _build_check_card(self):
        with dpg.collapsing_header(label="月度检查", default_open=True):
            dpg.add_text("选择年月执行月度杂费名称检查，发现未被规则覆盖的杂费名称。",
                         color=ThemeManager.get_color("text_secondary"), wrap=800)

            with dpg.group(horizontal=True):
                dpg.add_text("选择年月:", color=ThemeManager.get_color("text_secondary"))
                dpg.add_combo(tag="check_year", items=[str(y) for y in range(2003, 2051)],
                              default_value=str(datetime.now().year), width=80)
                dpg.add_text("年", color=ThemeManager.get_color("text_secondary"))
                dpg.add_combo(tag="check_month", items=[f"{m:02d}" for m in range(1, 13)],
                              default_value=f"{datetime.now().month:02d}", width=60)
                dpg.add_text("月", color=ThemeManager.get_color("text_secondary"))

            with dpg.group(horizontal=True):
                dpg.add_button(label="开始检查", callback=self._do_monthly_check, width=100)
                dpg.add_text(tag="check_status", default_value="准备就绪",
                             color=ThemeManager.get_color("text_secondary"))

            dpg.add_input_text(tag="check_log", multiline=True, readonly=True,
                               width=-1, height=200)

    def _do_monthly_check(self, _sender=None, _app_data=None, _user_data=None):
        self._set_check_status("正在检查...", "warning")
        self._clear_check_log()
        try:
            year = int(dpg.get_value("check_year"))
            month = int(dpg.get_value("check_month"))
            date_start = f"{year}-{month:02d}-01"
            if month == 12:
                date_end = f"{year + 1}-01-01"
            else:
                date_end = f"{year}-{month + 1:02d}-01"

            db = self.app.db

            # 步骤1：清理旧表
            self._append_check_log(f"{'='*60}")
            self._append_check_log(f"客户月结单检查 - {year}年{month}月")
            self._append_check_log(f"{'='*60}")
            self._append_check_log("步骤1: 删除旧表...")
            db.execute("DROP TABLE IF EXISTS `客户月结单TEMP`")
            db.execute("DROP TABLE IF EXISTS `_check_temp_raw`")
            self._append_check_log("[OK] 旧表已清理")

            # 步骤2：先生成 raw 数据（普通表，避免 TEMPORARY 跨连接丢失）
            self._append_check_log(f"步骤2: 生成客户月结单TEMP ({year}-{month:02d})...")
            db.execute(
                "CREATE TABLE `_check_temp_raw` AS "
                "SELECT t.INVDATE AS `日期`, t.INVOICECODE AS `發票號`, t.CUSTCODE AS `客戶編號`, "
                "COALESCE(cm.NAME, '') AS `客戶名稱`, "
                "t.NAME AS `司機姓名`, t.HKCP AS `香港車牌`, t.SZCP AS `大陸車牌`, "
                "t.DEST AS `地區`, t.CONCODE AS `櫃號`, t.SIZE AS `櫃尺碼`, "
                "t.TAKENO AS `提單號`, t.SHIP AS `船名`, t.SHIPCODE AS `托運號`, t.FEE AS `運費`, "
                "t.dp, t.pp, t.`運雜費合計` "
                "FROM ("
                "  SELECT im.INVDATE, im.INVOICECODE, im.CUSTCODE, cd.DRIVER, "
                "    dc.NAME, dc.HKCP, dc.SZCP, im.DEST, cd.CONCODE, cd.SIZE, cd.TAKENO, "
                "    im.SHIP, im.SHIPCODE, im.FEE, "
                "    GROUP_CONCAT(CASE WHEN id.WHOPAY=1 THEN id.DESCR END "
                "      ORDER BY id.NN ASC SEPARATOR '§') AS dp, "
                "    GROUP_CONCAT(CASE WHEN id.WHOPAY=1 THEN id.PRICE END "
                "      ORDER BY id.NN ASC SEPARATOR '§') AS pp, "
                "    COALESCE(im.FEE,0) + COALESCE(SUM(CASE WHEN id.WHOPAY=1 "
                "      THEN id.PRICE ELSE 0 END),0) AS `運雜費合計` "
                "  FROM INVOICE_MASTER im "
                "  LEFT JOIN CON_DETAIL cd ON cd.INVOICECODE = im.INVOICECODE AND cd.NN = 1 "
                "  LEFT JOIN DRIVER_CP dc ON dc.CUSTCODE = cd.DRIVER "
                "  LEFT JOIN INVOICE_DETAIL id ON id.INVOICECODE = im.INVOICECODE "
                "  WHERE im.INVDATE >= %s AND im.INVDATE < %s "
                "  GROUP BY im.INVOICECODE, im.INVDATE, im.CUSTCODE, cd.DRIVER, "
                "    dc.NAME, dc.HKCP, dc.SZCP, im.DEST, cd.CONCODE, cd.SIZE, "
                "    cd.TAKENO, im.SHIP, im.SHIPCODE, im.FEE"
                ") t LEFT JOIN CUST_MASTER cm ON cm.CUSTCODE = t.CUSTCODE",
                (date_start, date_end))

            # 构建20对杂费列
            misc_pairs = []
            for i in range(1, 21):
                misc_pairs.append(
                    f"IF(CHAR_LENGTH(dp)-CHAR_LENGTH(REPLACE(dp,'§',''))>={i - 1}, "
                    f"SUBSTRING_INDEX(SUBSTRING_INDEX(dp,'§',{i}),'§',-1), NULL) AS `雜費名稱{i}`"
                )
                misc_pairs.append(
                    f"IF(CHAR_LENGTH(pp)-CHAR_LENGTH(REPLACE(pp,'§',''))>={i - 1}, "
                    f"CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(pp,'§',{i}),'§',-1) AS DECIMAL(12,2)), NULL) AS `雜費金額{i}`"
                )

            db.execute(
                f"CREATE TABLE `客户月结单TEMP` AS "
                f"SELECT `日期`, `發票號`, `客戶編號`, `客戶名稱`, `司機姓名`, `香港車牌`, `大陸車牌`, "
                f"`地區`, `櫃號`, `櫃尺碼`, `提單號`, `船名`, `托運號`, `運費`, "
                f"{', '.join(misc_pairs)}, `運雜費合計` FROM `_check_temp_raw`")
            db.execute("DROP TABLE IF EXISTS `_check_temp_raw`")

            cnt = db.query("SELECT COUNT(*) AS cnt FROM `客户月结单TEMP`")[0]["cnt"]
            self._append_check_log(f"[OK] 客户月结单TEMP 生成完成 ({cnt} 条记录)")

            # 步骤3：归一化
            self._append_check_log("步骤3: 标准化杂费名称...")
            from ..utils.pipeline import normalize_misc_names
            normalize_misc_names(db, "客户月结单TEMP")
            self._append_check_log("[OK] 雜費名稱归一化 完成")

            # 步骤4：检查未匹配
            self._append_check_log("步骤4: 检查是否有新增未标准化的杂费名称...")
            misc_cols = db.query(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = 'SWT' AND TABLE_NAME = '客户月结单TEMP' "
                "AND COLUMN_NAME LIKE '雜費名稱%%' ORDER BY ORDINAL_POSITION")
            misc_cols = [r["COLUMN_NAME"] for r in misc_cols]

            rules = db.query(
                "SELECT pattern_type, keyword FROM misc_name_rules ORDER BY sort_order")

            rule_patterns = []
            for rule in rules:
                kw = rule["keyword"]
                ptype = rule["pattern_type"]
                if ptype == "exact":
                    pattern = f"^{re.escape(kw)}$"
                elif ptype == "contains":
                    pattern = f".*{re.escape(kw)}.*"
                else:
                    pattern = f"^{re.escape(kw)}"
                rule_patterns.append(re.compile(pattern, re.IGNORECASE))

            unmatched_data = {}
            for col in misc_cols:
                rows = db.query(
                    f"SELECT DISTINCT `{col}`, `發票號` FROM `客户月结单TEMP` "
                    f"WHERE `{col}` IS NOT NULL AND `{col}` != ''")
                for row in rows:
                    misc_name = row.get(col, "")
                    invoice = row.get("發票號", "")
                    if not misc_name or not misc_name.strip():
                        continue
                    matched = any(p.match(misc_name) for p in rule_patterns)
                    if not matched:
                        if misc_name not in unmatched_data:
                            unmatched_data[misc_name] = {"count": 0, "cols": set(), "invoices": set()}
                        unmatched_data[misc_name]["count"] += 1
                        unmatched_data[misc_name]["cols"].add(col)
                        if invoice:
                            unmatched_data[misc_name]["invoices"].add(invoice)

            if not unmatched_data:
                self._append_check_log("[OK] 检查结果：无新增未标准化的杂费名称")
            else:
                self._append_check_log(
                    f"[!!] 发现 {len(unmatched_data)} 个未标准化的杂费名称：")
                self._append_check_log(f"{'杂费名称':<25} {'次数':<8} {'涉及列':<20} {'示例发票号'}")
                self._append_check_log("-" * 90)
                for name, data in sorted(unmatched_data.items(),
                                         key=lambda x: x[1]["count"], reverse=True):
                    inv_list = sorted(data["invoices"])
                    inv_str = ", ".join(inv_list[:10])
                    if len(inv_list) > 10:
                        inv_str += "..."
                    self._append_check_log(
                        f"{name:<25} {data['count']:<8} "
                        f"{', '.join(sorted(data['cols'])):<20} {inv_str}")

            db.execute("DROP TABLE IF EXISTS `客户月结单TEMP`")
            self._append_check_log(f"\n{'='*60}")
            self._append_check_log("检查完成")
            self._set_check_status("检查完成", "success")

        except Exception as e:
            import traceback
            self._append_check_log(f"错误: {e}")
            self._append_check_log(traceback.format_exc())
            try:
                self.app.db.execute("DROP TABLE IF EXISTS `_check_temp_raw`")
                self.app.db.execute("DROP TABLE IF EXISTS `客户月结单TEMP`")
            except Exception:
                pass
            self._set_check_status(f"检查失败: {e}", "error")

    # ── 规则管理卡片 ────────────────────────────────

    def _build_rules_card(self):
        with dpg.collapsing_header(label="规则管理", default_open=True):
            dpg.add_text("管理 misc_name_rules 表中的杂费名称归一化规则，修改后立即生效。",
                         color=ThemeManager.get_color("text_secondary"), wrap=800)
            dpg.add_spacer(height=6)

            # 搜索栏（实时搜索）
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="rule_search", hint="输入关键字或替换值实时搜索...", width=300,
                                   callback=self._on_search)
                dpg.add_button(label="刷新", callback=self._on_refresh, width=60)
                dpg.add_text(tag="rule_count", default_value="",
                             color=ThemeManager.get_color("text_secondary"))

            dpg.add_spacer(height=4)

            # 规则列表
            with dpg.child_window(tag="rule_list_frame", width=-1, height=250, border=True):
                with dpg.group(tag="rule_list_group"):
                    dpg.add_text("加载中...", tag="rule_list_placeholder")

            dpg.add_spacer(height=6)

            # 编辑表单
            with dpg.collapsing_header(label="规则编辑", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("ID:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_text(tag="rule_id_display", default_value="-",
                                 color=ThemeManager.get_color("text_primary"))
                    dpg.add_text("  排序:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_input_int(tag="rule_sort_order", default_value=0,
                                      width=60, step=0)

                with dpg.group(horizontal=True):
                    dpg.add_text("匹配类型:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_combo(tag="rule_pattern_type", items=["prefix", "contains", "exact"],
                                  default_value="prefix", width=100)
                    dpg.add_text("  关键字:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_input_text(tag="rule_keyword", hint="输入关键字", width=200)
                    dpg.add_text("  替换值:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_input_text(tag="rule_replacement", hint="输入替换值", width=200)
                    dpg.add_text("  客户:", color=ThemeManager.get_color("text_secondary"))
                    dpg.add_input_text(tag="rule_cust_code", hint="留空=全局, 0332=专属", width=80)

                with dpg.group(horizontal=True):
                    dpg.add_button(label="新增", callback=self._add_rule, width=60)
                    dpg.add_button(label="修改", callback=self._edit_rule, width=60)
                    dpg.add_button(label="删除", callback=self._delete_rule, width=60)
                    dpg.add_button(label="清空", callback=self._clear_form, width=60)
                    dpg.add_button(label="↑", callback=lambda s, a, u: self._move_rule(-1), width=30)
                    dpg.add_button(label="↓", callback=lambda s, a, u: self._move_rule(1), width=30)

            dpg.add_spacer(height=4)

            dpg.add_button(label="更新储存过程", callback=self._update_procedures,
                          width=-1, height=30)

            dpg.add_spacer(height=4)

            with dpg.group(horizontal=True):
                dpg.add_button(label="导出规则", callback=self._export_rules, width=80)
                dpg.add_button(label="导入规则", callback=self._import_rules, width=80)

            # 初始加载数据
            if not self._first_load_done:
                self._refresh_table_data()

    # ── 规则列表 ────────────────────────────────────

    def _refresh_table_data(self, rules=None):
        if rules is None:
            try:
                try:
                    rules = self.app.db.query(
                        "SELECT id, sort_order, pattern_type, keyword, replacement, cust_code "
                        "FROM misc_name_rules ORDER BY sort_order")
                except Exception:
                    rules = self.app.db.query(
                        "SELECT id, sort_order, pattern_type, keyword, replacement "
                        "FROM misc_name_rules ORDER BY sort_order")
            except Exception as e:
                self._rules = []
                if dpg.does_item_exist("rule_count"):
                    dpg.set_value("rule_count", "数据库连接失败，请检查设置")
                self.app.show_error(f"数据库连接失败: {e}")
                self.app.navigate_to("settings")
                self._first_load_done = True
                return
        self._rules = rules
        group = "rule_list_group"
        if not dpg.does_item_exist(group):
            return
        dpg.delete_item(group, children_only=True)

        for rule in rules:
            cust = rule.get("cust_code") or ""
            label = (f"[{rule['id']:4d}]  {rule['sort_order']:4d} | "
                     f"{rule['pattern_type']:8s} | {cust:6s} | {rule['keyword']:20s} → {rule['replacement']}")
            dpg.add_selectable(
                label=label, parent=group,
                callback=self._on_rule_selected, user_data=rule["id"],
                span_columns=True)

        if dpg.does_item_exist("rule_count"):
            dpg.set_value("rule_count", f"共 {len(rules)} 条规则")
        self._first_load_done = True

    def _on_rule_selected(self, _sender, _app_data, user_data):
        rule_id = user_data
        for r in self._rules:
            if r["id"] == rule_id:
                self._selected_id = rule_id
                dpg.set_value("rule_id_display", str(r["id"]))
                dpg.set_value("rule_sort_order", r["sort_order"])
                dpg.set_value("rule_pattern_type", r["pattern_type"])
                dpg.set_value("rule_keyword", r["keyword"])
                dpg.set_value("rule_replacement", r["replacement"])
                dpg.set_value("rule_cust_code", r.get("cust_code") or "")
                break

    def _clear_form(self, _sender=None, _app_data=None, _user_data=None):
        self._selected_id = None
        dpg.set_value("rule_id_display", "-")
        dpg.set_value("rule_sort_order", 0)
        dpg.set_value("rule_pattern_type", "prefix")
        dpg.set_value("rule_keyword", "")
        dpg.set_value("rule_replacement", "")
        dpg.set_value("rule_cust_code", "")

    def _on_search(self, _sender, _app_data, _user_data=None):
        keyword = dpg.get_value("rule_search").strip()
        if not keyword:
            self._refresh_table_data()
            return
        rules = self.app.db.query(
            "SELECT id, sort_order, pattern_type, keyword, replacement, cust_code "
            "FROM misc_name_rules "
            "WHERE keyword LIKE %s OR replacement LIKE %s "
            "ORDER BY sort_order",
            (f"%{keyword}%", f"%{keyword}%"))
        self._refresh_table_data(rules)

    def _on_refresh(self, _sender=None, _app_data=None, _user_data=None):
        dpg.set_value("rule_search", "")
        self._refresh_table_data()

    # ── CRUD ────────────────────────────────────────

    def _add_rule(self, _sender=None, _app_data=None, _user_data=None):
        keyword = dpg.get_value("rule_keyword").strip()
        replacement = dpg.get_value("rule_replacement").strip()
        pattern_type = dpg.get_value("rule_pattern_type")
        cust_code = dpg.get_value("rule_cust_code").strip() or None

        if not keyword:
            self.app.set_status("关键字不能为空")
            return
        if not replacement:
            self.app.set_status("替换值不能为空")
            return

        row = self.app.db.query(
            "SELECT COUNT(*) AS cnt FROM misc_name_rules WHERE keyword = %s", (keyword,))
        if row[0]["cnt"] > 0:
            self.app.set_status(f"关键字「{keyword}」已存在")
            return

        row = self.app.db.query(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 AS cnt FROM misc_name_rules")
        sort_order = row[0]["cnt"]

        self.app.db.execute(
            "INSERT INTO misc_name_rules (sort_order, pattern_type, keyword, replacement, cust_code, memo) "
            "VALUES (%s, %s, %s, %s, %s, NULL)",
            (sort_order, pattern_type, keyword, replacement, cust_code))
        self._clear_form()
        self._refresh_table_data()
        self.app.set_status("规则添加成功")

    def _edit_rule(self, _sender=None, _app_data=None, _user_data=None):
        if self._selected_id is None:
            self.app.set_status("请先选择要修改的规则")
            return

        sort_order = dpg.get_value("rule_sort_order")
        pattern_type = dpg.get_value("rule_pattern_type")
        keyword = dpg.get_value("rule_keyword").strip()
        replacement = dpg.get_value("rule_replacement").strip()
        cust_code = dpg.get_value("rule_cust_code").strip() or None

        if not keyword:
            self.app.set_status("关键字不能为空")
            return
        if not replacement:
            self.app.set_status("替换值不能为空")
            return

        row = self.app.db.query(
            "SELECT COUNT(*) AS cnt FROM misc_name_rules WHERE keyword = %s AND id != %s",
            (keyword, self._selected_id))
        if row[0]["cnt"] > 0:
            self.app.set_status(f"关键字「{keyword}」已存在")
            return

        self.app.db.execute(
            "UPDATE misc_name_rules SET sort_order = %s, pattern_type = %s, "
            "keyword = %s, replacement = %s, cust_code = %s WHERE id = %s",
            (sort_order, pattern_type, keyword, replacement, cust_code, self._selected_id))
        self._clear_form()
        self._refresh_table_data()
        self.app.set_status("规则修改成功")

    def _move_rule(self, delta: int, _sender=None, _app_data=None, _user_data=None):
        """上下移动规则的排序顺序"""
        if self._selected_id is None:
            self.app.set_status("请先选择要移动的规则")
            return

        current = dpg.get_value("rule_sort_order")
        new_order = current + delta
        if new_order < 1:
            return

        # 找到目标位置的规则并交换
        target = self.app.db.query(
            "SELECT id, sort_order FROM misc_name_rules WHERE sort_order = %s AND id != %s",
            (new_order, self._selected_id))
        if target:
            # 交换 sort_order
            self.app.db.execute(
                "UPDATE misc_name_rules SET sort_order = %s WHERE id = %s",
                (current, target[0]["id"]))
            self.app.db.execute(
                "UPDATE misc_name_rules SET sort_order = %s WHERE id = %s",
                (new_order, self._selected_id))
        else:
            # 无冲突，直接更新
            self.app.db.execute(
                "UPDATE misc_name_rules SET sort_order = %s WHERE id = %s",
                (new_order, self._selected_id))

        self._refresh_table_data()
        dpg.set_value("rule_sort_order", new_order)
        self.app.set_status(f"已移动到位置 {new_order}")

    def _delete_rule(self, _sender=None, _app_data=None, _user_data=None):
        if self._selected_id is None:
            self.app.set_status("请先选择要删除的规则")
            return

        keyword = dpg.get_value("rule_keyword")
        replacement = dpg.get_value("rule_replacement")

        tag = "delete_confirm_dialog"

        def on_confirm():
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
            self.app.db.execute(
                "DELETE FROM misc_name_rules WHERE id = %s", (self._selected_id,))
            self._clear_form()
            self._refresh_table_data()
            self.app.set_status(f"已删除规则: {keyword} → {replacement}")

        def on_cancel():
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)

        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        with dpg.window(tag=tag, label="确认删除", modal=True, popup=True,
                        width=400, height=180, no_resize=True):
            dpg.add_text(f"确认删除以下规则?")
            dpg.add_spacer(height=8)
            dpg.add_text(f"关键字: {keyword}", color=ThemeManager.get_color("warning"))
            dpg.add_text(f"替换值: {replacement}", color=ThemeManager.get_color("warning"))
            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                dpg.add_button(label="确认删除", callback=on_confirm, width=100)
                dpg.add_button(label="取消", callback=on_cancel, width=80)

    # ── 导入导出 ────────────────────────────────────

    def _export_rules(self, _sender=None, _app_data=None, _user_data=None):
        rules = self.app.db.query(
            "SELECT id, sort_order, pattern_type, keyword, replacement, cust_code "
            "FROM misc_name_rules ORDER BY sort_order")
        if not rules:
            self.app.set_status("没有规则可导出")
            return

        out_dir = self.app.config.get("export_dir", "")
        if not os.path.isdir(out_dir):
            out_dir = os.getcwd()

        fname = f"misc_name_rules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        fpath = os.path.join(out_dir, fname)

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("# 杂费名称规则导出\n")
                f.write(f"# 导出时间: {datetime.now()}\n")
                f.write(f"# 共 {len(rules)} 条规则\n")
                f.write("# 格式: sort_order|pattern_type|keyword|replacement|cust_code\n\n")
                for r in rules:
                    cust = r.get("cust_code") or ""
                    f.write(
                        f"{r['sort_order']}|{r['pattern_type']}|{r['keyword']}|{r['replacement']}|{cust}\n")
            self.app.set_status(f"导出成功: {fname} ({len(rules)} 条)")
        except Exception as e:
            self.app.set_status(f"导出失败: {e}")

    def _import_rules(self, _sender=None, _app_data=None, _user_data=None):
        # 使用文件选择对话框
        if dpg.does_item_exist("rule_import_dialog"):
            dpg.delete_item("rule_import_dialog")
        dpg.add_file_dialog(
            tag="rule_import_dialog",
            callback=self._on_import_file_selected,
            cancel_callback=lambda: None,
            width=600, height=400,
            show=False,
        )

        # 设置扩展名过滤
        try:
            dpg.set_item_label("rule_import_dialog", "选择规则文件 (.txt)")
        except Exception:
            pass

        dpg.show_item("rule_import_dialog")

    def _on_import_file_selected(self, _sender, info, _user_data=None):
        filepath = info.get("file_path_name", "")
        if not filepath or not os.path.isfile(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            db = self.app.db
            imported = 0
            errors = 0

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("|")
                if len(parts) < 4:
                    errors += 1
                    continue

                try:
                    sort_order = int(parts[0])
                    pattern_type = parts[1]
                    keyword = parts[2]
                    replacement = parts[3]
                    cust_code = parts[4].strip() if len(parts) >= 5 else None
                    if not cust_code:
                        cust_code = None

                    db.execute(
                        "INSERT INTO misc_name_rules (sort_order, pattern_type, "
                        "keyword, replacement, cust_code, memo) VALUES (%s, %s, %s, %s, %s, NULL)",
                        (sort_order, pattern_type, keyword, replacement, cust_code))
                    imported += 1
                except Exception:
                    errors += 1

            self._refresh_table_data()
            self.app.set_status(
                f"导入完成: {imported} 条成功, {errors} 条失败 (共 {len(lines)} 行)")
        except Exception as e:
            self.app.set_status(f"导入失败: {e}")

    # ── 更新储存过程 ────────────────────────────────

    def _update_procedures(self, _sender=None, _app_data=None, _user_data=None):
        from ..widgets.modal_dialog import ModalDialog

        def on_confirm():
            if dpg.does_item_exist("update_proc_dialog"):
                dpg.delete_item("update_proc_dialog")

        if dpg.does_item_exist("update_proc_dialog"):
            dpg.delete_item("update_proc_dialog")
        with dpg.window(tag="update_proc_dialog", label="更新储存过程", modal=True,
                        width=450, height=180, no_resize=True):
            dpg.add_text("归一化功能已改为代码内执行，不再需要更新存储过程。")
            dpg.add_spacer(height=8)
            dpg.add_text("修改 misc_name_rules 表后自动生效。",
                         color=ThemeManager.get_color("text_secondary"))
            dpg.add_spacer(height=12)
            dpg.add_button(label="确定", callback=on_confirm, width=80)

    # ── helpers ─────────────────────────────────────

    def _append_check_log(self, text: str):
        if dpg.does_item_exist("check_log"):
            current = dpg.get_value("check_log")
            dpg.set_value("check_log", current + text + "\n")

    def _clear_check_log(self):
        if dpg.does_item_exist("check_log"):
            dpg.set_value("check_log", "")

    def _set_check_status(self, msg: str, level: str):
        color = ThemeManager.get_color(level)
        if dpg.does_item_exist("check_status"):
            dpg.set_value("check_status", msg)
            dpg.configure_item("check_status", color=color)

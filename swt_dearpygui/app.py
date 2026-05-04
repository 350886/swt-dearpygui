# swt_dearpygui/app.py
# -*- coding: utf-8 -*-
"""DearPyGUI 应用主循环"""

import os
import json
import dearpygui.dearpygui as dpg
from .theme import ThemeManager
from .widgets.sidebar import Sidebar
from .widgets.status_bar import StatusBar
from .utils.db_compat import DBCompat


DEFAULT_CONFIG = {
    "db_host": "127.0.0.1",
    "db_port": "3306",
    "db_user": "mysql",
    "db_password": "mysql",
    "db_name": "SWT",
    "export_dir": r"X:\客户月结单",
    "summary_dir": r"X:\月结单",
    "biz_dir": r"X:\月结单",
    "driver_export_dir": r"X:\司机月结单",
    "driver_summary_dir": r"X:\司机汇总表",
    "driver_biz_stats_dir": r"X:\司机业务量",
    "custom_table_dir": r"X:\客户月结单",
    "invoice_output_dir": r"X:\月结单",
    "theme": "light",
    "window_width": 1200,
    "window_height": 800,
}


class SWTApp:
    def __init__(self, config_file: str = None):
        self._config_file = config_file or self._detect_config()
        self._config = {}
        self._pages = {}
        self._current_page = None
        self._db = None
        self._status_bar = StatusBar()
        self._sidebar = Sidebar()
        self._load_config()
        self._setup_sidebar_nav()

    def _detect_config(self) -> str:
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "swt_config.json"),
            "swt_config.json",
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)
        return "swt_config.json"

    def _load_config(self):
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in loaded:
                        loaded[k] = v
                self._config = loaded
            except Exception:
                self._config = dict(DEFAULT_CONFIG)
        else:
            self._config = dict(DEFAULT_CONFIG)
        ThemeManager.load_from_config(self._config_file)

    def save_config(self):
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.show_error(f"保存配置失败: {e}")

    @property
    def config(self) -> dict:
        return self._config

    @property
    def config_file(self) -> str:
        return self._config_file

    @property
    def db(self) -> DBCompat:
        if self._db is None:
            self._db = DBCompat(self._config)
        return self._db

    def reconnect_db(self):
        """用最新配置重建数据库连接"""
        if self._db is not None:
            self._db = None
        return self.db

    def register_page(self, name: str, page):
        self._pages[name] = page

    def set_status(self, msg: str):
        self._status_bar.set_message(msg)

    def show_error(self, msg: str):
        self._status_bar.set_message(f"错误: {msg}")
        self._status_bar.set_color("error")

    def navigate_to(self, page_name: str):
        if page_name == self._current_page:
            return
        if dpg.does_item_exist("page_content"):
            dpg.delete_item("page_content", children_only=True)
        self._current_page = page_name
        self._sidebar.set_current_page(page_name)
        if page_name in self._pages:
            self._pages[page_name].build()
        self.set_status("就绪")

    def _setup_sidebar_nav(self):
        self._sidebar.add_category("业务", [
            ("keyword_check", "关键词检测"),
            ("customer_mgmt", "客户管理"),
            ("driver_mgmt", "司机管理"),
            ("custom_table", "自定义表格"),
        ])
        self._sidebar.add_category("统计", [
            ("company_stats", "公司统计"),
            ("biz_stats", "业务统计"),
        ])
        self._sidebar.add_category("系统", [
            ("settings", "设置"),
        ])
        self._sidebar.on_select(lambda name: self.navigate_to(name))

    def _build_ui(self):
        with dpg.window(
            tag="main_window",
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_close=True,
            no_collapse=True,
        ):
            with dpg.group(horizontal=True):
                self._sidebar.build()
                with dpg.child_window(tag="content_area", width=-1, height=-1):
                    with dpg.child_window(tag="page_content", border=False):
                        pass
                    self._status_bar.build(parent="content_area")

    def _setup_font(self):
        import os as _os
        bundled = _os.path.join(_os.path.dirname(__file__), "simhei.ttf")
        font_paths = [bundled, r"C:\Windows\Fonts\simhei.ttf"]
        font_path = None
        for fp in font_paths:
            if _os.path.exists(fp):
                font_path = fp
                break
        if font_path is None:
            return
        with dpg.font_registry():
            with dpg.font(font_path, size=15) as font_tag:
                pass
        dpg.bind_font(font_tag)

    def run(self):
        dpg.create_context()
        self._setup_font()

        width = int(self._config.get("window_width", 1200))
        height = int(self._config.get("window_height", 800))
        dpg.create_viewport(title="SWT", width=width, height=height)

        self._build_ui()
        dpg.set_primary_window("main_window", True)

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # 通过 Win32 API 设置中文标题，避免 dearpygui 编码问题导致乱码
        self._set_window_title("SWT 货运管理系统")

        if self._pages:
            first_page = list(self._pages.keys())[0]
            try:
                self.navigate_to(first_page)
            except Exception as e:
                self.show_error(f"数据库连接失败: {e}")
                self.navigate_to("settings")

        dpg.start_dearpygui()
        dpg.destroy_context()

    @staticmethod
    def _set_window_title(title: str):
        """通过 Win32 SetWindowTextW 设置窗口标题，正确处理 Unicode"""
        import ctypes
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "SWT")
            if hwnd:
                ctypes.windll.user32.SetWindowTextW(hwnd, title)
        except Exception:
            pass

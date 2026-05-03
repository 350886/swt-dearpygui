# swt_dearpygui/pages/base_page.py
# -*- coding: utf-8 -*-
"""页面基类"""


class BasePage:
    """所有页面的基类，定义统一的页面接口"""
    name: str = "base"

    def __init__(self, app):
        self.app = app

    def build(self):
        """构建页面内容，由子类实现"""
        raise NotImplementedError

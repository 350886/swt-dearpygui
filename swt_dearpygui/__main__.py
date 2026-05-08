# swt_dearpygui/__main__.py
"""入口：python -m swt_dearpygui"""

from .app import SWTApp
from .pages import (
    KeywordCheckPage, SettingsPage, CustomerMgmtPage,
    DriverMgmtPage, CustomTablePage, CompanyStatsPage, BizStatsPage,
    DeleteDataPage, AddDriverPage,
)


def main():
    app = SWTApp()
    app.register_page("keyword_check", KeywordCheckPage(app))
    app.register_page("customer_mgmt", CustomerMgmtPage(app))
    app.register_page("driver_mgmt", DriverMgmtPage(app))
    app.register_page("custom_table", CustomTablePage(app))
    app.register_page("company_stats", CompanyStatsPage(app))
    app.register_page("biz_stats", BizStatsPage(app))
    app.register_page("delete_data", DeleteDataPage(app))
    app.register_page("add_driver", AddDriverPage(app))
    app.register_page("settings", SettingsPage(app))
    app.run()


if __name__ == "__main__":
    main()

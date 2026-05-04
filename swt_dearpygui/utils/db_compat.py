# swt_dearpygui/utils/db_compat.py
# -*- coding: utf-8 -*-
"""数据库连接池适配层"""

import pymysql
from dbutils.pooled_db import PooledDB
import threading


class DBCompat:
    def __init__(self, config: dict):
        self._config = {
            'host': config.get('db_host', '127.0.0.1'),
            'port': int(config.get('db_port', 3306)),
            'user': config.get('db_user', 'mysql'),
            'password': config.get('db_password', 'mysql'),
            'database': config.get('db_name', 'SWT'),
            'charset': 'utf8mb4',
        }
        self._pool = None
        self._lock = threading.Lock()

    def ensure_pool(self):
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    self._pool = PooledDB(
                        creator=pymysql,
                        maxconnections=10,
                        mincached=2,
                        maxcached=5,
                        blocking=True,
                        maxusage=None,
                        setsession=[],
                        ping=1,
                        **self._config,
                    )
        return self._pool

    def query(self, sql: str, params: tuple = None) -> list:
        pool = self.ensure_pool()
        with self._lock:
            conn = pool.connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def execute(self, sql: str, params: tuple = None) -> int:
        pool = self.ensure_pool()
        with self._lock:
            conn = pool.connection()
        cursor = conn.cursor()
        try:
            rows = cursor.execute(sql, params or ())
            conn.commit()
            return rows
        finally:
            cursor.close()
            conn.close()

    def execute_many(self, sql: str, params_list: list) -> int:
        pool = self.ensure_pool()
        with self._lock:
            conn = pool.connection()
        cursor = conn.cursor()
        try:
            rows = cursor.executemany(sql, params_list)
            conn.commit()
            return rows
        finally:
            cursor.close()
            conn.close()

# database.py
"""数据库管理模块"""

import sqlite3
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_name='crypto_bot.db'):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_name='crypto_bot.db'):
        if not hasattr(self, 'initialized'):
            self.db_name = db_name
            self.conn = None
            self.init_database()
            self.initialized = True

    def get_connection(self):
        """获取数据库连接"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        return self.conn

    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                join_date TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                risk_level TEXT DEFAULT 'medium'
            )
        ''')

        # 创建价格提醒表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                target_price REAL,
                condition TEXT,
                created_at TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # 创建投资组合表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol TEXT,
                quantity REAL,
                avg_price REAL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, symbol)
            )
        ''')

        # 创建交易信号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                price REAL,
                created_at TEXT
            )
        ''')

        conn.commit()
        logger.info("Database initialized successfully")

    # 用户相关方法
    def save_user(self, user_id, username, first_name):
        """保存或更新用户"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, join_date) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat()))
        self.conn.commit()

    def get_user(self, user_id):
        """获取用户信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    # 价格提醒相关方法
    def add_alert(self, user_id, symbol, target_price, condition):
        """添加价格提醒"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO price_alerts 
            (user_id, symbol, target_price, condition, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, symbol, target_price, condition, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_alerts(self, user_id, active_only=True):
        """获取用户的价格提醒"""
        cursor = self.conn.cursor()
        query = '''
            SELECT id, symbol, target_price, condition, created_at 
            FROM price_alerts 
            WHERE user_id = ?
        '''
        if active_only:
            query += ' AND is_active = TRUE'
        query += ' ORDER BY created_at DESC'

        cursor.execute(query, (user_id,))
        return cursor.fetchall()

    def get_all_active_alerts(self):
        """获取所有活跃的价格提醒"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, user_id, symbol, target_price, condition 
            FROM price_alerts 
            WHERE is_active = TRUE
        ''')
        return cursor.fetchall()

    def deactivate_alert(self, alert_id):
        """停用价格提醒"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE price_alerts 
            SET is_active = FALSE 
            WHERE id = ?
        ''', (alert_id,))
        self.conn.commit()

    # 投资组合相关方法
    def get_portfolio(self, user_id):
        """获取用户投资组合"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT symbol, quantity, avg_price, updated_at 
            FROM portfolios 
            WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchall()

    def add_or_update_portfolio_item(self, user_id, symbol, quantity, avg_price):
        """添加或更新投资组合项目"""
        cursor = self.conn.cursor()

        # 检查是否已存在
        cursor.execute('SELECT quantity, avg_price FROM portfolios WHERE user_id = ? AND symbol = ?',
                       (user_id, symbol))
        existing = cursor.fetchone()

        if existing:
            # 更新现有记录（计算新的平均成本价）
            old_quantity, old_avg_price = existing
            new_quantity = old_quantity + quantity
            new_avg_price = ((old_quantity * old_avg_price) + (quantity * avg_price)) / new_quantity

            cursor.execute('''
                UPDATE portfolios 
                SET quantity = ?, avg_price = ?, updated_at = ?
                WHERE user_id = ? AND symbol = ?
            ''', (new_quantity, new_avg_price, datetime.now().isoformat(), user_id, symbol))
        else:
            # 新增记录
            cursor.execute('''
                INSERT INTO portfolios (user_id, symbol, quantity, avg_price, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, quantity, avg_price, datetime.now().isoformat()))

        self.conn.commit()

    def remove_portfolio_item(self, user_id, symbol):
        """删除投资组合项目"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM portfolios WHERE user_id = ? AND symbol = ?', (user_id, symbol))
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
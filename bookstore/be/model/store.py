import logging
import os
import sqlite3 as sqlite
import threading




    


class Store:
    database: str

    def __init__(self, db_path):
        self.database = os.path.join(db_path, "be.db")
        self.init_tables()

    def init_tables(self):
        try:
            conn = self.get_db_conn()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
                "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS user_store("
                "user_id TEXT, store_id, PRIMARY KEY(user_id, store_id));"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS store( "
                "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
                " PRIMARY KEY(store_id, book_id))"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT)"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order_detail( "
                "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
                "PRIMARY KEY(order_id, book_id))"
            )

            conn.commit()
        except sqlite.Error as e:
            logging.error(e)
            conn.rollback()

    def get_db_conn(self) -> sqlite.Connection:
        return sqlite.connect(self.database)


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()

import pymysql
from pymysql.cursors import DictCursor

# 定义数据库配置（从mysql_config提取）
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '021201hyj',
    'database': 'bookstore',
    'cursorclass': DictCursor  # 返回字典格式结果
}

def get_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**db_config)
        print("成功连接到MySQL数据库")
        return conn
    except pymysql.Error as e:
        print(f"数据库连接失败: {e}")
        raise

# 创建全局连接对象（实际使用时建议在函数内创建）
db = get_connection()

def init_database(app):
    # 延迟获取配置（确保app.config已设置）
    config = app.config
    
    # 使用get()避免KeyError
    host = config.get('MYSQL_HOST', 'localhost')
    user = config.get('MYSQL_USER', 'root')
    password = config.get('MYSQL_PASSWORD', '')
    database = config.get('MYSQL_DB', 'bookstore')


    
 
def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()

import logging
import os
from pymongo import MongoClient
import threading


class Store:
    database: str

    def __init__(self, db_path = "mongodb://localhost:27017/"):
        db_path = "mongodb://localhost:27017/"
        self.database = db_path
        self.init_tables()

    def init_tables(self):
        try:
            db = self.get_db_conn()  # 返回 MongoClient(self.database)["bookstore"]
            #----------- users 集合 ---------
            users_col = db["users"]
            users_col.create_index("user_id", unique=True)
            # ---------- stores 集合 ----------
            stores_col = db["stores"]
            # store_id 唯一索引
            stores_col.create_index("store_id", unique=True)
            # ---------- books 集合 -----------
            books_col = db["books"]
            # book_id 不设置 unique，因为同一本书可以在多个店铺销售
            books_col.create_index("book_id")
            # ---------- store_books 集合 ----------
            store_books_col = db["store_books"]
            # store_id + book_id 唯一索引，保证每个店铺的每类书唯一
            store_books_col.create_index([("store_id", 1), ("book_id", 1)], unique=True)
            store_books_col.create_index([
                ("title", "text"),
                ("book_intro", "text"),
                ("content", "text"),
                ("tags", "text")
            ])
            # ---------- orders 集合 ----------
            orders_col = db["orders"]
            # order_id 唯一索引
            orders_col.create_index("order_id", unique=True)
            # 用户和店铺查询索引
            orders_col.create_index("user_id")
            orders_col.create_index("store_id")
            # 状态查询索引
            orders_col.create_index("status")
            # 下单时间索引
            orders_col.create_index("created_at")
            # 超时订单查询优化：复合索引 (status, timeout_at)
            # 用于check_timeout_orders查询status="pending"且timeout_at<current_time的订单
            orders_col.create_index([("status", 1), ("timeout_at", 1)])

            # ---------- archived_orders 集合 ----------
            archived_orders_col = db["archived_orders"]
            archived_orders_col.create_index("order_id", unique=True)
            archived_orders_col.create_index("user_id")
            archived_orders_col.create_index("store_id")
            archived_orders_col.create_index("status")
            #archived_orders_col.create_index("created_at")
            #archived_orders_col.create_index("closed_at")

            logging.info("MongoDB collections and indexes initialized successfully.")

        except Exception as e:
            logging.error(f"Failed to initialize MongoDB collections: {e}")
    def get_db_conn(self) : ##返回连接的数据库
        return MongoClient(self.database)["bookstore"]


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()
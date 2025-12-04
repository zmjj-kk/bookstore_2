#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite到MongoDB数据迁移脚本
"""
import sqlite3
import sys
import os
import json
import base64
import pymongo
from datetime import datetime


def migrate_books():
    """迁移图书数据"""
    print("开始迁移图书数据...")

    # 连接SQLite数据库
    sqlite_conn = sqlite3.connect('book_lx.db')
    sqlite_cursor = sqlite_conn.cursor()

    # 连接MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["bookstore"]
    books_collection = db["books"]
    collections = ["books", "store_books", "stores", "users"]

    for name in collections:
        if name in db.list_collection_names():  # 判断集合是否存在
            db[name].delete_many({})  # 清空所有文档
            print(f"✅ 已清空集合 {name} 的所有数据（保留集合结构）")
        else:
            print(f"⚠️ 集合 {name} 不存在，跳过。")

    # 获取所有图书数据
    sqlite_cursor.execute("SELECT * FROM book")
    books = sqlite_cursor.fetchall()

    print(f"找到 {len(books)} 本图书需要迁移")

    # 批量插入MongoDB
    mongo_books = []
    for book in books:
        # 处理tags字段（从TEXT转换为数组）
        tags = []
        if book[15]:  # tags字段
            try:
                tags = json.loads(book[15]) if book[15].startswith('[') else [book[15]]
            except:
                tags = [book[15]] if book[15] else []

        # 处理图片字段（从BLOB转换为base64字符串数组）
        pictures = []
        if book[16]:  # picture字段
            try:
                # 将BLOB数据转换为base64
                picture_base64 = base64.b64encode(book[16]).decode('utf-8')
                pictures = [picture_base64]
            except:
                pictures = []

        mongo_book = {
            "book_id": str(book[0]),  # id
            "title": book[1] or "",
            "author": book[2] or "",
            "publisher": book[3] or "",
            "original_title": book[4] or "",
            "translator": book[5] or "",
            "pub_year": book[6] or "",
            "pages": book[7] or 0,
            "price": book[8] or 0,
            "currency_unit": book[9] or "",
            "binding": book[10] or "",
            "isbn": book[11] or "",
            "author_intro": book[12] or "",
            "book_intro": book[13] or "",
            "content": book[14] or "",
            "tags": tags,
            "pictures": pictures
        }
        mongo_books.append(mongo_book)

    # 批量插入到MongoDB
    if mongo_books:
        try:
            books_collection.insert_many(mongo_books)
            print(f"成功迁移 {len(mongo_books)} 本图书到MongoDB")
        except Exception as e:
            print(f"迁移图书数据时出错: {e}")

    sqlite_conn.close()
    client.close()


def create_sample_data():
    """创建示例数据（用户、店铺、库存等）"""
    print("创建示例数据...")

    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["bookstore"]

    # 创建示例用户
    sample_users = [
        {
            "user_id": "test_buyer_1",
            "password": "test_buyer_1",
            "balance": 100000,  # 1000元
            "token": "",
        },
        {
            "user_id": "test_seller_1",
            "password": "test_seller_1",
            "balance": 0,
            "token": "",
        }
    ]

    try:
        db.users.insert_many(sample_users)
        print("创建示例用户成功")
    except Exception as e:
        print(f"创建用户时出错: {e}")

    # 创建示例店铺
    sample_stores = [
        {
            "store_id": "test_store_1",
            "user_id": "test_seller_1"
        }
    ]

    try:
        db.stores.insert_many(sample_stores)
        print("创建示例店铺成功")
    except Exception as e:
        print(f"创建店铺时出错: {e}")

    # 创建示例库存（选择前10本书）
    try:
        books = list(db.books.find().limit(10))
        store_books = []

        for book in books:
            store_book = {
                "store_id": "test_store_1",
                "book_id": book["book_id"],
                "stock_level": 100,  # 每本书库存100本
                "title": book["title"],
                "book_intro": book["book_intro"],
                "content": book["content"],
                "tags": book["tags"],
                "price": book["price"]  # 添加价格字段
            }
            store_books.append(store_book)

        if store_books:
            db.store_books.insert_many(store_books)
            print(f"创建示例库存成功，共 {len(store_books)} 本书")
    except Exception as e:
        print(f"创建库存时出错: {e}")

    client.close()


def main():
    """主函数"""
    print("开始数据迁移...")

    # 迁移图书数据
    migrate_books()

    # 创建示例数据
    # create_sample_data()

    print("数据迁移完成！")


if __name__ == "__main__":
    main()

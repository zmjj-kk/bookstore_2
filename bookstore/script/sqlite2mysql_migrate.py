#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import mysql.connector
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------
# 配置 MySQL
# ----------------------
mysql_config = {
    'user': 'root',
    'password': 'prc13055590995',
    'unix_socket': '/var/run/mysqld/mysqld.sock',
    'database': 'bookstore'
}

# ----------------------
# 配置 SQLite
# ----------------------
sqlite_file = "../fe/data/book_lx_part.db"
sqlite_table = "book"
mysql_table  = "books"

# ----------------------
# 字段最大长度（超长自动截断）
# ----------------------
MAX_LENGTHS = {
    11: 50,    # currency_unit
    15: 2000   # tags
}

def migrate():
    # 连接 SQLite
    logging.info(f"正在读取 SQLite 数据库：{sqlite_file}")
    sqlite_conn = sqlite3.connect(sqlite_file)
    sqlite_cursor = sqlite_conn.cursor()

    sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{sqlite_table}'")
    if not sqlite_cursor.fetchone():
        logging.error(f"SQLite 数据库中不存在表 {sqlite_table}")
        return

    sqlite_cursor.execute(f"SELECT * FROM {sqlite_table}")
    rows = sqlite_cursor.fetchall()
    logging.info(f"共读取 {len(rows)} 条记录，开始写入 MySQL...")

    if not rows:
        logging.info("没有数据可迁移。")
        return

    # 连接 MySQL
    mysql_conn = mysql.connector.connect(**mysql_config)
    mysql_cursor = mysql_conn.cursor()

    num_fields = len(rows[0])
    placeholders = ", ".join(["%s"] * num_fields)
    # 使用 INSERT IGNORE 保证遇到重复记录不会报错
    insert_sql = f"INSERT IGNORE INTO {mysql_table} VALUES ({placeholders})"

    batch_size = 500
    batch = []

    for row_idx, row in enumerate(rows):
        row = list(row)
        for idx, max_len in MAX_LENGTHS.items():
            if idx < len(row) and row[idx] is not None:
                if len(str(row[idx])) > max_len:
                    logging.warning(
                        f"字段索引 {idx} 值过长，截断：原长度={len(str(row[idx]))}, 最大={max_len}"
                    )
                    row[idx] = str(row[idx])[:max_len]
        batch.append(row)

        if len(batch) >= batch_size:
            mysql_cursor.executemany(insert_sql, batch)
            mysql_conn.commit()
            batch = []

    if batch:
        mysql_cursor.executemany(insert_sql, batch)
        mysql_conn.commit()

    logging.info("迁移完成！")

    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()


if __name__ == "__main__":
    migrate()

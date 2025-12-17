# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 09:18:24 2025

@author: LL
"""

import sqlite3

# 创建或连接数据库文件（如果不存在会自动创建）
conn = sqlite3.connect('bookstore.db')  # 文件会生成在当前目录
print("数据库文件 bookstore.db 已创建/连接成功")

# 关闭连接（实际项目中建议用with语句自动管理）
conn.close()
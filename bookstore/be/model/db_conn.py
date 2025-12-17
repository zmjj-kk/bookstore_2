
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




from bookstore.be.model import store


class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    def user_id_exist(self, user_id):
        cursor = self.conn.execute(
            "SELECT user_id FROM user WHERE user_id = ?;", (user_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        cursor = self.conn.execute(
            "SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;",
            (store_id, book_id),
        )
        row = cursor.fetchone()
        if row is None:
            return False
        else:
            return True

    def store_id_exist(self, store_id):
        cursor = self.conn.execute(
            "SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return False
        else:
            return True


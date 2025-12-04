from pymongo import MongoClient
from be.model import error
from be.model import db_conn
import json


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        s = json.loads(book_json_str)
        result = self.conn["books"].find_one({"book_id": book_id})

        if result is None:
            self.conn["books"].insert_one({
                "book_id": book_id,
                "title": s["title"],
                "author": s["author"],
                "publisher": s["publisher"],
                "original_title": s["original_title"],
                "translator": s["translator"],
                "pub_year": s["pub_year"],
                "pages": s.get("pages", 0),
                "price": s.get("price", 0),
                "currency_unit": s.get("currency_unit", ""),
                "binding": s.get("binding",""),
                "isbn": s.get("isbn"),
                "author_intro": s.get("author_intro"),
                "book_intro": s.get("book_intro"),
                "content": s.get("content", ""),  # 添加 content 字段（目录）
                "tags": s.get("tags",[]),
                "pictures": s.get("pictures",[])
            })
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id)
        if not self.store_id_exist(store_id):
            return error.error_non_exist_store_id(store_id)
        if self.book_id_exist(store_id, book_id):
            return error.error_exist_book_id(book_id)
        title = s["title"]
        book_intro = s["book_intro"]
        content = s["content"]
        tags = s["tags"]
        price = s["price"]
        self.conn["store_books"].insert_one({
            "store_id": store_id,
            "book_id": book_id,
            "stock_level": stock_level,
            "title": title,
            "book_intro": book_intro,
            "content": content,
            "tags": tags,
            "price": price
        })
        return 200, "ok"

    def add_stock_level(
        self,
        user_id: str,
        store_id: str,  # 店铺ID
        book_id: str,  # 图书ID（每个文档代表一个店铺中的一类书）
        add_stock_level: int
    ):
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id)
        if not self.store_id_exist(store_id):
            return error.error_non_exist_store_id(store_id)
        if not self.book_id_exist(store_id, book_id):
            return error.error_non_exist_book_id(book_id)
        result = self.conn["store_books"].update_one(
            {"store_id": store_id, "book_id": book_id},  # 匹配条件
            {"$inc": {"stock_level": add_stock_level}}  # 增量更新操作
        )
        if result.matched_count == 0:
            return 529, f"未找到 store_id={store_id}, book_id={book_id} 的文档"
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id)
        if self.store_id_exist(store_id):
            return error.error_exist_store_id(store_id)
        self.conn["stores"].insert_one({
            "store_id": store_id,
            "user_id": user_id,

        })
        return 200, "ok"

    def ship_order(self, user_id: str, order_id: str) -> (int, str):
        """
        卖家发货功能
        只有 status='paid' 的订单才能发货
        """
        order = self.conn["orders"].find_one({"order_id": order_id})
        if not order:
            return error.error_invalid_order_id(order_id)            
        if order.get("status") != "paid":
            return 518, f"Order status is {order.get('status')}, cannot ship"
        
        store = self.conn["stores"].find_one({"store_id": order.get("store_id")})
        if not store:
            return error.error_non_exist_store_id(order.get("store_id"))
        
        if store.get("user_id") != user_id:
            return error.error_authorization_fail()
        
        result = self.conn["orders"].update_one(
            {"order_id": order_id},
            {"$set": {"status": "shipped"}}
        )
        
        if result.modified_count == 0:
            return 530, "Failed to update order status"
        
        return 200, "ok"

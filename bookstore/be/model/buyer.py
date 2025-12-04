import datetime
import uuid
import json
import logging
from pyexpat.errors import messages

from be.model import db_conn
from be.model import error
from pymongo.errors import PyMongoError


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(
        self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id) + (order_id,)
        if not self.store_id_exist(store_id):
            return error.error_non_exist_store_id(store_id) + (order_id,)
        uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
        order_id = uid
        for book_id, count in id_and_count:

            doc = self.conn["store_books"].find_one({"store_id": store_id, "book_id": book_id})

            if doc is None:
                return error.error_non_exist_book_id(book_id) + (order_id,)

            stock_level = doc.get("stock_level")
            book_intro = doc.get("book_intro")
            price = doc.get("price")

            if stock_level < count:
                return error.error_stock_level_low(book_id) + (order_id,)

            result = self.conn["store_books"].update_one(
                {
                    "store_id": store_id,
                    "book_id": book_id,
                },
                {
                    "$inc": {"stock_level": -count}  # 扣减库存
                }
            )
            new_item = {
                            "book_id": book_id,
                            "count": count,
                            "price": price
                        }
            if self.conn["orders"].find_one({"order_id": order_id}) is None:
                self.conn["orders"].insert_one({
                    "order_id": order_id,
                    "user_id": user_id,
                    "store_id": store_id,
                    "status": "pending",  # 新订单状态为待付款
                    "created_at": datetime.datetime.utcnow(),
                    "timeout_at": datetime.datetime.utcnow() + datetime.timedelta(days=2),
                    "items": [new_item]
                })
            else:
                self.conn["orders"].update_one({"order_id": order_id}, {"$push": {"items": new_item}} )

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        order = self.conn["orders"].find_one({"order_id": order_id})
        if order is None:
            return error.error_invalid_order_id(order_id)

        # 检查订单状态，防止重复支付
        if order.get("status") != "pending":
            return error.error_invalid_order_id(order_id)

        if order.get("user_id") != user_id:
            return error.error_authorization_fail()

        buyer = self.conn["users"].find_one({"user_id": user_id})
        if buyer is None:
            return error.error_non_exist_user_id(user_id)
        if buyer.get("password") != password:
            return error.error_authorization_fail()

        total_price = sum(item["count"] * item["price"] for item in order.get("items", []))

        if buyer.get("balance", 0) < total_price:
            return error.error_not_sufficient_funds(order_id)

        store = self.conn["stores"].find_one({"store_id": order.get("store_id")})
        if store is None:
            return error.error_non_exist_store_id(order.get("store_id"))
        seller_id = store.get("user_id")

        # 扣买家余额
        result = self.conn["users"].update_one(
            {"user_id": user_id, "balance": {"$gte": total_price}},
            {"$inc": {"balance": -total_price}}
        )
        if result.modified_count == 0:
            return error.error_not_sufficient_funds(order_id)

        # 加卖家余额
        result = self.conn["users"].update_one(
            {"user_id": seller_id},
            {"$inc": {"balance": total_price}}
        )
        if result.matched_count == 0:
            return error.error_non_exist_user_id(seller_id)

        # 更新订单状态为已支付
        self.conn["orders"].update_one(
            {"order_id": order_id},
            {"$set": {"status": "paid"}}
        )
        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        user = self.conn["users"].find_one({"user_id": user_id})
        if user is None:
            return error.error_non_exist_user_id(user_id)

        if user.get("password") != password:
            return error.error_authorization_fail()

        result = self.conn["users"].update_one(
            {"user_id": user_id},
            {"$inc": {"balance": add_value}}
        )
        if result.matched_count == 0:
            return error.error_non_exist_user_id(user_id)

        return 200, "ok"

    def receive_order(self, user_id: str, order_id: str) -> (int, str):
        """
        买家确认收货功能
        只有 status='shipped' 的订单才能确认收货
        收货后订单归档到 archived_orders
        """
        order = self.conn["orders"].find_one({"order_id": order_id})
        if not order:
            return error.error_invalid_order_id(order_id)
        
        if order.get("user_id") != user_id:
            return error.error_authorization_fail()
        
        if order.get("status") != "shipped":
            return 518, f"Order status is {order.get('status')}, cannot receive"
        
        archived_data = {
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "store_id": order["store_id"],
            "status": "delivered",
            "created_at": order["created_at"],
            "closed_at": datetime.datetime.utcnow(),
            "items": order["items"]
        }
        self.conn["archived_orders"].insert_one(archived_data)
        self.conn["orders"].delete_one({"order_id": order_id})
        
        return 200, "ok"

    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        """
        买家取消订单功能
        只有 status='pending' 的订单才能取消（未支付的订单）
        取消后库存返还，订单归档
        """
        order = self.conn["orders"].find_one({"order_id": order_id})
        if not order:
            return error.error_invalid_order_id(order_id)
        
        
        if order.get("user_id") != user_id:
            return error.error_authorization_fail()
        
        if order.get("status") != "pending":
            return 518, f"Order status is {order.get('status')}, cannot cancel"
        
        for item in order.get("items", []):
            self.conn["store_books"].update_one(
                {"store_id": order["store_id"], "book_id": item["book_id"]},
                {"$inc": {"stock_level": item["count"]}}
            )
        
        archived_data = {
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "store_id": order["store_id"],
            "status": "cancelled",
            "created_at": order["created_at"],
            "closed_at": datetime.datetime.utcnow(),
            "items": order["items"]
        }
        self.conn["archived_orders"].insert_one(archived_data)
        
        self.conn["orders"].delete_one({"order_id": order_id})
        
        return 200, "ok"

    def query_orders(self, user_id: str) -> (int, str, list):
        """
        查询用户的所有订单（包括活跃订单和历史订单）
        返回格式: (code, message, orders_list)
        """
        active_orders = list(self.conn["orders"].find(
            {"user_id": user_id},
            {"_id": 0} 
        ))
        
        archived_orders = list(self.conn["archived_orders"].find(
            {"user_id": user_id},
            {"_id": 0}
        ))
    
        all_orders = []
        for order in active_orders + archived_orders:
            if "created_at" in order and order["created_at"]:
                order["created_at"] = order["created_at"].isoformat()
            if "timeout_at" in order and order["timeout_at"]:
                order["timeout_at"] = order["timeout_at"].isoformat()
            if "closed_at" in order and order["closed_at"]:
                order["closed_at"] = order["closed_at"].isoformat()
            all_orders.append(order)
        
        return 200, "ok", all_orders

    def check_timeout_orders(self) -> (int, str):
        """
        检查并处理超时订单
        将所有超时未支付的订单取消，返还库存，归档
        """
        current_time = datetime.datetime.utcnow()
        
        timeout_orders = self.conn["orders"].find({
            "status": "pending",
            "timeout_at": {"$lt": current_time}
        })
        
        cancelled_count = 0
        for order in timeout_orders:
            for item in order.get("items", []):
                self.conn["store_books"].update_one(
                    {"store_id": order["store_id"], "book_id": item["book_id"]},
                    {"$inc": {"stock_level": item["count"]}}
                )
            
            archived_data = {
                "order_id": order["order_id"],
                "user_id": order["user_id"],
                "store_id": order["store_id"],
                "status": "cancelled",
                "created_at": order["created_at"],
                "closed_at": current_time,
                "items": order["items"]
            }
            self.conn["archived_orders"].insert_one(archived_data)
            
            self.conn["orders"].delete_one({"order_id": order["order_id"]})
            
            cancelled_count += 1
        
        return 200, f"Cancelled {cancelled_count} timeout orders"

    def search(self, keyword: str, field: str, store_id: str = None,
               page: int = 1, page_size: int = 10) -> (int, str, dict):
        try:
            if page <= 0:
                code,message = error.error_invalid_page(page)
                return code,message,{}
            if page_size <= 0:
                code,message = error.error_invalid_page_size(page_size)
                return code,message,{}
            skip_count = (page - 1) * page_size
            query = {}

            if store_id:
                row = self.conn["stores"].find_one({"store_id": store_id})
                if row is not None:
                    query["store_id"] = store_id
                else:
                    code,message = error.error_non_exist_store_id(store_id)
                    return code, message, {}

            if field == "all":
                query["$text"] = {"$search": keyword}
                projection = {"score": {"$meta": "textScore"}}
                cursor = self.conn["store_books"].find(query, projection).sort(
                    [("score", {"$meta": "textScore"})]
                )
            else:
                if field in ["title", "content", "book_intro"]:
                    query[field] = {"$regex": keyword, "$options": "i"}
                elif field == "tags":
                    query[field] = {"$elemMatch": {"$regex": keyword, "$options": "i"}}
                else:
                    code ,message = error.error_invalid_field(field)
                    return code,message, {}
                cursor = self.conn["store_books"].find(query)

            results = list(cursor.skip(skip_count).limit(page_size))
            total_count = self.conn["store_books"].count_documents(query)
            total_pages = (total_count + page_size - 1) // page_size

            if total_count == 0:
                code,message = error.error_not_found_results()
                return code,message,{}

            if total_pages < page:
                code,message = error.error_over_page(page,total_pages)
                return code,message,{}

            for result in results:
                if '_id' in result:
                    del result['_id']

            return 200, "Find the books in stores", {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_count": total_count,
                "results": results
            }
        except Exception as e:
            return 530, f"Internal error: {str(e)}", {}

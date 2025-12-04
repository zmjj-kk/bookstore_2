import pytest
import datetime
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB
from fe import conf
import uuid
from be.model.buyer import Buyer


class TestTimeoutOrders:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_timeout_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家
        self.seller_id = "test_timeout_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_timeout_store_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 添加图书
        book_db = BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 3)
        for book in self.books:
            assert self.seller.add_book(self.store_id, 10, book) == 200
        # 买家充值
        assert self.buyer.add_funds(1000000) == 200
        
        yield

    def test_check_timeout_orders_no_timeout(self):
        """测试没有超时订单时"""
        # 创建订单并立即支付（不会超时）
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
        # 检查超时订单
        buyer_model = Buyer()
        code, message = buyer_model.check_timeout_orders()
        assert code == 200
        assert "Cancelled 0 timeout orders" in message

    def test_check_timeout_orders_has_timeout(self):
        """测试有超时订单的情况"""
        from be.model import db_conn
        db = db_conn.DBConn()
        # 创建订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        # 手动设置订单超时时间为过去的时间
        past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.conn["orders"].update_one(
            {"order_id": order_id},
            {"$set": {"timeout_at": past_time}}
        ) 
        # 检查超时订单
        buyer_model = Buyer()
        code, message = buyer_model.check_timeout_orders()
        assert code == 200
        assert "Cancelled 1 timeout orders" in message
        # 验证订单已被取消
        cancelled_order = db.conn["archived_orders"].find_one({"order_id": order_id})
        assert cancelled_order is not None
        assert cancelled_order["status"] == "cancelled"
        # 验证订单不在活跃订单中
        active_order = db.conn["orders"].find_one({"order_id": order_id})
        assert active_order is None

    def test_timeout_order_stock_return(self):
        """测试超时订单的库存返还"""
        from be.model import db_conn
        db = db_conn.DBConn()
        # 记录初始库存
        initial_stock = db.conn["store_books"].find_one({
            "store_id": self.store_id,
            "book_id": self.books[0].id
        })["stock_level"]
        # 创建订单
        book_id_and_count = [(self.books[0].id, 2)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        # 验证库存已扣除
        after_order_stock = db.conn["store_books"].find_one({
            "store_id": self.store_id,
            "book_id": self.books[0].id
        })["stock_level"]
        assert after_order_stock == initial_stock - 2
        # 手动设置订单超时
        past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.conn["orders"].update_one(
            {"order_id": order_id},
            {"$set": {"timeout_at": past_time}}
        )
        # 检查超时订单
        buyer_model = Buyer()
        buyer_model.check_timeout_orders()
        # 验证库存已返还
        final_stock = db.conn["store_books"].find_one({
            "store_id": self.store_id,
            "book_id": self.books[0].id
        })["stock_level"]
        assert final_stock == initial_stock

    def test_timeout_multiple_orders(self):
        """测试多个超时订单的情况"""
        from be.model import db_conn
        db = db_conn.DBConn()
        # 创建多个订单
        order_ids = []
        for i in range(3):
            book_id_and_count = [(self.books[i].id, 1)]
            code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
            assert code == 200
            order_ids.append(order_id)
        # 设置所有订单为超时
        past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        for order_id in order_ids:
            db.conn["orders"].update_one(
                {"order_id": order_id},
                {"$set": {"timeout_at": past_time}}
            )
        # 检查超时订单
        buyer_model = Buyer()
        code, message = buyer_model.check_timeout_orders()
        assert code == 200
        assert "Cancelled 3 timeout orders" in message
        # 验证所有订单都已归档
        for order_id in order_ids:
            archived_order = db.conn["archived_orders"].find_one({"order_id": order_id})
            assert archived_order is not None
            assert archived_order["status"] == "cancelled"
            
            active_order = db.conn["orders"].find_one({"order_id": order_id})
            assert active_order is None

    def test_timeout_order_with_paid_order(self):
        """测试有已支付订单和超时订单混合的情况"""
        from be.model import db_conn
        db = db_conn.DBConn()
        # 创建第一个订单并支付
        book_id_and_count1 = [(self.books[0].id, 1)]
        code, order_id1 = self.buyer.new_order(self.store_id, book_id_and_count1)
        assert code == 200
        assert self.buyer.payment(order_id1) == 200
        # 创建第二个订单但不支付，设置超时
        book_id_and_count2 = [(self.books[1].id, 1)]
        code, order_id2 = self.buyer.new_order(self.store_id, book_id_and_count2)
        assert code == 200
        past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.conn["orders"].update_one(
            {"order_id": order_id2},
            {"$set": {"timeout_at": past_time}}
        )
        # 检查超时订单
        buyer_model = Buyer()
        code, message = buyer_model.check_timeout_orders()
        assert code == 200
        assert "Cancelled 1 timeout orders" in message
        # 验证只有未支付的超时订单被取消
        archived_order2 = db.conn["archived_orders"].find_one({"order_id": order_id2})
        assert archived_order2 is not None
        assert archived_order2["status"] == "cancelled"
        # 已支付的订单不应该被取消
        active_order1 = db.conn["orders"].find_one({"order_id": order_id1})
        assert active_order1 is not None
        assert active_order1["status"] == "paid"

    def test_timeout_order_closed_at_set(self):
        """测试超时订单的 closed_at 字段设置"""
        from be.model import db_conn
        db = db_conn.DBConn()
        # 创建订单并设置超时
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        
        past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.conn["orders"].update_one(
            {"order_id": order_id},
            {"$set": {"timeout_at": past_time}}
        )
        # 检查超时订单
        buyer_model = Buyer()
        before_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)  # 放宽1秒
        buyer_model.check_timeout_orders()
        after_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)   # 放宽1秒
        # 验证 archived_orders 中的 closed_at 字段
        archived_order = db.conn["archived_orders"].find_one({"order_id": order_id})
        assert archived_order is not None
        assert "closed_at" in archived_order
        # 验证 closed_at 在合理的时间范围内
        assert archived_order["closed_at"] >= before_time
        assert archived_order["closed_at"] <= after_time

    def test_timeout_orders_not_affect_normal_flow(self):
        """测试超时订单处理不影响正常流程"""
        # 创建正常订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        # 支付订单
        assert self.buyer.payment(order_id) == 200
        # 发货
        assert self.seller.ship_order(order_id) == 200
        # 检查超时订单（不应该影响已支付和已发货的订单）
        buyer_model = Buyer()
        code, message = buyer_model.check_timeout_orders()
        assert code == 200
        # 验证订单仍在活跃订单中
        from be.model import db_conn
        db = db_conn.DBConn()
        active_order = db.conn["orders"].find_one({"order_id": order_id})
        assert active_order is not None
        assert active_order["status"] == "shipped"


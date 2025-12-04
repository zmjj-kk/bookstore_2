import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import Book, BookDB
from fe import conf
import uuid


class TestQueryOrders:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_query_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家
        self.seller_id = "test_query_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_query_store_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 添加图书
        book_db = BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 3)
        for book in self.books:
            assert self.seller.add_book(self.store_id, 10, book) == 200
        # 买家充值
        assert self.buyer.add_funds(10000000) == 200
        
        yield

    def test_query_no_orders(self):
        """测试查询无订单用户"""
        # 创建一个新买家，没有任何订单
        new_buyer = register_new_buyer("buyer_no_orders_" + str(uuid.uuid1()), "password")
        code, orders = new_buyer.query_orders()
        assert code == 200
        assert len(orders) == 0

    def test_query_pending_orders(self):
        """测试查询待支付订单"""
        # 创建一个待支付订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        assert len(orders) >= 1
        
        found = False
        for order in orders:
            if order["order_id"] == order_id:
                assert order["status"] == "pending"
                assert order["user_id"] == self.buyer_id
                found = True
                break
        assert found

    def test_query_paid_orders(self):
        """测试查询已支付订单"""
        # 创建并支付订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        
        found = False
        for order in orders:
            if order["order_id"] == order_id:
                assert order["status"] == "paid"
                found = True
                break
        assert found

    def test_query_shipped_orders(self):
        """测试查询已发货订单"""
        # 创建、支付并发货
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
        assert self.seller.ship_order(order_id) == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        
        found = False
        for order in orders:
            if order["order_id"] == order_id:
                assert order["status"] == "shipped"
                found = True
                break
        assert found

    def test_query_delivered_orders(self):
        """测试查询已送达订单（历史订单）"""
        # 完整流程：创建、支付、发货、收货
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
        assert self.seller.ship_order(order_id) == 200
        assert self.buyer.receive_order(order_id) == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        
        found = False
        for order in orders:
            if order["order_id"] == order_id:
                assert order["status"] == "delivered"
                assert "closed_at" in order
                found = True
                break
        assert found

    def test_query_cancelled_orders(self):
        """测试查询已取消订单（历史订单）"""
        # 创建并取消订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.cancel_order(order_id) == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        
        found = False
        for order in orders:
            if order["order_id"] == order_id:
                assert order["status"] == "cancelled"
                assert "closed_at" in order
                found = True
                break
        assert found

    def test_query_multiple_orders(self):
        """测试查询多个订单"""
        order_ids = []
        
        # 创建多个订单
        for i in range(3):
            book_id_and_count = [(self.books[i].id, 1)]
            code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
            assert code == 200
            order_ids.append(order_id)
        
        # 支付第一个订单
        assert self.buyer.payment(order_ids[0]) == 200
        
        code, orders = self.buyer.query_orders()
        assert code == 200
        assert len(orders) >= 3
        
        found_count = 0
        for order_id in order_ids:
            for order in orders:
                if order["order_id"] == order_id:
                    found_count += 1
                    break
        assert found_count == 3

    def test_query_orders_with_details(self):
        """测试订单详情是否完整"""
        # 创建订单
        book_id_and_count = [(self.books[0].id, 2), (self.books[1].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        # 查询订单
        code, orders = self.buyer.query_orders()
        assert code == 200
        # 验证订单详情
        for order in orders:
            if order["order_id"] == order_id:
                assert "user_id" in order
                assert "store_id" in order
                assert "status" in order
                assert "created_at" in order
                assert "items" in order
                assert len(order["items"]) == 2
                # 验证商品详情
                for item in order["items"]:
                    assert "book_id" in item
                    assert "count" in item
                    assert "price" in item
                break


import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB
from fe import conf
import uuid


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_cancel_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家
        self.seller_id = "test_cancel_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_cancel_store_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 添加图书
        book_db = BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 2)
        for book in self.books:
            assert self.seller.add_book(self.store_id, 10, book) == 200
        # 买家充值
        assert self.buyer.add_funds(1000000) == 200
        
        yield

    def test_cancel_order_ok(self):
        """测试正常取消订单"""
        # 创建订单但不支付
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200        
        # 取消订单
        code = self.buyer.cancel_order(order_id)
        assert code == 200

    def test_cancel_order_invalid_order_id(self):
        """测试无效的订单ID"""
        code = self.buyer.cancel_order("invalid_order_id_xxx")
        assert code != 200

    def test_cancel_order_wrong_buyer(self):
        """测试非订单所属买家取消订单"""
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        wrong_buyer = register_new_buyer("wrong_buyer_" + str(uuid.uuid1()), "password")
        
        code = wrong_buyer.cancel_order(order_id)
        assert code != 200

    def test_cancel_paid_order(self):
        """测试无法取消已支付订单"""
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
 
        code = self.buyer.cancel_order(order_id)
        assert code != 200

    def test_cancel_order_stock_return(self):
        """测试取消订单后库存返还"""
        from be.model import db_conn
        db = db_conn.DBConn()
        initial_stock = db.conn["store_books"].find_one({
            "store_id": self.store_id,
            "book_id": self.books[0].id
        })["stock_level"]  
        # 创建订单
        book_id_and_count = [(self.books[0].id, 2)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200 
        # 取消订单
        assert self.buyer.cancel_order(order_id) == 200
        # 验证库存已返还
        final_stock = db.conn["store_books"].find_one({
            "store_id": self.store_id,
            "book_id": self.books[0].id
        })["stock_level"]
        
        assert final_stock == initial_stock

    def test_cancel_order_already_cancelled(self):
        """测试重复取消订单"""
        # 创建订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200    
        # 第一次取消
        assert self.buyer.cancel_order(order_id) == 200      
        # 第二次取消应该失败
        code = self.buyer.cancel_order(order_id)
        assert code != 200


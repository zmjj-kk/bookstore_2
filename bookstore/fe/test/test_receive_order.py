import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB
from fe import conf
import uuid


class TestReceiveOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_receive_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家
        self.seller_id = "test_receive_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_receive_store_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 添加图书
        book_db = BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 2)
        for book in self.books:
            assert self.seller.add_book(self.store_id, 10, book) == 200
        # 买家充值
        assert self.buyer.add_funds(1000000) == 200
        # 创建订单
        book_id_and_count = [(self.books[0].id, 1)]
        code, self.order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        # 支付订单
        assert self.buyer.payment(self.order_id) == 200
        # 发货
        assert self.seller.ship_order(self.order_id) == 200
        
        yield

    def test_receive_order_ok(self):
        """测试正常收货"""
        code = self.buyer.receive_order(self.order_id)
        assert code == 200

    def test_receive_order_invalid_order_id(self):
        """测试无效的订单ID"""
        code = self.buyer.receive_order("invalid_order_id_xxx")
        assert code != 200

    def test_receive_order_wrong_buyer(self):
        """测试非订单所属买家收货"""
        wrong_buyer = register_new_buyer("wrong_buyer_" + str(uuid.uuid1()), "password")
        code = wrong_buyer.receive_order(self.order_id)
        assert code != 200

    def test_receive_order_not_shipped(self):
        """测试未发货订单无法收货"""
        book_id_and_count = [(self.books[1].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        assert self.buyer.payment(order_id) == 200
        
        code = self.buyer.receive_order(order_id)
        assert code != 200

    def test_receive_order_already_received(self):
        """测试重复收货"""
        # 第一次收货
        assert self.buyer.receive_order(self.order_id) == 200
        # 第二次收货应该失败
        code = self.buyer.receive_order(self.order_id)
        assert code != 200


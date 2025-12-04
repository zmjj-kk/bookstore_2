import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB
from fe import conf
import uuid


class TestShipOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_ship_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家
        self.seller_id = "test_ship_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_ship_store_{}".format(str(uuid.uuid1()))
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
        
        yield

    def test_ship_order_ok(self):
        """测试正常发货"""
        code = self.seller.ship_order(self.order_id)
        assert code == 200

    def test_ship_order_invalid_order_id(self):
        """测试无效的订单ID"""
        code = self.seller.ship_order("invalid_order_id_xxx")
        assert code != 200

    def test_ship_order_wrong_seller(self):
        """测试非订单所属卖家发货"""
        wrong_seller = register_new_seller("wrong_seller_" + str(uuid.uuid1()), "password")
        code = wrong_seller.ship_order(self.order_id)
        assert code != 200

    def test_ship_order_not_paid(self):
        """测试未支付订单无法发货"""
        book_id_and_count = [(self.books[1].id, 1)]
        code, order_id = self.buyer.new_order(self.store_id, book_id_and_count)
        assert code == 200
        code = self.seller.ship_order(order_id)
        assert code != 200

    def test_ship_order_already_shipped(self):
        """测试重复发货"""
        # 第一次发货
        assert self.seller.ship_order(self.order_id) == 200
        # 第二次发货应该失败（订单已被移动到archived_orders）
        code = self.seller.ship_order(self.order_id)
        assert code != 200

    def test_ship_order_update_failed(self):
        """测试发货时状态更新失败"""
        # 正常发货应该成功
        code = self.seller.ship_order(self.order_id)
        assert code == 200
        
        # 再次发货应该失败（订单已被删除或状态已改变）
        code = self.seller.ship_order(self.order_id)
        assert code != 200


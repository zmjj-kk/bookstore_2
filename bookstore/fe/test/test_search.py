import pytest
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import BookDB
from fe import conf
import uuid


class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化买家
        self.buyer_id = "test_search_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        # 初始化卖家1
        self.seller_id = "test_search_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)
        # 创建店铺
        self.store_id = "test_search_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 添加图书
        book_db = BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 2)
        for book in self.books:
            assert self.seller.add_book(self.store_id, 10, book) == 200

        yield

    def test_ok(self):
        # 测试搜索功能
        keyword = self.books[0].title.split()[0]  # 使用第一本书标题的第一个单词作为搜索关键词
        code, result = self.buyer.search(keyword, "title", None, 1, 10)
        assert code == 200

        
    def test_non_exist_book(self):
        code, result = self.buyer.search("nonexistent_book_title", "title", None, 1, 10)
        assert code == 520
    def test_title(self):
        code, result = self.buyer.search(self.books[0].title, "title", None, 1, 10)
        assert code == 200
    def test_book_intro(self):
        code, result = self.buyer.search(self.books[0].book_intro.split("\n")[0], "book_intro", None, 1, 10)
        assert code == 200
    def test_content(self):
        code, result = self.buyer.search(self.books[0].content.split("\n")[0], "content", None, 1, 10)
        assert code == 200
    def test_tags(self):
        code, result = self.buyer.search(self.books[0].tags[0], "tags", None, 1, 10)
        assert code == 200
    def test_pagination(self):
        # 测试分页功能
        keyword = self.books[0].title.split()[0]  # 使用第一本书标题的第一个单词作为搜索关键词
        code, result1 = self.buyer.search(keyword, "title", None, 1, 5)
        assert code == 200
        code, result2 = self.buyer.search(keyword, "title", None, 2, 5)
        assert code == 200

    def test_invalid_page_size(self):
        # 测试无效的分页大小
        keyword = self.books[0].title.split()[0]  # 使用第一本书标题的第一个单词作为搜索关键词
        code, result = self.buyer.search(keyword, "title", None, 1, 0)
        assert code == 404

    def test_invalid_page(self):
        # 测试无效的分页页码
        keyword = self.books[0].title.split()[0]
        code, result = self.buyer.search(keyword, "title", None, -1, 10)
        assert code == 403

    def test_in_store(self):
        # 测试在指定店铺中搜索
        keyword = self.books[0].title.split()[0]
        code, result = self.buyer.search(keyword, "title", self.store_id, 1, 10)
        assert code == 200

    def test_non_exist_store(self):
        # 测试在不存在的店铺中搜索
        keyword = self.books[0].title.split()[0]
        code, result = self.buyer.search(keyword, "title", "nonexistent_store_id", 1, 10)
        assert code == 513

    def test_all_fields(self):
        # 测试搜索所有字段
        keyword = "了"  # 使用常用词为字段
        code, result = self.buyer.search(keyword, "all", None, 1, 10)
        assert code == 200

    def test_no_results_with_all_fields(self):
        keyword = "12e9wm0qw0d,qd-q0wd"
        code, result = self.buyer.search(keyword, "all", None, 1, 10)
        assert code == 520

    def test_page_overflow(self):
        keyword = self.books[0].title.split()[0]
        code, result = self.buyer.search(keyword, "title", None, 10000, 10)
        assert code == 521
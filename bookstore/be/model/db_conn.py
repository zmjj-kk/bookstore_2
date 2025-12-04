from be.model import store


class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    def user_id_exist(self, user_id):
        """
        判断用户是否存在
        """
        row = self.conn["users"].find_one({"user_id": user_id})
        return row is not None

    def book_id_exist(self, store_id, book_id):
        """
        判断某个店铺的某类书是否存在
        """
        row = self.conn["store_books"].find_one({
            "store_id": store_id,
            "book_id": book_id
        })
        return row is not None

    def store_id_exist(self, store_id):
        """
        判断店铺是否存在
        """
        row = self.conn["stores"].find_one({"store_id": store_id})
        return row is not None

import os
from pymongo import MongoClient
import sqlite3 as sqlite
import random
import base64
import simplejson as json


class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        client = MongoClient("mongodb://localhost:27017/")
        db = client["bookstore"]
        self.book_db = db["books"]

    def get_book_count(self):
        return self.book_db.count_documents({})

    def get_book_info(self, start, size) -> [Book]:
        books = []

        rows = self.book_db.find(
            {},  # 查询条件：{} 表示所有文档
            {
                "_id": 1,
                "title": 1,
                "author": 1,
                "publisher": 1,
                "original_title": 1,
                "translator": 1,
                "pub_year": 1,
                "pages": 1,
                "price": 1,
                "currency_unit": 1,
                "binding": 1,
                "isbn": 1,
                "author_intro": 1,
                "book_intro": 1,
                "content": 1,
                "tags": 1,
                "picture": 1
            }
        ).sort("_id", 1).skip(start).limit(size)

        for doc in rows:
            book = Book()
            book.id = str(doc.get("_id", ""))
            book.title = doc.get("title", "")
            book.author = doc.get("author", "")
            book.publisher = doc.get("publisher", "")
            book.original_title = doc.get("original_title", "")
            book.translator = doc.get("translator", "")
            book.pub_year = doc.get("pub_year", "")
            book.pages = doc.get("pages", 0)
            book.price = doc.get("price", 0.0)
            book.currency_unit = doc.get("currency_unit", "")
            book.binding = doc.get("binding", "")
            book.isbn = doc.get("isbn", "")
            book.author_intro = doc.get("author_intro", "")
            book.book_intro = doc.get("book_intro", "")
            book.content = doc.get("content", "")

            tags_field = doc.get("tags", [])
            if isinstance(tags_field, str):
                tags = [t.strip() for t in tags_field.split("\n") if t.strip()]
            elif isinstance(tags_field, list):
                tags = tags_field
            else:
                tags = []
            book.tags = tags

            picture = doc.get("pictures")
            book.pictures = []
            if picture:
                for _ in range(random.randint(0, 9)):
                    encode_str = base64.b64encode(picture).decode("utf-8")
                    book.pictures.append(encode_str)

            books.append(book)

        return books

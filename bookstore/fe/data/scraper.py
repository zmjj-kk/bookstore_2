# coding=utf-8

from lxml import etree
import sqlite3
import re
import requests
import random
import time
import logging

user_agent = [
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 "
    "Safari/534.50",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 "
    "Safari/534.50",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR "
    "3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
    "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 "
    "Safari/535.11",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET "
    "CLR 2.0.50727; SE 2.X MetaSr 1.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) "
    "Version/4.0 Mobile Safari/533.1",
    "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) "
    "AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
    "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) "
    "Version/4.0 Safari/534.13",
    "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 "
    "Mobile Safari/534.1+",
    "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) "
    "wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
    "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) "
    "AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
    "UCWEB7.0.2.37/28/999",
    "NOKIA5700/ UCWEB7.0.2.37/28/999",
    "Openwave/ UCWEB7.0.2.37/28/999",
    "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999",
    # iPhone 6：
    "Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 "
    "Mobile/10A5376e Safari/8536.25",
]


def get_user_agent():
    headers = {"User-Agent": random.choice(user_agent)}
    return headers


class Scraper:
    database: str
    tag: str
    page: int

    def __init__(self):
        self.database = "book.db"
        self.tag = ""
        self.page = 0
        self.pattern_number = re.compile(r"\d+\.?\d*")
        # 设置日志级别为INFO，并添加控制台输出
        logging.basicConfig(
            filename="scraper.log", 
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        # 添加控制台处理器，方便实时查看进度
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
        
        print("=" * 50)
        print("Scraper initialized")
        print(f"Database file: {self.database}")
        print(f"Log file: scraper.log")
        print("=" * 50)

    def get_current_progress(self) -> ():
        conn = sqlite3.connect(self.database)
        results = conn.execute("SELECT tag, page from progress where id = '0'")
        for row in results:
            return row[0], row[1]
        return "", 0

    def save_current_progress(self, current_tag, current_page):
        conn = sqlite3.connect(self.database)
        conn.execute(
            "UPDATE progress set tag = '{}', page = {} where id = '0'".format(
                current_tag, current_page
            )
        )
        conn.commit()
        conn.close()

    def start_grab(self) -> bool:
        print("\n[STEP 1] Starting scraping process...")
        logging.info("Starting scraping process")
        
        print("[STEP 2] Creating database tables...")
        logging.info("Creating database tables")
        self.create_tables()
        print("Database tables created successfully")
        
        print("[STEP 3] Fetching tag list...")
        logging.info("Starting to fetch tag list")
        if not self.grab_tag():
            print("ERROR: Tag fetching failed!")
            logging.error("Tag fetching failed")
            return False
        print("Tag fetching completed")
        
        print("[STEP 4] Getting current progress...")
        current_tag, current_page = self.get_current_progress()
        print(f"Current progress: tag={current_tag}, page={current_page}")
        logging.info(f"Current progress: tag={current_tag}, page={current_page}")
        
        print("[STEP 5] Getting tag list...")
        tags = self.get_tag_list()
        print(f"Found {len(tags)} tags: {tags[:5]}{'...' if len(tags) > 5 else ''}")
        logging.info(f"Found {len(tags)} tags")
        
        if len(tags) == 0:
            print("ERROR: No tags found!")
            logging.error("No tags found")
            return False
        
        print("[STEP 6] Starting to fetch book details...")
        logging.info("Starting to fetch book details")
        
        for i in range(0, len(tags)):
            print(f"\nProcessing tag {i+1}/{len(tags)}: {tags[i]}")
            logging.info(f"Processing tag {i+1}/{len(tags)}: {tags[i]}")
            
            no = 0
            if i == 0 and current_tag == tags[i]:
                no = current_page
                print(f"Resuming from last position: page {no}")
                logging.info(f"Resuming from last position: page {no}")
            
            page_count = 0
            while self.grab_book_list(tags[i], no):
                no = no + 20
                page_count += 1
                print(f"  Processed {page_count} pages")
            
            print(f"Tag {tags[i]} completed, {page_count} pages total")
            logging.info(f"Tag {tags[i]} completed, {page_count} pages total")
        
        print("\nAll scraping tasks completed!")
        logging.info("All scraping tasks completed")
        return True

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        print("  Creating tags table...")
        try:
            conn.execute("CREATE TABLE tags (tag TEXT PRIMARY KEY)")
            conn.commit()
            print("  Tags table created successfully")
        except sqlite3.Error as e:
            print(f"  Tags table already exists or creation failed: {str(e)}")
            logging.warning(f"Tags table creation: {str(e)}")
            conn.rollback()

        print("  Creating book table...")
        try:
            conn.execute(
                "CREATE TABLE book ("
                "id TEXT PRIMARY KEY, title TEXT, author TEXT, "
                "publisher TEXT, original_title TEXT, "
                "translator TEXT, pub_year TEXT, pages INTEGER, "
                "price INTEGER, currency_unit TEXT, binding TEXT, "
                "isbn TEXT, author_intro TEXT, book_intro text, "
                "content TEXT, tags TEXT, picture BLOB)"
            )
            conn.commit()
            print("  Book table created successfully")
        except sqlite3.Error as e:
            print(f"  Book table already exists or creation failed: {str(e)}")
            logging.warning(f"Book table creation: {str(e)}")
            conn.rollback()

        print("  Creating progress table...")
        try:
            conn.execute(
                "CREATE TABLE progress (id TEXT PRIMARY KEY, tag TEXT, page integer )"
            )
            conn.execute("INSERT OR IGNORE INTO progress values('0', '', 0)")
            conn.commit()
            print("  Progress table created successfully")
        except sqlite3.Error as e:
            print(f"  Progress table already exists or creation failed: {str(e)}")
            logging.warning(f"Progress table creation: {str(e)}")
            conn.rollback()
        
        conn.close()

    def grab_tag(self):
        print("  🌐 正在访问豆瓣标签页面...")
        url = "https://book.douban.com/tag/?view=cloud"
        try:
            r = requests.get(url, headers=get_user_agent(), timeout=10)
            r.encoding = "utf-8"
            print(f"  ✅ 页面访问成功，状态码: {r.status_code}")
            logging.info(f"豆瓣标签页面访问成功，状态码: {r.status_code}")
        except Exception as e:
            print(f"  ❌ 页面访问失败: {str(e)}")
            logging.error(f"豆瓣标签页面访问失败: {str(e)}")
            return False
        
        print("  🔍 正在解析标签...")
        h: etree.ElementBase = etree.HTML(r.text)
        
        # 先保存页面内容用于调试
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        print("  🔧 已保存页面内容到 debug_page.html 用于调试")
        
        # 尝试多种可能的XPath路径
        possible_xpaths = [
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]/div[@class="article"]'
            '/div[@class=""]/div[@class="indent tag_cloud"]'
            "/table/tbody/tr/td/a/@href",
            
            # 备选路径1
            '//div[@class="tag_cloud"]//a/@href',
            
            # 备选路径2  
            '//div[@id="content"]//div[@class="tag_cloud"]//a/@href',
            
            # 备选路径3
            '//table//a[contains(@href, "/tag/")]/@href',
            
            # 备选路径4
            '//a[contains(@href, "/tag/")]/@href'
        ]
        
        tags = []
        for i, xpath in enumerate(possible_xpaths):
            print(f"  🔍 尝试XPath路径 {i+1}...")
            try:
                found_tags = h.xpath(xpath)
                if len(found_tags) > 0:
                    tags = found_tags
                    print(f"  ✅ 路径 {i+1} 找到 {len(tags)} 个标签")
                    break
                else:
                    print(f"  ❌ 路径 {i+1} 未找到标签")
            except Exception as e:
                print(f"  ❌ 路径 {i+1} 解析错误: {str(e)}")
        
        if len(tags) == 0:
            print("  ❌ 所有XPath路径都无法找到标签!")
            print("  🔧 请检查 debug_page.html 文件，查看页面实际结构")
            logging.error("所有XPath路径都无法找到标签")
            return False
        
        print(f"  ✅ 找到 {len(tags)} 个标签")
        logging.info(f"找到 {len(tags)} 个标签")
        
        print("  💾 正在保存标签到数据库...")
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        saved_count = 0
        try:
            for tag in tags:
                t: str = tag.strip("/tag")
                try:
                    c.execute("INSERT OR IGNORE INTO tags VALUES (?)", (t,))
                    saved_count += 1
                except sqlite3.Error as e:
                    print(f"  ⚠️ 标签 {t} 保存失败: {str(e)}")
                    logging.warning(f"标签 {t} 保存失败: {str(e)}")
            
            conn.commit()
            print(f"  ✅ 成功保存 {saved_count} 个标签到数据库")
            logging.info(f"成功保存 {saved_count} 个标签到数据库")
        except sqlite3.Error as e:
            print(f"  ❌ 数据库操作失败: {str(e)}")
            logging.error(f"数据库操作失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            c.close()
            conn.close()
        
        return True

    def grab_book_list(self, tag="小说", pageno=1) -> bool:
        print(f"    📄 抓取标签 '{tag}' 第 {pageno} 页...")
        logging.info(f"开始抓取标签 {tag} 第 {pageno} 页")
        self.save_current_progress(tag, pageno)
        
        url = "https://book.douban.com/tag/{}?start={}&type=T".format(tag, pageno)
        try:
            r = requests.get(url, headers=get_user_agent(), timeout=10)
            r.encoding = "utf-8"
            print(f"    ✅ 页面访问成功，状态码: {r.status_code}")
        except Exception as e:
            print(f"    ❌ 页面访问失败: {str(e)}")
            logging.error(f"标签 {tag} 第 {pageno} 页访问失败: {str(e)}")
            return False
        
        h: etree.Element = etree.HTML(r.text)

        li_list: [] = h.xpath(
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]/div[@id="subject_list"]'
            '/ul/li/div[@class="info"]/h2/a/@href'
        )
        next_page = h.xpath(
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]/div[@id="subject_list"]'
            '/div[@class="paginator"]/span[@class="next"]/a[@href]'
        )
        has_next = True
        if len(next_page) == 0:
            has_next = False
        
        if len(li_list) == 0:
            print(f"    ⚠️ 第 {pageno} 页没有找到任何书籍")
            logging.warning(f"标签 {tag} 第 {pageno} 页没有找到任何书籍")
            return False

        print(f"    📚 找到 {len(li_list)} 本书，开始抓取详情...")
        success_count = 0
        fail_count = 0
        
        for i, li in enumerate(li_list):
            li.strip("")
            book_id = li.strip("/").split("/")[-1]
            print(f"      📖 [{i+1}/{len(li_list)}] 抓取书籍 {book_id}...")
            
            try:
                delay = float(random.randint(0, 200)) / 100.0
                time.sleep(delay)
                if self.crow_book_info(book_id):
                    success_count += 1
                    print(f"        ✅ 成功")
                else:
                    fail_count += 1
                    print(f"        ❌ 失败")
            except BaseException as e:
                fail_count += 1
                print(f"        ❌ 异常: {str(e)}")
                logging.error(f"抓取书籍 {book_id} 时发生异常: {str(e)}")
        
        print(f"    📊 本页完成: 成功 {success_count} 本，失败 {fail_count} 本")
        logging.info(f"标签 {tag} 第 {pageno} 页完成: 成功 {success_count} 本，失败 {fail_count} 本")
        
        if has_next:
            print(f"    ➡️ 还有下一页")
        else:
            print(f"    🏁 这是最后一页")
            
        return has_next

    def get_tag_list(self) -> [str]:
        ret = []
        conn = sqlite3.connect(self.database)
        results = conn.execute(
            "SELECT tags.tag from tags join progress where tags.tag >= progress.tag"
        )
        for row in results:
            ret.append(row[0])
        return ret

    def crow_book_info(self, book_id) -> bool:
        # 检查书籍是否已存在
        conn = sqlite3.connect(self.database)
        for _ in conn.execute("SELECT id from book where id = ?", (book_id,)):
            print(f"        ⚠️ 书籍 {book_id} 已存在，跳过")
            conn.close()
            return True
        conn.close()

        url = "https://book.douban.com/subject/{}/".format(book_id)
        try:
            r = requests.get(url, headers=get_user_agent(), timeout=10)
            r.encoding = "utf-8"
        except Exception as e:
            print(f"        ❌ 访问书籍页面失败: {str(e)}")
            logging.error(f"访问书籍 {book_id} 页面失败: {str(e)}")
            return False
        
        h: etree.Element = etree.HTML(r.text)
        e_text = h.xpath('/html/body/div[@id="wrapper"]/h1/span/text()')
        if len(e_text) == 0:
            print(f"        ❌ 无法获取书籍标题")
            logging.error(f"书籍 {book_id} 无法获取标题")
            return False

        title = e_text[0]
        print(f"        📖 标题: {title}")

        elements = h.xpath(
            '/html/body/div[@id="wrapper"]'
            '/div[@id="content"]/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]'
        )
        if len(elements) == 0:
            print(f"        ❌ 无法找到书籍详情区域")
            logging.error(f"书籍 {book_id} 无法找到详情区域")
            return False

        e_article = elements[0]
        print(f"        🔍 开始解析书籍详情...")

        book_intro = ""
        author_intro = ""
        content = ""
        tags = ""

        e_book_intro = e_article.xpath(
            'div[@class="related_info"]'
            '/div[@class="indent"][@id="link-report"]/*'
            '/div[@class="intro"]/*/text()'
        )
        for line in e_book_intro:
            line = line.strip()
            if line != "":
                book_intro = book_intro + line + "\n"

        e_author_intro = e_article.xpath(
            'div[@class="related_info"]'
            '/div[@class="indent "]/*'
            '/div[@class="intro"]/*/text()'
        )
        for line in e_author_intro:
            line = line.strip()
            if line != "":
                author_intro = author_intro + line + "\n"

        e_content = e_article.xpath(
            'div[@class="related_info"]'
            '/div[@class="indent"][@id="dir_' + book_id + '_full"]/text()'
        )
        for line in e_content:
            line = line.strip()
            if line != "":
                content = content + line + "\n"

        e_tags = e_article.xpath(
            'div[@class="related_info"]/'
            'div[@id="db-tags-section"]/'
            'div[@class="indent"]/span/a/text()'
        )
        for line in e_tags:
            line = line.strip()
            if line != "":
                tags = tags + line + "\n"

        e_subject = e_article.xpath(
            'div[@class="indent"]'
            '/div[@class="subjectwrap clearfix"]'
            '/div[@class="subject clearfix"]'
        )
        pic_href = e_subject[0].xpath('div[@id="mainpic"]/a/@href')
        picture = None
        if len(pic_href) > 0:
            res = requests.get(pic_href[0], headers=get_user_agent())
            picture = res.content

        info_children = e_subject[0].xpath('div[@id="info"]/child::node()')

        e_array = []
        e_dict = dict()

        for e in info_children:
            if isinstance(e, etree._ElementUnicodeResult):
                e_dict["text"] = e
            elif isinstance(e, etree._Element):
                if e.tag == "br":
                    e_array.append(e_dict)
                    e_dict = dict()
                else:
                    e_dict[e.tag] = e

        book_info = dict()
        for d in e_array:
            label = ""
            span = d.get("span")
            a_label = span.xpath("span/text()")
            if len(a_label) > 0 and label == "":
                label = a_label[0].strip()
            a_label = span.xpath("text()")
            if len(a_label) > 0 and label == "":
                label = a_label[0].strip()
            label = label.strip(":")
            text = d.get("text").strip()
            e_a = d.get("a")
            text.strip()
            text.strip(":")
            if label == "作者" or label == "译者":
                a = span.xpath("a/text()")
                if text == "" and len(a) == 1:
                    text = a[0].strip()
                if text == "" and e_a is not None:
                    text_a = e_a.xpath("text()")
                    if len(text_a) > 0:
                        text = text_a[0].strip()
                        text = re.sub(r"\s+", " ", text)
            if text != "":
                book_info[label] = text

        sql = (
            "INSERT INTO book("
            "id, title, author, "
            "publisher, original_title, translator, "
            "pub_year, pages, price, "
            "currency_unit, binding, isbn, "
            "author_intro, book_intro, content, "
            "tags, picture)"
            "VALUES("
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?)"
        )

        unit = None
        price = None
        pages = None
        conn = sqlite3.connect(self.database)
        try:
            s_price = book_info.get("定价")
            if s_price is None:
                print(f"        ❌ 无法获取价格信息")
                logging.error(f"书籍 {book_id} 无法获取价格信息")
                return False
            else:
                e = re.findall(self.pattern_number, s_price)
                if len(e) != 0:
                    number = e[0]
                    unit = s_price.replace(number, "").strip()
                    price = int(float(number) * 100)
                    print(f"        💰 价格: {number} {unit}")
                else:
                    print(f"        ❌ 价格格式无法解析: {s_price}")
                    logging.error(f"书籍 {book_id} 价格格式无法解析: {s_price}")
                    return False

            s_pages = book_info.get("页数")
            if s_pages is not None:
                e = re.findall(self.pattern_number, s_pages)
                if len(e) != 0:
                    pages = int(e[0])
                    print(f"        📄 页数: {pages}")

            print(f"        💾 正在保存到数据库...")
            conn.execute(
                sql,
                (
                    book_id,
                    title,
                    book_info.get("作者"),
                    book_info.get("出版社"),
                    book_info.get("原作名"),
                    book_info.get("译者"),
                    book_info.get("出版年"),
                    pages,
                    price,
                    unit,
                    book_info.get("装帧"),
                    book_info.get("ISBN"),
                    author_intro,
                    book_intro,
                    content,
                    tags,
                    picture,
                ),
            )
            conn.commit()
            print(f"        ✅ 保存成功")
            logging.info(f"书籍 {book_id} 保存成功")
        except sqlite3.Error as e:
            print(f"        ❌ 数据库保存失败: {str(e)}")
            logging.error(f"书籍 {book_id} 数据库保存失败: {str(e)}")
            conn.rollback()
            return False
        except TypeError as e:
            print(f"        ❌ 数据类型错误: {str(e)}")
            logging.error(f"书籍 {book_id} 数据类型错误: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
        return True


def test_douban_access():
    """测试豆瓣页面访问和解析"""
    print("🧪 测试豆瓣页面访问...")
    
    # 测试不同的URL
    test_urls = [
        "https://book.douban.com/tag/?view=cloud",
        "https://book.douban.com/tag/",
        "https://book.douban.com/tag/?view=type"
    ]
    
    for url in test_urls:
        print(f"\n🌐 测试URL: {url}")
        try:
            r = requests.get(url, headers=get_user_agent(), timeout=10)
            print(f"  状态码: {r.status_code}")
            print(f"  内容长度: {len(r.text)} 字符")
            
            if r.status_code == 200:
                h = etree.HTML(r.text)
                # 检查是否包含"tag"相关内容
                tag_elements = h.xpath('//*[contains(text(), "tag") or contains(@class, "tag")]')
                print(f"  包含'tag'的元素数量: {len(tag_elements)}")
                
                # 保存页面用于分析
                filename = f"debug_{url.split('/')[-1] or 'index'}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(f"  页面已保存到: {filename}")
                
        except Exception as e:
            print(f"  ❌ 访问失败: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_douban_access()
    else:
        scraper = Scraper()
        scraper.start_grab()

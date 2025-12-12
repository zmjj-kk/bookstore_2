-- 创建数据库（首次执行时运行，后续注释掉）
CREATE DATABASE IF NOT EXISTS bookstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bookstore;

-- 1. 用户表（users）
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID（自增主键）',
  name VARCHAR(50) NOT NULL COMMENT '用户名',
  email VARCHAR(100) UNIQUE NOT NULL COMMENT '用户邮箱（唯一）',
  password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
  role ENUM('buyer', 'seller', 'admin') NOT NULL DEFAULT 'buyer' COMMENT '用户角色：买家/卖家/管理员',
  token VARCHAR(255) DEFAULT NULL COMMENT '登录令牌'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 店铺表（stores）
CREATE TABLE stores (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '店铺ID（自增主键）',
  name VARCHAR(100) NOT NULL COMMENT '店铺名称',
  seller_id INT NOT NULL COMMENT '关联卖家用户ID',
  FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 图书表（books）
CREATE TABLE books (
  id VARCHAR(50) PRIMARY KEY COMMENT '图书ID（对应原SQLite的id）',
  title VARCHAR(255) NOT NULL COMMENT '书名',
  author VARCHAR(255) DEFAULT '' COMMENT '作者',
  publisher VARCHAR(255) DEFAULT '' COMMENT '出版社',
  original_title VARCHAR(255) DEFAULT '' COMMENT '原书名',
  translator VARCHAR(255) DEFAULT '' COMMENT '译者',
  pub_year VARCHAR(20) DEFAULT '' COMMENT '出版年份',
  pages INT DEFAULT 0 COMMENT '页数',
  price INT NOT NULL COMMENT '价格（单位：分）',
  currency_unit VARCHAR(10) DEFAULT 'CNY' COMMENT '货币单位',
  binding VARCHAR(50) DEFAULT '' COMMENT '装帧',
  isbn VARCHAR(20) UNIQUE COMMENT 'ISBN（唯一）',
  author_intro TEXT COMMENT '作者简介',
  book_intro TEXT COMMENT '图书简介',
  content TEXT COMMENT '内容简介',
  tags VARCHAR(255) DEFAULT '' COMMENT '标签（逗号分隔）',
  picture BLOB COMMENT '图书封面'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 店铺图书库存表（store_books）
CREATE TABLE store_books (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '库存记录ID',
  store_id INT NOT NULL COMMENT '关联店铺ID',
  book_id VARCHAR(50) NOT NULL COMMENT '关联图书ID',
  stock INT NOT NULL DEFAULT 0 COMMENT '库存数量',
  price INT NOT NULL COMMENT '店铺定价（单位：分）',
  title VARCHAR(255) NOT NULL COMMENT '图书标题（冗余字段，优化查询）',
  tags VARCHAR(255) DEFAULT '' COMMENT '图书标签（冗余字段）',
  FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE,
  FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
  UNIQUE KEY uk_store_book (store_id, book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 订单表（orders）
CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
  order_no VARCHAR(50) UNIQUE NOT NULL COMMENT '订单编号（唯一）',
  user_id INT NOT NULL COMMENT '关联买家ID',
  store_id INT NOT NULL COMMENT '关联店铺ID',
  status ENUM('pending', 'paid', 'shipped', 'received', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 订单明细表（order_items）
CREATE TABLE order_items (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '订单明细ID',
  order_id INT NOT NULL COMMENT '关联订单ID',
  book_id VARCHAR(50) NOT NULL COMMENT '关联图书ID',
  quantity INT NOT NULL DEFAULT 1 COMMENT '购买数量',
  price INT NOT NULL COMMENT '购买单价（单位：分）',
  title VARCHAR(255) NOT NULL COMMENT '图书标题（冗余字段）',
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 归档订单表（archived_orders）
CREATE TABLE archived_orders (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '归档订单ID',
  order_no VARCHAR(50) UNIQUE NOT NULL COMMENT '订单编号',
  user_id INT NOT NULL COMMENT '关联买家ID',
  store_id INT NOT NULL COMMENT '关联店铺ID',
  status ENUM('received', 'cancelled') NOT NULL COMMENT '归档状态（仅已完成/已取消）',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '归档时间',
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (store_id) REFERENCES stores(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 归档订单明细表（archived_order_items）
CREATE TABLE archived_order_items (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '归档订单明细ID',
  archived_order_id INT NOT NULL COMMENT '关联归档订单ID',
  book_id VARCHAR(50) NOT NULL COMMENT '关联图书ID',
  quantity INT NOT NULL COMMENT '购买数量',
  price INT NOT NULL COMMENT '购买单价',
  title VARCHAR(255) NOT NULL COMMENT '图书标题',
  FOREIGN KEY (archived_order_id) REFERENCES archived_orders(id) ON DELETE CASCADE,
  FOREIGN KEY (book_id) REFERENCES books(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 补充：作者表、标签表、关联表
CREATE TABLE authors (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '作者ID',
  name VARCHAR(255) NOT NULL COMMENT '作者姓名',
  intro TEXT COMMENT '作者简介',
  nationality VARCHAR(50) DEFAULT '' COMMENT '作者国籍'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tags (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '标签ID',
  name VARCHAR(50) NOT NULL COMMENT '标签名称',
  description TEXT COMMENT '标签描述'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE book_author (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
  book_id VARCHAR(50) NOT NULL COMMENT '图书ID',
  author_id INT NOT NULL COMMENT '作者ID',
  FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
  FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
  UNIQUE KEY uk_book_author (book_id, author_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE book_tag (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
  book_id VARCHAR(50) NOT NULL COMMENT '图书ID',
  tag_id INT NOT NULL COMMENT '标签ID',
  FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
  UNIQUE KEY uk_book_tag (book_id, tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

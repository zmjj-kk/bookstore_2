## Collections设计

### 1. users Collection (用户表)
存储用户基本信息和认证数据。

```javascript
{
  _id: ObjectId,                    // MongoDB自动生成的ID
  user_id: String,                  // 用户名，唯一标识
  password: String,                 // 密码(建议加密存储)
  balance: Number,                  // 账户余额(以分为单位)
  token: String,                    // JWT token
  terminal: String                  // 终端标识
}
```

### 2. stores Collection (店铺表)
存储店铺基本信息。

```javascript
{
  _id: ObjectId,
  store_id: String,                 // 店铺ID，唯一标识
  user_id: String                   // 店主用户ID
}
```


### 3. books Collection (图书信息表)
存储图书的详细信息，从SQLite的book表迁移而来。

```javascript
{
  _id: ObjectId,
  book_id: String,                  // 图书ID，唯一标识 (对应SQLite的id字段)
  title: String,                    // 书名
  author: String,                   // 作者
  publisher: String,                // 出版社
  original_title: String,           // 原书名
  translator: String,               // 译者
  pub_year: String,                 // 出版年份
  pages: Number,                    // 页数
  price: Number,                    // 标准价格(以分为单位)
  currency_unit: String,            // 货币单位
  binding: String,                  // 装帧方式
  isbn: String,                     // ISBN号
  author_intro: String,             // 作者简介
  book_intro: String,               // 图书简介
  content: String,                  // 目录
  tags: [String],                   // 标签数组 (从SQLite的TEXT字段转换)
  pictures: [String]                // 图片base64编码数组 (从SQLite的BLOB字段转换)
}
```


### 4. store_books Collection (店铺图书库存表)
存储店铺中图书的库存和价格信息，使用嵌套文档支持高效搜索。

```javascript
{
  _id: ObjectId,
  store_id: String,                 // 店铺ID
  book_id: String,                  // 图书ID (String格式，不是数组，因为每个文档代表一个店铺中的一本图书)
  stock_level: Number,              // 库存数量
  title: String,                  // 书名
  book_intro: String,            // 图书简介
  content: String,               // 目录
  tags: [String],                // 标签数组
  price: Number                  // 标准价格
}
```

### 5. orders Collection (活跃订单表)
存储进行中的订单，只保留更改频繁的部分，字段精简为必需项。

```javascript
{
  _id: ObjectId,
  order_id: String,          // 订单ID
  user_id: String,           // 买家ID
  store_id: String,          // 店铺ID
  status: String,            // pending/paid/shipped（对应待付款/待发货/待收货）
  created_at: Date,          // 下单时间
  timeout_at: Date           // 超时时间 
  items: [{                  // 订单明细
    book_id: String,
    count: Number,
    price: Number
  }]
}
```


### 6. archived_orders Collection (归档订单表)
存储已完成或已取消的订单，字段精简为必要项。

```javascript
{
  _id: ObjectId,
  order_id: String,          // 订单ID
  user_id: String,           // 买家ID
  store_id: String,          // 店铺ID
  status: String,            // delivered/cancelled（已送达/已取消（包括了超时和自主取消）
  created_at: Date,          // 下单时间
  closed_at: Date,           // 收货或取消时间
  items: [{                  // 订单明细
    book_id: String,
    count: Number,
    price: Number
  }]
}
```



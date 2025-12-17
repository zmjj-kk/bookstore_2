import sys
from pathlib import Path

# 将项目根目录添加到sys.path（绝对路径更安全）
project_root = Path(__file__).resolve().parent.parent.parent  # 适用于bookstore_2/bookstore/be/app.py结构
sys.path.insert(0, str(project_root))
print(f"已添加项目根目录到sys.path: {project_root}")  # 调试用


from flask import Flask

# 创建Flask应用实例
app = Flask(__name__)

# 配置数据库连接（示例）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:021201hyj@localhost/bookstore'

# 配置MySQL连接参数（必须早于导入store.py）
app.config.update({
    'MYSQL_HOST': 'localhost',
    'MYSQL_USER': 'root',
    'MYSQL_PASSWORD': '021201hyj',
    'MYSQL_DB': 'bookstore'
})

import sys
from pathlib import Path

# 将项目根目录添加到sys.path（绝对路径更安全）
project_root = Path(__file__).parent.parent.parent  # 适用于bookstore_2/bookstore/be/app.py结构
sys.path.append(str(project_root))


from bookstore.be import serve

if __name__ == "__main__":
    serve.be_run()

import logging
import os
from flask import Flask
from flask import Blueprint
from be.view import auth, seller, buyer
from be.model.store import init_database, db, init_completed_event  # 显式导入db
import sys
from pathlib import Path

os.environ['FLASK_SKIP_DOTENV'] = '1'  # 跳过.env加载
os.environ['FLASK_RUN_HOST'] = '0.0.0.0'  # 允许外部访问

# 将项目根目录添加到PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))


# 全局定义应用实例
app = Flask(__name__)

# 蓝图定义
bp_shutdown = Blueprint("shutdown", __name__)

@bp_shutdown.route("/shutdown")
def be_shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."

# 健康检查路由（全局注册）
@app.route("/db-health")
def db_health():
    try:
        session = db.session
        session.execute(text("SELECT 1"))
        return "MySQL connected successfully", 200
    except Exception as e:
        return f"DB error: {str(e)}", 500

def be_run():
    # 初始化配置
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:021201hyj@localhost:3306/bookstore"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # 初始化数据库
    init_database(app)
    
    # 注册蓝图
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    
    # 日志配置
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    log_file = os.path.join(parent_path, "app.log")
    
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
        ))
    logging.getLogger().addHandler(handler)

    # 临时路由验证（测试后移除）
    @app.route("/test-route")
    def test_route():
        return "This is a test route", 200

# 启动应用时打印所有路由
if __name__ == '__main__':        
    print("Registered routes before run:")        
for rule in app.url_map.iter_rules():            
    print(f"Endpoint: {rule.endpoint}, URL: {rule}")        
# 启动应用
app.run(host="0.0.0.0", port=5000)

import logging
import os
from flask import Flask
from flask import Blueprint
from flask import request
from be.view import auth
from be.view import seller
from be.view import buyer
from be.model.store import init_database, init_completed_event
from sqlalchemy import text

bp_shutdown = Blueprint("shutdown", __name__)


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@bp_shutdown.route("/shutdown")
def be_shutdown():
    shutdown_server()
    return "Server shutting down..."


def be_run():
    app = Flask(__name__)
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller) # 先创建应用实例
    
    # 修正后的配置
    app.config["SQLALCHEHEMY_DATABASE_URI"] = "mysql://root:021201hyj@localhost:3306/bookstore"
    app.config["SQLALCHEHEMY_TRACK_MODIFICATIONS"] = False
    
    # 初始化数据库
    init_database(app)
    
    # 原有代码保持
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    log_file = os.path.join(parent_path, "app.log")
    
    # 注册蓝图和启动
    app.register_blueprint(bp_shutdown)
    # ...其他蓝图注册...
    app.run(port=5000)  # 显式指定端口

    logging.basicConfig(filename=log_file, level=logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)



@app.route("/db-health")
def db_health():
    try:
        # 实际项目中替换为真实查询
        session = db.session 
        session.execute(text("SELECT 1"))
        return "MySQL connected successfully", 200
    except Exception as e:
        return f"DB error: {str(e)}", 500
    
app.register_blueprint(buyer.bp_buyer)
init_completed_event.set()
app.run()

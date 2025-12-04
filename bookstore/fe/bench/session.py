from fe.bench.workload import Workload
from fe.bench.workload import NewOrder
from fe.bench.workload import Payment
from fe.bench.workload import ShipOrder
from fe.bench.workload import ReceiveOrder
from fe.bench.workload import CancelOrder
from fe.bench.workload import QueryOrders
from fe.bench.workload import Search
import time
import threading
import random


class Session(threading.Thread):
    def __init__(self, wl: Workload):
        threading.Thread.__init__(self)
        self.workload = wl
        self.new_order_request = []
        self.payment_request = []
        self.ship_order_request = []
        self.receive_order_request = []
        self.cancel_order_request = []
        self.query_orders_request = []
        # 统计计数器
        self.search_i = 0
        self.payment_i = 0
        self.new_order_i = 0
        self.ship_order_i = 0
        self.receive_order_i = 0
        self.cancel_order_i = 0
        self.query_orders_i = 0
        # 成功计数器
        self.payment_ok = 0
        self.search_ok = 0
        self.new_order_ok = 0
        self.ship_order_ok = 0
        self.receive_order_ok = 0
        self.cancel_order_ok = 0
        self.query_orders_ok = 0
        # 时间统计
        self.time_search = 0
        self.time_new_order = 0
        self.time_payment = 0
        self.time_ship_order = 0
        self.time_receive_order = 0
        self.time_cancel_order = 0
        self.time_query_orders = 0
        self.thread = None
        # 存储订单ID和对应的store_id，用于后续操作
        self.paid_orders = []  # (order_id, store_id, buyer)
        self.shipped_orders = []  # (order_id, buyer)
        self.pending_orders = []  # (order_id, buyer)
        self.gen_procedure()

    def gen_procedure(self):
        for i in range(0, self.workload.procedure_per_session):
            new_order = self.workload.get_new_order()
            self.new_order_request.append(new_order)

    def run(self):
        self.run_gut()

    def run_gut(self):
        for new_order in self.new_order_request:
            # 1. 创建订单
            before = time.time()
            ok, order_id = new_order.run()
            after = time.time()
            self.time_new_order = self.time_new_order + after - before
            self.new_order_i = self.new_order_i + 1
            if ok:
                self.new_order_ok = self.new_order_ok + 1
                # 80%的订单会付款，20%保持pending状态（可用于取消测试）
                if random.random() < 0.8:
                    payment = Payment(new_order.buyer, order_id)
                    self.payment_request.append((payment, order_id, new_order.store_id, new_order.buyer))
                else:
                    # pending订单可用于取消测试
                    self.pending_orders.append((order_id, new_order.buyer))
            
            # 定期处理批量操作和统计
            if self.new_order_i % 100 == 0 or self.new_order_i == len(self.new_order_request):
                # 2. 批量付款，只有付款成功后才加入paid_orders
                for payment, order_id, store_id, buyer in self.payment_request:
                    before = time.time()
                    ok = payment.run()
                    after = time.time()
                    self.time_payment = self.time_payment + after - before
                    self.payment_i = self.payment_i + 1
                    if ok:
                        self.payment_ok = self.payment_ok + 1
                        # 只有付款成功后才加入paid_orders，用于后续发货
                        self.paid_orders.append((order_id, store_id, buyer))
                self.payment_request = []
                
                # 3. 卖家发货（随机选择70%的已付款订单发货）
                orders_to_ship = []
                for order_id, store_id, buyer in self.paid_orders[:]:
                    if random.random() < 0.7:
                        seller = self.workload.sellers.get(store_id)
                        if seller:
                            ship_order = ShipOrder(seller, order_id)
                            self.ship_order_request.append((ship_order, order_id, store_id, buyer))
                            orders_to_ship.append((order_id, store_id, buyer))
                
                # 从paid_orders中移除待发货的订单
                for order_info in orders_to_ship:
                    if order_info in self.paid_orders:
                        self.paid_orders.remove(order_info)
                
                for ship_order, order_id, store_id, buyer in self.ship_order_request:
                    before = time.time()
                    ok = ship_order.run()
                    after = time.time()
                    self.time_ship_order = self.time_ship_order + after - before
                    self.ship_order_i = self.ship_order_i + 1
                    if ok:
                        self.ship_order_ok = self.ship_order_ok + 1
                        # 只有发货成功后才加入shipped_orders，用于后续收货
                        self.shipped_orders.append((order_id, buyer))
                self.ship_order_request = []
                
                # 4. 买家确认收货（随机选择80%的已发货订单确认收货）
                orders_to_receive = []
                for order_id, buyer in self.shipped_orders[:]:
                    if random.random() < 0.8:
                        receive_order = ReceiveOrder(buyer, order_id)
                        self.receive_order_request.append((receive_order, order_id, buyer))
                        orders_to_receive.append((order_id, buyer))
                
                # 从shipped_orders中移除待收货的订单
                for order_info in orders_to_receive:
                    if order_info in self.shipped_orders:
                        self.shipped_orders.remove(order_info)
                
                for receive_order, order_id, buyer in self.receive_order_request:
                    before = time.time()
                    ok = receive_order.run()
                    after = time.time()
                    self.time_receive_order = self.time_receive_order + after - before
                    self.receive_order_i = self.receive_order_i + 1
                    if ok:
                        self.receive_order_ok = self.receive_order_ok + 1
                self.receive_order_request = []
                
                # 5. 买家取消订单（随机选择50%的pending订单取消）
                orders_to_cancel = []
                for order_id, buyer in self.pending_orders[:]:
                    if random.random() < 0.5:
                        cancel_order = CancelOrder(buyer, order_id)
                        self.cancel_order_request.append(cancel_order)
                        orders_to_cancel.append((order_id, buyer))
                
                # 从pending_orders中移除已取消的订单
                for order_info in orders_to_cancel:
                    if order_info in self.pending_orders:
                        self.pending_orders.remove(order_info)
                
                for cancel_order in self.cancel_order_request:
                    before = time.time()
                    ok = cancel_order.run()
                    after = time.time()
                    self.time_cancel_order = self.time_cancel_order + after - before
                    self.cancel_order_i = self.cancel_order_i + 1
                    if ok:
                        self.cancel_order_ok = self.cancel_order_ok + 1
                self.cancel_order_request = []
                
                # 6. 随机查询订单（每100个订单中随机查询10次）
                from fe.access.buyer import Buyer
                from fe import conf
                for _ in range(min(10, self.workload.buyer_num)):
                    # 随机选择一个买家进行查询
                    buyer_no = random.randint(1, self.workload.buyer_num)
                    buyer_id, buyer_password = self.workload.to_buyer_id_and_password(buyer_no)
                    buyer = Buyer(url_prefix=conf.URL, user_id=buyer_id, password=buyer_password)
                    query_orders = QueryOrders(buyer)
                    self.query_orders_request.append(query_orders)
                
                for query_orders in self.query_orders_request:
                    before = time.time()
                    ok, order_count = query_orders.run()
                    after = time.time()
                    self.time_query_orders = self.time_query_orders + after - before
                    self.query_orders_i = self.query_orders_i + 1
                    if ok:
                        self.query_orders_ok = self.query_orders_ok + 1
                self.query_orders_request = []
                
                # 随机搜索测试（每100个订单中随机执行5次搜索）
                for _ in range(min(5, self.workload.buyer_num)):
                    search_op = self.workload.get_search()
                    before = time.time()
                    ok, total_count = search_op.run()
                    after = time.time()

                    self.time_search += after - before
                    self.search_i += 1
                    if ok:
                        self.search_ok += 1

                # 更新统计信息
                self.workload.update_stat(
                    self.new_order_i,
                    self.payment_i,
                    self.ship_order_i,
                    self.receive_order_i,
                    self.cancel_order_i,
                    self.query_orders_i,
                    self.new_order_ok,
                    self.payment_ok,
                    self.ship_order_ok,
                    self.receive_order_ok,
                    self.cancel_order_ok,
                    self.query_orders_ok,
                    self.time_new_order,
                    self.time_payment,
                    self.time_ship_order,
                    self.time_receive_order,
                    self.time_cancel_order,
                    self.time_query_orders,
                    # 可选: 若 update_stat 支持, 可加入如下三项
                    # self.search_i,
                    # self.search_ok,
                    # self.time_search,
                )

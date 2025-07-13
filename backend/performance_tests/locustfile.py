from locust import HttpUser, task, between
import random


class BarcodeAPIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """用户开始时的初始化"""
        # 可以在这里添加登录逻辑
        pass

    @task(3)
    def get_barcodes(self):
        """获取条码列表"""
        self.client.get("/api/barcodes/")

    @task(2)
    def get_barcode_detail(self):
        """获取单个条码详情"""
        # 假设有一个条码ID为1的记录
        self.client.get("/api/barcodes/1/")

    @task(1)
    def create_barcode(self):
        """创建新条码"""
        barcode_data = {
            "code": f"TEST{random.randint(1000, 9999)}",
            "description": f"Test barcode {random.randint(1, 100)}",
            "barcode_type": "CODE128",
        }
        self.client.post("/api/barcodes/", json=barcode_data)

    @task(2)
    def search_barcodes(self):
        """搜索条码"""
        search_term = random.choice(["test", "code", "barcode"])
        self.client.get(f"/api/barcodes/search/?q={search_term}")

    @task(1)
    def get_statistics(self):
        """获取统计信息"""
        self.client.get("/api/statistics/")

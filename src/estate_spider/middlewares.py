# src/estate_spider/middlewares.py

import requests
import logging

class ProxyMiddleware:
    def __init__(self, proxy_url):
        self.proxy_url = proxy_url
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_url=crawler.settings.get('PROXY_POOL_URL')
        )

    def process_request(self, request, spider):
        # 如果请求已经有了代理（比如 retry 重试时可能已经有了），跳过
        if request.meta.get('proxy'):
            return

        try:
            # 1. 请求 Docker 容器里的接口
            response = requests.get(f"{self.proxy_url}/get/", timeout=5)
            
            if response.status_code == 200:
                res_json = response.json()
                # jhao104 的返回格式中，ip 在 "proxy" 字段里
                proxy = res_json.get("proxy")
                
                if proxy:
                    # 2. 拼接协议头 (贝壳是 HTTPS，这里必须注意)
                    # 免费代理大多数只支持 HTTP，但部分能隧道转发 HTTPS
                    # 我们先设为 http://，让 Scrapy 自己去 connect
                    request.meta['proxy'] = f"http://{proxy}"
                    self.logger.debug(f"🛡️ [ProxyMiddleware] 装备代理: {proxy}")
                else:
                    self.logger.warning("⚠️ 代理池接口返回空，正在裸奔！")
        except Exception as e:
            self.logger.error(f"❌ 连接代理池服务失败: {e}")
            # 失败了不要抛异常，让它继续用本机 IP 跑，保证稳定性
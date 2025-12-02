# Scrapy settings for estate_spider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "estate_spider"

SPIDER_MODULES = ["estate_spider.spiders"]
NEWSPIDER_MODULE = "estate_spider.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "estate_spider (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "estate_spider.middlewares.EstateSpiderSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 禁用默认的 UserAgent 中间件
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    
    # ❌ 删除或注释掉下面这一行（这是导致报错的罪魁祸首）
    # 'estate_spider.middlewares.EstateSpiderDownloaderMiddleware': 543,

    # ✅ 必须改成你在 middlewares.py 里实际定义的类名
    # 如果你用的是 Docker 那个代理池，类名是 ProxyMiddleware
    # 'estate_spider.middlewares.ProxyMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'estate_spider.pipelines.DataCleaningPipeline': 200,
   'estate_spider.pipelines.MysqlPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# IP 池 API 地址 (对应 Docker 里的端口)
PROXY_POOL_URL = 'http://localhost:5010'

# 增加超时时间 (默认是 180秒，免费代理可能连不上，设短一点让它快速失败重试)
DOWNLOAD_TIMEOUT = 10 

# 失败重试次数 (免费代理极其不稳定，多试几次)
RETRY_TIMES = 5


# src/estate_spider/settings.py

# --- 🎭 Playwright 核心配置 ---

# 1. 启用 Playwright 下载处理器
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# 2. 必须切换到 Asyncio 核心（Playwright 是异步的）
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# 3. 浏览器启动参数
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # ⚠️ 设为 False！让你能看到浏览器弹出来，方便手动过验证码
    "timeout": 20 * 1000,  # 20秒超时
    "args": [
        "--disable-blink-features=AutomationControlled", # 隐藏自动化特征（防检测）
        "--no-sandbox",
    ]
}

# 4. 禁用默认 User-Agent 中间件 (Playwright 会自动管理)
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# 5. 关掉之前的那些 Cookie 和 Header 配置，Playwright 不需要手动塞这些
COOKIES_ENABLED = False # 交给浏览器自己管
ROBOTSTXT_OBEY = False

# --- 🗄️ MySQL 数据库配置 ---
# 对应 docker-compose.yml 中的设置
MYSQL_HOST = 'localhost'
MYSQL_PORT = 53308        # 如果你本地的 MySQL 端口被占，在 docker-compose 里改成 3307 了，这里也要改成 3307
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'  # 对应 docker-compose 里的密码
MYSQL_DB = 'estate_db'

# --- 启用 Pipeline ---
# 确保清洗排在入库前面
ITEM_PIPELINES = {
   # 优先级 200: 先清洗数据 (DataCleaningPipeline)
   'estate_spider.pipelines.DataCleaningPipeline': 200,
   
   # 优先级 300: 后入库 (MysqlPipeline)
   'estate_spider.pipelines.MysqlPipeline': 300,
}
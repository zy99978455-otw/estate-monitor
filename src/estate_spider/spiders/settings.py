# 文件路径: src/estate_spider/settings.py

BOT_NAME = "estate_spider"

SPIDER_MODULES = ["estate_spider.spiders"]
NEWSPIDER_MODULE = "estate_spider.spiders"

# --- 🛠️ 修复 WinError 10013 报错 ---
# 禁用 Telnet 控制台 (在 Windows 开发环境下通常不需要)
TELNETCONSOLE_ENABLED = False

# --- 🚀 核心反爬配置 (必须生效) ---

# 1. 必须禁用 Robots 协议 (日志显示你之前是 True，必须改为 False)
ROBOTSTXT_OBEY = False

# 2. 伪装 User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'

# 3. 开启 Cookie
COOKIES_ENABLED = True

# 4. 请求头 (这里必须填入你刚才抓到的真实 Cookie)
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
   'Accept-Language': 'zh-CN,zh;q=0.9',
   'Cache-Control': 'no-cache',
   
   # ⬇️ 必须加上 Referer
   'Referer': 'https://cd.ke.com/',
   
   # ⬇️ 这里是你刚刚给我的完整 Cookie（注意：这必须是一行，不要手动换行！）
   'Cookie': 'lianjia_ssid=d8640791-d641-4b01-8a94-6552d6b96073; lianjia_uuid=f8c6164e-a50d-44fc-8209-3b1524b28d4e; crosSdkDT2019DeviceId=so7ukc--1vlpj0-oxmn24wwbi38fai-ttl921kli; hip=1sk4F6Y9cfCEcDoUSi_lGYlVUTkz-DZldMG39e1w-7akc4cUVS0GlqfiFgaFD6mYzBWsEWecvEiExdZ-MJU5Y8FY2IZvP_U5QOLZNjkyoYfPgedF1H7vHqxCyC08ArqQsCNAplfCyTf_jLcY5Ro-rapfrMXdbjlxBYjnR36V7UODGVkGSxo66rv3GMUU4cri-bjSLYJDe8wKWNMbMh_CVF2KNU6b_OQret_HtyDLfqJYScIaVGI%3D',
}

# 5. 下载延迟 (设置 3 秒，防止被封)
DOWNLOAD_DELAY = 3

# --- 基础配置 ---
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
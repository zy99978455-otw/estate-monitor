import scrapy
import json
from scrapy.http import HtmlResponse
from ..items import EstateItem

class BeikeSpider(scrapy.Spider):
    name = "beike"
    allowed_domains = ["cd.ke.com"]
    
    # ============================================================
    # 🔧 最终确认配置
    # ============================================================
    
    # 1. 区域基准地址 (棕北)
    BASE_URL = "https://cd.ke.com/ershoufang/zongbei/"
    
    # 2. 筛选参数 (完全按照你的 URL)
    # co32: 最新发布
    # l2l3: 二室、三室
    # p5:   价格区间 (100-150万)
    FILTER_CODE = "co32l2l3p5"

    def start_requests(self):
            # 第 1 页 URL: https://cd.ke.com/ershoufang/zongbei/co32l2l3p5/
            first_page_url = f"{self.BASE_URL}{self.FILTER_CODE}/"
            
            yield scrapy.Request(
                first_page_url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "is_first_page": True, # 开启第一页人工验证
                },
                callback=self.parse
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        is_first_page = response.meta.get("is_first_page", False)

        # ============================================================
        # 🛑 第一页专属逻辑：人工干预 (只在第一次启动时触发)
        # ============================================================
        if is_first_page:
            print("="*60)
            print(f"🕵️‍♂️ [Playwright] 浏览器已启动！正在渲染第一页...")
            print("🚨🚨🚨 【人工干预时刻】 🚨🚨🚨")
            print("1. 请在浏览器中手动完成验证码。")
            print("2. 确认浏览器里已经出现了【房源列表】。")
            print("3. 确认无误后，代码将自动检测并开始跑全量数据...")
            print("="*60)

            # 智能轮询等待 (最多等 120秒)
            for i in range(20):
                try:
                    # 尝试寻找分页数据 div (这标志着页面加载完全成功)
                    await page.wait_for_selector('div.house-lst-page-box', timeout=6000)
                    print("🎉 检测到页面加载成功！开始自动化采集...")
                    break
                except:
                    print(f"⏳ ({i+1}/20) 等待人工过验证码...")
                    # 模拟鼠标轻微晃动，防止被判定为死链接
                    await page.mouse.move(100, 100)
        else:
            # 后续页面：只需要简单等待列表出现即可
            print(f"🔄 [自动翻页] 正在抓取: {response.url}")
            try:
                await page.wait_for_selector('ul.sellListContent', timeout=10000)
            except:
                print(f"⚠️ 警告: 页面加载超时 {response.url}")

        # ============================================================
        # 📥 数据提取逻辑
        # ============================================================
        content = await page.content()
        await page.close() # 抓完当前页就关闭这个 Page tab
        
        response = HtmlResponse(url=response.url, body=content, encoding='utf-8')
        house_list = response.css('ul.sellListContent li.clear')

        print(f"✅ [本页数据] 提取到 {len(house_list)} 条房源")

        for house in house_list:
            item = EstateItem()
            item['title'] = house.css('.title a::text').get()
            item['detail_url'] = house.css('.title a::attr(href)').get()
            item['community'] = house.css('.positionInfo a::text').re_first(r'(.+)')
            
            position_info = house.css('.positionInfo a::text').getall()
            item['region'] = "-".join(position_info[1:]) if len(position_info) > 1 else ""
            
            # ✨ 修复：合并 houseInfo 下的所有文本，防止抓到空值
            info_texts = house.css('.houseInfo *::text').getall()
            item['house_info'] = "".join(info_texts).strip()
            
            item['total_price'] = house.css('.totalPrice span::text').get()
            item['unit_price'] = house.css('.unitPrice span::text').get()

            yield item

        # ============================================================
        # 📑 自动翻页逻辑 (只在第一页触发)
        # ============================================================
        if is_first_page:
            # 1. 从 HTML 中提取分页数据
            # 贝壳的分页信息在 <div class="page-box ..." page-data='{"totalPage":5,"curPage":1}'>
            page_data_str = response.css('div.house-lst-page-box::attr(page-data)').get()
            
            if page_data_str:
                try:
                    page_data = json.loads(page_data_str)
                    total_page = page_data.get("totalPage", 0)
                    print(f"📚 [分页分析] 共检测到 {total_page} 页数据，开始生成后续任务...")

                    # 2. 循环生成后续页面的 Request
                    # 从第 2 页 到 第 total_page 页
                    for page_num in range(2, total_page + 1):
                        # 构造 URL: .../zongbei/pg2co32l2l3p5/
                        next_url = f"{self.BASE_URL}pg{page_num}{self.FILTER_CODE}/"
                        
                        yield scrapy.Request(
                            next_url,
                            meta={
                                "playwright": True,
                                "playwright_include_page": True,
                                "is_first_page": False, # 🚩 标记：后续页面不需要人工干预
                            },
                            callback=self.parse
                        )
                except Exception as e:
                    print(f"❌ 解析分页数据失败: {e}")
            else:
                print("⚠️ 未找到分页数据，可能只有 1 页，或被反爬拦截。")
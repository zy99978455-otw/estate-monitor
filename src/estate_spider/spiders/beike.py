import scrapy
import json
from scrapy.http import HtmlResponse
# 假设你的 items.py 在上一级目录
from ..items import EstateItem 

class BeikeSpider(scrapy.Spider):
    name = "beike"
    allowed_domains = ["cd.ke.com"]
    
    BASE_URL = "https://cd.ke.com/ershoufang/"
    REGIONS = ["zongbei", "yulin"]
    FILTER_CODE = "co32l2l3p5"

    def start_requests(self):
        # 1. 遍历区域列表 (修复 URL 拼接错误)
        for region in self.REGIONS:
            # 正确构造: .../ershoufang/zongbei/co32.../
            first_page_url = f"{self.BASE_URL}{region}/{self.FILTER_CODE}/"
            
            yield scrapy.Request(
                first_page_url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "is_first_page": True,
                    # 关键修复：传递当前区域，用于后续翻页拼接
                    "current_region": region, 
                    # 关键修复：指定 context_name，让所有页面共享同一个浏览器Session (保留验证码Cookie)
                    "playwright_context": "persistent_context", 
                },
                callback=self.parse
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        is_first_page = response.meta.get("is_first_page", False)
        # 取出当前区域
        current_region = response.meta.get("current_region")

        # --- 第一页人工干预逻辑 ---
        if is_first_page:
            print("="*60)
            print(f"🕵️‍♂️ [正在初始化区域]: {current_region}")
            print("🚨 如遇验证码，请在弹出的浏览器中手动完成！")
            print("="*60)

            try:
                # 等待列表容器出现
                await page.wait_for_selector('div.house-lst-page-box', timeout=60000) # 延长到60秒给人工留时间
                print("🎉 页面加载成功！")
            except:
                print("⚠️ 等待超时，可能被反爬或加载失败")

        else:
            print(f"🔄 [翻页中] {current_region} - {response.url}")
            try:
                await page.wait_for_selector('ul.sellListContent', timeout=10000)
            except:
                pass

        # --- 提取数据 ---
        content = await page.content()
        await page.close() # 关闭当前页签
        
        # 重新封装 Response
        response = HtmlResponse(url=response.url, body=content, encoding='utf-8')
        house_list = response.css('ul.sellListContent li.clear')
        
        print(f"✅ [{current_region}] 提取到 {len(house_list)} 条房源")

        for house in house_list:
            item = EstateItem()
            item['title'] = house.css('.title a::text').get()
            item['detail_url'] = house.css('.title a::attr(href)').get()
            item['community'] = house.css('.positionInfo a::text').re_first(r'(.+)')
            
            position_info = house.css('.positionInfo a::text').getall()
            item['region'] = "-".join(position_info[1:]) if len(position_info) > 1 else ""
            
            # 清理换行符
            raw_info = "".join(house.css('.houseInfo *::text').getall())
            item['house_info'] = raw_info.replace("\n", "").strip()
            
            item['total_price'] = house.css('.totalPrice span::text').get()
            item['unit_price'] = house.css('.unitPrice span::text').get()
            
            yield item

        # --- 自动翻页逻辑 ---
        if is_first_page:
            page_data_str = response.css('div.house-lst-page-box::attr(page-data)').get()
            
            if page_data_str:
                try:
                    page_data = json.loads(page_data_str)
                    total_page = page_data.get("totalPage", 0)
                    print(f"📚 [{current_region}] 共 {total_page} 页，开始生成任务...")

                    for page_num in range(2, total_page + 1):
                        # 修复 URL：带上 current_region
                        # 格式: .../ershoufang/zongbei/pg2co32.../
                        next_url = f"{self.BASE_URL}{current_region}/pg{page_num}{self.FILTER_CODE}/"
                        
                        yield scrapy.Request(
                            next_url,
                            meta={
                                "playwright": True,
                                "playwright_include_page": True,
                                "is_first_page": False,
                                "current_region": current_region, # 传递区域信息
                                "playwright_context": "persistent_context", # 保持 Session
                            },
                            callback=self.parse
                        )
                except Exception as e:
                    print(f"❌ 分页解析错误: {e}")
            else:
                print("⚠️ 未检测到分页信息")
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EstateItem(scrapy.Item):
    # --- 原始数据 (从网页直接抓下来的) ---
    title = scrapy.Field()
    community = scrapy.Field()
    region = scrapy.Field()
    house_info = scrapy.Field()  # 脏数据: "2室1厅 | 78.5平米 | 南"
    total_price = scrapy.Field() # 脏数据: " 158 "
    unit_price = scrapy.Field()  # 脏数据: "20,123元/平"
    detail_url = scrapy.Field()

    # --- 清洗后的数据 (存入 MySQL 的) ---
    rooms = scrapy.Field()       # 室 (int)
    halls = scrapy.Field()       # 厅 (int)
    area = scrapy.Field()        # 面积 (float)
    orientation = scrapy.Field() # 朝向 (str)
    price_total = scrapy.Field() # 总价 (float, 万)
    price_unit = scrapy.Field()  # 单价 (float, 元/平)
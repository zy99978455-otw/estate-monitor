# src/estate_spider/pipelines.py
import re
import pymysql

class DataCleaningPipeline:
    def process_item(self, item, spider):
        # --- 1. 清洗总价 ---
        try:
            # 原始: " 258 " -> 清洗后: 258.0
            raw_total = item.get('total_price', '')
            item['price_total'] = float(raw_total.strip())
        except:
            item['price_total'] = 0.0

        # --- 2. 清洗单价 ---
        try:
            # 原始: "29,888元/平" -> 清洗后: 29888.0
            raw_unit = item.get('unit_price', '')
            # 去掉逗号、单位
            clean_unit = raw_unit.replace(',', '').replace('元/平', '').strip()
            item['price_unit'] = float(clean_unit)
        except:
            item['price_unit'] = 0.0

        # --- 3. 深度拆解 house_info ---
        # 原始: "3室2厅 | 89.5平米 | 南 | 精装"
        raw_info = item.get('house_info', '')
        
        # 默认值
        item['rooms'] = 0
        item['halls'] = 0
        item['area'] = 0.0
        item['orientation'] = "未知"

        if raw_info:
            parts = [p.strip() for p in raw_info.split('|')]
            
            # A. 提取户型 (正则找 "X室Y厅")
            room_match = re.search(r'(\d+)室(\d+)厅', raw_info)
            if room_match:
                item['rooms'] = int(room_match.group(1))
                item['halls'] = int(room_match.group(2))
            
            # B. 提取面积 (找带 "平米" 的部分)
            for p in parts:
                if '平米' in p:
                    try:
                        area_str = p.replace('平米', '').strip()
                        item['area'] = float(area_str)
                    except:
                        pass
                    break
            
            # C. 提取朝向 (通常在第3位，但也可能变动，这里简单取第3段)
            if len(parts) >= 3:
                # 排除掉包含数字的段（防止把楼层当朝向）
                if not any(char.isdigit() for char in parts[2]):
                    item['orientation'] = parts[2]

        # --- 4. 控制台可视化打印 (Debug专用) ---
        print("-" * 60)
        print(f"🏠 小区: {item['community']}")
        print(f"📄 原始信息: {raw_info}")
        print(f"✨ 清洗结果: {item['rooms']}室 {item['halls']}厅 | {item['area']}平 | 朝向:{item['orientation']}")
        print(f"💰 价格清洗: 总价[{item['price_total']}万]  单价[{item['price_unit']}元/平]")
        print("-" * 60)

        return item
    
class MysqlPipeline:
    """
    负责将清洗后的结构化数据存入 MySQL 数据库
    """
    # 1. 初始化方法：从 settings.py 读取配置
    def __init__(self, host, user, password, db, port):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        
        # 确保在运行前安装了 pymysql
        if 'pymysql' not in globals():
            raise ImportError("请先安装 pymysql: pip install pymysql")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST'),
            user=crawler.settings.get('MYSQL_USER'),
            password=crawler.settings.get('MYSQL_PASSWORD'),
            db=crawler.settings.get('MYSQL_DB'),
            port=crawler.settings.get('MYSQL_PORT'),
        )

    # 2. 爬虫启动时：连接数据库并创建表
    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db,
            port=self.port,
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()
        
        # 核心：建表语句，字段必须与清洗后的 Item 对应
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS beike_house (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            community VARCHAR(100),
            region VARCHAR(100),
            
            rooms INT DEFAULT 0,
            halls INT DEFAULT 0,
            area FLOAT DEFAULT 0,
            orientation VARCHAR(50),
            price_total FLOAT DEFAULT 0,
            price_unit FLOAT DEFAULT 0,
            
            detail_url VARCHAR(255) UNIQUE,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.cursor.execute(create_table_sql)
        self.conn.commit()
        print("✅ [Pipeline] MySQL 连接成功且表已就绪！")

    # 3. 爬虫关闭时：断开连接
    def close_spider(self, spider):
        self.conn.close()

    # 4. 接收 Item：执行插入操作
    def process_item(self, item, spider):
        # 使用 INSERT IGNORE 避免重复插入 (基于 detail_url 的 UNIQUE 约束)
        sql = """
        INSERT IGNORE INTO beike_house 
        (title, community, region, rooms, halls, area, orientation, price_total, price_unit, detail_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(sql, (
                item.get('title'),
                item.get('community'),
                item.get('region'),
                item.get('rooms'),
                item.get('halls'),
                item.get('area'),
                item.get('orientation'),
                item.get('price_total'),
                item.get('price_unit'),
                item.get('detail_url')
            ))
            self.conn.commit()
            # 这里的打印可以在调试结束后删除
            print(f"💾 [MySQL] 已存储: {item.get('community')} ({item.get('price_total')}万)")
        except Exception as e:
            # 忽略重复插入的错误，只打印其他错误
            if 'Duplicate entry' not in str(e):
                print(f"❌ [MySQL] 插入失败: {e}")
            self.conn.rollback()
            
        return item
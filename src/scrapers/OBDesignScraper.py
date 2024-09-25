import sys
import os
from typing import List, Dict, Any
import logging
from tqdm import tqdm

# 將專案根目錄添加到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from src.base_scraper import BaseScraper
import time

class OBDesignScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.obdesign.com.tw/v2/official/SalePageCategory/487529?sortMode=Newest"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")

    def fetch_data(self, product_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info("開始獲取產品詳細資料...")
        driver = None

        try:
            driver = webdriver.Remote(
                command_executor='http://selenium:4444/wd/hub',
                options=self.chrome_options
            )

            
            for product_info in tqdm(product_list, desc="處理產品", unit="項"):
                self.logger.info(f"正在處理產品：{product_info['name']}")
                driver.get(product_info['url'])

                # 等待頁面加載完成
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # 找到所有尺寸表格
                tables = driver.find_elements(By.CSS_SELECTOR, 'table.common_size_table')
                for table in tables:
                    header = table.find_element(By.TAG_NAME, 'th').text.strip()
                    if header == '尺寸':
                        product_info['size_info'] = self.extract_table_data(table)
                    elif header == '試穿人員':
                        product_info['fitting_report'] = self.extract_table_data(table)

                self.logger.info(f"成功獲取產品 {product_info['name']} 的詳細資料")
        except Exception as e:
            self.logger.error(f"獲取產品詳細資料時發生錯誤：{str(e)}")
        finally:
            if driver:
                driver.quit()

        return product_list

    def extract_table_data(self, table) -> Dict[str, Dict[str, str]]:
        data = {}
        headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, 'th')]
        rows = table.find_elements(By.TAG_NAME, 'tr')[1:]  # 跳過表頭行
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if cells:
                key = cells[0].text.strip()
                row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells[1:], start=1)}
                data[key] = row_data
        return data

    def scrape_product_list(self):
       
        driver = None
        try:
            driver = webdriver.Remote(
                command_executor='http://selenium:4444/wd/hub',
                options=self.chrome_options
            )
            
            self.logger.info("正在訪問網頁...")
            driver.get(self.base_url)
            
            # 等待頁面加載完成
            self.logger.info("等待頁面加載...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 滾動到頁面底部
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 等待頁面加載
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # 等待產品元素加載完成
            self.logger.info("等待產品元素加載...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.sc-dGcaAO.gBGVJh.product-card__vertical.product-card__vertical--hover.new-product-card"))
            )
            
            products = []
            # 收集所有產品元素
            self.logger.info("開始收集產品信息...")
            product_elements = driver.find_elements(By.CSS_SELECTOR, "a.sc-dGcaAO.gBGVJh.product-card__vertical.product-card__vertical--hover.new-product-card")
            self.logger.info(f"找到 {len(product_elements)} 個產品元素")
            
            for index, product_element in enumerate(product_elements):
                try:
                    product_url = product_element.get_attribute("href")
                    product_name = product_element.find_element(By.CSS_SELECTOR, "div.sc-iGtWQ.cUlTYm").text
                    
                    products.append({
                        "name": product_name,
                        "url": product_url
                    })
                    self.logger.info(f"成功處理第 {index + 1} 個產品")
                except Exception as e:
                    self.logger.error(f"處理第 {index + 1} 個產品時發生錯誤：{str(e)}")
                    continue
            
            return products
        except Exception as e:
            self.logger.error(f"爬取過程中發生錯誤：{str(e)}")
            return []
        finally:
            if driver:
                driver.quit()

# 使用示例
if __name__ == "__main__":
    MONGODBNAME = "obdesign"
    LANCENAME = "obdesign"
    scraper = OBDesignScraper()
    
    categoryDict = {
        '上衣': 'tops',
        '褲子': 'pants',
        '裙子': 'skirts',
        '外套': 'outerwear',
        '鞋子': 'shoes',
        '配飾': 'accessories'
    }
    scraper.mongo_to_lancedb(MONGODBNAME, LANCENAME, categoryDict)
    exit()
    results = scraper.scrape_product_list()
    print(f"爬取到 {len(results)} 個產品")
    
    product_data = scraper.fetch_data(results)
    
    scraper.save_to_mongo(product_data, "obdesign")
    
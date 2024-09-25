import abc
from typing import List, Dict, Any
from pymongo import MongoClient, UpdateOne
import logging
from tqdm import tqdm
from collections import defaultdict

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(abc.ABC):
    def __init__(self):
        self.mongo_client = None

    @abc.abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        pass

    def save_to_mongo(self, product_list: List[Dict[str, Any]], collection_name: str):
        try:
            # 連接到MongoDB容器
            self.client = MongoClient('mongodb://mongo:27017/')
            db = self.client['scraper_db']
            # 檢查集合是否存在，如果不存在則創建
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"已創建新的集合: {collection_name}")
            
            collection = db[collection_name]
            # 使用tqdm顯示進度
            for product in tqdm(product_list, desc="保存產品到數據庫", unit="件"):
                result = collection.update_one(
                    {'url': product['url']},  # 使用URL作為唯一標識符
                    {'$set': product},
                    upsert=True
                )

                if result.upserted_id:
                    logger.info(f"新增產品: {product['name']}")
                elif result.modified_count:
                    logger.info(f"更新產品: {product['name']}")
                else:
                    logger.info(f"產品已存在且無需更新: {product['name']}")

            logger.info(f"成功保存 {len(product_list)} 個產品到數據庫")

        except Exception as e:
            logger.error(f"處理數據時發生錯誤：{str(e)}")

        finally:
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("MongoDB連接已關閉")

    
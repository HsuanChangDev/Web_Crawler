from pymongo import MongoClient
import pandas as pd
import os

# 連接到 MongoDB
client = MongoClient('mongodb://mongo:27017/')

# 選擇資料庫和集合
db = client['scraper_db']
collection = db['obdesign']

# 查詢所有文件並只獲取 name 欄位
cursor = collection.find({}, {'name': 1, '_id': 0})

# 將查詢結果轉換為 list
data = list(cursor)

# 創建 DataFrame
df = pd.DataFrame(data)

# 將 DataFrame 匯出為 CSV 檔案
df.to_csv('names.csv', index=False, encoding='utf-8-sig')

# 設置文件權限
os.chmod('names.csv', 0o777)

print("資料已匯出至 names.csv")

# 關閉連接
client.close()
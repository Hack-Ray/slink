# Slink - URL Shortener

一個基於 FastAPI 的 URL 縮短服務，具有以下功能：

- URL 縮短
- 點擊統計
- URL 安全性檢查
- 自動過期機制
- Redis 快取支持

## 安裝

1. 克隆專案
2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 設置環境變數（複製 .env.example 到 .env 並修改）
4. 運行服務：
   ```bash
   uvicorn app.main:app --reload
   ```

## API 端點

- POST /shorten - 創建短網址
- GET /{short_code} - 重定向到原始網址
- GET /stats/{short_code} - 獲取點擊統計

## 技術棧

- FastAPI
- PostgreSQL
- Redis

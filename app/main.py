import os
import json
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv


from .db.session import get_db, engine
from .db import models
from .services.validator import validate_url
from .services.shortener import create_short_url
from .cache.redis import get_url_mapping, increment_click_count, get_click_stats

load_dotenv()

# 創建資料庫表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Slink - URL Shortener")

# 設置靜態文件和模板
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首頁"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/shorten")
async def shorten_url(url: str = Form(...), db: Session = Depends(get_db)):
    """創建短網址"""
    # 驗證 URL
    is_safe, error_message = validate_url(url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=error_message)

    # 創建短網址
    short_url = create_short_url(db, url)
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    return {
        "short_url": f"{base_url}/{short_url.short_code}",
        "expires_at": short_url.expires_at
    }

@app.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    """重定向到原始網址"""
    # 先從 Redis 查詢
    url_data = get_url_mapping(short_code)
    if not url_data:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # 增加點擊次數
    increment_click_count(short_code)

    # 重定向到原始網址
    return RedirectResponse(url=url_data["original_url"])

@app.get("/stats/{short_code}", response_class=HTMLResponse)
async def get_stats(short_code: str, request: Request, db: Session = Depends(get_db)):
    """獲取短網址統計信息"""
    stats = get_click_stats(short_code)
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "short_code": short_code,
            "stats": json.dumps(stats)
        }
    )

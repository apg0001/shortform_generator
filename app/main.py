# app/main.py
import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 네 기존 코드 임포트 (오타 수정: crwaler -> crawler)
from .summarizer import Summarizer
from .crawler import Crawler

# 앱 생성
app = FastAPI(title="URL → 본문 크롤링 → 요약", version="0.1.0")

# 정적/템플릿
BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 싱글톤 인스턴스 (모델 로딩 비용↓)
crawler = Crawler()
summarizer = Summarizer()  # 기본 모델: lcw99/t5-base-korean-text-summary

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize", response_class=HTMLResponse)
def summarize(
    request: Request,
    url: str = Form(...),
    max_length: int = Form(96),          # 한 번에 뽑는 요약 길이 (토큰 기준)
    chunk_min_chars: int = Form(500),    # 문단을 이 글자수 이상이 되도록 묶어서 요약
):
    # 1) 본문 크롤링
    content = crawler.extract_article(url)
    if not content or content.startswith("[ERROR]"):
        raise HTTPException(status_code=422, detail="기사 본문 추출 실패")

    # 2) 문단 묶음 요약 (문단은 이미 "\n\n"로 구분된 상태라고 했으니 그대로 사용)
    try:
        script = summarizer.summarize_aggregated(
            content, min_chars=chunk_min_chars, max_length=max_length
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 실패: {e}")

    # 3) 결과 화면
    # sample = content[:700] + ("..." if len(content) > 700 else "")
    sample = content
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "url": url,
            "summary": script,           # 여러 묶음 요약을 "\n\n"로 연결한 결과
            "original_preview": sample,
            "length": len(content),
        },
    )
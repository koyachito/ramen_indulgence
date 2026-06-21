from contextlib import asynccontextmanager
from datetime import date, datetime

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import get_stats, init_db, record_judgment, record_result
from .diagnosis import RAMEN_TYPES, diagnose, maps_url, x_share_url
from .models import DiagnosisInput


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="ラーメン免罪符", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"total": get_stats()["total"]},
    )


@app.get("/diagnosis", response_class=HTMLResponse)
async def diagnosis_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="diagnosis.html",
        context={"ramen_types": RAMEN_TYPES},
    )


@app.post("/result", response_class=HTMLResponse)
async def result(
    request: Request,
    current_hour: int = Form(..., ge=0, le=23),
    current_month: int = Form(..., ge=1, le=12),
    current_day: int = Form(..., ge=1, le=31),
    meals: int = Form(..., ge=0, le=5),
    walked: bool = Form(False),
    worked: bool = Form(False),
    ramen_type: str = Form(...),
):
    selected_ramen = ramen_type if ramen_type in RAMEN_TYPES else "その他"
    try:
        selected_date = date(2000, current_month, current_day)
    except ValueError:
        today = date.today()
        selected_date = date(2000, today.month, today.day)
    data = DiagnosisInput(
        current_hour=current_hour,
        meals=meals,
        walked=walked,
        worked=worked,
        current_date=selected_date,
        ramen_type=selected_ramen,
    )
    judgment = diagnose(data)
    record_result(judgment.result_type, selected_ramen, current_hour)
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": judgment,
            "ramen_type": selected_ramen,
            "share_url": x_share_url(judgment, selected_ramen, base_url),
            "maps_url": maps_url(selected_ramen),
        },
    )

@app.get("/result")
async def result_get_redirect():
    return RedirectResponse(url="/", status_code=303)

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html")


@app.get("/hidden-confession", response_class=HTMLResponse)
async def hidden_confession(request: Request):
    return templates.TemplateResponse(request=request, name="hidden_confession.html")


@app.post("/hidden-judgment", response_class=HTMLResponse)
async def hidden_judgment(request: Request):
    record_judgment("sleep")
    return templates.TemplateResponse(request=request, name="hidden_result.html")


@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request, hour: int | None = Query(None, ge=0, le=23)):
    labels = {
        "full": "完全免罪",
        "conditional": "条件付き免罪",
        "no_rice": "半ライス禁止付き免罪",
        "soup": "スープ残し推奨",
        "sleep": "今日は寝ろ（幻の判決）",
    }
    return templates.TemplateResponse(
        request=request,
        name="stats.html",
        context={
            "stats": get_stats(datetime.now().hour if hour is None else hour),
            "labels": labels,
            "ramen_types": RAMEN_TYPES,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

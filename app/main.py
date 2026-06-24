from contextlib import asynccontextmanager
from datetime import date, datetime
import os

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .choices import DIAGNOSIS_QUESTIONS, QUESTION_MESSAGES, VALID_CHOICE_VALUES
from .database import get_stats, init_db, record_judgment, record_result
from .diagnosis import RAMEN_TYPES, diagnose, maps_url, share_text, x_share_url
from .models import DiagnosisInput

PUBLIC_APP_URL = os.getenv(
    "APP_PUBLIC_URL", "https://ramen-indulgence.onrender.com/"
)


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
        context={"total": get_stats()["total"], "show_stats": False},
    )


@app.get("/diagnosis", response_class=HTMLResponse)
async def diagnosis_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="diagnosis.html",
        context={
            "show_stats": False,
            "diagnosis_questions": DIAGNOSIS_QUESTIONS,
            "question_messages": QUESTION_MESSAGES,
        },
    )


@app.post("/result", response_class=HTMLResponse)
async def result(
    request: Request,
    current_hour: int = Form(..., ge=0, le=23),
    current_month: int = Form(..., ge=1, le=12),
    current_day: int = Form(..., ge=1, le=31),
    meals: int = Form(..., ge=0, le=4),
    ramen_count_today: int = Form(0, ge=0, le=3),
    achievement: str = Form(...),
    mood: str = Form(...),
    after_plan: str = Form(...),
    reason_not_to_eat: str = Form(...),
    ramen_type: str = Form(...),
    forgiveness_style: str = Form(...),
    reroll: bool = Form(False),
):
    submitted = {
        "achievement": achievement,
        "mood": mood,
        "after_plan": after_plan,
        "reason_not_to_eat": reason_not_to_eat,
        "ramen_type": ramen_type,
        "forgiveness_style": forgiveness_style,
    }
    if any(value not in VALID_CHOICE_VALUES[name] for name, value in submitted.items()):
        return RedirectResponse(url="/diagnosis", status_code=303)
    try:
        selected_date = date(2000, current_month, current_day)
    except ValueError:
        today = date.today()
        selected_date = date(2000, today.month, today.day)

    data = DiagnosisInput(
        current_hour=current_hour,
        current_month=selected_date.month,
        current_day=selected_date.day,
        meals=meals,
        ramen_count_today=ramen_count_today if meals >= 3 else 0,
        achievement=achievement,
        mood=mood,
        after_plan=after_plan,
        reason_not_to_eat=reason_not_to_eat,
        ramen_type=ramen_type,
        forgiveness_style=forgiveness_style,
    )
    judgment = diagnose(data)

    if not reroll:
        record_result(data, judgment)
    stats = get_stats()
    post_text = share_text(judgment, PUBLIC_APP_URL)
    response = templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": judgment,
            "form_data": data,
            "share_text": post_text,
            "share_url": x_share_url(post_text),
            "maps_url": maps_url(judgment.ramen_label),
            "total": stats["total"],
            "show_stats": True,
        },
    )
    return response


@app.get("/result")
async def result_get_redirect():
    return RedirectResponse(url="/", status_code=303)


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(
        request=request, name="about.html", context={"show_stats": False}
    )


@app.get("/hidden-confession", response_class=HTMLResponse)
async def hidden_confession(request: Request):
    return templates.TemplateResponse(
        request=request, name="hidden_confession.html", context={"show_stats": True}
    )


@app.post("/hidden-judgment", response_class=HTMLResponse)
async def hidden_judgment(request: Request):
    record_judgment("banzai")
    post_text = (
        "ラーメン免罪符の奥で、特別な祝福を授かりました。\n\n"
        "祝福結果：ラーメンばんざい！\n\n"
        "今日も堂々と、ラーメンを愛します。\n"
        "ラーメンばんざい！\n\n"
        f"{PUBLIC_APP_URL}\n"
        "#ラーメン免罪符"
    )
    return templates.TemplateResponse(
        request=request,
        name="hidden_result.html",
        context={
            "show_stats": True,
            "share_url": x_share_url(post_text),
            "total": get_stats()["total"],
        },
    )


@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request, hour: int | None = Query(None, ge=0, le=23)):
    labels = {
        "forgiven": "完全なる赦し",
        "worry": "見守りの赦し",
        "angry": "反省を促す赦し",
        "ogre": "やむなき慈悲の赦し",
        "sleep": "今日は寝ろ（幻の助言）",
        "banzai": "ラーメンばんざい！（どこかに隠された祝福）",
    }
    return templates.TemplateResponse(
        request=request,
        name="stats.html",
        context={
            "stats": get_stats(hour),
            "labels": labels,
            "ramen_types": RAMEN_TYPES,
            "show_stats": True,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

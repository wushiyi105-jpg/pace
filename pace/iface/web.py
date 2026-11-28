"""FastAPI + Jinja2：本周课表、配速表、周完成率。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..adapters.store import SqliteStore
from ..app.run import current, export, zone_table
from ..config import Settings

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Pace", version="1.0.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )
    store = store or SqliteStore(settings.db_path)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, w: int = 1) -> HTMLResponse:
        r = current(store)
        goal = store.goal()
        done = store.done_map()
        rows = [s for s in store.list_sessions() if s.week == w]
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"r": r, "goal": goal, "week": w, "rows": rows, "done": done,
             "table": zone_table(goal) if goal else {}, "today": date.today().isoformat()},
        )

    @app.get("/week/{w}.ics", response_class=PlainTextResponse)
    def week_ics(w: int) -> PlainTextResponse:
        try:
            return PlainTextResponse(export(store, w), media_type="text/calendar; charset=utf-8")
        except ValueError:
            return PlainTextResponse("先设目标", status_code=404)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "sessions": len(store.list_sessions())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)


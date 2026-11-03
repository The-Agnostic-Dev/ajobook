from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import LoginRequired
from .config import Settings, load_settings
from .db import Base, make_engine, make_session_factory
from .routes import auth, dashboard, groups, members, payments
from .services import summary


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.seed_demo:
            from .seed import seed_demo

            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            with app.state.session_factory() as db:
                seed_demo(db)
        else:
            Base.metadata.create_all(engine)
        summary.clear()
        yield
        engine.dispose()

    app = FastAPI(title="Ajobook", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.state.session_factory = make_session_factory(engine)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.exception_handler(LoginRequired)
    async def _login_required(request: Request, exc: LoginRequired):
        return RedirectResponse(f"/login?next={exc.next_path}", status_code=303)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    for module in (auth, dashboard, groups, members, payments):
        app.include_router(module.router)
    return app


app = create_app()

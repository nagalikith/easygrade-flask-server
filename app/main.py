from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.core.settings import settings
from app.routers import assignments, auth, exec_code, sections, users


def create_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CORS_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

    app.include_router(exec_code.router)
    app.include_router(assignments.router)
    app.include_router(users.router)
    app.include_router(sections.router)
    app.include_router(auth.router)

    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        pass

    return app


app = create_app()

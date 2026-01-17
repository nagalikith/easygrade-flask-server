from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

import route_assn_rel
import route_exec_code
import route_user_rel
import route_sec_rel
import py_lib.user_auth as user_auth


class Config:
    CORS_ORIGIN = "http://localhost:3000"
    SECRET_KEY = "7A{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%"


def create_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[Config.CORS_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

    app.include_router(route_exec_code.router)
    app.include_router(route_assn_rel.router)
    app.include_router(route_user_rel.router)
    app.include_router(route_sec_rel.router)
    app.include_router(user_auth.bp)

    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        pass

    return app


app = create_app()

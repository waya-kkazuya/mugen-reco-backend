from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import dynamodb, table
from app.routers import (
    route_post,
    route_category,
    route_auth,
    route_comment,
    route_like,
)
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from app.schemas.common import SuccessMsg
from app.schemas.auth import CsrfSettings
from mangum import Mangum
import sys
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f"sys.path: {sys.path}")
print(f"sys.path: {sys.path}")

app = FastAPI()


app.include_router(route_auth.router)
app.include_router(route_post.router)
app.include_router(route_category.router)
app.include_router(route_comment.router)
app.include_router(route_like.router)

# CORSホワイトリスト、フロントエンドのURL
allowed_origins = [
    "http://localhost:5173",
    "https://www.mugen-reco.com",
    "https://mugen-reco.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


# exception_handlerで例外の整頓
@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", response_model=SuccessMsg)
def read_root():
    return {"message": "Welcome to Fast API"}


@app.get("/debug/sys-path")
def get_sys_path():
    return {"sys_path": sys.path}


@app.get("/ping-dynamodb")
def ping_dynamodb():
    try:
        tables = dynamodb.list_tables()
        return {"status": "ok", "tables": tables.get("TableNames", [])}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Lambdaエントリーポイント
handler = Mangum(app)

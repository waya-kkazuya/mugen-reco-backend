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
from app.exceptions import (
    PostRetrievalError,
    PostCreationError,
    DatabaseError,
    PasswordValidationError,
    UserCreationError,
    UserAlreadyExistsError,
    UsernameAlreadyExistsError,
    SignupError,
    UserAuthenticationError,
    LoginError,
    UserRetrievalError,
    PostUpdateError,
    PostOwnershipError,
    PostDeletionError,
    PostNotFoundError,
    UserPermissionError,
    CommentCreationError,
    CommentRetrievalError,
    CommentNotFoundError,
    CommentDeletionError,
    CommentOwnershipError,
    LikeRetrievalError,
    LikeAlreadyExistsError,
    LikeCreationError,
    LikeDeletionError,
    LikeNotFoundError,
    LikeOwnershipError,
    CategoryRetrievalError,
)
import datetime
from app.config.logging_config import LoggingConfig
import logging

# ログの設定は一度だけ
LoggingConfig.setup_logging()

# main.py用のloggerを取得
logger = logging.getLogger(__name__)  # または logger = logging.getLogger('main')

app = FastAPI()


# 例外を階層化する
@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """データベースエラーのハンドラー"""

    logger.error(
        "Database error occurred",
        extra={
            "event_type": "database_error",
            "error_message": exc.message,
            "url": str(request.url),
            "method": request.method,
            "severity": "high",
        },
        exc_info=True,
    )  # ✅ スタックトレース自動追加

    return JSONResponse(
        status_code=500,
        content={
            "error": "DATABASE_ERROR",
            "message": "データベース処理中にエラーが発生しました",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PostRetrievalError)
async def post_retrieval_error_handler(request: Request, exc: PostRetrievalError):
    logger.warning(f"Post retrieval error occurred: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=400,
        content={"error": "POST_RETRIEVAL_ERROR", "message": exc.message},
    )


@app.exception_handler(PostNotFoundError)
async def post_not_found_error_handler(request: Request, exc: PostNotFoundError):
    logger.info(f"Post not found: {exc.message}")
    return JSONResponse(
        status_code=404,  # Not Found
        content={
            "error": "POST_NOT_FOUND",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PostCreationError)
async def post_creation_error_handler(request: Request, exc: PostCreationError):
    """投稿作成エラーのハンドラー"""

    logger.warning(
        f"Post creation failed for user: {exc.username}, error: {exc.message}"
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": "POST_CREATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PostOwnershipError)
async def post_ownership_error_handler(request: Request, exc: PostOwnershipError):
    logger.warning(f"Post ownership error: {exc.message}")
    return JSONResponse(
        status_code=403,  # Forbidden
        content={
            "error": "POST_OWNERSHIP_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PasswordValidationError)
async def password_validation_error_handler(
    request: Request, exc: PasswordValidationError
):
    logger.warning(f"Password validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "PASSWORD_VALIDATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(UsernameAlreadyExistsError)
async def username_already_exists_error_handler(
    request: Request, exc: UsernameAlreadyExistsError
):
    logger.warning(f"Username already exists error: {exc.message}")
    return JSONResponse(
        status_code=409,  # Conflict
        content={
            "error": "USERNAME_ALREADY_EXISTS",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# ユーザー関連エラー
@app.exception_handler(UserCreationError)
async def user_creation_error_handler(request: Request, exc: UserCreationError):
    logger.warning(f"User creation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "USER_CREATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_error_handler(
    request: Request, exc: UserAlreadyExistsError
):
    logger.warning(f"User already exists error: {exc.message}")
    return JSONResponse(
        status_code=409,  # Conflict
        content={
            "error": "USER_ALREADY_EXISTS",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(SignupError)
async def signup_error_handler(request: Request, exc: SignupError):
    logger.warning(f"Signup error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "SIGNUP_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(UserAuthenticationError)
async def user_authentication_error_handler(
    request: Request, exc: UserAuthenticationError
):
    logger.warning(f"User authentication error: {exc.message}")
    return JSONResponse(
        status_code=401,  # Unauthorized
        content={
            "error": "AUTHENTICATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LoginError)
async def login_error_handler(request: Request, exc: LoginError):
    logger.warning(f"Login error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "LOGIN_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(UserRetrievalError)
async def user_retrieval_error_handler(request: Request, exc: UserRetrievalError):
    logger.warning(f"User retrieval error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "USER_RETRIEVAL_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# 投稿関連エラー（追加分）
@app.exception_handler(PostUpdateError)
async def post_update_error_handler(request: Request, exc: PostUpdateError):
    logger.warning(f"Post update error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "POST_UPDATE_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PostDeletionError)
async def post_deletion_error_handler(request: Request, exc: PostDeletionError):
    logger.warning(f"Post deletion error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "POST_DELETION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(PostNotFoundError)
async def post_not_found_error_handler(request: Request, exc: PostNotFoundError):
    logger.info(f"Post not found: {exc.message}")
    return JSONResponse(
        status_code=404,  # Not Found
        content={
            "error": "POST_NOT_FOUND",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(UserPermissionError)
async def user_permission_error_handler(request: Request, exc: UserPermissionError):
    logger.warning(f"User permission error: {exc.message}")
    return JSONResponse(
        status_code=403,  # Forbidden
        content={
            "error": "USER_PERMISSION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# コメント関連エラー
@app.exception_handler(CommentCreationError)
async def comment_creation_error_handler(request: Request, exc: CommentCreationError):
    logger.warning(f"Comment creation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "COMMENT_CREATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(CommentRetrievalError)
async def comment_retrieval_error_handler(request: Request, exc: CommentRetrievalError):
    logger.warning(f"Comment retrieval error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "COMMENT_RETRIEVAL_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(CommentNotFoundError)
async def comment_not_found_error_handler(request: Request, exc: CommentNotFoundError):
    logger.info(f"Comment not found: {exc.message}")
    return JSONResponse(
        status_code=404,  # Not Found
        content={
            "error": "COMMENT_NOT_FOUND",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(CommentDeletionError)
async def comment_deletion_error_handler(request: Request, exc: CommentDeletionError):
    logger.warning(f"Comment deletion error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "COMMENT_DELETION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(CommentOwnershipError)
async def comment_ownership_error_handler(request: Request, exc: CommentOwnershipError):
    logger.warning(f"Comment ownership error: {exc.message}")
    return JSONResponse(
        status_code=403,  # Forbidden
        content={
            "error": "COMMENT_OWNERSHIP_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# いいね関連エラー
@app.exception_handler(LikeRetrievalError)
async def like_retrieval_error_handler(request: Request, exc: LikeRetrievalError):
    logger.warning(f"Like retrieval error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "LIKE_RETRIEVAL_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LikeAlreadyExistsError)
async def like_already_exists_error_handler(
    request: Request, exc: LikeAlreadyExistsError
):
    logger.info(f"Like already exists: {exc.message}")
    return JSONResponse(
        status_code=409,  # Conflict
        content={
            "error": "LIKE_ALREADY_EXISTS",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LikeCreationError)
async def like_creation_error_handler(request: Request, exc: LikeCreationError):
    logger.warning(f"Like creation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "LIKE_CREATION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LikeDeletionError)
async def like_deletion_error_handler(request: Request, exc: LikeDeletionError):
    logger.warning(f"Like deletion error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "LIKE_DELETION_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LikeNotFoundError)
async def like_not_found_error_handler(request: Request, exc: LikeNotFoundError):
    logger.info(f"Like not found: {exc.message}")
    return JSONResponse(
        status_code=404,  # Not Found
        content={
            "error": "LIKE_NOT_FOUND",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(LikeOwnershipError)
async def like_ownership_error_handler(request: Request, exc: LikeOwnershipError):
    logger.warning(f"Like ownership error: {exc.message}")
    return JSONResponse(
        status_code=403,  # Forbidden
        content={
            "error": "LIKE_OWNERSHIP_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(CategoryRetrievalError)
async def category_retrieval_error_handler(
    request: Request, exc: CategoryRetrievalError
):
    logger.warning(f"Category retrieval error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "CATEGORY_RETRIEVAL_ERROR",
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """予期しない例外発生時のハンドラー（最後のフォールバック）"""

    logger.critical(
        "Unexpected error occurred in route",
        extra={
            "event_type": "unexpected_error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "url": str(request.url),
            "method": request.method,
            "client_ip": request.client.host,
            "requires_immediate_attention": True,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "予期しないエラーが発生しました。",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


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
    "https://infinite-reco-frontend.vercel.app",
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


@app.get("/ping-dynamodb")
def ping_dynamodb():
    try:
        tables = dynamodb.list_tables()
        return {"status": "ok", "tables": tables.get("TableNames", [])}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Lambdaエントリーポイント
handler = Mangum(app)

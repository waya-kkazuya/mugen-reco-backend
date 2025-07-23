from fastapi import APIRouter
from fastapi import HTTPException, Response, Request, Depends, status, Path
from app.cruds.crud_user import db_signup, db_login, db_get_user_by_username
from app.schemas.common import SuccessMsg
from app.schemas.auth import Csrf
from app.schemas.user import UserBody, UserInfo, UsernameCheckResponse
from app.auth.auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect
from app.auth.cookie_utils import CookieManager
from typing import Annotated
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


@router.get("/api/csrftoken", response_model=Csrf)
def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    logger.info("[ROUTE] Generating CSRF token")

    raw_token, signed_token = csrf_protect.generate_csrf_tokens()
    res = {"csrf_token": signed_token}

    logger.info("[ROUTE] CSRF token generated successfully")
    return res


@router.post("/api/register", response_model=UserInfo)
def signup(request: Request, user: UserBody, csrf_protect: CsrfProtect = Depends()):
    logger.info(f"[ROUTE] User signup request: username={user.username}")

    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効
    logger.debug("[ROUTE] CSRF token validated successfully")

    new_user = db_signup(user)
    logger.info(f"[ROUTE] User signup completed successfully: username={user.username}")
    return new_user


@router.post("/api/login", response_model=UserInfo)
def login(
    request: Request,
    response: Response,
    user: UserBody,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] User login request: username={user.username}")

    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効
    logger.debug("[ROUTE] CSRF token validated successfully")

    token, username = db_login(user)
    cookie_manager.set_jwt_cookie(response, token)

    logger.info(f"[ROUTE] User login completed successfully: username={username}")
    return {"username": username}


@router.post("/api/logout", response_model=SuccessMsg)
def logout(request: Request, response: Response, csrf_protect: CsrfProtect = Depends()):
    logger.info("[ROUTE] User logout request")

    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効
    logger.debug("[ROUTE] CSRF token validated successfully")

    # JWTのトークンを空に
    cookie_manager.clear_jwt_cookie(response)
    logger.info("[ROUTE] User logout completed successfully")
    return {"message": "Successfully logged-out"}


@router.get("/api/user", response_model=UserInfo)
def get_user_refresh_jwt(request: Request, response: Response):
    logger.info("[ROUTE] Get user and JWT refresh request")

    new_token, subject = auth.verify_update_jwt(request)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(f"[ROUTE] JWT refresh completed successfully: username={subject}")
    return {"username": subject}


@router.get(
    "/api/check-username/{username}",
    response_model=UsernameCheckResponse,
)
async def check_username_availability(
    username: Annotated[
        str,
        Path(
            title="ユーザー名",
            description="3-20文字の半角英数字、アンダースコア(_)、ハイフン(-)、ドット(.)が使用可能",
            regex=r"^[a-zA-Z0-9._-]{3,20}$",
            example="test.user_name-123",
        ),
    ],
) -> UsernameCheckResponse:
    """ユーザー名の利用可能性をチェック"""
    logger.info(f"[ROUTE] Checking username availability: username={username}")

    # ユーザー名が既に存在するかチェック
    user = db_get_user_by_username(username)

    if not user:
        is_available = True
        message = "このユーザー名は利用可能です"
        logger.info(f"[ROUTE] Username is available: username={username}")
    else:
        is_available = False
        message = "このユーザー名は既に使用されています"
        logger.info(f"[ROUTE] Username is not available: username={username}")

    return UsernameCheckResponse(is_available=is_available, message=message)

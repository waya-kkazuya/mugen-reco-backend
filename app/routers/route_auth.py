from fastapi import APIRouter
from fastapi import HTTPException, Response, Request, Depends, status, Path
from app.cruds.crud_user import db_signup, db_login, db_get_user_by_username
from app.schemas.common import SuccessMsg
from app.schemas.auth import Csrf
from app.schemas.user import UserBody, UserInfo, UsernameCheckResponse
from app.auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect
from app.cookie_utils import CookieManager
from typing import Annotated

router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


@router.get("/api/csrftoken", response_model=Csrf)
def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    raw_token, signed_token = csrf_protect.generate_csrf_tokens()
    res = {"csrf_token": signed_token}
    return res


@router.post("/api/register", response_model=UserInfo)
def signup(request: Request, user: UserBody, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効

    try:
        new_user = db_signup(user)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Signup failed")


@router.post("/api/login", response_model=UserInfo)
def login(
    request: Request,
    response: Response,
    user: UserBody,
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効

    token, username = db_login(user)
    print("username", username)
    cookie_manager.set_jwt_cookie(response, token)
    return {"username": username}


@router.post("/api/logout", response_model=SuccessMsg)
def logout(request: Request, response: Response, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効

    # JWTのトークンを空に
    cookie_manager.clear_jwt_cookie(response)
    return {"message": "Successfully logged-out"}


@router.get("/api/user", response_model=UserInfo)
def get_user_refresh_jwt(request: Request, response: Response):
    new_token, subject = auth.verify_update_jwt(request)
    cookie_manager.set_jwt_cookie(response, new_token)
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
    """
    ユーザー名の利用可能性をチェック

    - **username**: チェックするユーザー名

    Returns:
    - **is_available**: ユーザー名が利用可能かどうか
    - **message**: 結果メッセージ
    """

    try:
        # ユーザー名が既に存在するかチェック
        user = db_get_user_by_username(username)

        if not user:
            is_available = True
            message = "このユーザー名は利用可能です"
        else:
            is_available = False
            message = "このユーザー名は既に使用されています"

        return UsernameCheckResponse(is_available=is_available, message=message)

    except Exception as e:
        print(f"Unexpected error checking username {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー名の確認中にエラーが発生しました",
        )

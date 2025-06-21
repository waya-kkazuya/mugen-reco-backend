from fastapi import APIRouter
from fastapi import HTTPException, Response, Request, Depends
from cruds.crud_user import db_signup, db_login
from schemas.common import SuccessMsg
from schemas.auth import Csrf
from schemas.user import UserBody, UserInfo
from auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect

router = APIRouter()
auth = AuthJwtCsrf()


@router.get("/api/csrftoken", response_model=Csrf)
def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf()
    res = {"csrf_token": csrf_token}
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


@router.post("/api/login", response_model=SuccessMsg)
def login(
    request: Request,
    response: Response,
    user: UserBody,
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効

    token = db_login(user)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    return {"message": "Successfully logged-in"}


@router.post("/api/logout", response_model=SuccessMsg)
def logout(request: Request, response: Response, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)  # 例外が発生しなければCSRFトークンが有効

    # JWTのトークンを空に
    response.set_cookie(
        key="access_token", value="", httponly=True, samesite="none", secure=True
    )
    return {"message": "Successfully logged-out"}


@router.get("/api/user", response_model=UserInfo)
def get_user_refresh_jwt(request: Request, response: Response):
    new_token, subject = auth.verify_update_jwt(request)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    return {"username": subject}

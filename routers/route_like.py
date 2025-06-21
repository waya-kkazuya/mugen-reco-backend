from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
from schemas.common import SuccessMsg
from schemas.like import LikeStatusResponse, LikeCountResponse
from cruds.crud_like import (
    db_add_like,
    db_remove_like,
    db_get_like_status,
    db_get_like_count,
    db_get_like,
)
from starlette.status import HTTP_201_CREATED
from typing import List
from fastapi_csrf_protect import CsrfProtect
from auth_utils import AuthJwtCsrf

router = APIRouter()
auth = AuthJwtCsrf()


# ユーザー本人のいいねなので、認証が必要
@router.get("/posts/{post_id}/likes/status", response_model=LikeStatusResponse)
def get_like_status(request: Request, post_id: str):
    username = auth.verify_jwt(request)
    # username = 'loggined_test_user' # JWTから取得ダミー
    try:
        liked = db_get_like_status(post_id, username)
        return {"liked": liked}
    except Exception:
        raise HTTPException(status_code=500, detail="Like status check failed")


# エラーハンドリング必要 exception_handlerを設定する
@router.post("/posts/{post_id}/likes", response_model=SuccessMsg)
def like_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    # username = 'loggined_test_user' # JWTから取得ダミー
    res = db_add_like(post_id, username)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return {"message": "Like added successfully"}
    raise HTTPException(status_code=400, detail="Like already exists")


# 認可必要
# エラーハンドリング必要
@router.delete("/posts/{post_id}/likes", response_model=SuccessMsg)
def unlike_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    # username = 'loggined_test_user' # JWTから取得ダミー
    # 認可
    like = db_get_like(post_id, username)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    if like[username] != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this like"
        )

    res = db_remove_like(post_id, username)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return {"message": "Like removed successfully"}
    raise HTTPException(status_code=404, detail="Like not found")


# 誰ても投稿についているいいね数は見れる
@router.get("/posts/{post_id}/likes", response_model=LikeCountResponse)
def get_like_count(post_id: str):
    try:
        count = db_get_like_count(post_id)
        return {"like_count": count}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get like count")

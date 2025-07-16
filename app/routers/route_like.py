from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
from app.schemas.common import SuccessMsg
from app.schemas.like import LikeStatusResponse, LikeCountResponse, LikeToggleResponse
from app.cruds.crud_like import (
    db_add_like,
    db_remove_like,
    db_get_like_status,
    db_get_like_count,
    db_get_like,
)
from starlette.status import HTTP_201_CREATED
from typing import List
from fastapi_csrf_protect import CsrfProtect
from app.auth_utils import AuthJwtCsrf
from app.cookie_utils import CookieManager

router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


# ユーザー本人のいいねなので、認証が必要
@router.get("/api/posts/{post_id}/likes/status", response_model=LikeStatusResponse)
def get_like_status(request: Request, post_id: str):
    username = auth.verify_jwt(request)
    try:
        liked = db_get_like_status(post_id, username)
        return {"liked": liked}
    except Exception:
        raise HTTPException(status_code=500, detail="Like status check failed")


@router.post("/api/posts/{post_id}/like-toggle", response_model=LikeToggleResponse)
def toggle_like(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    try:
        # いいね状態:bool
        current_status = db_get_like_status(post_id, username)
        if current_status:
            # いいねを解除
            is_success = db_remove_like(post_id, username)
            if not is_success:
                raise HTTPException(status_code=500, detail="Failed to remove like")
            is_liked = False
            action = "removed"
        else:
            # いいねを追加
            is_success = db_add_like(post_id, username)
            if not is_success:
                raise HTTPException(status_code=409, detail="Like already exists")
            is_liked = True
            action = "added"

        # 総いいね数を取得
        like_count = db_get_like_count(post_id)

        cookie_manager.set_jwt_cookie(response, new_token)

        return {
            "message": f"Like {action} successfully",
            "is_liked": is_liked,
            "like_count": like_count,
            "post_id": post_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in toggle_like: {e}")
        raise HTTPException(status_code=500, detail="Like toggle failed")


# エラーハンドリング必要 exception_handlerを設定する
@router.post("/api/posts/{post_id}/likes", response_model=SuccessMsg)
def like_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    res = db_add_like(post_id, username)
    cookie_manager.set_jwt_cookie(response, new_token)
    if res:
        return {"message": "Like added successfully"}
    raise HTTPException(status_code=400, detail="Like already exists")


# 認可必要
# エラーハンドリング必要
@router.delete("/api/posts/{post_id}/likes", response_model=SuccessMsg)
def unlike_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    # 認可チェック
    like = db_get_like(post_id, username)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    if like[username] != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this like"
        )

    res = db_remove_like(post_id, username)
    cookie_manager.set_jwt_cookie(response, new_token)
    if res:
        return {"message": "Like removed successfully"}
    raise HTTPException(status_code=404, detail="Like not found")


# 誰ても投稿についているいいね数は見れる
@router.get("/api/posts/{post_id}/likes", response_model=LikeCountResponse)
def get_like_count(post_id: str):
    try:
        count = db_get_like_count(post_id)
        return {"like_count": count}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get like count")

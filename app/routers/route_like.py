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
from app.auth.auth_utils import AuthJwtCsrf
from app.auth.cookie_utils import CookieManager
import logging
from app.exceptions import LikeOwnershipError

logger = logging.getLogger(__name__)

router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


# ユーザー本人のいいねなので、認証が必要
@router.get("/api/posts/{post_id}/likes/status", response_model=LikeStatusResponse)
def get_like_status(request: Request, post_id: str):
    logger.info(f"[ROUTE] Getting like status: post_id={post_id}")

    username = auth.verify_jwt(request)
    logger.debug(
        f"[ROUTE] User authenticated for like status check: username={username}"
    )

    liked = db_get_like_status(post_id, username)

    logger.info(
        f"[ROUTE] Like status retrieved successfully: post_id={post_id}, username={username}, liked={liked}"
    )
    return {"liked": liked}


@router.post("/api/posts/{post_id}/like-toggle", response_model=LikeToggleResponse)
def toggle_like(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Toggling like: post_id={post_id}")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    logger.debug(f"[ROUTE] User authenticated for like toggle: username={username}")

    current_status = db_get_like_status(post_id, username)
    logger.debug(
        f"[ROUTE] Current like status: post_id={post_id}, username={username}, current_status={current_status}"
    )

    if current_status:
        # いいねを解除
        db_remove_like(post_id, username)
        is_liked = False
        action = "removed"
    else:
        # いいねを追加
        db_add_like(post_id, username)
        is_liked = True
        action = "added"

    # 総いいね数を取得
    like_count = db_get_like_count(post_id)

    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(
        f"[ROUTE] Like toggled successfully: post_id={post_id}, username={username}, action={action}, new_status={is_liked}"
    )
    return {
        "message": f"Like {action} successfully",
        "is_liked": is_liked,
        "like_count": like_count,
        "post_id": post_id,
    }


# エラーハンドリング必要 exception_handlerを設定する
@router.post("/api/posts/{post_id}/likes", response_model=SuccessMsg)
def like_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Adding like: post_id={post_id}")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    logger.debug(f"[ROUTE] User authenticated for like addition: username={username}")

    db_add_like(post_id, username)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(
        f"[ROUTE] Like added successfully: post_id={post_id}, username={username}"
    )
    return {"message": "Like added successfully"}


@router.delete("/api/posts/{post_id}/likes", response_model=SuccessMsg)
def unlike_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Removing like: post_id={post_id}")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    logger.debug(f"[ROUTE] User authenticated for like removal: username={username}")

    # 認可チェック
    like = db_get_like(post_id, username)
    if like["username"] != username:
        logger.warning(
            f"[ROUTE] Unauthorized like deletion attempt: post_id={post_id}, username={username}"
        )
        raise LikeOwnershipError(message="このいいねを削除する権限がありません。")

    db_remove_like(post_id, username)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(
        f"[ROUTE] Like removed successfully: post_id={post_id}, username={username}"
    )
    return {"message": "Like removed successfully"}


# 誰ても投稿についているいいね数は見れる
@router.get("/api/posts/{post_id}/likes", response_model=LikeCountResponse)
def get_like_count(post_id: str):
    logger.info(f"[ROUTE] Getting like count: post_id={post_id}")

    count = db_get_like_count(post_id)
    logger.info(
        f"[ROUTE] Like count retrieved successfully: post_id={post_id}, count={count}"
    )
    return {"like_count": count}

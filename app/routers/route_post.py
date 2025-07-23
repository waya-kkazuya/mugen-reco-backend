from fastapi import APIRouter, Query
from fastapi import Response, Request, HTTPException, Depends
from app.schemas.common import SuccessMsg
from app.schemas.post import PostBody, PostResponse, PaginatedPostsResponse
from ..cruds.crud_post import (
    db_get_single_post,
    db_delete_post_and_related_items,
)
from starlette.status import HTTP_201_CREATED
from typing import Optional
from app.auth.auth_utils import AuthJwtCsrf
from app.auth.cookie_utils import CookieManager
from fastapi_csrf_protect import CsrfProtect
import json
from app.services.post_service import PostService
import logging
from app.exceptions import PostOwnershipError, UserPermissionError

logger = logging.getLogger(__name__)
router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


@router.post("/api/posts", response_model=PostResponse)
def create_post(
    request: Request,
    response: Response,
    data: PostBody,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] POST /api/posts called")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    logger.info(f"[ROUTE] Authentication successful for user: {username}")

    res = PostService.create_post_with_like_info(username, data)

    response.status_code = HTTP_201_CREATED
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(f"[ROUTE] POST /api/posts completed successfully for user: {username}")

    return res


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts", response_model=PaginatedPostsResponse)
def get_posts_paginated(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    logger.info(f"[ROUTE] GET /api/posts called: limit={limit}")

    username = auth.get_current_user_optional(request)

    lek = json.loads(last_evaluated_key) if last_evaluated_key else None
    result = PostService.get_posts_with_like_info(
        limit=limit, last_evaluated_key=lek, username=username
    )
    # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
    if result["last_evaluated_key"]:
        result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])

    logger.info(f"[ROUTE] GET /api/posts completed: count={len(result['posts'])}")

    return result


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/category/{category}", response_model=PaginatedPostsResponse)
def get_posts_by_category_paginated(
    request: Request,
    category: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    logger.info(
        f"[ROUTE] Getting posts by category: category={category}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    username = auth.get_current_user_optional(request)
    logger.debug(f"[ROUTE] User authentication status: username={username}")

    lek = json.loads(last_evaluated_key) if last_evaluated_key else None
    result = PostService.get_posts_by_category_with_like_info(
        category, limit=limit, last_evaluated_key=lek, username=username
    )
    # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
    if result["last_evaluated_key"]:
        result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])

    logger.info(
        f"[ROUTE] Posts by category retrieved successfully: category={category}, count={len(result.get('posts', []))}"
    )
    return result


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/{post_id}", response_model=PostResponse)
def get_single_post(request: Request, post_id: str):
    logger.info(f"[ROUTE] Getting single post: post_id={post_id}")

    # ログイン中ならusernameを取得する
    username = auth.get_current_user_optional(request)
    logger.debug(f"[ROUTE] User authentication status: username={username}")

    result = PostService.get_single_post_with_like_info(post_id, username)
    logger.info(f"[ROUTE] Single post retrieved successfully: post_id={post_id}")
    return result


@router.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post(
    request: Request,
    response: Response,
    post_id: str,
    data: PostBody,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Updating post: post_id={post_id}")

    # 認証
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    # 認可: 投稿の所有者であることの確認
    post = db_get_single_post(post_id)
    if post["username"] != username:
        logger.warning(
            f"[ROUTE] Unauthorized post update attempt: post_id={post_id}, username={username}"
        )
        raise PostOwnershipError(message="この投稿を更新する権限がありません。")

    result = PostService.update_post_with_like_info(post_id, data, username)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(f"[ROUTE] Post updated successfully: post_id={post_id}")
    return result


# 特定のpost_idのpostを削除し、それについているcommmentもすべて削除する
# 削除権限のあるユーザーか、認可が必要 new_token, subject =で取得
@router.delete("/api/posts/{post_id}", response_model=SuccessMsg)
def delete_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Deleting post: post_id={post_id}")

    # 認証
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    logger.debug(f"[ROUTE] User authenticated for post deletion: username={username}")

    # 認可: 投稿の所有者であることの確認
    post = db_get_single_post(post_id)

    if post["username"] != username:
        logger.warning(
            f"[ROUTE] Unauthorized post deletion attempt: post_id={post_id}, username={username}, owner={post['username']}"
        )
        raise PostOwnershipError(message="この投稿を削除する権限がありません。")

    logger.info(
        f"[ROUTE] Authorization verified for post deletion: post_id={post_id}, username={username}"
    )

    result = db_delete_post_and_related_items(post_id)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(
        f"[ROUTE] Post deleted successfully: post_id={post_id}, username={username}"
    )
    return {"message": f"Post {post_id} deleted successfully."}


# ログインが必要=JWT認証が必要
@router.get("/api/users/{username}/posts", response_model=PaginatedPostsResponse)
def get_posts_by_user_paginated(
    request: Request,
    username: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    logger.info(
        f"[ROUTE] Getting posts by user: username={username}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    token_username = auth.verify_jwt(request)

    # 権限チェック：現在は自分の投稿のみ表示
    if token_username != username:
        logger.warning(
            f"[ROUTE] Unauthorized access attempt: token_username={token_username}, requested_username={username}"
        )
        raise UserPermissionError(message="自分の投稿のみ閲覧できます。")

    logger.info(
        f"[ROUTE] Authorization verified for user posts access: username={username}"
    )

    lek = json.loads(last_evaluated_key) if last_evaluated_key else None

    result = PostService.get_posts_by_user_with_like_info(
        limit=limit, last_evaluated_key=lek, username=username
    )

    # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
    if result["last_evaluated_key"]:
        result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])

    logger.info(
        f"[ROUTE] User posts retrieved successfully: username={username}, count={len(result.get('posts', []))}"
    )
    return result


# 無限スクロール対応版（オプション）
@router.get("/api/users/{username}/liked-posts", response_model=PaginatedPostsResponse)
def get_user_liked_posts_paginated(
    request: Request,
    username: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    """ユーザーがいいねした投稿一覧を取得（ページネーション対応）"""
    logger.info(
        f"[ROUTE] Getting user liked posts: username={username}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    token_username = auth.verify_jwt(request)

    if token_username != username:
        logger.warning(
            f"[ROUTE] Unauthorized liked posts access attempt: token_username={token_username}, requested_username={username}"
        )
        raise UserPermissionError(message="自分のいいね投稿のみ閲覧できます。")

    logger.debug(f"[ROUTE] User authenticated: token_username={token_username}")

    # last_evaluated_keyをparseする
    lek = json.loads(last_evaluated_key) if last_evaluated_key else None

    result = PostService.get_user_liked_posts_with_like_info(
        username=username, limit=limit, last_evaluated_key=lek
    )

    # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
    if result["last_evaluated_key"]:
        result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])

    logger.info(
        f"[ROUTE] User liked posts retrieved successfully: username={username}, count={len(result.get('posts', []))}"
    )
    return result

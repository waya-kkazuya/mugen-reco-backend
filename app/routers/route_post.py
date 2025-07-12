from fastapi import APIRouter, Query
from fastapi import Response, Request, HTTPException, Depends
from app.schemas.common import SuccessMsg
from app.schemas.post import PostBody, PostResponse, PaginatedPostsResponse
from ..cruds.crud_post import (
    db_get_single_post,
    db_delete_post_and_related_items,
)
from app.auth_utils import AuthJwtCsrf
from starlette.status import HTTP_201_CREATED
from typing import List, Optional
from fastapi_csrf_protect import CsrfProtect
import json
from app.services.post_service import PostService
from pydantic import ValidationError

router = APIRouter()
auth = AuthJwtCsrf()


@router.post("/api/posts", response_model=PostResponse)
def create_post(
    request: Request,
    response: Response,
    data: PostBody,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    try:
        res = PostService.create_post_with_like_info(username, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Create post failed")

    response.status_code = HTTP_201_CREATED
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return res
    raise HTTPException(status_code=404, detail="Create post failed")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts", response_model=PaginatedPostsResponse)
def get_posts_paginated(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    username = auth.get_current_user_optional(request)

    try:
        lek = json.loads(last_evaluated_key) if last_evaluated_key else None
        result = PostService.get_posts_with_like_info(
            limit=limit, last_evaluated_key=lek, username=username
        )
        # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
        if result["last_evaluated_key"]:
            result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get posts failed")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/category/{category}", response_model=PaginatedPostsResponse)
def get_posts_by_category_paginated(
    request: Request,
    category: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    username = auth.get_current_user_optional(request)

    try:
        lek = json.loads(last_evaluated_key) if last_evaluated_key else None
        result = PostService.get_posts_by_category_with_like_info(
            category, limit=limit, last_evaluated_key=lek, username=username
        )
        # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
        if result["last_evaluated_key"]:
            result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get posts by category failed")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/{post_id}", response_model=PostResponse)
def get_single_post(request: Request, post_id: str):
    # ログイン中ならusernameを取得する
    username = auth.get_current_user_optional(request)
    try:
        result = PostService.get_single_post_with_like_info(post_id, username)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get single post failed")

    if result:
        return result
    raise HTTPException(status_code=404, detail=f"Post of ID:{post_id} doesn't exist")


@router.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post(
    request: Request,
    response: Response,
    post_id: str,
    data: PostBody,
    csrf_protect: CsrfProtect = Depends(),
):
    # 認証
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    # 認可: 投稿の所有者であることの確認
    post = db_get_single_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 修正
    if post["username"] != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    try:
        result = PostService.update_post_with_like_info(post_id, data, username)
        print("like_infoを追加したあとのres")
        print(result)
    except ValidationError as e:
        print(f"❌ バリデーションエラー: {e.errors()}")
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        print("500エラー発生")
        raise HTTPException(status_code=500, detail="Update post failed")

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if result:
        return result
    raise HTTPException(status_code=404, detail="Update post failed")


# 特定のpost_idのpostを削除し、それについているcommmentもすべて削除する
# 削除権限のあるユーザーか、認可が必要 new_token, subject =で取得
@router.delete("/api/posts/{post_id}", response_model=SuccessMsg)
def delete_post(
    request: Request,
    response: Response,
    post_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    # 認証
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    # 認可: 投稿の所有者であることの確認
    post = db_get_single_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post["username"] != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    try:
        result = db_delete_post_and_related_items(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Delete post failed")

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if result:
        return {"message": f"Post {post_id} deleted successfully."}
    raise HTTPException(status_code=404, detail="Delete post failed")


# ログインが必要=JWT認証が必要
@router.get("/api/users/{username}/posts", response_model=PaginatedPostsResponse)
def get_posts_by_user_paginated(
    request: Request,
    username: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    token_username = auth.verify_jwt(request)

    # 権限チェック：現在は自分の投稿のみ表示
    if token_username != username:
        raise HTTPException(status_code=403, detail="You can only view your own posts")
    try:
        lek = json.loads(last_evaluated_key) if last_evaluated_key else None
        result = PostService.get_posts_by_user_with_like_info(
            limit=limit, last_evaluated_key=lek, username=username
        )
        # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
        if result["last_evaluated_key"]:
            result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get user's posts failed")


# 無限スクロール対応版（オプション）
@router.get("/api/users/{username}/liked-posts", response_model=PaginatedPostsResponse)
def get_user_liked_posts_paginated(
    request: Request,
    username: str,
    limit: int = Query(10, ge=1, le=50),
    last_evaluated_key: Optional[str] = None,
):
    """ユーザーがいいねした投稿一覧を取得（ページネーション対応）"""
    token_username = auth.verify_jwt(request)

    if token_username != username:
        raise HTTPException(
            status_code=403, detail="You can only view your own liked posts"
        )
    try:
        # last_evaluated_keyをparseする
        lek = json.loads(last_evaluated_key) if last_evaluated_key else None
        result = PostService.get_user_liked_posts_with_like_info(
            limit=limit, last_evaluated_key=lek, username=username
        )
        # last_evaluated_keyを文字列化、フロントでなくサーバー側で処理
        if result["last_evaluated_key"]:
            result["last_evaluated_key"] = json.dumps(result["last_evaluated_key"])
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [get_user_liked_posts_paginated] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get liked posts")

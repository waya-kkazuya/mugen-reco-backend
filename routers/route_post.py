from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
from schemas.common import SuccessMsg
from schemas.post import PostBody, PostResponse
from cruds.crud_post import (
    db_create_post,
    db_get_posts,
    db_get_single_post,
    db_update_post,
    db_get_posts_by_category,
    db_get_posts_by_user,
    db_delete_post_and_related_items,
)
from starlette.status import HTTP_201_CREATED
from typing import List
from fastapi_csrf_protect import CsrfProtect
from auth_utils import AuthJwtCsrf

router = APIRouter()
auth = AuthJwtCsrf()


# JWTとCSRFの処理は後で追加
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
        res = db_create_post(username, data)
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
@router.get("/api/posts", response_model=List[PostResponse])
def get_posts():
    try:
        res = db_get_posts()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get posts failed")

    return res


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/category/{category}", response_model=List[PostResponse])
def get_posts_by_category(category: str):
    try:
        res = db_get_posts_by_category(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get posts by category failed")

    if res:
        return res
    raise HTTPException(status_code=404, detail="No posts found in this category")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/{post_id}", response_model=PostResponse)
def get_single_post(post_id: str):
    try:
        res = db_get_single_post(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get single post failed")

    if res:
        return res
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

    if post["user_id"].replace("USER#", "") != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    try:
        res = db_update_post(post_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Update post failed")

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return res
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

    if post["user_id"].replace("USER#", "") != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    try:
        res = db_delete_post_and_related_items(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Delete post failed")

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return {"message": f"Post {post_id} deleted successfully."}
    raise HTTPException(status_code=404, detail="Delete post failed")


@router.get("/api/users/{user_id}/posts", response_model=List[PostResponse])
def get_posts_by_user(user_id: str):
    try:
        res = db_get_posts_by_user(user_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get user's posts failed")

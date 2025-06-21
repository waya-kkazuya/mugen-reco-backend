from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
from schemas.common import SuccessMsg
from schemas.comment import CommentBody, CommentResponse
from cruds.crud_comment import (
    db_create_comment,
    db_get_comments,
    db_delete_comment,
    db_get_single_comment,
)
from starlette.status import HTTP_201_CREATED
from typing import List
from fastapi_csrf_protect import CsrfProtect
from auth_utils import AuthJwtCsrf

router = APIRouter()
auth = AuthJwtCsrf()


@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
def create_post(
    request: Request,
    response: Response,
    post_id: str,
    data: CommentBody,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    # username = 'test' #本番環境では、JWTをdecodeして取得したsubjectを取得
    try:
        res = db_create_comment(username, post_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Create comment failed")

    response.status_code = HTTP_201_CREATED
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    print(res)
    if res:
        return res
    raise HTTPException(status_code=404, detail="Create comment failed")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: str):
    try:
        res = db_get_comments(post_id)
        print(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get comment failed")

    return res


@router.delete("/posts/{post_id}/comments/{comment_id}", response_model=SuccessMsg)
def delete_post(
    request: Request,
    response: Response,
    post_id: str,
    comment_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    # 認可: コメントの所有者か確認
    comment = db_get_single_comment(post_id, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["user_id"].replace("USER#", "") != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    try:
        res = db_delete_comment(post_id, comment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Delete comment failed")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return {"message": f"Comment {comment_id} deleted successfully."}
    raise HTTPException(status_code=404, detail="Delete comment failed")

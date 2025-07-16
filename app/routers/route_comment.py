from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
from app.schemas.common import SuccessMsg
from app.schemas.comment import CommentBody, CommentResponse
from app.cruds.crud_comment import (
    db_create_comment,
    db_get_comments,
    db_delete_comment,
    db_get_single_comment,
)
from app.auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect
from app.cookie_utils import CookieManager
from starlette.status import HTTP_201_CREATED
from typing import List
import logging
import traceback
import sys

# ✅ 基本設定（ファイルの最上部に配置）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

router = APIRouter()
auth = AuthJwtCsrf()
cookie_manager = CookieManager()


@router.post("/api/posts/{post_id}/comments", response_model=CommentResponse)
def create_comment(
    request: Request,
    response: Response,
    post_id: str,
    data: CommentBody,
    csrf_protect: CsrfProtect = Depends(),
):

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    logger.warning("🔍 === CREATE COMMENT START ===")
    logger.warning(f"🔍 Post ID: {post_id}")
    try:
        res = db_create_comment(username, post_id, data)
        print("db_create_comment後")
        response.status_code = HTTP_201_CREATED
        cookie_manager.set_jwt_cookie(response, new_token)
        return res
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"🔍 Error type: {type(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Create comment failed")


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: str):
    logger.warning("🔍 === GET COMMENTS START ===")
    logger.warning(f"🔍 Post ID: {post_id}")
    try:
        res = db_get_comments(post_id)
        print(res)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get comment failed")


@router.delete("/api/posts/{post_id}/comments/{comment_id}", response_model=SuccessMsg)
def delete_comment(
    request: Request,
    response: Response,
    post_id: str,
    comment_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )
    print(f"Looking for comment: post_id={post_id}, comment_id={comment_id}")

    # 認可: コメントの所有者か確認
    comment = db_get_single_comment(post_id, comment_id)
    print(f"Comment found: {comment}")  # デバッグログ
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["username"] != username:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    try:
        res = db_delete_comment(post_id, comment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Delete comment failed")

    cookie_manager.set_jwt_cookie(response, new_token)

    if res:
        return {"message": f"Comment {comment_id} deleted successfully."}
    raise HTTPException(status_code=404, detail="Delete comment failed")

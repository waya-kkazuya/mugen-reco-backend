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
from app.auth.auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect
from app.auth.cookie_utils import CookieManager
from starlette.status import HTTP_201_CREATED
from typing import List
import logging
import sys
from app.exceptions import CommentOwnershipError

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
    logger.info(f"[ROUTE] Creating comment: post_id={post_id}")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    logger.debug(
        f"[ROUTE] User authenticated for comment creation: username={username}"
    )

    res = db_create_comment(username, post_id, data)

    response.status_code = HTTP_201_CREATED
    cookie_manager.set_jwt_cookie(response, new_token)
    logger.info(
        f"[ROUTE] Comment created successfully: post_id={post_id}, comment_id={res.get('comment_id')}, username={username}"
    )
    return res


# ログインしなくても見れるようにするので、JWT認証は必要なし
@router.get("/api/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: str):
    logger.info(f"[ROUTE] Getting comments for post: post_id={post_id}")

    res = db_get_comments(post_id)

    logger.info(
        f"[ROUTE] Comments retrieved successfully: post_id={post_id}, count={len(res)}"
    )
    return res


@router.delete("/api/posts/{post_id}/comments/{comment_id}", response_model=SuccessMsg)
def delete_comment(
    request: Request,
    response: Response,
    post_id: str,
    comment_id: str,
    csrf_protect: CsrfProtect = Depends(),
):
    logger.info(f"[ROUTE] Deleting comment: post_id={post_id}, comment_id={comment_id}")

    new_token, username = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers
    )

    logger.debug(
        f"[ROUTE] User authenticated for comment deletion: username={username}"
    )

    # 認可: コメントの所有者か確認
    comment = db_get_single_comment(post_id, comment_id)
    if comment["username"] != username:
        logger.warning(
            f"[ROUTE] Unauthorized comment deletion attempt: post_id={post_id}, comment_id={comment_id}, username={username}, owner={comment['username']}"
        )
        raise CommentOwnershipError(message="このコメントを削除する権限がありません。")

    res = db_delete_comment(post_id, comment_id)
    cookie_manager.set_jwt_cookie(response, new_token)

    logger.info(
        f"[ROUTE] Comment deleted successfully: post_id={post_id}, comment_id={comment_id}, username={username}"
    )
    return {"message": f"Comment {comment_id} deleted successfully."}

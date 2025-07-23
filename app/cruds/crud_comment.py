from boto3.dynamodb.conditions import Key
from app.database import table
from typing import Union, List
import uuid
from datetime import datetime, timezone
from .crud_post import db_get_single_post
from fastapi import HTTPException
import logging
from botocore.exceptions import ClientError
from app.exceptions import (
    CommentCreationError,
    PostNotFoundError,
    CommentRetrievalError,
    CommentNotFoundError,
    CommentDeletionError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


def db_create_comment(username: str, post_id: str, data: dict) -> dict:
    logger.info(f"[CRUD] Creating comment: username={username}, post_id={post_id}")

    try:
        # 投稿の存在確認
        post = db_get_single_post(post_id)
        if not post:
            logger.warning(
                f"[CRUD] Comment creation failed - post not found: post_id={post_id}"
            )
            raise PostNotFoundError(message=f"投稿ID '{post_id}' が存在しません。")

        comment_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": f"POST#{post_id}",
            "SK": f"COMMENT#{comment_id}",
            "comment_id": comment_id,
            "content": data.comment,
            "user_id": f"USER#{username}",
            "created_at": now,  # commentの編集機能は作らないので、updated_atは不要
        }

        table.put_item(Item=item)

        result = {
            "comment_id": comment_id,
            "username": username,
            "post_id": post_id,
            "content": data.comment,
            "created_at": now,
        }

        logger.info(
            f"[CRUD] Comment created successfully: comment_id={comment_id}, post_id={post_id}"
        )
        return result

    except PostNotFoundError:
        # 投稿未発見エラーは再スロー
        raise

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB put_item error for comment: username={username}, post_id={post_id}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        if error_code in [
            "ThrottlingException",
            "ResourceNotFoundException",
            "InternalServerError",
        ]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise CommentCreationError(
                message="コメントの作成に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_create_comment: username={username}, post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise CommentCreationError(
            message="コメント作成で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_comments(post_id: str) -> List[dict]:
    logger.info(f"[CRUD] Getting comments for post: post_id={post_id}")

    try:
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"POST#{post_id}")
            & Key("SK").begins_with("COMMENT#")
        )
        items = response.get("Items", [])

        # コメントデータの変換
        comments = []
        for item in items:
            try:
                comment = {
                    "comment_id": item["comment_id"],
                    "username": item["user_id"].replace("USER#", ""),
                    "post_id": item["PK"].replace("POST#", ""),
                    "content": item["content"],
                    "created_at": item["created_at"],
                }
                comments.append(comment)
            except KeyError as e:
                logger.warning(
                    f"[CRUD] Skipping invalid comment data for post '{post_id}' - missing field: {str(e)}"
                )
                continue

        logger.info(
            f"[CRUD] Comments retrieved successfully: post_id={post_id}, count={len(comments)}"
        )
        return comments

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error for comments: post_id={post_id}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        if error_code in [
            "ThrottlingException",
            "ResourceNotFoundException",
            "InternalServerError",
        ]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise CommentRetrievalError(
                message=f"投稿'{post_id}'のコメント取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_comments: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise CommentRetrievalError(
            message=f"投稿'{post_id}'のコメント取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_single_comment(post_id: str, comment_id: str) -> dict:
    logger.info(
        f"[CRUD] Getting single comment: post_id={post_id}, comment_id={comment_id}"
    )

    try:
        response = table.get_item(
            Key={"PK": f"POST#{post_id}", "SK": f"COMMENT#{comment_id}"}
        )
        item = response.get("Item")

        if not item:
            logger.info(
                f"[CRUD] Comment not found: post_id={post_id}, comment_id={comment_id}"
            )
            raise CommentNotFoundError(
                message=f"コメントID '{comment_id}' が存在しません。"
            )

        try:
            comment = {
                "comment_id": item["comment_id"],
                "username": item["user_id"].replace("USER#", ""),
                "post_id": item["PK"].replace("POST#", ""),
                "content": item["content"],
                "created_at": item["created_at"],
            }

            logger.info(
                f"[CRUD] Single comment retrieved successfully: post_id={post_id}, comment_id={comment_id}"
            )
            return comment

        except KeyError as e:
            logger.warning(f"[CRUD] Invalid comment data - missing field: {str(e)}")
            raise CommentRetrievalError(
                message="コメントデータが不正です。管理者にお問い合わせください。",
                original_error=e,
            )

    except CommentNotFoundError:
        # CommentNotFoundErrorは再スロー
        raise

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB get_item error for comment: post_id={post_id}, comment_id={comment_id}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        if error_code in [
            "ThrottlingException",
            "ResourceNotFoundException",
            "InternalServerError",
        ]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise CommentRetrievalError(
                message="コメントの取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_single_comment: post_id={post_id}, comment_id={comment_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise CommentRetrievalError(
            message="コメント取得で予期しないエラーが発生しました。",
            original_error=e,
        )


# JWTとCSRFの認証必要
def db_delete_comment(post_id: str, comment_id: str) -> bool:
    logger.info(f"[CRUD] Deleting comment: post_id={post_id}, comment_id={comment_id}")

    try:
        response = table.delete_item(
            Key={"PK": f"POST#{post_id}", "SK": f"COMMENT#{comment_id}"},
            ReturnValues="ALL_OLD",  # 削除前のアイテムを返す（存在確認にも使える）
        )

        deleted_item = response.get("Attributes")

        if deleted_item:
            logger.info(
                f"[CRUD] Comment deleted successfully: post_id={post_id}, comment_id={comment_id}"
            )
            return True

        logger.info(
            f"[CRUD] Comment not found for deletion: post_id={post_id}, comment_id={comment_id}"
        )
        raise CommentNotFoundError(
            message=f"削除対象のコメントID '{comment_id}' が存在しません。"
        )

    except CommentNotFoundError:
        # CommentNotFoundErrorは再スロー
        raise

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB delete_item error for comment: post_id={post_id}, comment_id={comment_id}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        if error_code in [
            "ThrottlingException",
            "ResourceNotFoundException",
            "InternalServerError",
        ]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise CommentDeletionError(
                message="コメントの削除に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_delete_comment: post_id={post_id}, comment_id={comment_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise CommentDeletionError(
            message="コメント削除で予期しないエラーが発生しました。",
            original_error=e,
        )

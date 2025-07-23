from app.database import table
from boto3.dynamodb.conditions import Key
from typing import Union
from datetime import datetime, timezone
import logging
from botocore.exceptions import ClientError
from app.exceptions import (
    LikeRetrievalError,
    LikeAlreadyExistsError,
    LikeCreationError,
    LikeDeletionError,
    LikeNotFoundError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


def db_get_like(post_id: str, username: str) -> dict:
    logger.debug(f"[CRUD] Getting like status: post_id={post_id}, username={username}")

    try:
        response = table.get_item(
            Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"}
        )
        item = response.get("Item")

        if not item:
            logger.info(
                f"[CRUD] Like not found: post_id={post_id}, username={username}"
            )
            raise LikeNotFoundError(
                message=f"投稿ID '{post_id}' へのいいねが存在しません。"
            )

        try:
            like_data = {
                "post_id": item["post_id"],
                "username": item["user_id"].replace("USER#", ""),
                "created_at": item["created_at"],
            }

            logger.info(f"[CRUD] Like found: post_id={post_id}, username={username}")
            return like_data

        except KeyError as e:
            logger.warning(f"[CRUD] Invalid like data - missing field: {str(e)}")
            raise LikeRetrievalError(
                message="いいねデータが不正です。管理者にお問い合わせください。",
                original_error=e,
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB get_item error for like: post_id={post_id}, username={username}, error_code={error_code}, message={error_message}",
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
            raise LikeRetrievalError(
                message="いいね情報の取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_like: post_id={post_id}, username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise LikeRetrievalError(
            message="いいね情報取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_like_status(post_id: str, username: str) -> bool:
    logger.debug(f"[CRUD] Getting like status: post_id={post_id}, username={username}")

    try:
        response = table.get_item(
            Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"}
        )
        has_like = "Item" in response

        logger.debug(
            f"[CRUD] Like status retrieved successfully: post_id={post_id}, username={username}, liked={has_like}"
        )
        return has_like

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB get_item error for like status: post_id={post_id}, username={username}, error_code={error_code}, message={error_message}",
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
            raise LikeRetrievalError(
                message="いいね状態の取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_like_status: post_id={post_id}, username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise LikeRetrievalError(
            message="いいね状態取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_add_like(post_id: str, username: str) -> bool:
    logger.info(f"[CRUD] Adding like: post_id={post_id}, username={username}")

    try:
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "PK": f"POST#{post_id}",
            "SK": f"LIKE#{username}",
            "post_id": post_id,
            "user_id": f"USER#{username}",
            "created_at": now,
            # GSI5: ユーザーがいいねした投稿を効率的に取得
            "GSI5_PK": f"USER#{username}",  # いいねしたユーザー
            "GSI5_SK": f"{now}#{post_id}",  # いいねした日時 + 投稿ID
        }

        # 条件式で重複した書き込みを防ぐ
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )

        logger.info(
            f"[CRUD] Like added successfully: post_id={post_id}, username={username}"
        )
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        if error_code == "ConditionalCheckFailedException":
            logger.warning(
                f"[CRUD] Like already exists: post_id={post_id}, username={username}"
            )
            raise LikeAlreadyExistsError(
                message="既にいいねされています。",
                original_error=e,
            )

        logger.error(
            f"[CRUD] DynamoDB put_item error for like: post_id={post_id}, username={username}, error_code={error_code}, message={error_message}",
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
            raise LikeCreationError(
                message="いいねの追加に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_add_like: post_id={post_id}, username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise LikeCreationError(
            message="いいね追加で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_remove_like(post_id: str, username: str) -> bool:
    logger.info(f"[CRUD] Removing like: post_id={post_id}, username={username}")
    try:
        response = table.delete_item(
            Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"},
            ReturnValues="ALL_OLD",
        )
        deleted_item = response.get("Attributes")

        if deleted_item:
            logger.info(
                f"[CRUD] Like removed successfully: post_id={post_id}, username={username}"
            )
            return True

        logger.info(
            f"[CRUD] Like not found for removal: post_id={post_id}, username={username}"
        )
        raise LikeNotFoundError(
            message=f"削除対象のいいねが存在しません。投稿ID: {post_id}"
        )

    except LikeNotFoundError:
        # LikeNotFoundErrorは再スロー
        raise

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB delete_item error for like: post_id={post_id}, username={username}, error_code={error_code}, message={error_message}",
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
            raise LikeDeletionError(
                message="いいねの削除に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_remove_like: post_id={post_id}, username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise LikeDeletionError(
            message="いいね削除で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_like_count(post_id: str) -> int:
    logger.debug(f"[CRUD] Getting like count for post: post_id={post_id}")
    try:
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"POST#{post_id}")
            & Key("SK").begins_with("LIKE#"),
            Select="COUNT",  # カウントのみ取得
        )

        like_count = response.get("Count", 0)

        logger.debug(
            f"[CRUD] Like count retrieved successfully: post_id={post_id}, count={like_count}"
        )
        return like_count

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error for like count: post_id={post_id}, error_code={error_code}, message={error_message}",
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
            raise LikeRetrievalError(
                message=f"投稿'{post_id}'のいいね数取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_like_count: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise LikeRetrievalError(
            message=f"投稿'{post_id}'のいいね数取得で予期しないエラーが発生しました。",
            original_error=e,
        )

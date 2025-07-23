from app.database import table
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Union, Optional, Any
import uuid
from datetime import datetime, timezone
from app.config.logging_config import LoggingConfig
from app.exceptions import (
    PostRetrievalError,
    PostNotFoundError,
    PostCreationError,
    PostUpdateError,
    PostDeletionError,
    DatabaseError,
)
import logging

logger = logging.getLogger(__name__)


# 降順＝新しい順にソート
def db_get_posts(limit: int = 10, last_evaluated_key: dict = None) -> list[dict]:
    logger.info(
        f"[CRUD] Getting posts: limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    try:
        query_params = {
            "IndexName": "GSI_PostList",
            "KeyConditionExpression": Key("GSI1_PK").eq("POST#ALL"),
            "Limit": limit,
            "ScanIndexForward": False,
        }

        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**query_params)

        items = response.get("Items", [])
        last_key = response.get("LastEvaluatedKey")

        # 投稿データの変換
        posts = []
        for item in items:
            try:
                post = {
                    "post_id": item["PK"].split("#")[1],
                    "username": item["user_id"].replace("USER#", ""),
                    "category": item["category"],
                    "title": item["title"],
                    "description": item["description"],
                    "recommend1": item["recommend1"],
                    "recommend2": item["recommend2"],
                    "recommend3": item["recommend3"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                }
                posts.append(post)
            except KeyError as e:
                # 個別アイテムのデータ不備は警告ログだけでスキップ
                logger.warning(
                    f"[CRUD] Skipping invalid post data - missing field: {str(e)}"
                )
                continue

        logger.info(
            f"[CRUD] Posts retrieved successfully: count={len(posts)}, has_more={last_key is not None}"
        )

        result = {
            "posts": posts,
            "last_evaluated_key": last_key,
        }

        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error: error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        # 必要最低限：重要なエラーのみDatabaseError
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
            # その他はPostRetrievalError
            raise PostRetrievalError(
                message="投稿一覧の取得に失敗しました。", original_error=e
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_posts: error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise PostRetrievalError(
            message="投稿一覧取得で予期しないエラーが発生しました。", original_error=e
        )


# 降順＝新しい順にソート
def db_get_posts_by_category(
    category: str, limit: int = 10, last_evaluated_key: Optional[dict] = None
) -> dict:
    logger.info(
        f"[CRUD] Getting posts by category: category={category}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    try:
        query_params = {
            "IndexName": "GSI_Category",
            "KeyConditionExpression": Key("GSI2_PK").eq(f"CATEGORY#{category}"),
            "Limit": limit,
            "ScanIndexForward": False,
        }

        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**query_params)
        items = response.get("Items", [])
        last_key = response.get("LastEvaluatedKey")

        posts = []
        for item in items:
            try:
                post = {
                    "post_id": item["PK"].split("#")[1],
                    "username": item["user_id"].replace("USER#", ""),
                    "category": item["category"],
                    "title": item["title"],
                    "description": item["description"],
                    "recommend1": item["recommend1"],
                    "recommend2": item["recommend2"],
                    "recommend3": item["recommend3"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                }
                posts.append(post)
            except KeyError as e:
                # 📝 ログ②: 個別アイテムのデータ不備警告（新規追加）
                logger.warning(
                    f"[CRUD] Skipping invalid post data in category '{category}' - missing field: {str(e)}"
                )
                continue

        logger.info(
            f"[CRUD] Posts by category retrieved successfully: category={category}, count={len(posts)}, has_more={last_key is not None}"
        )

        result = {
            "posts": posts,
            "last_evaluated_key": last_key,
        }

        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        logger.error(
            f"[CRUD] DynamoDB query error for category {category}: {error_code}",
            exc_info=True,
        )

        if error_code in ["ThrottlingException", "ResourceNotFoundException"]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。", original_error=e
            )
        else:
            raise PostRetrievalError(
                message=f"カテゴリ'{category}'の投稿取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error getting posts by category {category}: {str(e)}",
            exc_info=True,
        )

        raise PostRetrievalError(
            message=f"カテゴリ'{category}'の投稿取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_single_post(post_id: str) -> dict:
    logger.info(f"[CRUD] Getting single post: post_id={post_id}")

    try:
        response = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"})
        item = response.get("Item")  # 該当データがなければ None

        if not item:
            logger.info(f"[CRUD] Post not found: post_id={post_id}")
            raise PostNotFoundError(message=f"投稿ID '{post_id}' が存在しません。")

        try:
            post = {
                "post_id": item["PK"].replace("POST#", ""),
                "username": item["user_id"].replace("USER#", ""),
                "category": item["category"],
                "title": item["title"],
                "description": item["description"],
                "recommend1": item["recommend1"],
                "recommend2": item["recommend2"],
                "recommend3": item["recommend3"],
                "created_at": datetime.fromisoformat(item["created_at"]),
                "updated_at": datetime.fromisoformat(item["updated_at"]),
            }

            logger.info(f"[CRUD] Single post retrieved successfully: post_id={post_id}")
            return post

        except KeyError as e:
            logger.warning(f"[CRUD] Invalid post data - missing field: {str(e)}")
            raise PostRetrievalError(
                message="投稿データが不正です。管理者にお問い合わせください。",
                original_error=e,
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB get_item error: post_id={post_id}, error_code={error_code}, message={error_message}",
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
            raise PostRetrievalError(
                message="投稿の取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_single_post: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise PostRetrievalError(
            message="投稿取得で予期しないエラーが発生しました。",
            original_error=e,
        )


# usernameはログイン中のユーザー名
def db_create_post(username: str, data: dict) -> dict:
    logger.info(f"[CRUD] Starting post creation for user: {username}")

    try:
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # ここでJSON型に加工
        item = {
            "PK": f"POST#{post_id}",
            "SK": "META",
            "user_id": f"USER#{username}",  # USER#+usernameでuser_idとする
            "category": data.category,
            "title": data.title,
            "description": data.description,
            "recommend1": data.recommend1,
            "recommend2": data.recommend2,
            "recommend3": data.recommend3,
            "created_at": now,
            "updated_at": now,
            # GSI1: 全投稿一覧
            "GSI1_PK": "POST#ALL",
            "GSI1_SK": f"{now}#{post_id}",
            # GSI2: カテゴリ別
            "GSI2_PK": f"CATEGORY#{data.category}",
            "GSI2_SK": f"{now}#{post_id}",
            # GSI3: ユーザー別
            "GSI3_PK": f"USER#{username}",
            "GSI3_SK": f"{now}#{post_id}",
        }

        table.put_item(
            Item=item
        )  # 200以外は例外botocore.exceptions.ClientErrorをスロー

        logger.info(
            f"[CRUD] Post created successfully: post_id={post_id}, username={username}, category={data.category}"
        )

        return {
            "post_id": post_id,
            "username": username,
            "category": data.category,
            "title": data.title,
            "description": data.description,
            "recommend1": data.recommend1,
            "recommend2": data.recommend2,
            "recommend3": data.recommend3,
            "created_at": now,
            "updated_at": now,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        logger.error(f"[CRUD] DynamoDB error: {error_code}", exc_info=True)

        if error_code in ["ThrottlingException", "ResourceNotFoundException"]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise PostCreationError(
                message="投稿の作成に失敗しました。入力内容を確認してください。",
                username=username,
                original_error=e,
            )

    # 予期しないエラー
    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_create_post: username={username}, error={str(e)}",
            exc_info=True,
        )
        # logger.error(f"[CRUD] Traceback: {traceback.format_exc()}")

        raise PostCreationError(
            message="投稿作成で予期しないエラーが発生しました",
            username=username,
            original_error=e,
        )


def db_update_post(post_id: str, data: dict) -> dict:
    logger.info(f"[CRUD] Updating post: post_id={post_id}")

    try:
        now = datetime.now(timezone.utc).isoformat()

        existing_item = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"}).get(
            "Item"
        )  # 既存データ取得

        if not existing_item:
            logger.info(f"[CRUD] Post not found for update: post_id={post_id}")
            raise PostNotFoundError(
                message=f"更新対象の投稿ID '{post_id}' が存在しません。"
            )

        created_at = existing_item.get("created_at", now)
        item = {
            "PK": f"POST#{post_id}",
            "SK": "META",
            "user_id": existing_item["user_id"],
            "category": data.category,
            "title": data.title,
            "description": data.description,
            "recommend1": data.recommend1,
            "recommend2": data.recommend2,
            "recommend3": data.recommend3,
            "created_at": created_at,
            "updated_at": now,
            # GSI1: 全投稿一覧
            "GSI1_PK": "POST#ALL",
            "GSI1_SK": f"{now}#{post_id}",
            # GSI2: カテゴリ別
            "GSI2_PK": f"CATEGORY#{data.category}",
            "GSI2_SK": f"{now}#{post_id}",
            # GSI3: ユーザー別
            "GSI3_PK": existing_item["user_id"],
            "GSI3_SK": f"POST#{post_id}",
        }

        response = table.put_item(Item=item)

        result = {
            "post_id": post_id,
            "username": existing_item["user_id"].replace("USER#", ""),
            "category": data.category,
            "title": data.title,
            "description": data.description,
            "recommend1": data.recommend1,
            "recommend2": data.recommend2,
            "recommend3": data.recommend3,
            "created_at": created_at,
            "updated_at": now,
        }

        logger.info(f"[CRUD] Post updated successfully: post_id={post_id}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB update error: post_id={post_id}, error_code={error_code}, message={error_message}",
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
            raise PostUpdateError(
                message="投稿の更新に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_update_post: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise PostUpdateError(
            message="投稿更新で予期しないエラーが発生しました。",
            original_error=e,
        )


# postと紐づいているcomments,likesを削除する
# SQSへ退避処理を後ほど実装
def db_delete_post_and_related_items(post_id: str) -> bool:
    logger.info(
        f"[CRUD] Attempting to delete post and related items: post_id={post_id}"
    )

    try:
        # 投稿・コメント・いいねをすべて取得
        response = table.query(KeyConditionExpression=Key("PK").eq(f"POST#{post_id}"))
        items = response.get("Items", [])

        if not items:
            logger.warning(f"[CRUD] No items found for deletion: post_id={post_id}")
            raise PostNotFoundError(
                message=f"削除対象の投稿ID '{post_id}' が存在しません。"
            )

        # 一括削除（最大25件ずつ処理され、25件より大きい数を処理可能）
        with table.batch_writer() as batch:
            for item in items:
                logger.debug(f"[CRUD] Deleting item: PK={item['PK']}, SK={item['SK']}")
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        logger.info(
            f"[CRUD] Post and related items deleted successfully: post_id={post_id}"
        )
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(
            f"[CRUD] DynamoDB batch delete error: post_id={post_id}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )
        raise PostDeletionError(
            message="投稿および関連データの削除に失敗しました。",
            original_error=e,
        )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_delete_post_and_related_items: post_id={post_id}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )
        raise PostDeletionError(
            message="投稿および関連データの削除中に予期しないエラーが発生しました。",
            original_error=e,
        )


# 降順＝新しい順にソート
def db_get_posts_by_user_paginated(
    username: str, limit: int = 10, last_evaluated_key: dict = None
) -> dict[str, Any]:
    logger.info(
        f"[CRUD] Getting posts by user: username={username}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    try:
        query_params = {
            "IndexName": "GSI_UserPosts",
            "KeyConditionExpression": Key("GSI3_PK").eq(f"USER#{username}"),
            "Limit": limit,
            "ScanIndexForward": False,
        }

        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**query_params)

        items = response.get("Items", [])
        last_key = response.get("LastEvaluatedKey")

        # 投稿データの変換
        posts = []
        for item in items:
            try:
                post = {
                    "post_id": item["PK"].split("#")[1],
                    "username": item["user_id"].replace("USER#", ""),
                    "category": item["category"],
                    "title": item["title"],
                    "description": item["description"],
                    "recommend1": item["recommend1"],
                    "recommend2": item["recommend2"],
                    "recommend3": item["recommend3"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                }
                posts.append(post)
            except KeyError as e:
                logger.warning(
                    f"[CRUD] Skipping invalid post data for user '{username}' - missing field: {str(e)}"
                )
                continue

        logger.info(
            f"[CRUD] Posts by user retrieved successfully: username={username}, count={len(posts)}, has_more={last_key is not None}"
        )

        result = {
            "posts": posts,
            "last_evaluated_key": last_key,
        }

        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error for user '{username}': error_code={error_code}, message={error_message}",
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
            raise PostRetrievalError(
                message=f"ユーザー'{username}'の投稿取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_posts_by_user_paginated: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise PostRetrievalError(
            message=f"ユーザー'{username}'の投稿取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_get_user_liked_posts_paginated(
    username: str, limit: int = 10, last_evaluated_key: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    logger.info(
        f"[CRUD] Getting user liked posts: username={username}, limit={limit}, has_last_key={last_evaluated_key is not None}"
    )

    try:
        query_params = {
            "IndexName": "GSI5_UserLikes",
            "KeyConditionExpression": Key("GSI5_PK").eq(f"USER#{username}"),
            "Limit": limit,
            "ScanIndexForward": False,  # いいねした順（新しい順）
        }

        if last_evaluated_key:
            query_params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**query_params)
        like_items = response.get("Items", [])

        if not like_items:
            logger.info(f"[CRUD] No liked posts found for user: username={username}")
            return {"posts": [], "last_evaluated_key": None, "count": 0}

        # 取得したpost_idsを使って、Batch処理で一括高速「投稿詳細データ」取得
        post_ids = [item["post_id"] for item in like_items]
        liked_posts = []

        # BatchGetItemで取得
        request_items = {
            table.table_name: {
                "Keys": [
                    {"PK": f"POST#{post_id}", "SK": "META"} for post_id in post_ids
                ]
            }
        }

        batch_response = table.meta.client.batch_get_item(RequestItems=request_items)

        # バッチ処理のレスポンスの中から必要なデータを取り出し、配列を生成
        for item in batch_response.get("Responses", {}).get(table.table_name, []):
            post_detail = {
                "post_id": item["PK"].split("#")[1],
                "username": item["user_id"].replace("USER#", ""),
                "category": item["category"],
                "title": item["title"],
                "description": item["description"],
                "recommend1": item["recommend1"],
                "recommend2": item["recommend2"],
                "recommend3": item["recommend3"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
            }
            liked_posts.append(post_detail)

        # いいねした順序を保持、順序逆引き用
        post_order = {post_id: idx for idx, post_id in enumerate(post_ids)}
        liked_posts.sort(key=lambda x: post_order.get(x["post_id"], 999))

        logger.info(
            f"[CRUD] User liked posts retrieved successfully: username={username}, count={len(liked_posts)}, has_more={response.get('LastEvaluatedKey') is not None}"
        )

        result = {
            "posts": liked_posts,
            "last_evaluated_key": response.get("LastEvaluatedKey"),
            "count": len(liked_posts),
        }

        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error for user liked posts: username={username}, error_code={error_code}, message={error_message}",
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
            raise PostRetrievalError(
                message=f"ユーザー'{username}'のいいね投稿取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_user_liked_posts_paginated: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise PostRetrievalError(
            message=f"ユーザー'{username}'のいいね投稿取得で予期しないエラーが発生しました。",
            original_error=e,
        )

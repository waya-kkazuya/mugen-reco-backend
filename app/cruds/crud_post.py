from app.database import table
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Union, List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import traceback
import json


# 降順＝新しい順にソート
def db_get_posts(limit: int = 10, last_evaluated_key: dict = None) -> List[dict]:
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
        print(last_key)
        return {
            "posts": [
                {
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
                for item in items
            ],
            "last_evaluated_key": last_key,
        }
    except Exception as e:
        print("❌ [db_get_posts] DynamoDB query failed:", str(e))
        print("🔍 Traceback:\n", traceback.format_exc())
        raise  # 再スローして FastAPI 側で HTTPException にする


# 降順＝新しい順にソート
def db_get_posts_by_category(
    category: str, limit: int = 10, last_evaluated_key: Optional[Dict] = None
) -> dict:
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

        return {
            "posts": [
                {
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
                for item in items
            ],
            "last_evaluated_key": last_key,
        }
    except Exception as e:
        print(f"❌ [db_get_posts_by_category] DynamoDB query failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


def db_get_single_post(post_id: str) -> Union[dict, bool]:
    try:
        response = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"})
        item = response.get("Item")  # 該当データがなければ None
        if item:
            return {
                "post_id": item["PK"].replace("POST#", ""),  # "POST#abc123" → "abc123"
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
        return False
    except Exception as e:
        print(f"❌ [db_get_single_post] DynamoDB get_item failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


# usernameはログイン中のユーザー名
def db_create_post(username: str, data: dict) -> Union[dict, bool]:
    try:
        post_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

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
    except Exception as e:
        print(f"❌ [db_create_post] DynamoDB put_item failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


def db_update_post(post_id: str, data: dict) -> Union[dict, bool]:
    try:
        now = datetime.utcnow().isoformat()

        existing_item = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"}).get(
            "Item"
        )  # 既存データ取得

        if not existing_item:
            print(f"⚠️ [db_update_post] Post with ID {post_id} not found.")
            return False

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

        return {
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
    except Exception as e:
        print(f"❌ [db_update_post] DynamoDB put_item failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


# 使用していない
def db_delete_post(post_id: str) -> Union[bool, str]:
    try:
        response = table.delete_item(
            Key={"PK": f"POST#{post_id}", "SK": "META"},
            ReturnValues="ALL_OLD",  # 削除前のアイテムを返す（存在確認にも使える）
        )
        deleted_item = response.get("Attributes")

        if deleted_item:
            print(f"⚠️ [db_delete_post] Post with ID {post_id} not found.")
            return True
        return False
    except Exception as e:
        print(f"❌ [db_delete_post] DynamoDB delete_item failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


# postと紐づいているcomments,likesを削除する
def db_delete_post_and_related_items(post_id: str) -> bool:
    try:
        # 投稿・コメント・いいねをすべて取得
        response = table.query(KeyConditionExpression=Key("PK").eq(f"POST#{post_id}"))
        items = response.get("Items", [])

        if not items:
            print(
                f"⚠️ [db_delete_post_and_related_items] No items found for POST#{post_id}"
            )
            return False  # 該当なし

        # 一括削除（最大25件ずつ処理され、25件より大きい数を処理可能）
        with table.batch_writer() as batch:
            for item in items:
                print(f"🗑️ Deleting item: PK={item['PK']}, SK={item['SK']}")
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        return True

    except Exception as e:
        print(f"❌ [db_delete_post_and_related_items] batch_writer failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        # □SQSへ退避処理を後で追加
        raise


# 降順＝新しい順にソート
def db_get_posts_by_user_paginated(
    username: str, limit: int = 10, last_evaluated_key: dict = None
) -> List[dict]:
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
        print(last_key)
        return {
            "posts": [
                {
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
                for item in items
            ],
            "last_evaluated_key": last_key,
        }
    except Exception as e:
        print("❌ [db_get_posts] DynamoDB query failed:", str(e))
        print("🔍 Traceback:\n", traceback.format_exc())
        raise  # 再スローして FastAPI 側で HTTPException にする


def db_get_user_liked_posts_paginated(
    username: str, limit: int = 10, last_evaluated_key: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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
            return {"posts": [], "last_evaluated_key": None, "count": 0}

        # 取得したpost_idsを使って、Batch処理で一括高速データ詳細取得
        # 投稿詳細を取得（基本版と同じロジック）
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

        return {
            "posts": liked_posts,
            "last_evaluated_key": response.get("LastEvaluatedKey"),
            "count": len(liked_posts),
        }

    except Exception as e:
        print(f"❌ [db_get_user_liked_posts_paginated] Failed: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise

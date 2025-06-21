from database import table
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import Union, List
import uuid
from datetime import datetime


# DynamoDB側でエラー起きる可能性
def db_get_posts() -> list:
    response = table.query(
        IndexName="GSI_PostList", KeyConditionExpression=Key("GSI1_PK").eq("POST#ALL")
    )
    items = response.get("Items", [])
    return [
        {
            "id": item["PK"].split("#")[1],
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
    ]


def db_get_posts_by_category(category: str) -> Union[List[dict], bool]:
    response = table.query(
        IndexName="GSI_Category",  # 作成したGSIの名前（例：GSI_Category）
        KeyConditionExpression=Key("GSI2_PK").eq(f"CATEGORY#{category}"),
    )
    items = response.get("Items", [])
    if items:
        return [
            {
                "id": item["PK"].split("#")[1],
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
        ]
    return False


def db_get_single_post(post_id: str) -> Union[dict, bool]:
    response = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"})
    item = response.get("Item")  # 該当データがなければ None
    if item:
        return {
            "id": item["PK"].replace("POST#", ""),  # "POST#abc123" → "abc123"
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


# usernameはログイン中のユーザー名
def db_create_post(username: str, data: dict) -> Union[dict, bool]:
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
        "GSI1_SK": f"POST#{post_id}",
        # GSI2: カテゴリ別
        "GSI2_PK": f"CATEGORY#{data.category}",
        "GSI2_SK": f"POST#{post_id}",
        # GSI3: ユーザー別
        "GSI3_PK": f"USER#{username}",
        "GSI3_SK": f"POST#{post_id}",
    }

    table.put_item(Item=item)  # 200以外は例外botocore.exceptions.ClientErrorをスロー
    return {
        "id": post_id,
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


def db_update_post(post_id: str, data: dict) -> Union[dict, bool]:
    now = datetime.utcnow().isoformat()

    existing_item = table.get_item(Key={"PK": f"POST#{post_id}", "SK": "META"}).get(
        "Item"
    )  # 既存データ取得

    if not existing_item:
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
        "GSI1_SK": f"POST#{post_id}",
        # GSI2: カテゴリ別
        "GSI2_PK": f"CATEGORY#{data.category}",
        "GSI2_SK": f"POST#{post_id}",
        # GSI3: ユーザー別
        "GSI3_PK": existing_item["user_id"],
        "GSI3_SK": f"POST#{post_id}",
    }

    response = table.put_item(Item=item)
    return {
        "id": post_id,
        "user_id": existing_item["user_id"],
        "category": data.category,
        "title": data.title,
        "description": data.description,
        "recommend1": data.recommend1,
        "recommend2": data.recommend2,
        "recommend3": data.recommend3,
        "created_at": created_at,
        "updated_at": now,
    }


def db_delete_post(post_id: str) -> Union[bool, str]:
    response = table.delete_item(
        Key={"PK": f"POST#{post_id}", "SK": "META"},
        ReturnValues="ALL_OLD",  # 削除前のアイテムを返す（存在確認にも使える）
    )
    deleted_item = response.get("Attributes")

    if deleted_item:
        return True
    return False


# postと紐づいているcomments,likesを削除する
def db_delete_post_and_related_items(post_id: str) -> bool:
    try:
        # 投稿・コメント・いいねをすべて取得
        response = table.query(KeyConditionExpression=Key("PK").eq(f"POST#{post_id}"))
        items = response.get("Items", [])

        if not items:
            return False  # 該当なし

        # 一括削除（最大25件ずつ処理され、25件より大きい数を処理可能）
        with table.batch_writer() as batch:
            for item in items:
                print(item)
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
        return True
    except Exception as e:
        print("batch_writerによる一括削除エラー:", e)
        # □SQSへ退避処理を後で追加
        raise


def db_get_posts_by_user(user_id: str) -> List[dict]:
    response = table.query(
        IndexName="GSI_UserPosts",  # GSI3 の設定と一致させる、GSIのインデックスを保存していないと載ってこない
        KeyConditionExpression=Key("GSI3_PK").eq(f"USER#{user_id}"),
    )

    items = response.get("Items", [])

    return [
        {
            "id": item["PK"].split("#")[1],
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
    ]

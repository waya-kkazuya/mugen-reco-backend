from app.database import table
from boto3.dynamodb.conditions import Key
from typing import Union
from datetime import datetime


def db_get_like(post_id: str, username: str) -> Union[dict, bool]:
    response = table.get_item(Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"})
    item = response.get("Item")
    if item:
        return {
            "post_id": item["post_id"],
            "username": item["user_id"].replace("USER#", ""),
            "created_at": item["created_at"],
        }
    return False


def db_get_like_status(post_id: str, username: str) -> bool:
    response = table.get_item(Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"})
    return "Item" in response


def db_add_like(post_id: str, username: str) -> bool:
    now = datetime.utcnow().isoformat()

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
    return True


def db_remove_like(post_id: str, username: str) -> bool:
    response = table.delete_item(
        Key={"PK": f"POST#{post_id}", "SK": f"LIKE#{username}"}, ReturnValues="ALL_OLD"
    )
    deleted_item = response.get("Attributes")

    if deleted_item:
        return True
    return False


def db_get_like_count(post_id: str) -> int:
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"POST#{post_id}")
        & Key("SK").begins_with("LIKE#"),
        Select="COUNT",  # カウントのみ取得
    )
    return response.get("Count", 0)

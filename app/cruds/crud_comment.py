from boto3.dynamodb.conditions import Key
from app.database import table
from typing import Union, List
import uuid
from datetime import datetime
from .crud_post import db_get_single_post
from fastapi import HTTPException


# JWTからsubjectのusernameを取得する→route_commentの上位レベルで
def db_create_comment(username: str, post_id: str, data: dict) -> Union[dict, bool]:

    # 投稿の存在確認
    post = db_get_single_post(post_id)
    if not post:
        print("✖post_idの投稿が存在しません")
        raise HTTPException(status_code=404, detail="Post not found")

    comment_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    item = {
        "PK": f"POST#{post_id}",
        "SK": f"COMMENT#{comment_id}",
        "comment_id": comment_id,
        "content": data.comment,
        "user_id": f"USER#{username}",
        "created_at": now,  # commentの編集機能は作らないので、updated_atは不要
    }
    print("put_item前")
    table.put_item(Item=item)  # 200以外は例外botocore.exceptions.ClientErrorをスロー
    return {
        "comment_id": comment_id,
        "username": username,
        "post_id": post_id,
        "content": data.comment,
        "created_at": now,
    }


def db_get_comments(post_id: str) -> List[dict]:
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"POST#{post_id}")
        & Key("SK").begins_with("COMMENT#")
    )
    items = response.get("Items", [])
    return [
        {
            "comment_id": item["comment_id"],
            "username": item["user_id"].replace("USER#", ""),
            "post_id": item["PK"].replace("POST#", ""),  #'PKから取得
            "content": item["content"],
            "created_at": item["created_at"],
        }
        for item in items
    ]


def db_get_single_comment(post_id: str, comment_id: str) -> dict | None:
    response = table.get_item(
        Key={"PK": f"POST#{post_id}", "SK": f"COMMENT#{comment_id}"}
    )
    item = response.get("Item")
    if not item:
        return None

    return {
        "comment_id": item["comment_id"],
        "username": item["user_id"].replace("USER#", ""),
        "post_id": item["PK"].replace("POST#", ""),
        "content": item["content"],
        "created_at": item["created_at"],
    }


# JWTとCSRFの認証必要
def db_delete_comment(post_id: str, comment_id: str) -> bool:
    response = table.delete_item(
        Key={"PK": f"POST#{post_id}", "SK": f"COMMENT#{comment_id}"},
        ReturnValues="ALL_OLD",  # 削除前のアイテムを返す（存在確認にも使える）
    )

    deleted_item = response.get("Attributes")

    if deleted_item:
        return True
    return False

from database import table
from typing import Union, List
from datetime import datetime
import uuid
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException
from auth_utils import AuthJwtCsrf


auth = AuthJwtCsrf()


def db_create_user(username: str, password_hash: str) -> Union[dict, bool]:
    now = datetime.utcnow().isoformat()
    user_id = str(uuid.uuid4())

    item = {
        "PK": f"USER#{user_id}",
        "SK": "META",
        "username": username,
        "password": password_hash,  # ハッシュ化されたパスワードを保存
        "created_at": now,  # 更新の機能は作成しないため、updated_atは省略
        # GSI: username検索用
        "GSI4_PK": f"USERNAME#{username}",
        "GSI4_SK": "PROFILE",
    }
    print("put_itemの前の行")
    table.put_item(Item=item)
    print("put_itemの次の行")
    return {"id": user_id, "username": username, "created_at": now}


# ユーザー取得
def db_get_user_by_username(username: str) -> Union[dict, None]:
    response = table.query(
        IndexName="GSI_Username",
        KeyConditionExpression=Key("GSI4_PK").eq(f"USERNAME#{username}")
        & Key("GSI4_SK").eq("PROFILE"),
    )
    items = response.get("Items", [])
    if items:
        return items[0]
    return None


def db_signup(data: dict) -> dict:
    username = data.username
    password = data.password
    overlap_user = db_get_user_by_username(username)
    if overlap_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    if not password or len(password) < 6:
        print("passwordバリデーション失敗")
        raise HTTPException(status_code=400, detail="Password too short")
    # 問題がなければユーザーを作成
    new_user = db_create_user(username, auth.generate_hashed_pw(password))
    return new_user


def db_login(data: dict) -> str:  # JWTを返却
    username = data.username
    password = data.password
    user = db_get_user_by_username(username)
    print(user)
    if not user or not auth.verify_pw(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.encode_jwt(user["username"])
    return token

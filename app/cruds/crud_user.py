from app.database import table
from typing import Union
from datetime import datetime, timezone
import uuid
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException
from app.auth.auth_utils import AuthJwtCsrf
import traceback

auth = AuthJwtCsrf()


def db_create_user(username: str, password_hash: str) -> Union[dict, bool]:
    now = datetime.now(timezone.utc).isoformat()
    user_id = str(uuid.uuid4())

    # ユーザー名の

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
    try:
        # ユーザー名の重複を防ぐため、トランザクション処理に変更
        print(f"🔸 [db_create_user] Creating user: {username} (USER#{user_id})")
        table.put_item(Item=item)
        print("✅ [db_create_user] put_item succeeded")
        return {"id": user_id, "username": username, "created_at": now}

    except Exception as e:
        print(f"❌ [db_create_user] Failed to create user {username}: {str(e)}")
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


# ユーザー取得
def db_get_user_by_username(username: str) -> Union[dict, None]:
    try:
        response = table.query(
            IndexName="GSI_Username",
            KeyConditionExpression=Key("GSI4_PK").eq(f"USERNAME#{username}")
            & Key("GSI4_SK").eq("PROFILE"),
        )
        items = response.get("Items", [])
        if items:
            return items[0]
        return None

    except Exception as e:
        print(
            f"❌ [db_get_user_by_username] Query failed for USERNAME#{username}: {str(e)}"
        )
        print("🔍 Traceback:\n", traceback.format_exc())
        raise


def db_signup(data: dict) -> dict:
    username = data.username
    password = data.password
    overlap_user = db_get_user_by_username(username)
    if overlap_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    if not password or len(password) < 6:
        print("❌ Password validation failed: too short")
        raise HTTPException(status_code=400, detail="Password too short")
    # 問題がなければユーザーを作成
    new_user = db_create_user(username, auth.generate_hashed_pw(password))
    print(f"✅ New user created: {username}")
    return new_user


def db_login(data: dict) -> tuple[str, dict]:  # JWTを返却
    username = data.username
    password = data.password
    user_data = db_get_user_by_username(username)
    print("user_data", user_data)

    if not user_data or not auth.verify_pw(password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.encode_jwt(user_data["username"])
    return token, user_data["username"]

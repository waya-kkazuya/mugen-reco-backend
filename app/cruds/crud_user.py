from app.database import table
from typing import Union
from datetime import datetime, timezone
import uuid
from boto3.dynamodb.conditions import Key, Attr
from fastapi import HTTPException
from app.auth.auth_utils import AuthJwtCsrf
import traceback
import logging
from botocore.exceptions import ClientError
from app.exceptions import (
    PasswordValidationError,
    UserCreationError,
    UserAlreadyExistsError,
    UsernameAlreadyExistsError,
    UserRetrievalError,
    SignupError,
    UserAuthenticationError,
    LoginError,
    DatabaseError,
)

logger = logging.getLogger(__name__)
auth = AuthJwtCsrf()


# ユーザー名の重複を防ぐため、トランザクション処理に変更予定
def db_create_user(username: str, password_hash: str) -> Union[dict, bool]:
    logger.info(f"[CRUD] Creating user: username={username}")

    try:
        now = datetime.now(timezone.utc).isoformat()
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

        table.put_item(Item=item, ConditionExpression=Attr("GSI4_PK").not_exists())

        result = {"id": user_id, "username": username, "created_at": now}

        logger.info(
            f"[CRUD] User created successfully: username={username}, user_id={user_id}"
        )
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB put_item error for user creation: username={username}, error_code={error_code}, message={error_message}",
            exc_info=True,
        )

        if error_code == "ConditionalCheckFailedException":
            raise UserAlreadyExistsError(
                message=f"ユーザー名'{username}'は既に使用されています。",
                original_error=e,
            )
        elif error_code in [
            "ThrottlingException",
            "ResourceNotFoundException",
            "InternalServerError",
        ]:
            raise DatabaseError(
                message="データベースサービスで問題が発生しました。しばらく待ってから再試行してください。",
                original_error=e,
            )
        else:
            raise UserCreationError(
                message="ユーザーの作成に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_create_user: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise UserCreationError(
            message="ユーザー作成で予期しないエラーが発生しました。",
            original_error=e,
        )


# ユーザー取得
def db_get_user_by_username(username: str) -> Union[dict, None]:
    logger.info(f"[CRUD] Getting user by username: username={username}")

    try:
        response = table.query(
            IndexName="GSI_Username",
            KeyConditionExpression=Key("GSI4_PK").eq(f"USERNAME#{username}")
            & Key("GSI4_SK").eq("PROFILE"),
        )
        items = response.get("Items", [])

        if items:
            try:
                user = items[0]
                # 必要最小限のフィールドチェック
                required_fields = ["username", "password", "created_at"]
                for field in required_fields:
                    if field not in user:
                        raise KeyError(field)

                logger.info(f"[CRUD] User found successfully: username={username}")
                return user

            except KeyError as e:
                logger.warning(f"[CRUD] Invalid user data - missing field: {str(e)}")
                return None

        logger.info(f"[CRUD] User not found: username={username}")
        return None

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB query error for user: username={username}, error_code={error_code}, message={error_message}",
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
            raise UserRetrievalError(
                message=f"ユーザー'{username}'の取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_user_by_username: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise UserRetrievalError(
            message=f"ユーザー'{username}'の取得で予期しないエラーが発生しました。",
            original_error=e,
        )


def db_signup(data: dict) -> dict:
    username = data.username
    password = data.password

    logger.info(f"[CRUD] Starting user signup: username={username}")

    # ユーザー名の重複チェック
    overlap_user = db_get_user_by_username(username)
    if overlap_user:
        logger.warning(
            f"[CRUD] Signup failed - username already exists: username={username}"
        )
        raise UsernameAlreadyExistsError(
            message=f"ユーザー名'{username}'は既に使用されています。"
        )

    if not password or len(password) < 6:
        logger.warning(
            f"[CRUD] Signup failed - password validation error: username={username}"
        )
        raise PasswordValidationError(
            message="パスワードは6文字以上で入力してください。"
        )

    try:
        # 問題がなければユーザーを作成
        new_user = db_create_user(username, auth.generate_hashed_pw(password))
        logger.info(f"[CRUD] User signup completed successfully: username={username}")
        return new_user

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_signup: username={username}", exc_info=True
        )
        raise SignupError(
            message="サインアップ処理でエラーが発生しました。", original_error=e
        )


def db_login(data: dict) -> tuple[str, dict]:  # JWTを返却
    username = data.username
    password = data.password

    logger.info(f"[CRUD] Starting user login: username={username}")
    try:
        user_data = db_get_user_by_username(username)

        if not user_data:
            logger.warning(f"[CRUD] Login failed - user not found: username={username}")
            raise UserAuthenticationError(message="ユーザーデータが存在しません。")

        if not auth.verify_pw(password, user_data["password"]):
            logger.warning(
                f"[CRUD] Login failed - invalid password: username={username}"
            )
            raise UserAuthenticationError(
                message="ユーザー名またはパスワードが正しくありません。"
            )

        token = auth.encode_jwt(user_data["username"])
        logger.info(f"[CRUD] User login completed successfully: username={username}")
        return token, user_data["username"]

    except UserAuthenticationError:
        # 認証エラーは再スロー
        raise

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_login: username={username}, error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )
        raise LoginError(
            message="ログイン処理でエラーが発生しました。", original_error=e
        )

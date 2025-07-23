from boto3.dynamodb.conditions import Key
from app.database import table
import logging
from botocore.exceptions import ClientError
from app.exceptions import (
    CategoryRetrievalError,
    DatabaseError,
)


logger = logging.getLogger(__name__)


def db_get_categories():
    logger.info("[CRUD] Getting all categories")
    try:
        response = table.scan(
            FilterExpression=Key("PK").begins_with("CATEGORY#") & Key("SK").eq("META")
        )
        items = response.get("Items", [])

        # カテゴリデータの変換
        categories = []
        for item in items:
            try:
                category = {"id": item["PK"].split("#")[1], "name": item["name"]}
                categories.append(category)
            except KeyError as e:
                logger.warning(
                    f"[CRUD] Skipping invalid category data - missing field: {str(e)}"
                )
                continue

        logger.info(
            f"[CRUD] Categories retrieved successfully: count={len(categories)}"
        )
        return categories

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        logger.error(
            f"[CRUD] DynamoDB scan error for categories: error_code={error_code}, message={error_message}",
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
            raise CategoryRetrievalError(
                message="カテゴリ一覧の取得に失敗しました。",
                original_error=e,
            )

    except Exception as e:
        logger.error(
            f"[CRUD] Unexpected error in db_get_categories: error_type={type(e).__name__}, error_message={str(e)}",
            exc_info=True,
        )

        raise CategoryRetrievalError(
            message="カテゴリ取得で予期しないエラーが発生しました。",
            original_error=e,
        )

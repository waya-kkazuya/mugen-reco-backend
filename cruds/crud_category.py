from boto3.dynamodb.conditions import Key
from database import table

def db_get_categories():
    try:
        # ひとまずScanで様子を見る
        response = table.scan(
            FilterExpression=Key("PK").begins_with("CATEGORY#") & Key("SK").eq("META")
        )
        items = response.get("Items", [])
        print(items)
        return [
            {
                "id": item["PK"].split("#")[1],
                "name": item["name"]
            }
            for item in items
        ]
    except Exception as e:
        print("カテゴリ取得エラー:", e)
        return []

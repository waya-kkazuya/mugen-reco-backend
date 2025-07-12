from boto3.dynamodb.conditions import Key
from app.database import table


def db_get_categories():
    response = table.scan(
        FilterExpression=Key("PK").begins_with("CATEGORY#") & Key("SK").eq("META")
    )
    items = response.get("Items", [])
    return [{"id": item["PK"].split("#")[1], "name": item["name"]} for item in items]

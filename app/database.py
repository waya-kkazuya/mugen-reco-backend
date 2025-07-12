import os
import boto3

IS_LOCAL = os.getenv("IS_LOCAL", "false").lower() == "true"

if IS_LOCAL:
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        region_name="ap-northeast-1",
        aws_access_key_id="DUMMYID",
        aws_secret_access_key="DUMMYKEY",
    )
else:
    dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")

table = dynamodb.Table("MugenRecoTable")

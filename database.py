import boto3

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="ap-northeast-1",
    aws_access_key_id="DUMMYID",
    aws_secret_access_key="DUMMYKEY",
)

table = dynamodb.Table("MugenRecoTable")

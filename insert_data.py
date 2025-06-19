import boto3

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='ap-northeast-1',
    aws_access_key_id='DUMMYID',
    aws_secret_access_key='DUMMYKEY'
)

table = dynamodb.Table('Users')

# データ挿入
table.put_item(Item={
    'user_id': 'user_001',
    'name': 'Taro Yamada',
    'email': 'taro@example.com'
})

print("1件のユーザーを追加しました")

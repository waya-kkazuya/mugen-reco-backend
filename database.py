import boto3

def get_dynamodb_client():
    return boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='ap-northeast-1',
        aws_access_key_id='DUMMYID',
        aws_secret_access_key='DUMMYKEY'
    )
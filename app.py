import boto3
from dotenv import load_dotenv
import os

load_dotenv()

AWS_SERVER_PUBLIC_KEY = os.environ.get("AWS_SERVER_PUBLIC_KEY")
AWS_SERVER_SECRET_KEY = os.environ.get("AWS_SERVER_SECRET_KEY")

client = boto3.client('dynamodb', aws_access_key_id=AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=AWS_SERVER_SECRET_KEY, region_name='us-east-1')

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=AWS_SERVER_SECRET_KEY, region_name='us-east-1')

try:
    table = client.create_table(
        TableName='users',
        KeySchema=[
            {
                'AttributeName': 'username',
                'KeyType': 'HASH' 
            },
            {
                'AttributeName': 'last_name',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'last_name',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print("Creating table...")
    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName='users')
    print("Table created")
except Exception as e:
    table = dynamodb.Table('users')
    table.put_item(
        Item={
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 25,
            'account_type': 'standard_user',
        }
    )
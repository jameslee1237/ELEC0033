import boto3
from dotenv import load_dotenv
import os
from boto3.dynamodb.conditions import Key, Attr

load_dotenv()



class DynamoDB:
    def __init__(self):
        load_dotenv()
        self.AWS_SERVER_PUBLIC_KEY = os.environ.get("AWS_SERVER_PUBLIC_KEY")
        self.AWS_SERVER_SECRET_KEY = os.environ.get("AWS_SERVER_SECRET_KEY")
        self.client = boto3.client('dynamodb', aws_access_key_id=self.AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=self.AWS_SERVER_SECRET_KEY, region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb', aws_access_key_id=self.AWS_SERVER_PUBLIC_KEY, aws_secret_access_key=self.AWS_SERVER_SECRET_KEY, region_name='us-east-1')

    def test(self):
            try:
                table = self.client.create_table(
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
                waiter = self.client.get_waiter('table_exists')
                waiter.wait(TableName='users')
                print("Table created")
            except Exception as e:
                table = self.dynamodb.Table('users')
                table.put_item(
                    Item={
                        'username': 'johndoe',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'age': 25,
                        'account_type': 'standard_user',
                    }
                )
                print("Inserting item")

    def get_data(self):
        table = self.dynamodb.Table('users')
        response = table.query(
            KeyConditionExpression=Key('username').eq('johgit ndoe')
        )
        items = response['Items']
        print(items)


if __name__ == "__main__":
    dynamodb = DynamoDB()
    dynamodb.get_data()
    pass
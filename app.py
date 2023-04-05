import boto3
from dotenv import load_dotenv
import os
from boto3.dynamodb.conditions import Key, Attr
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from flask import Flask, render_template

app = Flask(__name__, template_folder='templates',)

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

    def create_heatmap_table(self):
        try:
            table = self.client.create_table(
                TableName='heatmaps',
                KeySchema=[
                    {
                        'AttributeName': 'section',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'reading',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'section',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'reading',
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
            waiter.wait(TableName='heatmaps')
            print("Table created")
        except Exception as e:
            print("Table already exists")
    
    def insert_heatmap_data(self):
        randata = np.random.randint(0, 255, 9)
        count = 1
        table = self.dynamodb.Table('heatmaps')
        for item in randata:
            table.put_item(
                Item={
                    'section': 'section' + str(count),
                    'reading': str(item),
                }
            )
            count += 1

    def delete_table(self, name):
        try:
            table = self.dynamodb.Table(name)
            table.delete()

            print(f"Deleteing table {name}...")
            table.wait_until_not_exists()
            print("Table deleted")
        except:
            print("Table does not exist")

    def get_data(self, name, key, value):
        table = self.dynamodb.Table(name)
        response = table.query(
            KeyConditionExpression=Key(key).eq(value)
        )
        items = response['Items']
        print(items)

    def get_table(self, name):
        table = self.dynamodb.Table(name)
        try:
            response = table.scan()
            data = response['Items']
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                data.extend(response['Items'])
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response

    def sample_heatmap(self, data):
        readings = [int(x['reading']) for x in data]
        readings = readings[0:3]
        random1, random2 = np.random.randint(readings[0] - 10, readings[0] + 10), np.random.randint(readings[2] - 10, readings[2] + 10)
        r12, r23 = np.average([readings[0], readings[1]]), np.average([readings[1], readings[2]])
        r1n, r3n = np.average([readings[0], random1]), np.average([readings[2], random2])
        temp = [r12, readings[0], r1n, readings[1], 0, 0, r23, readings[2], r3n]
        for t in temp:
            if t != 0:
                t += 20
        temp = np.array(temp)
        temp = np.reshape(temp, (3, 3))
        if os.path.exists('static/image/heatmap.png'):
            return 0
        else:
            heatmap = sns.heatmap(temp, annot=True, cmap='Reds', fmt='.2f')
            heatmap.figure.savefig('static/image/heatmap.png')
            return 0

@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/heatmap')
def heatmap():
    dynamodb = DynamoDB()
    data = dynamodb.get_table('heatmaps')
    dynamodb.sample_heatmap(data['Items'])
    image_path = 'static/image/heatmap.png'
    return render_template('./heatmap.html', image_path = image_path)

if __name__ == "__main__":
    #dynamodb.create_heatmap_table()
    #dynamodb.insert_heatmap_data()
    #dynamodb.get_data('heatmaps', 'section', 'section1')
    #dynamodb.delete_table(name='heatmaps')
    #data = dynamodb.get_table('heatmaps')
    #dynamodb.sample_heatmap(data['Items'])
    app.run(host="0.0.0.0", port=5000)

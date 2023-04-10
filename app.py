import boto3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import os
import base64
import json
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, render_template, request, url_for, jsonify
from dotenv import load_dotenv
from decimal import Decimal

last_modified = 0

app = Flask(__name__, template_folder='templates')

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
                        'AttributeName': 'sensor',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'reading',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'sensor',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'reading',
                        'AttributeType': 'N'
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
        latest_items = {}
        latest_heatmap = {}
        for item in data:
            section = item["Section"]
            timestamp = item["ts"]
            if section not in latest_items or timestamp > latest_items[section]["ts"]:
                latest_items[section] = item
        for section in latest_items:
            readings = [int(Decimal(latest_items[section]["sensor1"])), int(Decimal(latest_items[section]["sensor2"])), 
                        int(Decimal(latest_items[section]["sensor3"]))]
            random1, random2 = np.random.randint(readings[0] - 20, readings[0] + 20), np.random.randint(readings[2] - 20, readings[2] + 20)
            r12, r23 = np.average([readings[0], readings[1]]), np.average([readings[1], readings[2]])
            r1n, r3n = np.average([readings[0], random1]), np.average([readings[2], random2])
            temp = [r12, readings[0], r1n, readings[1], 0, 0, r23, readings[2], r3n]
            for t in temp:
                if t != 0:
                    t += 20
            temp = np.array(temp)
            temp = np.reshape(temp, (3, 3))
            latest_heatmap[section] = temp
        for section, data in zip(latest_heatmap.keys(), latest_heatmap.values()):
            heatmap = sns.heatmap(temp, annot=True, cmap='Reds', fmt='.2f', vmin=0, vmax=255)
            filename = f'static/image/heatmap_{section}.png'
            if os.path.exists(filename):
                os.remove(filename)
            heatmap.figure.savefig(filename)
            plt.clf()
            return list(latest_heatmap.keys())

@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/heatmap', methods=['GET', 'POST'])
def heatmap():
    dynamodb = DynamoDB()
    #tables = list(dynamodb.dynamodb.tables.all())
    #tables = [x.name for x in tables]
    data = dynamodb.get_table("Heatmap")
    section_list = dynamodb.sample_heatmap(data['Items'])
    images = []
    encodings = []
    for section in section_list:
        image_path = f'static/image/heatmap_{section}.png'
        images.append(image_path)
    if request.method == 'POST':
        data = dynamodb.get_table("Heatmap")
        section_list = dynamodb.sample_heatmap(data['Items'])
        images.clear()
        for section in section_list:
            image_path = f'static/image/heatmap_{section}.png'
            images.append(image_path)
    for image in images:
        with open(image, 'rb') as image_file:
            encoding = base64.b64encode(image_file.read()).decode('utf-8')
            encodings.append(encoding)
    response = {}
    for encoding in encodings:
        response.update({'image' + str(encodings.index(encoding)): encoding})
    return render_template('./heatmap.html', images = encodings)

@app.route("/update", methods=['POST'])
def update():
    if request.method == 'POST':
        dynamodb = DynamoDB()
        data = dynamodb.get_table("Heatmap")
        section_list = dynamodb.sample_heatmap(data['Items'])
        image_urls = []
        encodings = []
        for section in section_list:
            image_path = f'static/image/heatmap_{section}.png'
            image_urls.append(image_path)
        for image in image_urls:
            with open(image, 'rb') as image_file:
                encoding = base64.b64encode(image_file.read()).decode('utf-8')
                encodings.append(encoding)
        response = {}
        for encoding in encodings:
            response.update({'image' + str(encodings.index(encoding)): encoding})
        return jsonify(response)

if __name__ == "__main__":
    #dynamodb = DynamoDB()
    #dynamodb.create_heatmap_table()
    #dynamodb.insert_heatmap_data()
    #dynamodb.get_data('heatmaps', 'section', 'section1')
    #dynamodb.delete_table(name='heatmaps')
    #data = dynamodb.get_table('heatmaps')
    #dynamodb.sample_heatmap(data['Items'])
    app.run(host="0.0.0.0", port=5000)

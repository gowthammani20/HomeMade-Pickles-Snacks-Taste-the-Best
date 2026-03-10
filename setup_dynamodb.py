"""
Run this ONCE after setting up your AWS credentials in .env
This creates all DynamoDB tables and seeds sample product data.
Usage: python setup_dynamodb.py
"""

import boto3
import os
import uuid
from dotenv import load_dotenv
import time

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'ap-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def create_table(name, key_name):
    try:
        table = dynamodb.create_table(
            TableName=name,
            KeySchema=[{'AttributeName': key_name, 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': key_name, 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        print(f"✅ Created table: {name}")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"⚠️  Table {name} already exists — skipping")
        return dynamodb.Table(name)

def seed_products():
    table = dynamodb.Table('Products')
    products = [
        {'ProductID': 'p1', 'name': 'Mango Pickle', 'price': '199', 'category': 'pickle', 'stock': 50, 'description': 'Tangy raw mango pickle made with traditional spices and cold-pressed mustard oil. Zero preservatives.', 'emoji': '🥭'},
        {'ProductID': 'p2', 'name': 'Lemon Pickle', 'price': '149', 'category': 'pickle', 'stock': 40, 'description': 'Zesty whole lemon pickle in a blend of spices, fermented for 30 days for maximum flavor.', 'emoji': '🍋'},
        {'ProductID': 'p3', 'name': 'Mixed Veg Pickle', 'price': '179', 'category': 'pickle', 'stock': 35, 'description': 'Assortment of seasonal vegetables pickled with aromatic spices. Goes with everything.', 'emoji': '🥗'},
        {'ProductID': 'p4', 'name': 'Garlic Pickle', 'price': '229', 'category': 'pickle', 'stock': 25, 'description': 'Bold garlic cloves marinated in a spicy, tangy masala. Aged for 2 weeks.', 'emoji': '🧄'},
        {'ProductID': 'p5', 'name': 'Murukku', 'price': '129', 'category': 'snack', 'stock': 60, 'description': 'Crispy rice flour spirals fried to golden perfection. Classic South Indian snack.', 'emoji': '🌀'},
        {'ProductID': 'p6', 'name': 'Chakli', 'price': '139', 'category': 'snack', 'stock': 45, 'description': 'Spiral-shaped savory snack made from rice and urad dal. Perfectly crunchy.', 'emoji': '🌾'},
        {'ProductID': 'p7', 'name': 'Mixture', 'price': '119', 'category': 'snack', 'stock': 70, 'description': 'Spiced namkeen mixture with peanuts, curry leaves, and crispy sev.', 'emoji': '🥜'},
        {'ProductID': 'p8', 'name': 'Tamarind Chutney', 'price': '99', 'category': 'chutney', 'stock': 55, 'description': 'Sweet and tangy tamarind chutney, handcrafted with jaggery and spices.', 'emoji': '🫙'},
    ]
    for p in products:
        table.put_item(Item=p)
    print(f"✅ Seeded {len(products)} products")

if __name__ == '__main__':
    print("\n🚀 Setting up DynamoDB tables for HomeMade Pickles & Snacks...\n")
    create_table('Products', 'ProductID')
    create_table('Orders', 'OrderID')
    create_table('Users', 'UserID')
    time.sleep(2)
    seed_products()
    print("\n🎉 Setup complete! You can now run: python app.py\n")

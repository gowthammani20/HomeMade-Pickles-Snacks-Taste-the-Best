from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import boto3
from boto3.dynamodb.conditions import Attr
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'pickles-secret-2024')

def get_dynamodb():
    return boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'ap-south-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

def get_mock_products():
    return [
        {'ProductID':'p1','name':'Mango Pickle','price':'199','category':'pickle','stock':'50','description':'Tangy raw mango pickle made with traditional spices and cold-pressed mustard oil. Zero preservatives.','emoji':'🥭'},
        {'ProductID':'p2','name':'Lemon Pickle','price':'149','category':'pickle','stock':'40','description':'Zesty whole lemon pickle in a blend of spices, fermented for 30 days for maximum flavor.','emoji':'🍋'},
        {'ProductID':'p3','name':'Mixed Veg Pickle','price':'179','category':'pickle','stock':'35','description':'Assortment of seasonal vegetables pickled with aromatic spices. Goes with everything.','emoji':'🥗'},
        {'ProductID':'p4','name':'Garlic Pickle','price':'229','category':'pickle','stock':'25','description':'Bold garlic cloves marinated in a spicy, tangy masala. Aged for 2 weeks.','emoji':'🧄'},
        {'ProductID':'p5','name':'Murukku','price':'129','category':'snack','stock':'60','description':'Crispy rice flour spirals fried to golden perfection. Classic South Indian snack.','emoji':'🌀'},
        {'ProductID':'p6','name':'Chakli','price':'139','category':'snack','stock':'45','description':'Spiral-shaped savory snack made from rice and urad dal. Perfectly crunchy.','emoji':'🌾'},
        {'ProductID':'p7','name':'Mixture','price':'119','category':'snack','stock':'70','description':'Spiced namkeen mixture with peanuts, curry leaves, and crispy sev.','emoji':'🥜'},
        {'ProductID':'p8','name':'Tamarind Chutney','price':'99','category':'chutney','stock':'55','description':'Sweet and tangy tamarind chutney, handcrafted with jaggery and spices.','emoji':'🫙'},
    ]

@app.route('/')
def index():
    try:
        db = get_dynamodb()
        table = db.Table('Products')
        response = table.scan(Limit=8)
        products = response.get('Items', [])
        if not products:
            products = get_mock_products()
    except Exception:
        products = get_mock_products()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    try:
        db = get_dynamodb()
        table = db.Table('Products')
        if category == 'all':
            response = table.scan()
        else:
            response = table.scan(FilterExpression=Attr('category').eq(category))
        products = response.get('Items', [])
        if not products:
            products = get_mock_products()
    except Exception:
        products = get_mock_products()
    if category != 'all':
        products = [p for p in products if p.get('category') == category]
    return render_template('products.html', products=products, category=category)

@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        db = get_dynamodb()
        table = db.Table('Products')
        response = table.get_item(Key={'ProductID': product_id})
        product = response.get('Item')
        if not product:
            product = next((p for p in get_mock_products() if p['ProductID'] == product_id), get_mock_products()[0])
    except Exception:
        product = next((p for p in get_mock_products() if p['ProductID'] == product_id), get_mock_products()[0])
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = str(uuid.uuid4())
        name = request.form['name']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        try:
            db = get_dynamodb()
            table = db.Table('Users')
            table.put_item(Item={
                'UserID': user_id, 'name': name, 'email': email,
                'password': password, 'created_at': datetime.now().isoformat()
            })
        except Exception:
            pass
        session['user_id'] = user_id
        session['user_name'] = name
        flash('Account created! Welcome to HomeMade Pickles & Snacks 🥒', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        try:
            db = get_dynamodb()
            table = db.Table('Users')
            response = table.scan(FilterExpression=Attr('email').eq(email) & Attr('password').eq(password))
            users = response.get('Items', [])
            if users:
                session['user_id'] = users[0]['UserID']
                session['user_name'] = users[0]['name']
                flash('Welcome back! 🙏', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception:
            session['user_id'] = 'demo-' + str(uuid.uuid4())[:6]
            session['user_name'] = email.split('@')[0].title()
            flash('Logged in (Demo mode - connect DynamoDB to persist)', 'info')
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(float(item['price']) * int(item['qty']) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == data['product_id']:
            item['qty'] = int(item['qty']) + 1
            session['cart'] = cart
            session.modified = True
            return jsonify({'status': 'updated', 'count': sum(int(i['qty']) for i in cart)})
    cart.append({
        'product_id': data['product_id'],
        'name': data['name'],
        'price': data['price'],
        'emoji': data.get('emoji', '🥒'),
        'qty': 1
    })
    session['cart'] = cart
    session.modified = True
    return jsonify({'status': 'added', 'count': sum(int(i['qty']) for i in cart)})

@app.route('/remove-from-cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    session['cart'] = [i for i in cart if i['product_id'] != product_id]
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout.', 'error')
        return redirect(url_for('login'))
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    total = sum(float(item['price']) * int(item['qty']) for item in cart_items)
    if request.method == 'POST':
        order_id = str(uuid.uuid4())[:8].upper()
        try:
            db = get_dynamodb()
            orders_table = db.Table('Orders')
            orders_table.put_item(Item={
                'OrderID': order_id,
                'UserID': session['user_id'],
                'items': cart_items,
                'total': str(total),
                'name': request.form.get('name'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'status': 'Confirmed',
                'created_at': datetime.now().isoformat()
            })
            products_table = db.Table('Products')
            for item in cart_items:
                try:
                    products_table.update_item(
                        Key={'ProductID': item['product_id']},
                        UpdateExpression='SET stock = stock - :q',
                        ExpressionAttributeValues={':q': int(item['qty'])}
                    )
                except:
                    pass
        except Exception:
            pass
        session['cart'] = []
        session['last_order'] = order_id
        session.modified = True
        return redirect(url_for('order_success'))
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/order-success')
def order_success():
    order_id = session.get('last_order', 'DEMO123')
    return render_template('order_success.html', order_id=order_id)

@app.route('/orders')
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        db = get_dynamodb()
        table = db.Table('Orders')
        response = table.scan(FilterExpression=Attr('UserID').eq(session['user_id']))
        orders = sorted(response.get('Items', []), key=lambda x: x.get('created_at',''), reverse=True)
    except Exception:
        orders = []
    return render_template('orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

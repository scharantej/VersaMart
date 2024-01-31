
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secretkey'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/products')
def products():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products/<category>')
def products_by_category(category):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category = ?", (category,))
    products = c.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/product/<product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form['product_id']
    qty = request.form['qty']
    if 'cart' not in session:
        session['cart'] = {}
    if product_id in session['cart']:
        session['cart'][product_id] += int(qty)
    else:
        session['cart'][product_id] = int(qty)
    return redirect(url_for('cart'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form['product_id']
    qty = request.form['qty']
    if product_id in session['cart']:
        session['cart'][product_id] = int(qty)
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form['product_id']
    if product_id in session['cart']:
        del session['cart'][product_id]
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    total = 0
    for product_id, qty in session['cart'].items():
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        c.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
        price = c.fetchone()[0]
        total += price * qty
        conn.close()
    return render_template('cart.html', cart=session['cart'], total=total)

@app.route('/checkout')
def checkout():
    if 'cart' not in session or len(session['cart']) == 0:
        return redirect(url_for('products'))
    return render_template('checkout.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form['name']
    email = request.form['email']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zip = request.form['zip']
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (name, email, address, city, state, zip) VALUES (?, ?, ?, ?, ?, ?)", (name, email, address, city, state, zip))
    order_id = c.lastrowid
    for product_id, qty in session['cart'].items():
        c.execute("INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)", (order_id, product_id, qty))
    conn.commit()
    conn.close()
    session['cart'] = {}
    return redirect(url_for('order_confirmation', order_id=order_id))

@app.route('/order_confirmation/<order_id>')
def order_confirmation(order_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order = c.fetchone()
    c.execute("SELECT products.name, products.price, order_items.qty FROM order_items JOIN products ON order_items.product_id = products.product_id WHERE order_id = ?", (order_id,))
    order_items = c.fetchall()
    total = 0
    for item in order_items:
        total += item[1] * item[2]
    conn.close()
    return render_template('order_confirmation.html', order=order, order_items=order_items, total=total)

@app.route('/account')
def account():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return render_template('account.html', user=user)

@app.route('/update_account', methods=['POST'])
def update_account():
    username = request.form['username']
    email = request.form['email']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zip = request.form['zip']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET email = ?, address = ?, city = ?, state = ?, zip = ? WHERE username = ?", (email, address, city, state, zip, username))
    conn.commit()
    conn.close()
    return redirect(url_for('account'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

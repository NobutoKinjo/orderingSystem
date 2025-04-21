# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farm_shop.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/farm_shop'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# メール設定
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nobuto0502@gmail.com'  # 実際のメールアドレスに変更
app.config['MAIL_PASSWORD'] = 'nobuto002047'  # 実際のパスワードに変更
app.config['MAIL_DEFAULT_SENDER'] = 'nobuto0502@gmail.com'  # 実際のメールアドレスに変更

db = SQLAlchemy(app)
mail = Mail(app)

# モデル定義
class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    products = db.relationship('Product', backref='farmer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)
    stock_items = db.relationship('Stock', backref='product', lazy=True)
    shipping_items = db.relationship('ShippingProduct', backref='product', lazy=True)

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    stocks = db.relationship('Stock', backref='shop', lazy=True)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='staff')  # staff, admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ShippingProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='available')  # available, shipped

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ルート定義
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Staff.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('ログインしました', 'success')
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが間違っています', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('ログアウトしました', 'success')
    return redirect(url_for('login'))

# 農家と農作物の管理画面
@app.route('/farmers')
def farmers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    farmers = Farmer.query.all()
    return render_template('farmers.html', farmers=farmers)

@app.route('/farmers/add', methods=['GET', 'POST'])
def add_farmer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        
        new_farmer = Farmer(name=name, address=address, phone=phone, email=email)
        db.session.add(new_farmer)
        db.session.commit()
        
        flash('農家を追加しました', 'success')
        return redirect(url_for('farmers'))
    
    return render_template('add_farmer.html')

@app.route('/farmers/edit/<int:id>', methods=['GET', 'POST'])
def edit_farmer(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    farmer = Farmer.query.get_or_404(id)
    
    if request.method == 'POST':
        farmer.name = request.form['name']
        farmer.address = request.form['address']
        farmer.phone = request.form['phone']
        farmer.email = request.form['email']
        
        db.session.commit()
        flash('農家情報を更新しました', 'success')
        return redirect(url_for('farmers'))
    
    return render_template('edit_farmer.html', farmer=farmer)

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        farmer_id = request.form['farmer_id']
        
        new_product = Product(name=name, description=description, farmer_id=farmer_id)
        db.session.add(new_product)
        db.session.commit()
        
        flash('農作物を追加しました', 'success')
        return redirect(url_for('products'))
    
    farmers = Farmer.query.all()
    return render_template('add_product.html', farmers=farmers)

# ショップ情報登録画面
@app.route('/shops')
def shops():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    shops = Shop.query.all()
    return render_template('shops.html', shops=shops)

@app.route('/shops/add', methods=['GET', 'POST'])
def add_shop():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        
        new_shop = Shop(name=name, address=address, phone=phone, email=email)
        db.session.add(new_shop)
        db.session.commit()
        
        flash('ショップを追加しました', 'success')
        return redirect(url_for('shops'))
    
    return render_template('add_shop.html')

@app.route('/shops/edit/<int:id>', methods=['GET', 'POST'])
def edit_shop(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    shop = Shop.query.get_or_404(id)
    
    if request.method == 'POST':
        shop.name = request.form['name']
        shop.address = request.form['address']
        shop.phone = request.form['phone']
        shop.email = request.form['email']
        
        db.session.commit()
        flash('ショップ情報を更新しました', 'success')
        return redirect(url_for('shops'))
    
    return render_template('edit_shop.html', shop=shop)

# 担当者登録画面
@app.route('/staff')
def staff():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('権限がありません', 'danger')
        return redirect(url_for('index'))
    
    staff = Staff.query.all()
    return render_template('staff.html', staff=staff)

@app.route('/staff/add', methods=['GET', 'POST'])
def add_staff():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('権限がありません', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        
        existing_user = Staff.query.filter_by(username=username).first()
        if existing_user:
            flash('このユーザー名は既に使用されています', 'danger')
            return render_template('add_staff.html')
        
        new_staff = Staff(username=username, name=name, email=email, phone=phone, role=role)
        new_staff.set_password(password)
        db.session.add(new_staff)
        db.session.commit()
        
        flash('担当者を追加しました', 'success')
        return redirect(url_for('staff'))
    
    return render_template('add_staff.html')

# 農家の発送可能な農作物登録画面
@app.route('/shipping_products/farmer/<int:farmer_id>', methods=['GET', 'POST'])
def farmer_shipping_products(farmer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    farmer = Farmer.query.get_or_404(farmer_id)
    products = Product.query.filter_by(farmer_id=farmer_id).all()
    
    if request.method == 'POST':
        staff_emails = [staff.email for staff in Staff.query.all()]
        
        for product in products:
            quantity = request.form.get(f'quantity_{product.id}', 0)
            if int(quantity) > 0:
                shipping_product = ShippingProduct(product_id=product.id, quantity=int(quantity))
                db.session.add(shipping_product)
        
        db.session.commit()
        
        # メール送信
        msg = Message(
            subject=f"{farmer.name}から発送可能な農作物のお知らせ",
            recipients=staff_emails,
            body=f"""
            {farmer.name}から発送可能な農作物が登録されました。
            
            詳細は管理システムにてご確認ください。
            """
        )
        mail.send(msg)
        
        flash('発送可能な農作物を登録しました。担当者にメールを送信しました。', 'success')
        return redirect(url_for('farmers'))
    
    return render_template('farmer_shipping_products.html', farmer=farmer, products=products)

# 担当者が各農家の発送可能な農作物を確認する画面
@app.route('/available_products')
def available_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    shipping_products = ShippingProduct.query.filter_by(status='available').all()
    return render_template('available_products.html', shipping_products=shipping_products)

# 在庫管理画面
@app.route('/stock')
def stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stocks = Stock.query.all()
    return render_template('stock.html', stocks=stocks)

@app.route('/stock/add', methods=['GET', 'POST'])
def add_stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        shop_id = request.form['shop_id']
        quantity = request.form['quantity']
        
        existing_stock = Stock.query.filter_by(product_id=product_id, shop_id=shop_id).first()
        
        if existing_stock:
            existing_stock.quantity = int(quantity)
        else:
            new_stock = Stock(product_id=product_id, shop_id=shop_id, quantity=int(quantity))
            db.session.add(new_stock)
        
        db.session.commit()
        flash('在庫を更新しました', 'success')
        return redirect(url_for('stock'))
    
    products = Product.query.all()
    shops = Shop.query.all()
    return render_template('add_stock.html', products=products, shops=shops)

@app.route('/stock/edit/<int:id>', methods=['GET', 'POST'])
def edit_stock(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stock = Stock.query.get_or_404(id)
    
    if request.method == 'POST':
        stock.quantity = int(request.form['quantity'])
        db.session.commit()
        flash('在庫を更新しました', 'success')
        return redirect(url_for('stock'))
    
    return render_template('edit_stock.html', stock=stock)

if __name__ == '__main__':
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    with app.app_context():
        db.create_all()
        
        # 管理者アカウントがなければ作成
        admin = Staff.query.filter_by(username='admin').first()
        if not admin:
            admin = Staff(username='admin', name='管理者', email='admin@example.com', role='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True)

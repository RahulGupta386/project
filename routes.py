from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from forms import LoginForm, RegistrationForm, SearchForm
from models import User, CartItem, Order
from mock_data import PRODUCT_DATA, search_products # Added import for search_products

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    results = []
    if form.validate_on_submit() or request.args.get('query'):
        query = form.query.data or request.args.get('query')
        found_products = search_products(query)
        # Flatten the results for display
        for product_name, stores in found_products.items():
            for item in stores:
                item['product_name'] = product_name  # Add product name to each result
                results.append(item)
    return render_template('search.html', form=form, results=results)

@app.route('/add_to_cart/<store>/<product>/<float:price>')
@login_required
def add_to_cart(store, product, price):
    cart_item = CartItem(user_id=current_user.id, product_name=product,
                        price=price, store=store)
    db.session.add(cart_item)
    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('search'))

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    for item in cart_items:
        order = Order(user_id=current_user.id, product_name=item.product_name,
                     price=item.price, quantity=item.quantity, store=item.store)
        db.session.add(order)
        db.session.delete(item)
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('history.html', orders=orders)
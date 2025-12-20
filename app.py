from flask import Flask, render_template, request, redirect, url_for, session
from db import get_db
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', ye020209)

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products LIMIT 6")
    popular_products = cur.fetchall()
    return render_template("index.html", products=popular_products)

@app.route("/catalog")
@app.route("/catalog/<int:category_id>")
def catalog_page(category_id=None):
    db = get_db()
    cur = db.cursor()
    
    
    cur.execute("SELECT * FROM categories WHERE parent_id IS NULL")
    main_categories = cur.fetchall()
    
    subcategories = []
    products = []
    current_category = None

    if category_id:
        
        cur.execute("SELECT * FROM categories WHERE id=?", (category_id,))
        current_category = cur.fetchone()

        
        cur.execute("SELECT * FROM categories WHERE parent_id=?", (category_id,))
        subcategories = cur.fetchall()

        
        all_ids = [category_id] + [sub['id'] for sub in subcategories]
        placeholders = ",".join("?" * len(all_ids))
        cur.execute(f"SELECT * FROM products WHERE category_id IN ({placeholders})", all_ids)
        products = cur.fetchall()
    
    return render_template(
        "catalog.html",
        main_categories=main_categories,
        subcategories=subcategories,
        products=products,
        current_category=current_category
    )

@app.route("/product/<int:product_id>")
def product_page(product_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    return render_template("product.html", product=product)

@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    db = get_db()
    cur = db.cursor()
    items = []
    total = 0
    for product_id, qty in cart.items():
        cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = cur.fetchone()
        if product:
            product_data = dict(product)
            product_data["qty"] = qty
            product_data["total_price"] = qty * product_data["price"]
            total += product_data["total_price"]
            items.append(product_data)
    return render_template("cart.html", items=items, total=total)

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("index"))

@app.route("/clear_cart")
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("cart"))

@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        customer_name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]
        comment = request.form.get("comment", "")
        cart_data = session.get("cart", {})
        if not cart_data:
            return redirect(url_for("cart"))
        db = get_db()
        cur = db.cursor()
        total_price = 0
        items_list = []
        for product_id, qty in cart_data.items():
            cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
            product = cur.fetchone()
            if product:
                price = product["price"]
                total_price += price * qty
                items_list.append({"id": product_id, "name": product["name"], "qty": qty, "price": price})
        import json
        cur.execute(
            "INSERT INTO orders (customer_name, phone, address, comment, items, total_price) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_name, phone, address, comment, json.dumps(items_list), total_price)
        )
        db.commit()
        session["cart"] = {}
        return render_template("order.html", success=True)
    return render_template("order.html", success=False)

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")


if __name__ == "__main__":
    app.run(debug=True)


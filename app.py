from flask import Flask, render_template, request, redirect, url_for, session
from db import get_db
import json
from datetime import datetime



app = Flask(__name__)
app.secret_key = "sbgear_secret_key"


@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products LIMIT 6")
    products = cur.fetchall()
    return render_template("index.html", products=products)

@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}


@app.route("/catalog")
@app.route("/catalog/<int:category_id>")
def catalog_page(category_id=None):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM categories WHERE parent_id IS NULL")
    main_categories = cur.fetchall()

    products = []
    current_category = None

    if category_id:
        cur.execute("SELECT * FROM categories WHERE id=?", (category_id,))
        current_category = cur.fetchone()

        cur.execute("SELECT id FROM categories WHERE parent_id=?", (category_id,))
        sub_ids = [row["id"] for row in cur.fetchall()]

        all_ids = [category_id] + sub_ids
        placeholders = ",".join("?" * len(all_ids))

        cur.execute(
            f"SELECT * FROM products WHERE category_id IN ({placeholders})",
            all_ids
        )
        products = cur.fetchall()

    return render_template(
        "catalog.html",
        main_categories=main_categories,
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
    cart_data = session.get("cart", {})
    db = get_db()
    cur = db.cursor()

    items = []
    total = 0

    for product_id, qty in cart_data.items():
        cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = cur.fetchone()
        if product:
            product = dict(product)
            product["qty"] = qty
            product["total_price"] = product["price"] * qty
            total += product["total_price"]
            items.append(product)

    return render_template("cart.html", items=items, total=total)


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    return redirect(request.referrer or url_for("catalog_page"))


@app.route("/clear_cart")
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("cart"))


@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]
        comment = request.form.get("comment", "")

        cart_data = session.get("cart", {})
        if not cart_data:
            return redirect(url_for("cart"))

        db = get_db()
        cur = db.cursor()

        items = []
        total_price = 0

        for product_id, qty in cart_data.items():
            cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
            product = cur.fetchone()
            if product:
                items.append({
                    "id": product["id"],
                    "name": product["name"],
                    "qty": qty,
                    "price": product["price"]
                })
                total_price += product["price"] * qty

        cur.execute(
            """
            INSERT INTO orders (customer_name, phone, address, comment, items, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, phone, address, comment, json.dumps(items), total_price)
        )
        db.commit()

        session["cart"] = {}
        return render_template("order.html", success=True)

    return render_template("order.html", success=False)


@app.route("/contacts")
def contacts():
    return redirect(url_for("index") + "#contacts")


if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_db
import json
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "sbgear_secret_key"
app.config['DATABASE'] = 'sbgear.db'


def row_to_dict(row):
    """Преобразует sqlite3.Row в словарь"""
    if row is None:
        return None
    return dict(row)

def rows_to_dicts(rows):
    """Преобразует список sqlite3.Row в список словарей"""
    return [dict(row) for row in rows] if rows else []


def generate_triplets(text):
    """Генерирует триплеты (группы по 3 буквы) для поиска"""
    if not text:
        return set()
    text = text.lower().replace(" ", "")
    triplets = set()
    for i in range(len(text) - 2):
        triplets.add(text[i:i+3])
    return triplets

def calculate_similarity(query, target):
    """Вычисляет сходство по триплетам"""
    query_triplets = generate_triplets(query)
    target_triplets = generate_triplets(target)
    
    if not query_triplets or not target_triplets:
        return 0
    
    intersection = query_triplets.intersection(target_triplets)
    similarity = len(intersection) / len(query_triplets)
    return similarity

def smart_search(query, products, threshold=0.3):
    """Умный поиск товаров с учетом опечаток"""
    if not query or len(query.strip()) < 2:
        return products
    
    query = query.strip().lower()
    scored_products = []
    
    fields_to_check = ['name', 'description', 'manufacturer', 'article']
    
    for product in products:
        max_similarity = 0
        
        for field in fields_to_check:
            if field in product and product[field]:
                field_value = str(product[field]).lower()
                
                if query in field_value:
                    max_similarity = max(max_similarity, 1.0)
                    continue
                
                similarity = calculate_similarity(query, field_value)
                max_similarity = max(max_similarity, similarity)
        
        if max_similarity >= threshold:
            scored_products.append((product, max_similarity))
    
    scored_products.sort(key=lambda x: x[1], reverse=True)
    return [product for product, _ in scored_products]


@app.context_processor
def inject_now():
    """Добавляет переменные во все шаблоны"""
    return {
        'current_year': datetime.now().year,
        'cart_count': sum(session.get('cart', {}).values()) if session.get('cart') else 0
    }


@app.route("/")
def index():
    """Главная страница"""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products LIMIT 6")
    products = rows_to_dicts(cur.fetchall())
    return render_template("index.html", products=products)


@app.route("/catalog")
@app.route("/catalog/<int:category_id>")
def catalog_page(category_id=None):
    """Страница каталога товаров"""
    db = get_db()
    cur = db.cursor()
    
    search_query = request.args.get('search', '').strip()

    cur.execute("SELECT * FROM categories WHERE parent_id IS NULL")
    main_categories = rows_to_dicts(cur.fetchall())

    cur.execute("SELECT * FROM categories WHERE parent_id IS NOT NULL")
    subcategories = rows_to_dicts(cur.fetchall())

    products = []
    current_category = None

    if category_id:

        cur.execute("SELECT * FROM categories WHERE id=?", (category_id,))
        current_category = row_to_dict(cur.fetchone())

        if current_category:

            cur.execute("SELECT id FROM categories WHERE parent_id=?", (category_id,))
            sub_ids = [row["id"] for row in cur.fetchall()]

            all_ids = [category_id] + sub_ids
            placeholders = ",".join("?" * len(all_ids))
            cur.execute(
                f"SELECT * FROM products WHERE category_id IN ({placeholders})",
                all_ids
            )
            products = rows_to_dicts(cur.fetchall())

    if not products or not category_id:

        cur.execute("SELECT * FROM products")
        products = rows_to_dicts(cur.fetchall())


    if search_query:
        products = smart_search(search_query, products)
    
    return render_template(
        "catalog.html",
        main_categories=main_categories,
        subcategories=subcategories,
        products=products,
        current_category=current_category,
        search_query=search_query
    )

@app.route("/search", methods=["GET"])
def search():
    """Страница поиска товаров"""
    search_query = request.args.get('q', '').strip()
    
    if not search_query:
        return redirect(url_for('catalog_page'))
    
    db = get_db()
    cur = db.cursor()
    
    cur.execute("SELECT * FROM categories WHERE parent_id IS NULL")
    main_categories = rows_to_dicts(cur.fetchall())

    cur.execute("SELECT * FROM categories WHERE parent_id IS NOT NULL")
    subcategories = rows_to_dicts(cur.fetchall())


    cur.execute("SELECT * FROM products")
    all_products = rows_to_dicts(cur.fetchall())
    

    products = smart_search(search_query, all_products)
    
    return render_template(
        "catalog.html",
        main_categories=main_categories,
        subcategories=subcategories,
        products=products,
        current_category=None,
        search_query=search_query
    )


@app.route("/product/<int:product_id>")
def product_page(product_id):
    """Детальная страница товара"""
    db = get_db()
    cur = db.cursor()
    

    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = row_to_dict(cur.fetchone())
    
    if not product:
        return redirect(url_for('catalog_page'))
    

    category = None
    parent_category = None
    if product.get('category_id'):
        cur.execute("SELECT * FROM categories WHERE id=?", (product['category_id'],))
        category = row_to_dict(cur.fetchone())
        

        if category and category.get('parent_id'):
            cur.execute("SELECT * FROM categories WHERE id=?", (category['parent_id'],))
            parent_category = row_to_dict(cur.fetchone())
    

    similar_products = []
    if product.get('category_id'):
        cur.execute("""
            SELECT * FROM products 
            WHERE category_id = ? AND id != ? 
            LIMIT 4
        """, (product['category_id'], product_id))
        similar_products = rows_to_dicts(cur.fetchall())
    

    reviews = []
    avg_rating = 0
    try:
        cur.execute("""
            SELECT * FROM reviews 
            WHERE product_id = ? 
            ORDER BY created_at DESC
            LIMIT 5
        """, (product_id,))
        reviews = rows_to_dicts(cur.fetchall())
        
        if reviews:
            total_rating = sum(review.get('rating', 0) for review in reviews)
            avg_rating = round(total_rating / len(reviews), 1)
    except sqlite3.Error:
        pass
    

    viewed_products = []
    viewed_ids = session.get('viewed_products', [])
    if viewed_ids:
        placeholders = ','.join('?' * len(viewed_ids))
        cur.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders}) AND id != ? LIMIT 4", 
            viewed_ids + [product_id]
        )
        viewed_products = rows_to_dicts(cur.fetchall())
    

    if 'viewed_products' not in session:
        session['viewed_products'] = []
    
    if product_id not in session['viewed_products']:
        session['viewed_products'].insert(0, product_id)
        session['viewed_products'] = session['viewed_products'][:10]
        session.modified = True
    
    return render_template(
        "product.html",
        product=product,
        category=category,
        parent_category=parent_category,
        similar_products=similar_products,
        reviews=reviews,
        avg_rating=avg_rating,
        viewed_products=viewed_products
    )

@app.route("/cart")
def cart():
    """Страница корзины"""
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


    recommended_products = []
    if items:

        category_ids = list(set(item.get('category_id') for item in items if item.get('category_id')))
        if category_ids:
            placeholders = ','.join('?' * len(category_ids))
            cart_ids = list(cart_data.keys())
            cart_placeholders = ','.join('?' * len(cart_ids)) if cart_ids else 'NULL'
            
            query = f"""
                SELECT * FROM products 
                WHERE category_id IN ({placeholders}) 
                AND id NOT IN ({cart_placeholders if cart_ids else '0'})
                LIMIT 4
            """
            
            params = category_ids + cart_ids if cart_ids else category_ids
            cur.execute(query, params)
            recommended_products = rows_to_dicts(cur.fetchall())

    return render_template("cart.html", 
                         items=items, 
                         total=total,
                         recommended_products=recommended_products)

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    """Добавление товара в корзину"""
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'cart_count': sum(cart.values())
        })
    
    return redirect(request.referrer or url_for("catalog_page"))

@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    """Уменьшение количества товара в корзине"""
    cart = session.get("cart", {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        else:
            del cart[product_id_str]
        session["cart"] = cart
    
    return redirect(url_for("cart"))

@app.route("/delete_from_cart/<int:product_id>")
def delete_from_cart(product_id):
    """Полное удаление товара из корзины"""
    cart = session.get("cart", {})
    product_id_str = str(product_id)
    if product_id_str in cart:
        del cart[product_id_str]
        session["cart"] = cart
    
    return redirect(url_for("cart"))

@app.route("/clear_cart")
def clear_cart():
    """Очистка всей корзины"""
    session["cart"] = {}
    return redirect(url_for("cart"))

@app.route("/update_cart", methods=["POST"])
def update_cart():
    """Обновление количества товаров в корзине"""
    cart = session.get("cart", {})
    

    action = request.form.get('action')
    product_id = request.form.get('product_id')
    
    if action and product_id:
        if action == 'increase':
            cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        elif action == 'decrease' and str(product_id) in cart:
            if cart[str(product_id)] > 1:
                cart[str(product_id)] -= 1
            else:
                del cart[str(product_id)]
    else:

        for key, value in request.form.items():
            if key.startswith('qty_'):
                pid = key[4:] 
                try:
                    qty_int = int(value)
                    if qty_int > 0:
                        cart[pid] = qty_int
                    else:
                        if pid in cart:
                            del cart[pid]
                except ValueError:
                    pass
    
    session["cart"] = cart
    

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'cart_count': sum(cart.values())
        })
    
    return redirect(url_for("cart"))


@app.route("/order", methods=["GET", "POST"])
def order():
    """Страница оформления заказа"""
    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        city = request.form.get("city", "")
        address = request.form["address"]
        email = request.form.get("email", "")
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


        try:
            cur.execute(
                """
                INSERT INTO orders (customer_name, phone, email, city, address, comment, items, total_price, order_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, phone, email, city, address, comment, json.dumps(items), total_price, datetime.now())
            )
            
            order_id = cur.lastrowid
            db.commit()
            

            session["cart"] = {}
            return render_template("order.html", success=True, order_id=order_id, total_price=total_price)
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return render_template("order.html", success=False, error="Помилка бази даних")


    cart_data = session.get("cart", {})
    if not cart_data:
        return redirect(url_for("cart"))
    

    db = get_db()
    cur = db.cursor()
    items = []
    for product_id, qty in cart_data.items():
        cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = cur.fetchone()
        if product:
            product_dict = dict(product)
            product_dict["qty"] = qty
            items.append(product_dict)
    
    return render_template("order.html", success=False, items=items)

@app.route("/add_review/<int:product_id>", methods=["POST"])
def add_review(product_id):
    """Добавление отзыва к товару"""
    if request.method == "POST":
        name = request.form.get("name", "Аноним")
        rating = int(request.form.get("rating", 5))
        comment = request.form.get("comment", "")
        
        db = get_db()
        cur = db.cursor()
        
        try:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    name TEXT,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            """)
            

            cur.execute(
                "INSERT INTO reviews (product_id, name, rating, comment) VALUES (?, ?, ?, ?)",
                (product_id, name, rating, comment)
            )
            db.commit()
        except sqlite3.Error as e:
            print(f"Error adding review: {e}")
        
        return redirect(url_for('product_page', product_id=product_id) + '#reviews')


@app.route("/contacts")
def contacts():
    """Страница контактов"""
    return redirect(url_for("index") + "#contacts")


@app.route("/admin/orders")
def admin_orders():
    """Страница управления заказами"""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM orders ORDER BY order_date DESC")
    orders = rows_to_dicts(cur.fetchall())
    return render_template("admin_orders.html", orders=orders)

@app.route("/api/cart_count")
def api_cart_count():
    """API для получения количества товаров в корзине"""
    cart_data = session.get("cart", {})
    total_items = sum(cart_data.values()) if cart_data else 0
    return jsonify({"count": total_items})

@app.route("/api/product/<int:product_id>")
def api_product_info(product_id):
    """API для получения информации о товаре"""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, name, price, image, article FROM products WHERE id=?", (product_id,))
    product = cur.fetchone()
    
    if product:
        return jsonify({
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "article": product["article"]
        })
    return jsonify({"error": "Product not found"}), 404

@app.route("/api/cart_info")
def api_cart_info():
    """API для получения информации о корзине"""
    cart_data = session.get("cart", {})
    db = get_db()
    cur = db.cursor()
    
    items = []
    total = 0
    
    for product_id, qty in cart_data.items():
        cur.execute("SELECT id, name, price, image FROM products WHERE id=?", (product_id,))
        product = cur.fetchone()
        if product:
            product_dict = dict(product)
            product_dict["qty"] = qty
            product_dict["total_price"] = product_dict["price"] * qty
            total += product_dict["total_price"]
            items.append(product_dict)
    
    return jsonify({
        "items": items,
        "total": total,
        "count": sum(cart_data.values()) if cart_data else 0
    })

@app.route("/api/update_quantity", methods=["POST"])
def api_update_quantity():
    """API для обновления количества товара"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    if not product_id or not isinstance(quantity, int) or quantity < 0:
        return jsonify({"error": "Invalid data"}), 400
    
    cart = session.get("cart", {})
    
    if quantity == 0:
        if str(product_id) in cart:
            del cart[str(product_id)]
    else:
        cart[str(product_id)] = quantity
    
    session["cart"] = cart
    
    return jsonify({
        "success": True,
        "cart_count": sum(cart.values())
    })


@app.errorhandler(404)
def page_not_found(e):
    """Обработка 404 ошибки"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Обработка 500 ошибки"""
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
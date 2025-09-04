from models import db, User, Order,Food
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from fpdf import FPDF
from models import db, Order, Food
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@localhost/aimanager"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from flask import request, jsonify


@app.route("/admin/update", methods=["POST"])
def admin_update():
    if "user_id" not in session or session["user_id"] != 1:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    food_id = data.get("food_id")
    quantity = int(data.get("quantity"))

    food_item = Food.query.get(food_id)
    if food_item:
        food_item.quantity = quantity
        db.session.commit()
        return jsonify({"status": "success", "new_quantity": food_item.quantity})

    return jsonify({"status": "error"}), 400


@app.route('/')
def home():
    return render_template("Main.html")

@app.route('/order', methods=["POST", "GET"])
def order():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        pq1 = int(request.form.get("pizza_qty") or 0)
        pq2 = int(request.form.get("burger_qty") or 0)
        pq3 = int(request.form.get("fries_qty") or 0)

        items_ordered = []

        # Fetch foods
        pizza = Food.query.get(1)
        burger = Food.query.get(2)
        fries = Food.query.get(3)

        # Pizza
        if pq1 >=0 and pizza.quantity >= pq1:
            pizza.quantity -= pq1
            db.session.add(Order(item_name="Pizza", quantity=pq1, user_id=session["user_id"]))
            items_ordered.append(("Pizza", pq1))
            db.session.add(pizza)

        # Burger
        if pq2 >=0 and burger.quantity >= pq2:
            burger.quantity -= pq2
            db.session.add(Order(item_name="Burger", quantity=pq2, user_id=session["user_id"]))
            items_ordered.append(("Burger", pq2))
            db.session.add(burger)

        # Fries
        if pq3 >=0 and fries.quantity >= pq3:
            fries.quantity -= pq3
            db.session.add(Order(item_name="Fries", quantity=pq3, user_id=session["user_id"]))
            items_ordered.append(("Fries", pq3))
            db.session.add(fries)

        if len(items_ordered)!=3:
            return "<h3>Sorry We dont have necessary Quantities</h3>"

        db.session.commit()

        # Generate PDF with table
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Food Order Bill", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(0, 10, f"User ID: {session['user_id']}", ln=True)
        pdf.ln(10)

        # Table header
        pdf.set_font("Arial", "B", 12)
        pdf.cell(80, 10, "Item", border=1)
        pdf.cell(40, 10, "Quantity", border=1, ln=True)

        # Table rows
        pdf.set_font("Arial", "", 12)
        for item, qty in items_ordered:
            pdf.cell(80, 10, item, border=1)
            pdf.cell(40, 10, str(qty), border=1, ln=True)

        # Save PDF to memory correctly
        pdf_bytes = pdf.output(dest='S').encode('latin1')  # returns bytes
        pdf_buffer = io.BytesIO(pdf_bytes)

        return send_file(pdf_buffer, as_attachment=True, download_name="order_bill.pdf", mimetype="application/pdf")

    return render_template("Orderfood.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user_id" not in session or session["user_id"] != 1:
        return """
        <script>
            alert("Unauthorized access! Only admin can login here.");
            window.location.href = "/login";
        </script>
        """

    if request.method == "POST":
        food_id = request.form.get("food_id")
        new_quantity = request.form.get("quantity")

        food_item = Food.query.get(food_id)
        if food_item:
            food_item.quantity = int(new_quantity)
            db.session.commit()

        return redirect(url_for("admin"))

    foods = Food.query.all()
    return render_template("admin.html", foods=foods)



@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=username, password=password).first()

        if user:
            session["user_id"] = user.id
            session["username"] = user.name
            return redirect(url_for("home"))
        else:
            return "Invalid username or password"

    return render_template("Login.html")

@app.route("/myorders")
def myorders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template("MyOrders.html", name=session["username"], orders=orders)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone_number = request.form.get("phone")
        password = request.form.get("password")

        new_user = User(
            name=name,
            email=email,
            phone_number=phone_number,
            password=password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("Signup.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

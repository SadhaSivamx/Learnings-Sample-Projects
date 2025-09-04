from flask import Flask, render_template, request, redirect, url_for, session, send_file
from databases import User,Calorie,db
import requests
from flask import request
from datetime import datetime, timedelta
from sqlalchemy import text
from Model import fn
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@localhost/calorietrack"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/analytics', methods=["GET", "POST"])
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)

    if request.method == "POST":
        start_str = request.form.get("start_date")
        end_str = request.form.get("end_date")

        if start_str and end_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
            except ValueError:
                pass

    sql = text("""
        SELECT 
            SUM(total_calories) AS total_calories,
            SUM(protein) AS total_protein,
            SUM(carbs) AS total_carbs,
            SUM(fats) AS total_fats
        FROM calorie
        WHERE user_id = :uid
        AND created_at BETWEEN :start_date AND :end_date
    """)

    result = db.session.execute(sql, {
        "uid": user_id,
        "start_date": start_date,
        "end_date": end_date
    }).fetchone()

    return render_template(
        "Analytics.html",
        total_calories=result.total_calories or 0,
        total_protein=result.total_protein or 0,
        total_carbs=result.total_carbs or 0,
        total_fats=result.total_fats or 0,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )

@app.route('/')
def home():
    return render_template("Main.html")

@app.route('/eat', methods=["POST", "GET"])
def eat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        quantity=int(request.form.get("quantity"))
        file = request.files.get("food_image")
        if not file:
            return "No image uploaded", 400

        url = "http://127.0.0.1:3000/api/predict"
        files = {"file": file}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            data = response.json()
            prediction = data['prediction']
            confidence = data['confidence']
            nutrition = fn[data['prediction']]
            if prediction!="Unknown":
                nC=Calorie(fname=prediction,user_id=session.get("user_id"),total_calories=nutrition["calories"]*quantity
                        ,protein=nutrition["proteins"]*quantity,carbs=nutrition["carbs"]*quantity,fats=nutrition["fats"]*quantity)
                try:
                    db.session.add(nC)
                    db.session.commit()
                    print(prediction, confidence, nutrition)
                    return redirect(url_for("eat"))
                except Exception as e:
                    return f"Error: {str(e)}"
            return render_template("FoodRec.html")
        else:
            return f"Prediction API Error: {response.text}", 500

    return render_template("FoodRec.html")

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

@app.route("/signout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@localhost/aimanager"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.name}>"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    foodname = db.Column(db.String(120), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Food {self.foodname} ({self.quantity} available)>"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
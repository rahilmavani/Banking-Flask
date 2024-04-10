from flask import Flask, render_template, redirect, session, request
from flask_session import Session
from cs50 import SQL
import random, string

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///bank.db")

db.execute(""" CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    account_number TEXT UNIQUE NOT NULL,
                    balance NUMERIC DEFAULT 0)
           """)

db.execute(""" CREATE TABLE IF NOT EXISTS banker
               ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                passkey TEXT UNIQUE NOT NULL)
               """)
db.execute(""" CREATE TABLE IF NOT EXISTS passkeys
                (keys TEXT UNIQUE NOT NULL)
           """)
keys_to_insert = ["secret101", "universe42"]

for key in keys_to_insert:
    existing_key = db.execute("SELECT keys FROM passkeys WHERE keys = ?", key)
    if not existing_key:
        db.execute("INSERT INTO passkeys (keys) VALUES (?)", key)

def generate_account_number():
    while True:
        account_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
        existing_account = db.execute("SELECT * FROM users WHERE account_number = ?", account_number)
        if not existing_account:
            return account_number

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        check = db.execute("SELECT username FROM users WHERE username = ?", username)
        if check:
            return render_template("register.html", error = "Account already registered.")

        account_number = generate_account_number()
        db.execute("INSERT INTO users (username, password, account_number) VALUES (?, ?, ?)", username, password, account_number)
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", username, password)
        if len(user) == 1:
            session["user_id"] = user[0]["id"]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error = "Invalid username or password")
    else:
        return render_template("login.html", error = "")
    
@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    user_id = session.get("user_id")
    if user_id == None:
        redirect ("/")
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]

    if request.method == "POST":
        if request.form["action"] == "deposit":
            amount = int(request.form.get("amount"))
            db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", amount, user_id)
            return redirect("/dashboard")

        elif request.form["action"] == "withdraw":
            amount = int(request.form.get("amount"))
            balance = int(user["balance"])
            if balance >= amount:
                db.execute("UPDATE users SET balance = balance - ? WHERE id = ?", amount, user_id)
                return redirect("/dashboard")
            else:
                return redirect("/dashboard")
        elif request.form["action"] == "transfer":
            amount = int(request.form.get("transfer_amount"))
            balance = int(user["balance"])
            to_username = request.form.get("to_username") 

            recipient = db.execute("SELECT * FROM users WHERE username = ?", to_username)
            if not recipient:
                return render_template("dashboard.html", error="Recipient username does not exist.")

            if balance >= amount:
                db.execute("UPDATE users SET balance = balance - ? WHERE id = ?", amount, user_id)
                db.execute("UPDATE users SET balance = balance + ? WHERE username = ?", amount, to_username)
                return redirect("/dashboard")
            else:
                return render_template("dashboard.html", error="Insufficient Balance.")
    return render_template("dashboard.html", user = user)

@app.route("/logout", methods = ["GET", "POST"])
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/banker_reg", methods=["GET", "POST"])
def banker_reg():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        passkey = request.form.get("passkey")

        check = db.execute("SELECT username FROM banker WHERE username = ?", username)
        if check:
            return render_template("banker_reg.html", error="Account already registered.")

        passkey_check = db.execute("SELECT * FROM passkeys WHERE keys = ?", passkey)
        if not passkey_check:
            return render_template("banker_reg.html", error="Invalid passkey.")

        db.execute("INSERT INTO banker (username, password, passkey) VALUES (?, ?, ?)", username, password, passkey)
        return redirect("/")
    else:
        return render_template("banker_reg.html")


@app.route("/banker_login", methods = ["GET", "POST"])
def banker_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        banker = db.execute("SELECT * FROM banker WHERE username = ? AND password = ?", username, password)
        if len(banker) == 1:
            session["banker_id"] = banker[0]["id"]
            return redirect("/banker_dashboard")
        else:
            return render_template("banker_login.html", error = "Invalid username or password")
    else:
        return render_template("banker_login.html", error = "")

@app.route("/banker_dashboard")
def banker_dashboard():
    banker_id = session.get("banker_id")
    if banker_id == None:
        redirect ("/")
    users = db.execute("SELECT * FROM users")
    return render_template("banker_dashboard.html", users=users)


if __name__ == "__main__":
    app.run(debug = True)

from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from cs50 import SQL
import random
import string

app = Flask(__name__)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///bank.db")



db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            balance NUMERIC DEFAULT 0
        )
    """)

# Helper function to generate a unique account number
def generate_account_number():
    while True:
        account_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        existing_account = db.execute("SELECT * FROM users WHERE account_number = ?", account_number)
        if not existing_account:
            return account_number

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        account_number = generate_account_number()
        db.execute("INSERT INTO users (username, password, account_number) VALUES (?, ?, ?)",
                   username, password, account_number)
        return redirect('/')
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", username, password)
        if len(user) == 1:
            session['user_id'] = user[0]['id']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")
    else:
        return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect('/')
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    
    if request.method == 'POST':
        if request.form['action'] == 'deposit':
            amount = float(request.form.get('amount'))
            db.execute("UPDATE users SET balance = balance + ? WHERE id = ?", amount, user_id)
            return redirect('/dashboard')
        elif request.form['action'] == 'withdraw':
            amount = float(request.form.get('amount'))
            balance = float(user['balance'])  # Convert balance to float
            if balance >= amount:
                db.execute("UPDATE users SET balance = balance - ? WHERE id = ?", amount, user_id)
                return redirect('/dashboard')
            else:
                error = "Insufficient balance"
                return render_template('dashboard.html', user=user, error=error)
    
    return render_template('dashboard.html', user=user)


@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

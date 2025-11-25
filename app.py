import os
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Auto reload templates
app.config["TEMPLATES_AUTO_RELOAD"] = True

# No caching
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Jinja USD filter
app.jinja_env.filters["usd"] = usd

# Session
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database
db = SQL("sqlite:///finance.db")

# API key must be set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


# ============================
# INDEX
# ============================
@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT * FROM portfolio WHERE userid = :id", id=session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])[0]['cash']
    total = cash

    for row in rows:
        quote = lookup(row["symbol"])
        row["name"] = quote["name"]
        row["price"] = quote["price"]
        row["total"] = row["price"] * row["shares"]
        total += row["total"]
        row["price"] = usd(row["price"])
        row["total"] = usd(row["total"])

    return render_template("index.html", rows=rows, cash=usd(cash), sum=usd(total))


# ============================
# BUY
# ============================
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    symbol = request.form.get("symbol")
    shares = request.form.get("shares")

    quote = lookup(symbol)

    if not quote:
        return apology("invalid stock symbol", 400)

    if not shares or not shares.isdigit() or int(shares) <= 0:
        return apology("invalid number of shares", 400)

    symbol = symbol.upper()
    shares = int(shares)
    cost = quote["price"] * shares

    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])[0]["cash"]
    if cost > cash:
        return apology("insufficient funds", 400)

    row = db.execute("SELECT * FROM portfolio WHERE userid = :id AND symbol = :symbol",
                     id=session["user_id"], symbol=symbol)

    if len(row) != 1:
        db.execute("INSERT INTO portfolio (userid, symbol, shares) VALUES (:id, :symbol, 0)",
                   id=session["user_id"], symbol=symbol)

    oldshares = db.execute("SELECT shares FROM portfolio WHERE userid = :id AND symbol = :symbol",
                           id=session["user_id"], symbol=symbol)[0]["shares"]

    newshares = oldshares + shares

    db.execute("UPDATE portfolio SET shares = :s WHERE userid = :id AND symbol = :symbol",
               s=newshares, id=session["user_id"], symbol=symbol)

    db.execute("UPDATE users SET cash = :new WHERE id = :id",
               new=cash - cost, id=session["user_id"])

    db.execute("INSERT INTO history (userid, symbol, shares, method, price) VALUES (:id, :symbol, :shares, 'Buy', :price)",
               id=session["user_id"], symbol=symbol, shares=shares, price=quote["price"])

    return redirect("/")


# ============================
# PASSWORD CHANGE
# ============================
@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "GET":
        return render_template("password.html")

    if not request.form.get("oldpass") or not request.form.get("newpass") or not request.form.get("confirm"):
        return apology("missing fields", 400)

    oldpass = request.form.get("oldpass")
    newpass = request.form.get("newpass")
    confirm = request.form.get("confirm")

    hash_old = db.execute("SELECT hash FROM users WHERE id = :id",
                          id=session["user_id"])[0]["hash"]

    if not check_password_hash(hash_old, oldpass):
        return apology("incorrect old password", 400)

    if newpass != confirm:
        return apology("passwords do not match", 400)

    db.execute("UPDATE users SET hash = :h WHERE id = :id",
               h=generate_password_hash(newpass), id=session["user_id"])

    return redirect("/logout")


# ============================
# HISTORY
# ============================
@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT * FROM history WHERE userid = :id", id=session["user_id"])
    return render_template("history.html", rows=rows)


# ============================
# LOGIN
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        if not request.form.get("password"):
            return apology("must provide password", 400)

        rows = db.execute("SELECT * FROM users WHERE username = :u",
                          u=request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username or password", 400)

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")


# ============================
# LOGOUT
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ============================
# QUOTE
# ============================
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")

    data = lookup(request.form.get("symbol"))

    if not data:
        return apology("invalid stock symbol", 400)

    data["price"] = usd(data["price"])

    return render_template("quoted.html", symbol=data)


# ============================
# REGISTER
# ============================
@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        if not request.form.get("password"):
            return apology("must provide password", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        username = request.form.get("username")
        hash_pw = generate_password_hash(request.form.get("password"))

        rows = db.execute("SELECT * FROM users WHERE username = :u", u=username)
        if len(rows) != 0:
            return apology("username already taken", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (:u, :h)",
                   u=username, h=hash_pw)

        return redirect("/")

    return render_template("register.html")


# ============================
# SELL
# ============================
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        portfolio = db.execute("SELECT symbol FROM portfolio WHERE userid = :id",
                               id=session["user_id"])
        return render_template("sell.html", portfolio=portfolio)

    symbol = request.form.get("symbol")
    shares = request.form.get("shares")

    if not shares or not shares.isdigit() or int(shares) <= 0:
        return apology("invalid number of shares", 400)

    shares = int(shares)

    quote = lookup(symbol)

    row = db.execute("SELECT * FROM portfolio WHERE userid = :id AND symbol = :s",
                     id=session["user_id"], s=symbol)

    if len(row) != 1:
        return apology("invalid stock symbol", 400)

    oldshares = row[0]["shares"]

    if shares > oldshares:
        return apology("cannot sell more than you own", 400)

    value = quote["price"] * shares

    cash = db.execute("SELECT cash FROM users WHERE id = :id",
                      id=session["user_id"])[0]["cash"]

    cash += value

    db.execute("UPDATE users SET cash = :c WHERE id = :id",
               c=cash, id=session["user_id"])

    newshares = oldshares - shares

    if newshares > 0:
        db.execute("UPDATE portfolio SET shares = :ns WHERE userid = :id AND symbol = :s",
                   ns=newshares, id=session["user_id"], s=symbol)
    else:
        db.execute("DELETE FROM portfolio WHERE userid = :id AND symbol = :s",
                   id=session["user_id"], s=symbol)

    db.execute("INSERT INTO history (userid, symbol, shares, method, price) VALUES (:id, :sym, :sh, 'Sell', :pr)",
               id=session["user_id"], sym=symbol, sh=shares, pr=quote["price"])

    return redirect("/")


# ============================
# ERROR HANDLING
# ============================
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

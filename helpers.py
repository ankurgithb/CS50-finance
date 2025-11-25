import os
import requests
import urllib.parse

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up **real price** for stock symbol using Alpha Vantage."""

    api_key = os.environ.get("API_KEY")
    if not api_key:
        return None

    try:
        symbol = symbol.upper()

        # GLOBAL_QUOTE gives live price
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={urllib.parse.quote(symbol)}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()

        # If no valid data returned
        if "Global Quote" not in data or not data["Global Quote"]:
            return None

        quote = data["Global Quote"]

        return {
            "symbol": symbol,
            "name": symbol,
            "price": float(quote["05. price"])
        }

    except Exception:
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def is_int(value):
    """Check if a value is an integer."""
    try:
        int(value)
        return True
    except:
        return False

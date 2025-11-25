💰 CS50 Finance — Stock Trading Web App

This project is my implementation of CS50x Problem Set 9: Finance. It’s a full-stack web application where users can register, log in, look up real-time stock prices, buy and sell shares, and track their portfolio and transaction history. The app is built using Flask, SQLite, Python, and the IEX API.

🚀 Features

🔐 User Authentication

Secure registration and login, password hashing, and session handling.

📈 Buying & Selling Stocks

Real-time stock lookup, buy/sell transactions, validation to prevent invalid trades, and instant balance updates.

💼 Portfolio Dashboard

Displays current holdings, stock values, and remaining cash based on real-time prices.

📜 Transaction History

Shows every buy and sell with timestamps and share quantities.

🛠️ Technologies Used
	•	Python (Flask)
	•	SQLite
	•	HTML, CSS, Jinja
	•	IEX Cloud API
	•	Werkzeug for password hashing

📂 Project Structure

application.py — main Flask app
helpers.py — lookup, apology, login_required
finance.db — SQLite database
static/ — CSS files
templates/ — HTML templates (index, buy, sell, register, history, etc.)

📝 How to Run Locally
	1.	Install dependencies:
pip install -r requirements.txt
	2.	Set your API key:
export API_KEY=your_iex_key
	3.	Start the server:
flask run

🎓 About This Project

This project was completed as part of Harvard’s CS50x. It demonstrates backend logic, database design, authentication, API integration, and front-end templating.

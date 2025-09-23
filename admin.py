from flask import Flask, render_template, redirect, url_for
from flask_session import Session
import mysql.connector
import sys
from conn import *


app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False      # The session will expire when the browser is closed
app.config['SESSION_TYPE'] = 'filesystem'    # The session data is stored in the disk

Session(app)                                 # Initialize Flask-session for the web server

db = mysql.connector.connect(
    host=r_host,
    user=r_username,
    password=r_password,
    database=r_database
)
cursor = db.cursor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transaction")
def transaction():
    return render_template("transaction.html", date='26-05-2025')

@app.route("/product_management")
def product_management():
    return render_template("product_management.html")


if __name__ == "__main__":
    app.run(debug=True) # Starts the server in debug mode. This avoids server restarts on code changes
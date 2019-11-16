import os
import requests

from functools import wraps

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Login Required Decorator
# See https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
def index():
    return "Project 1: TODO"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure the username already exists
        user_check = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        if user_check is None:
            return render_template("error.html", headline="Username Error", message="The username you entered does "
                                                                                    "not exist.")

        # Ensure the password is correct
        # flask-bcrypt Usage: bcrypt.check_password_hash(pw_hash, candidate)
        if not bcrypt.check_password_hash(user_check[2].encode('utf-8'), password.encode('utf-8')):
            return render_template("error.html", headline="Password Error", message="The password you entered is " 
                                                                                    "incorrect.")

        # Remember which user has logged in
        session["user_id"] = result[0]
        session["user_name"] = result[1]

        return redirect(url_for("index"))

    else:
        return render_template("login.html", headline="Login Here")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget user id in session
    session.clear()

    # User submits the form via POST
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Check if username already exists
        user_check = db.execute("SELECT * FROM users WHERE username = :username",
                                {"username": username}).fetchone()
        if user_check:
            return render_template("error.html", headline="Error", message="Username already exists.")

        # Check that password matches password confirmation
        elif password != request.form.get("confirmation"):
            return render_template("error.html", headline="Error", message="Passwords do not match.")

        # Hash password documentation: https://flask-bcrypt.readthedocs.io/en/0.7.1/
        # Need to decode hashed password before storing to database: https://stackoverflow.com/a/38262440/6297414
        # Otherwise check password hash would not work as the password format would be wrong
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert username and password to users database
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                   {"username": username, "password": hashed_password})

        # Commit change to users database
        db.commit()

        return redirect(url_for("login"))

    else:
        return render_template("register.html", message="Please register here.")


@app.route("/logout")
def logout():

    # Forget user id
    session.clear()

    return redirect(url_for("login"))



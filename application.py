import os
import requests

from functools import wraps

from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
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
    """ Loads the index page and shows the search box. """
    return render_template("index.html")


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
        session["user_id"] = user_check[0]
        session["user_name"] = user_check[1]
        session["logged_in"] = True

        flash("You are logged in.")
        return redirect(url_for("index"))

    else:
        # Return unlogged-in user to login for logging in
        return render_template("login.html", headline="login here")


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


@app.route("/search", methods=["GET"])
@login_required
def search():
    # https://stackoverflow.com/a/16664376
    # capitalize search query
    query = ('%' + request.args.get("book") + '%').title()

    rows = db.execute(
        "SELECT isbn, title, author, year FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query LIMIT 10",
        {"query": query})

    if rows.rowcount == 0:
        return render_template("error.html", headline="Search Error", message="We cannot find the book "
                                                                              "you are searching for."), 404

    books = rows.fetchall()

    return render_template("results.html", books=books)


@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "GET":

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn})

        # fetchone returns tuple, use fetchall for a list
        book_info = row.fetchall()

        """ FETCH GOODREADS REVIEWS """
        key = os.getenv("GOODREADS_KEY")

        # API call: https://www.goodreads.com/api/index#book.review_counts
        review_query = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})

        if review_query.status_code == 422 or review_query.status_code == 404:
            raise Exception("ERROR: API request unsuccessful.")

        # Clean the query data, end result is a dict
        review_stats = review_query.json()["books"][0]

        book_info.append(review_stats)

        """ FETCH USER REVIEWS FROM DATABASE """
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})
        book_id = row.fetchone()[0] # tuple format (id, )

        # Fetch book reviews
        rows = db.execute("SELECT username, review, rating FROM users JOIN reviews ON users.id = reviews.user_id \
                    WHERE book_id = :book_id", {"book_id": book_id})

        reviews = rows.fetchall() # When empty, returns empty []

        return render_template("book.html", book_info=book_info, reviews=reviews)
    else:
        # POST method
        current_user = session["user_id"]

        # Fetch data from the form in book.html
        rating = request.form.get("rating")
        review = request.form.get("review")

        # Get book id
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})
        book_id = row.fetchone()[0] # tuple format (id, )

        # Check if current user can submit a review (each user submits only 1 review per book)
        check_row = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                               {"user_id": current_user, "book_id": book_id})

        if check_row.rowcount == 1:
            flash("You already submitted a review for this book", "warning")
            return redirect("/book/" + isbn)

        # Save rating and review
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES (:user_id, :book_id, :review, :rating)",
                                 {"user_id": current_user, "book_id": book_id, "review": review, "rating": rating})
        db.commit()

        flash("Your review has been submitted.", "info")

        return redirect("/book/" + isbn)


@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):
    row = db.execute("SELECT title, author, year, isbn, COUNT(reviews.id) as review_count, \
                        AVG(reviews.rating) as average_score FROM books JOIN reviews \
                        ON books.id = reviews.book_id WHERE isbn = :isbn \
                        GROUP BY title, author, year, isbn", {"isbn": isbn})

    if row.rowcount != 1:
        return jsonify({"Error": "Invalid ISBN"}), 422

    data = row.fetchone()
    api_data = dict(data.items())

    # Round Avg Score to 2 decimals.
    api_data['average_score'] = float('%.2f' % (api_data['average_score']))

    return jsonify(api_data)
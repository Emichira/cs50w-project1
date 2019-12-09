# CS50W Project 1: Books

## Web Programming with Python and JavaScript

(Project Instructions)[https://docs.cs50.net/ocw/web/projects/1/project1.html]

## App Screenshots
![Login Page](https://github.com/nahuakang/cs50w-project1/blob/master/static/login.png)
![Login Page](https://github.com/nahuakang/cs50w-project1/blob/master/static/register.png)
![Login Page](https://github.com/nahuakang/cs50w-project1/blob/master/static/index.png)
![Login Page](https://github.com/nahuakang/cs50w-project1/blob/master/static/search.png)
![Login Page](https://github.com/nahuakang/cs50w-project1/blob/master/static/book.png)

## Usage
1. Register for an account
2. Login
3. Search for the book by its ISBN, author name, or title
4. Get the information about the book and write your review
5. Logout

## Setup
```
# Clone repo
$ git clone https://github.com/nahuakang/cs50w-project1.git

$ cd cs50-project1

# Create a conda env (Preferred)
$ conda create --name cs50-project1 python=3

# Activate the Conda env
$ conda activate cs50-project1

# Install all dependencies
$ pip install -r requirements.txt

# ENV Variables
$ export FLASK_APP = application.py
$ export DATABASE_URL = Your Heroku Postgres DB URI
$ export FLASK_DEBUG = 1
$ export GOODREADS_KEY = Your Goodreads Developer API Key # See: https://www.goodreads.com/api
```

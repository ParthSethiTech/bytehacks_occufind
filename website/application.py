import os
import cryptography
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, redirect, render_template, url_for, session, request, flash, redirect, session
from datetime import timedelta
import psycopg2
import requests
import json
from flask import jsonify
from cryptography.fernet import Fernet

from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Check for environment variable
if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))




@app.route("/")
def index():
	return render_template("index.html")


@app.route("/signup")
def signup():
	if "user" in session:
		return redirect(url_for('returnLogged'))

	else:
		return render_template("signup.html")



@app.route("/jobPost", methods = ["POST"])
def postJob():
	user = session["user"]
	title = request.form.get("title").lower()
	description = request.form.get("description")
	criteria = request.form.get("criteria")

	db.execute("INSERT INTO jobs (username,title,description,criteria) VALUES (:user, :title, :description, :criteria)", {"user":user, "title":title, "description":description, "criteria":criteria})
	db.execute("COMMIT")

	return redirect(url_for('returnLogged'))



@app.route("/signup", methods=["POST"])
def createAccount():

	if "user" in session:
		return redirect(url_for('postJob'))

	else:

		username = request.form.get("username")
		password = request.form.get("password")
		email = request.form.get("email")

		password = pbkdf2_sha256.hash(password)
		
		user_list = db.execute("SELECT * FROM user2 WHERE username = :username", {"username":username}).fetchall()
		if(user_list):
			warn = "This account already exists!"
			return render_template("signup.html", warn = warn)
		else:
			db.execute("INSERT INTO user2 (username, password,email) VALUES (:username, :password, :email)", {"username":username,"password":password,"email":email})
			db.execute("COMMIT")

			success = "Account Created Successfully!"
			return render_template('signup.html', success = success)


@app.route("/validation", methods=["POST"])

def login():

	usernameLog = request.form.get("usernameLog")
	passwordLog = request.form.get("passwordLog")

	hash = db.execute("SELECT password FROM user2 WHERE username = :username", {"username":usernameLog}).fetchone()

	hash = ''.join(hash)

	isCorrect = pbkdf2_sha256.verify(passwordLog, hash)

	

	if(isCorrect):
		session["user"] = usernameLog
		return redirect(url_for('returnLogged'))

	else:
		warn = "Wrong username or password"
		return render_template("signup.html", warn = warn)
		

@app.route("/logout")
def logout():
	session.pop("user", None)
	return redirect(url_for('signup'))

@app.route("/loggedIn")
def returnLogged():

	applicant_list = db.execute("SELECT name,email,title FROM applications").fetchall()

	job_list = db.execute("SELECT title,username,description,criteria FROM jobs").fetchall()
	username = session["user"]

	posted_applications = db.execute("SELECT name,email,title FROM applications WHERE name = :username", {"username":username})

	posted_jobs = db.execute("SELECT title, description, criteria FROM jobs WHERE username = :username", {"username":username})
	return render_template("logHome.html", job_list=job_list, posted_jobs=posted_jobs, posted_applications=posted_applications, applicant_list = applicant_list)

@app.route("/apply", methods=["POST"])
def apply():
	title = request.form.get("title").lower()
	email = request.form.get("email").lower()
	name = session["user"]

	db.execute("INSERT INTO applications (name, email, title) VALUES (:name, :email, :title) ", {"name":name, "email": email, "title":title} )
	db.execute("COMMIT")

	return redirect(url_for('returnLogged'))
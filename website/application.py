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

@app.route("/loggedIn")
def returnLogged():


	title_list = db.execute("SELECT title FROM jobs").fetchall()

	criteria_list = db.execute("SELECT criteria FROM jobs").fetchall()

	location_list = db.execute("SELECT location FROM jobs").fetchall()

	applicant_list = db.execute("SELECT name,email,title FROM applications").fetchall()

	job_list = db.execute("SELECT title,username,description,criteria FROM jobs").fetchall()
	username = session["user"]

	posted_applications = db.execute("SELECT name,email,title FROM applications WHERE name = :username", {"username":session["user"]})

	posted_jobs = db.execute("SELECT title, description, criteria,location FROM jobs WHERE username = :username", {"username":session["user"]})
	return render_template("logHome.html", job_list=job_list, posted_jobs=posted_jobs, posted_applications=posted_applications, applicant_list = applicant_list, title_list=title_list, criteria_list=criteria_list, location_list=location_list)


@app.route("/loggedIn", methods = ["POST"])
def postJob():
	user = session["user"]
	title = request.form.get("title").lower()
	description = request.form.get("description")
	criteria = request.form.get("criteria")
	location = request.form.get("location")

	db.execute("INSERT INTO jobs (username,title,description,criteria,location) VALUES (:user, :title, :description, :criteria, :location)", {"user":user, "title":title, "description":description, "criteria":criteria, "location":location})
	db.execute("COMMIT")

	success = "Job Posted Successfully"

	title_list = db.execute("SELECT title FROM jobs").fetchall()

	criteria_list = db.execute("SELECT criteria FROM jobs").fetchall()

	location_list = db.execute("SELECT location FROM jobs").fetchall()

	applicant_list = db.execute("SELECT name,email,title FROM applications").fetchall()

	job_list = db.execute("SELECT title,username,description,criteria,location FROM jobs").fetchall()
	username = session["user"]

	posted_applications = db.execute("SELECT name,email,title FROM applications WHERE name = :username", {"username":username})

	posted_jobs = db.execute("SELECT title, description, criteria FROM jobs WHERE username = :username", {"username":username})
	return render_template("logHome.html", location_list=location_list,job_list=job_list, posted_jobs=posted_jobs, posted_applications=posted_applications, applicant_list = applicant_list, title_list=title_list, criteria_list=criteria_list, success=success)


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



@app.route("/apply", methods=["POST"])
def apply():
	title = request.form.get("title").lower()
	email = request.form.get("email").lower()
	name = session["user"]

	db.execute("INSERT INTO applications (name, email, title) VALUES (:name, :email, :title) ", {"name":name, "email": email, "title":title} )
	db.execute("COMMIT")

	return redirect(url_for('returnLogged'))

@app.route('/search', methods = ['POST'])
def filterSearch():

	title = request.form.get("title")
	criteria = request.form.get("criteria")
	location = request.form.get("location")

	req_job_list = db.execute("SELECT title,username,description,criteria,location FROM jobs WHERE title = :title AND criteria = :criteria AND location=:location",{"title":title,"criteria":criteria, "location":location}).fetchall()

	title_list = db.execute("SELECT title FROM jobs").fetchall()

	criteria_list = db.execute("SELECT criteria FROM jobs").fetchall()

	applicant_list = db.execute("SELECT name,email,title FROM applications").fetchall()

	location_list = db.execute("SELECT location FROM jobs").fetchall()

	job_list = db.execute("SELECT title,username,description,criteria,location FROM jobs").fetchall()
	username = session["user"]

	posted_applications = db.execute("SELECT name,email,title FROM applications WHERE name = :username", {"username":username})

	posted_jobs = db.execute("SELECT title, description, criteria,location FROM jobs WHERE username = :username", {"username":username})
	return render_template("logHome.html", job_list=job_list, posted_jobs=posted_jobs, posted_applications=posted_applications, applicant_list = applicant_list, title_list=title_list, criteria_list=criteria_list,req_job_list=req_job_list,location_list=location_list)
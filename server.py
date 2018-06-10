from flask import Flask, request, redirect, render_template, session, flash
import md5

app = Flask(__name__)
app.secret_key = 'myreallysecretkey'

from mysqlconnection import MySQLConnector
mysql = MySQLConnector(app, 'the_wall_db')

import re
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")

@app.route('/')
def index():
    if session.get('id') != None:
        return redirect('/wall')
    return render_template('index.html')

@app.route('/wall')
def success():
    if session.get('id') == None:
        return redirect('index.html')
    return render_template('wall.html')

@app.route('/register', methods=['POST'])
def register():
    session['first_name'] = request.form['first_name']
    session['last_name'] = request.form['last_name']
    session['email'] = request.form['email']
    session['password'] = request.form['password']
    session['password_confirm'] = request.form['password_confirm']
    print session['first_name']

    first_name_valid = False
    last_name_valid = False
    email_valid = False
    password_valid = False
    confirm_password_valid = False

    query = "SELECT * FROM users WHERE email=:email"
    data = {
        'email': session['email']
    }

    user = mysql.query_db(query, data) #this finds anyone that has entered the same email in the form that exists in the DB.  

    if len(user) != 0:
        flash('email is taken')
        return redirect('/')

    if session['first_name'].isalpha() and len(session['first_name']) > 1:
        first_name_valid = True
    else:
        if not session['first_name'].isalpha():
            flash("first name must contain only letters")
        if len(session['first_name']) > 2:
            flash("first name must be at least 2 letters")
    
    if session['last_name'].isalpha() and len(session['last_name']) > 1:
        last_name_valid = True
    else:
        if not session['last_name'].isalpha():
            flash("first name must contain only letters")
        if len(session['last_name']) > 2:
            flash("first name must be at least 2 letters")

    if EMAIL_REGEX.match(session['email']):
        email_valid = True
    else:
        flash('email entered must be valid email address')

    if len(session['password']) > 7:
        password_valid = True
    else:
        flash('password must contain at least 8 characters')

    if session['password'] == session['password_confirm']:
        confirm_password_valid = True
    else:
        flash('passwords do not match')

    if first_name_valid and last_name_valid and email_valid and password_valid and confirm_password_valid:
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())" #the ':' before each value means we want the inserted value of that variable.
    
        data = {
            'first_name': session['first_name'],
            'last_name': session['last_name'],
            'email': session['email'],
            'password': md5.new(session['password']).hexdigest()
        }

        mysql.query_db(query, data) #sends above info into DB so users are actually inserted into DB. If this was made into a variable = mysql.query_db(...) - note that it would print the NUMBER of records that match rather than a dictionary of the inserted info.

        #once inserted into DB, then we want to pull the newly inserted data
        query = "SELECT * FROM users WHERE first_name=:first_name AND last_name=:last_name AND email=:email"
        data= {
            'first_name': session['first_name'],
            'last_name': session['last_name'],
            'email': session['email'],
        }
        user = mysql.query_db(query, data)
        print user
        session.clear()
        session['id'] = user[0]['id']
        session['first_name'] = user[0]['first_name']
        return redirect('/wall')
    else:
        return redirect('/')
        
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()

    query = "SELECT * FROM users WHERE email=:email AND password=:password"
    data = {
        'email': email,
        'password': password
    }
    login_user = mysql.query_db(query, data)
    print login_user

    if len(login_user) != 0:
        session['id'] = login_user[0]['id']
        session['first_name'] = login_user[0]['first_name']
        return redirect('/wall')
    else:
        flash('incorrect email and password')
        return redirect('/')

@app.route('/wall')
def wall():

    if session.get('id') == None:
        return redirect('/')

    query = """SELECT messages.id, messages.user_id, CONCAT(users.first_name, ' ', users.last_name) AS posted_by, DATE_FORMAT(messages.created_at, '%M %D, %Y') AS posted_on, messages.message as content  
        FROM messages
        JOIN users ON messages.user_id = users.id"""
    messages = mysql.query_db(query)
    print messages


@app.route('/add_message', methods=['POST'])
def add_message():
    user_id = session['id']
    message = request.form['message']
    query = "INSERT INTO messages (user_id, message, updated_at, created_at) VALUES (:user_id, :message, NOW(), NOW())"
    data = {
        'user_id':user_id,
        'message': message
    }
    mysql.query_db(query, data)

    return redirect('/wall')


    #return redirect('/')

app.run(debug=True)

        

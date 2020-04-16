from flask import Flask, render_template, request, redirect, flash, session
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re
app = Flask(__name__)
app.secret_key = "lfgbutfortulsa"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt= Bcrypt(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['POST'])
def registration():
    is_valid = True
    query = ('SELECT email FROM users')
    mysql = connectToMySQL('lfg_db')
    email_unique = mysql.query_db(query)
    for email in email_unique:
        if request.form['email'] == email['email']:
            is_valid = False
            flash('Email already registered. Please log in.')
    if len(request.form['f_name'])<2:
        is_valid = False
        flash("Please enter a first name.")
    if len(request.form['l_name'])<2:
        is_valid = False
        flash('Please enter a last name.')
    if not EMAIL_REGEX.match(request.form['email']):   
        flash("Invalid email address.")
        is_valid = False
    if len(request.form['email'])<1:
        is_valid = False
        flash('Please enter an email address.')
    if len(request.form['pass'])<1:
        is_valid = False
        flash('Please enter a password.')
    if len(request.form['pass'])<8:
        is_valid = False
        flash('Please enter a password of 8 characters at least.')
    if request.form['pass'] != request.form['pass_c']:
        is_valid = False
        flash('Please check password confirmation.')
    if is_valid:
        flash("Welcome! ")
        print("Validated")
        pw_hash = bcrypt.generate_password_hash(request.form['pass']) 
        query = ("INSERT INTO users (first_name,last_name,email,password,created_at,updated_at) VALUES (%(f_name)s,%(l_name)s,%(email)s,%(password_hash)s,now(),now());")
        data = {
            'f_name': request.form['f_name'],
            'l_name': request.form['l_name'],
            'email':request.form['email'],
            'password_hash' : pw_hash
        }
        print(request.form)
        mysql = connectToMySQL('lfg_db')
        reg_info = mysql.query_db(query,data)
        flash("Please sign in.")
        print("Added to DB")
    return redirect("/")

@app.route('/login', methods =['POST'])
def login():
    query = ("SELECT * FROM users WHERE email = %(email)s;")
    data = {
        'email' : request.form['email']
    }
    mysql = connectToMySQL('lfg_db')
    credentials = mysql.query_db(query, data)
    if credentials:
        if bcrypt.check_password_hash(credentials[0]['password'], request.form['password']):
            session['id'] = credentials[0]['id']
            session['fname'] = credentials[0]['first_name']
            session['lname'] = credentials[0]['last_name']
            session['email'] = credentials[0]['email']
            return redirect('/dashboard')
        else:
            flash('Invalid Password')
            print('Check your Email & Password.')
            return redirect('/')
    else:
        flash('Please Try Again')
        return redirect('/')

@app.route('/signout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'id' not in session:
        session.clear()
        return redirect('/')
    query = ("SELECT events.id, title, events.system, events.description, city, state_abbr FROM events JOIN addresses ON addresses.id = events.id;")
    data = {
        'email' : session['email']
    }
    mysql = connectToMySQL('lfg_db')
    all_events= mysql.query_db(query,data)
    return render_template('dashboard.html', all_events = all_events)

@app.route('/add_event', methods=["POST"])
def add_event():
    if len(request.form['title']) < 2:
        flash('Please enter a longer title.')
        return redirect('/new_event')
    if len(request.form['system']) < 2:
        flash('Please enter a longer rule system name.')
        return redirect('/new_event')
    if len(request.form['description']) < 2:
        flash('Please tell us more about it.')
        return redirect('/new_event')
    if len(request.form['street']) < 2:
        flash('Please be specific about where.')
        return redirect('/new_event')    
    query = ("INSERT INTO addresses (street, city, state_abbr,created_at,updated_at) VALUES (%(street)s,%(city)s,%(state)s,now(), now());")
    data = {
        'street' : request.form['street'],
        'city' : request.form['city'],
        'state' : request.form['stateAbbr']
    }
    mysql = connectToMySQL('lfg_db')
    new_address = mysql.query_db(query,data)
    query = ("SELECT id FROM addresses WHERE street = %(street)s AND city = %(city)s AND state_abbr = %(state)s;")
    data = {
        'street' : request.form['street'],
        'city' : request.form['city'],
        'state' : request.form['stateAbbr']
    }
    mysql = connectToMySQL('lfg_db')
    address_id = mysql.query_db(query,data)
    print(address_id[0]['id'],'<--Should be a good ID')
    query = ("INSERT INTO events (title, events.system, events.description, created_at, updated_at, events.users_id, events.addresses_id) VALUES (%(title)s,%(system)s,%(description)s,now(), now(),%(user_id)s,%(address_id)s);")
    data = {
        'title' : request.form['title'],
        'system' : request.form['system'],
        'description' : request.form['description'],
        'user_id' : session['id'],
        'address_id' : address_id[0]['id']
    }
    mysql = connectToMySQL('lfg_db')
    new_event = mysql.query_db(query,data)
    return redirect('/dashboard')

@app.route('/myaccount')
def my_account():
    if 'id' not in session:
        session.clear()
        return redirect('/')
    query = ("SELECT first_name, last_name, email FROM users WHERE id = %(userid)s")
    data = {
        'userid' : session['id']
    }
    mysql = connectToMySQL('quote_dash_db')
    user_info = mysql.query_db(query,data)
    return render_template('my_account.html', user_info = user_info[0])

@app.route('/edit_user', methods=["POST"])
def edit_user():
    is_valid = True
    query = ('SELECT email FROM users')
    mysql = connectToMySQL('quote_dash_db')
    email_unique2 = mysql.query_db(query)
    if session['email'] != request.form['edit_email']:   
        for x in email_unique2:
            if request.form['edit_email'] == x['email']:
                is_valid = False
                flash('Email already registered. Please use another.')
                return redirect('/myaccount')
    if len(request.form['edit_fname'])<1:
        is_valid = False
        flash("Please enter a first name.")
    if len(request.form['edit_lname'])<1:
        is_valid = False
        flash('Please enter a last name.')
    if not EMAIL_REGEX.match(request.form['edit_email']):   
        flash("Invalid email address.")
        is_valid = False
    if len(request.form['edit_email'])<1:
        is_valid = False
        flash('Please enter an email address.')
    if is_valid == True:
        print('in the right query at least')
        query1 = ("UPDATE users SET first_name = %(fname)s, last_name = %(lname)s, email = %(email)s WHERE id = %(userid)s ;")
        data1 = {
            'fname' : request.form['edit_fname'],
            'lname' : request.form['edit_lname'],
            'email' : request.form['edit_email'],
            'userid' : session['id']
        }
        mysql3 = connectToMySQL('quote_dash_db')
        mysql3.query_db(query1, data1)
        session['fname'] = request.form['edit_fname']
        session['lname'] = request.form['edit_lname']
        session['email'] = request.form['edit_email']
        return redirect('/quotes')
    return redirect('/myaccount')

@app.route('/delete_quote/<int:quote_id>')
def delete_quote(quote_id):
    if 'id' not in session:
        session.clear()
        return redirect('/')
    query = ("DELETE FROM quotes WHERE quotes.id = %(quote_id)s;")
    data = {
        'quote_id' : quote_id
    }
    mysql = connectToMySQL('quote_dash_db')
    mysql.query_db(query,data)
    return redirect('/quotes')

@app.route('/user/<user_id>')
def user(user_id):
    if 'id' not in session:
        session.clear()
        return redirect('/')
    query = ('SELECT * FROM users RIGHT JOIN quotes ON users.id = users_id WHERE users.id = %(u_id)s')
    data = {
        'u_id' : user_id
    }
    mysql = connectToMySQL('quote_dash_db')
    user_quotes = mysql.query_db(query,data)
    print(user_quotes)
    if user_quotes == ():
        return redirect('/quotes')
    return render_template('user.html', user_quotes = user_quotes)

@app.route('/new_event')
def new_event():
    if 'id' not in session:
        session.clear()
        return redirect('/')
    return render_template('new_event.html')

if __name__ == "__main__":
    app.run(debug=True)
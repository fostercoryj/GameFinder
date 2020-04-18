from flask import Flask, render_template, request, redirect, flash, session
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re
import config
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
    query = ("SELECT events.id, title, events.system, events.description,events.date, city, state_abbr FROM events JOIN addresses ON addresses.id = events.id;")
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
    query = ("INSERT INTO events (title, events.system, events.description, date, created_at, updated_at, events.users_id, events.addresses_id) VALUES (%(title)s,%(system)s,%(description)s, %(date)s,now(), now(),%(user_id)s,%(address_id)s);")
    data = {
        'title' : request.form['title'],
        'system' : request.form['system'],
        'description' : request.form['description'],
        'date' : request.form['date'],
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
    query = ("SELECT first_name, last_name, email, title FROM users JOIN events on users.id WHERE users.id = %(userid)s;")
    data = {
        'userid' : session['id']
    }
    mysql = connectToMySQL('lfg_db')
    user_info = mysql.query_db(query,data)
    return render_template('users.html', user_info = user_info)

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

@app.route('/event/<int:event_id>')
def event(event_id):
    editable = False
    if 'id' not in session:
        session.clear()
        return redirect('/')
    mysql = connectToMySQL('lfg_db')
    query = ("SELECT street, city, state_abbr, events.title, events.system, events.description, events.date, events.id, addresses.id,first_name, last_name,users_id FROM addresses JOIN events ON addresses_id = addresses.id JOIN users on users.id = events.users_id WHERE events.id = %(event_id)s;")
    data = {
        'event_id' : event_id
    }
    event_info = mysql.query_db(query,data)
    session['event_id'] = event_id
    if session['id'] == event_info[0]['users_id']:
        editable = True
    return render_template('event.html', event_info = event_info, editable = editable, shhstring = config.shhstring)

@app.route('/event/edit')
def edit_event():
    if 'id' not in session:
        session.clear()
        return redirect('/')
    mysql = connectToMySQL('lfg_db')
    query = ("SELECT street, city, state_abbr, events.title, events.system, events.description, events.date, events.id, addresses.id,first_name, last_name,users_id FROM addresses JOIN events ON addresses_id = addresses.id JOIN users on users.id = events.users_id WHERE events.id = %(event_id)s;")
    data = {
        'event_id' : session['event_id']
    }
    edit_info = mysql.query_db(query,data)
    return render_template('edit_event.html', edit_info = edit_info)

@app.route('/edit/submit',methods=['POST'])
def submit_edit():
    if len(request.form['title']) < 2:
        flash('Please enter a longer title.')
        return redirect('/event/edit')
    if len(request.form['system']) < 2:
        flash('Please enter a longer rule system name.')
        return redirect('/event/edit')
    if len(request.form['description']) < 2:
        flash('Please tell us more about it.')
        return redirect('/event/edit')
    if len(request.form['street']) < 2:
        flash('Please be specific about where.')
        return redirect('/event/edit')   
    print('Valid updates')
    query = ("UPDATE addresses SET street=%(street)s, city=%(city)s, state_abbr=%(state)s, updated_at=now() WHERE addresses.id=%(event_id)s;")
    data = {
        'street' : request.form['street'],
        'city' : request.form['city'],
        'state' : request.form['stateAbbr'],
        'event_id' : session['event_id']
    }
    mysql = connectToMySQL('lfg_db')
    edit_address = mysql.query_db(query,data)
    query = ("UPDATE events SET events.title=%(title)s, events.system=%(system)s, events.description=%(description)s, events.date=%(date)s, events.updated_at=now() WHERE events.id = %(event_id)s;")
    data = {
        'title' : request.form['title'],
        'system' : request.form['system'],
        'description' : request.form['description'],
        'date' : request.form['date'],
        'event_id' : session['event_id']
    }
    mysql = connectToMySQL('lfg_db')
    new_event = mysql.query_db(query,data)
    return redirect('/dashboard')

@app.route('/new_event')
def new_event():
    if 'id' not in session:
        session.clear()
        return redirect('/')
    return render_template('new_event.html')

if __name__ == "__main__":
    app.run(debug=True)
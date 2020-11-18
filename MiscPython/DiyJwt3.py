# DIY JWT in a Flask server app (without using Flask-JWT)
# https://www.geeksforgeeks.org/using-jwt-for-user-authentication-in-flask/
# To register:
# curl -X POST --form "email=ra@ja.com" --form "name=john" --form "password=john" http://localhost:5000/signup 
# to get the token into the clip board:
# curl -X POST --form "email=ra@ja.com" --form "password=john" http://localhost:5000/login  | clip
# To access protected pages: (replace tok.tok.tok with your token!)
# curl -H "Content-Type: application/json" -H "x-access-token: tok.tok.tok" -X GET http://localhost:5000/secure

# pip install sqlalchemy-utils

from werkzeug.security import generate_password_hash, check_password_hash 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy_utils.functions import database_exists
##from sqlalchemy import create_engine, MetaData, Table
from flask import Flask, request  
from flask import render_template, redirect
from flask_cors import CORS
import jwt  # PyJWT authentication 
from config import Config
from datetime import datetime, timedelta 
from functools import wraps 

CLOUD_URL = 'http://192.168.0.100'
PORT = 5000
app = Flask(__name__) 
app.config.from_object (Config)
CORS(app)
db = SQLAlchemy (app) 

# --- Database ORM  ----------------------------------------------------------------
class User (db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    name = db.Column(db.String(64)) 
    email = db.Column(db.String(64), unique = True) 
    password = db.Column(db.String(32)) 

    def __repr__(self):
        return ('<{}#{}>'.format (self.name, self.id))

# --- decorator for verifying the token --------------------------------------------
# You can send the header {Authorization : Bearer  <token>}
def token_required (f): 
    @wraps (f) 
    def decorated (*args, **kwargs): 
        token = None
        # jwt is passed in a request header 
        if 'x-access-token' in request.headers: 
            token = request.headers['x-access-token'] 
        if not token: 
            return  ({'error' : 'missing security token'}, 401)
        try: 
            # decode the payload to fetch the current user
            decoded_token = jwt.decode (token, app.config['SECRET_KEY']) 
            print ('Decoded token: ', decoded_token)
            mail = decoded_token['email']
            current_user = User.query.filter_by (email=mail).first() 
        except Exception as e:
            print ('Exception: ', e) 
            return  ({'error' : str(e)}, 401)
        if (not current_user):    
            return  ({'error' : 'invalid or expired token'}, 401)
        # returns the current logged in user's contex to the routes 
        return f (current_user, *args, **kwargs) 
    return decorated 

# --- app routes -------------------------------------------------------------------
 
@app.route('/') 
def home():
    try:
        user = User.query.filter_by(email='non@exist.ant').first() 
        if user: 
            print ('That improbale email actually exists!')
        else:
            print ('That email, of course, does not exist.')
    except Exception as e:
        print ('\n\n ***** DB Tables may be missing ! ***** \n\n')
        return ('PANIC: Database tables are missing!')
    return 'Welcome to DIY JWT login manager.<br/>Options:<br>/login<br/>/signup<br/>/list/users<br/>/secure'

@app.route('/create/db')
def create_test_db():
    print ('Deleting the old database...')
    db.drop_all()     # to avoid violating the unique value constraints        
    print ('Creating a test database...')
    db.create_all()   # populate afresh    
    #return (add_test_users())
    return ({'result': 'User DB created'})  

@app.route('/add/users') 
def add_test_users():
    insert_user ('ra@ja.com', 'john', 'john')
    insert_user ('ad@min.com', 'admin', 'admin')    
    return ({'result': 'Test users added'})            
    
@app.route('/delete/db')
def delete_test_db ():
    #print ('{} is deleting the user database...'.format(current_user))
    db.drop_all()      
    return ({'result': 'Test DB removed'})

@app.route ('/remove/users')
@token_required
def remove_all_users (current_user):
    print ('{} is removing all user records...'.format(current_user))    
    usrs = User.query.all()
    print ('{} records found.'.format(len(usrs)))
    for u in usrs:
        db.session.delete(u)
    db.session.commit()
    return ({'result': 'All user records removed'})
        
@app.route('/list/users', methods =['GET']) 
def get_all_users (): 
    users = User.query.all() 
    output = [] 
    for user in users: 
        output.append({ 
            'name' : user.name, 
            'email' : user.email, 
            'password_hash' : user.password
        }) 
    return ({'users': output}) 

#-----------------------------------------------------------------------

@app.route ('/insecure')
def insecure_page ():
    return ({'result' : 'This is an open page'}, 200)
    
@app.route ('/secure')
@token_required
def secure_page (current_user):
    msg = 'Authenticated user: {}'.format(current_user)
    print (msg)
    return ({'result' : msg}, 200)
    
@app.route ('/hub')
@token_required
def hub_home (current_user):
    print ('Authenticated user: {}'.format(current_user))
    return redirect (CLOUD_URL)  # google.com
        
@app.route ('/reconnect/db')
@token_required
def reconnect_db (current_user):
    print ('Authenticated user: {}'.format(current_user))
    return redirect (CLOUD_URL +'/reconnect/db')
    
@app.route ('/list/device/types')
@token_required
def device_types (current_user):
    print ('Authenticated user: {}'.format(current_user))
    return redirect (CLOUD_URL +'/list/device/types')
    
@app.route ('/list/room/types')
@token_required
def room_types (current_user):
    print ('Authenticated user: {}'.format(current_user))
    return redirect (CLOUD_URL +'/list/room/types')    
            
# login and get the token
@app.route('/login', methods =['POST']) 
def login(): 
    # creates dictionary of form data 
    form = request.form 
    print ('Form: ', form)
    if not form : 
        return ({'error' : 'Missing login credentials'}, 401)     
    for key, val in form.items():
        print (key, ' -> ',  val)
    if not form.get('email') or not form.get('password'): 
        return ({'error' : 'Missing email or password'}, 401) 

    user = User.query.filter_by (email=form.get('email')).first() 
    print ('User credentials for: {}'.format(user))
    if not user: 
        return ({'error' : 'invalid email or password'},  401) 
    if not check_password_hash (user.password, form.get('password')): 
        return ({'error' : 'invalid email or password'},  403) 
    
    print ('Authenticated. generating token..')
    payload = {'email': user.email,  
               'hubid' : app.config["HUB_ID"], 
               'exp' : datetime.utcnow() + timedelta (minutes=30)} 
    token = jwt.encode (payload, app.config['SECRET_KEY']) 
    return ({'token' : token.decode('UTF-8')}, 201) 
        

def insert_user (email, name, password):
    # check for existing user (user name is not unique, but mail is unique)
    user = User.query.filter_by(email = email).first() 
    if user: 
        print ('email already exists: {}'.format(user))
        return False
    user = User( 
        name = name, 
        email = email, 
        password = generate_password_hash (password) 
    ) 
    db.session.add(user) 
    db.session.commit() 
    print ('Added user: {}'.format(user))
    return True
        
        
@app.route('/signup', methods =['POST']) 
def signup(): 
    # make a dictionary out of the form data 
    data = request.form 
    # gets name, email and password 
    name, email = data.get('name'), data.get('email') 
    password = data.get('password') 
    if insert_user (email, name, password):
        return ({'result' : 'successfully registered'}, 201) 
    else: 
        # returns 202 if user already exists 
        return ({'result' : 'email already registered'}, 202) 

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------
import sys

if __name__ == "__main__": 
    if database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
        print ('\nUserDb Database exists.')
    else:
        print ('\n*** PANIC: User Database is missing ! ******\n')
        #sys.exit(1)
    '''------------------------------------------------------
    # SQLAlchemy version 1.4 only:    
    if (db.engine.reflection.Inspector.has_table ('user')):
        print ('\nUser Table exists.')
    else:
        print ('\n*** PANIC: User Table is missing ! ******\n') 
        #sys.exti(1)   
    ---------------------------------------------------------'''
    
    print ('DIY JWT User Manager listening on port 5000...\n\n')
    
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False) 

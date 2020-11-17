# DIY JWT in a Flask server app (without using Flask-JWT)
# https://www.geeksforgeeks.org/using-jwt-for-user-authentication-in-flask/
# to get the token:
# curl -X POST --form "email=ra@ja.com" --form "password=raman" http://localhost:5000/login
# To access protected pages: (replace tok.tok.tok with your token!)
# curl -H "Content-Type: application/json" -H "x-access-token: tok.tok.tok" -X GET http://localhost:5000/secure
 
from flask import Flask, request  
from flask_sqlalchemy import SQLAlchemy 
import uuid # for public id 
from werkzeug.security import generate_password_hash, check_password_hash 
# for PyJWT authentication 
import jwt 
from datetime import datetime, timedelta 
from functools import wraps 

PORT = 5000
app = Flask(__name__) 
app.config['SECRET_KEY'] = '!a-very-secret-key!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///userdb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) 


# --- Database ORM  ----------------------------------------------------------------
class User (db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    public_id = db.Column(db.String(50), unique = True) 
    name = db.Column(db.String(64)) 
    email = db.Column(db.String(64), unique = True) 
    password = db.Column(db.String(32)) 

    def __repr__(self):
        return ('<[{}] {}>'.format (self.id, self.name))

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
            pubid = decoded_token['public_id']
            current_user = User.query.filter_by (public_id=pubid).first() 
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
    return 'Welcome to DIY JWT login manager.<br/>Options:<br>/login<br/>/signup'

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
    insert_user ('ra@ja.com', 'raja', 'raman')
    insert_user ('ad@min.com', 'admin', 'admin')    
    return ({'result': 'Test users added'})            
    
@app.route('/delete/db')
@token_required
def delete_test_db (current_user):
    print ('{} is deleting the user database...'.format(current_user))
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
            'public_id': user.public_id, 
            'name' : user.name, 
            'email' : user.email 
        }) 
    return ({'users': output}) 

#-----------------------------------------------------------------------

@app.route ('/secure')
@token_required
def secure_page (current_user):
    msg = 'Authenticated user: {}'.format(current_user)
    return ({'result' : msg}, 200)
    
@app.route ('/insecure')
def insecure_page ():
    return ({'result' : 'This is an open page'}, 200)
    
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
    payload = {'public_id': user.public_id,  
               'exp' : datetime.utcnow() + timedelta (minutes = 30)} 
    token = jwt.encode (payload, app.config['SECRET_KEY']) 
    return ({'token' : token.decode('UTF-8')}, 201) 
        

def insert_user (email, name, password):
    # check for existing user (user name is not unique, but mail is unique)
    user = User.query.filter_by(email = email).first() 
    if user: 
        print ('email already exists: {}'.format(user))
        return False
    user = User( 
        public_id = str(uuid.uuid4()), 
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
        return ({'error' : 'email already registered'}, 202) 

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------
if __name__ == "__main__": 
    print ('DIY JWT User Manager listening on port 5000...')
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False) 

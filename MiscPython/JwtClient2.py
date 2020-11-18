# Test client for a secure server with JWT tokens
# This is for the DIY JWT in a Flask server app (without using Flask-JWT)
# https://www.geeksforgeeks.org/using-jwt-for-user-authentication-in-flask/

# To register:
# curl -X POST --form "email=ra@ja.com" --form "name=john" --form "password=raman" http://localhost:5000/signup 
# to get the token into the clip board:
# curl -X POST --form "email=ra@ja.com" --form "password=raman" http://localhost:5000/login  | clip
# To access protected pages: (replace tok.tok.tok with your token!)
# curl -H "Content-Type: application/json" -H "x-access-token: tok.tok.tok" -X GET http://localhost:5000/secure


import json
import random
import requests
from time import sleep

#---------------------------------------------------------------------------------
# HELPERS
#---------------------------------------------------------------------------------

HTTP_OK = requests.codes.ok
HTTP_OK_THRESHOLD = 203

def get_it (url, payload=None):
    print ('GET ', url)
    res = requests.get(url, params=payload)  #,headers=headers
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code)) 
        print ("Explanation: ", res.reason)        
        res.raise_for_status() 
    print (res.json())  # res.text
    print()


def post_it (url, jpayload):
    print ('POST ', url)
    jheader = {"content-type" : "application/json"}
    res = requests.post(url, json=jpayload, headers=jheader)
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code))  
        print ("Explanation: ", res.reason)        
    print (res.json()) # res.text
    print()
    

def post_form (url, jform):
    print ('POST ', url)
    #jheader = {"content-type" : "application/json"}
    res = requests.post(url, data=jform)  #, headers=jheader)
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code))  
        print ("Explanation: ", res.reason)        
    print (res.text)  # (res.json())  
    print()
    
    
def get_jwt_token (url, email, password):
    print ('Getting JWT token...')
    print ('POST ', url)
    #jheader = {"content-type" : "application/json"}  # this header is mandatory for Flask-JWT!
    jpayload = { "email": email, "password": password }  
    res = requests.post(url, data=jpayload)  #, headers=jheader)
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code))  
        print ("Explanation: ", res.reason)        
        print (res.json())  # res.text
        print()
        return None
    jtoken = res.json()  # res.text
    print()
    print (jtoken)
    if ('token' not in jtoken):
        print ("Error: No JWT token received")  
        print()
        return None        
    return  jtoken['token']
        
'''----------------------------------
Headers is a Pyhon dictionary with key-value pairs in the form header_name:header_value
Example:
headers = {
    "content-type" : "application/json",
    "Accept-Encoding" : "compress, gzip",
    "User-Agent" :  "Mozilla/4.0",
    "Cookie" : "cookie1=value1;cookie2=value2",
    "Authorization" :  "JWT  my_jwt_token" 
}
-------------------------------------'''    

def get_it_with_headers (url, headers):
    print ('GET ', url)
    #jheader = {"content-type" : "application/json"}  # this header is mandator for Flask-JWT to work ***
    jheader = {}
    for key,value in headers.items():  
        jheader[key] = value
    print ('sending header: ', jheader)
    res = requests.get (url, headers=jheader)
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code))  
        print ("Explanation: ", res.reason)
    else:
        #print (res.json())
        print(res.text)
    print()    
    
    
def post_it_with_headers (url, payload, headers):
    print ('POST ', url)
    jheader = {"content-type" : "application/json"}
    for key,value in headers.items():  
        jheader[key] = value
    print ('sending header: ', jheader)
    res = requests.post(url, json=payload, headers=jheader)
    print ('HTTP status code: ', res.status_code)
    if (res.status_code > HTTP_OK_THRESHOLD):
        print ("HTTP error: {}".format (res.status_code))  
        print ("Explanation: ", res.reason)        
    else:
        print (res.json())
    print()    
#---------------------------------------------------------------------------------
# UNIT TESTS
#---------------------------------------------------------------------------------

def test1():
    print('Sending correct credentials to /login...')
    url = 'http://127.0.0.1:5000/login'  
    payload = { "email": "ra@ja.com", "password": "john" }   
    post_form (url, payload)
    
def test2():
    print('Sending invalid password to /login..[expected: 403]')
    url = 'http://127.0.0.1:5000/login'  
    payload = {  "email": "ra@ja.com",  "password": "junk" }   
    post_form (url, payload)
    
def test3():
    print('Sending invalid mail id AND password to /login...[expected: 401]')
    url = 'http://127.0.0.1:5000/login'  
    payload = { "email": "non@exis.tant", "password": "junk" }   
    post_form (url, payload)       
    
def test4():
    print('Accessing protected page without authorization header..')
    url = 'http://127.0.0.1:5000/secure'  
    get_it (url)   
    
def test5():
    print('Accessing protected page with wrong JWT token...')
    url = 'http://127.0.0.1:5000/secure'  
    header = { "x-access-token" : "ABCD.EFGH.IJKL"}
    get_it_with_headers (url, header)
    
def test6 (token):
    print('Accessing protected page with the right JWT token...')
    url = 'http://127.0.0.1:5000/secure'  
    header = { "x-access-token" : token }
    get_it_with_headers (url, header)
        
def test7 (token):
    print('Accessing Hub server...')
    url = 'http://127.0.0.1:5000/hub'  
    header = { "x-access-token" : token }
    get_it_with_headers (url, header)        
    
def test8 (token):
    print('Getting room types..')
    url = 'http://127.0.0.1:5000/list/room/types'  
    header = { "x-access-token" : token }
    get_it_with_headers (url, header)    
        
def test9 (token):
    print('Getting device types..')
    url = 'http://127.0.0.1:5000/list/device/types'  
    header = { "x-access-token" : token }
    get_it_with_headers (url, header)  
            
def test10 (token):
    print('Reconnecting db...')
    url = 'http://127.0.0.1:5000/reconnect/db'  
    header = { "x-access-token" : token }
    get_it_with_headers (url, header)   
                
def get_token (email, passwd):
    print('Getting auth token...')
    url = 'http://127.0.0.1:5000/login'  
    return get_jwt_token (url, email, passwd)       
#---------------------------------------------------------------------------------
# MAIN
#---------------------------------------------------------------------------------
mail = 'ra@ja.com'
pwd = 'john'

print()
test1()
test2()
test3()

try:
    test4()  # calling without any Authorization header
except Exception as e:
    print ('Oh! that raised an exception:')
    print (e)
print()    
    
test5()  # Authorization header present, but with wrong token

token = get_token (mail, pwd)   
#print (token)
#print()
test6 (token)  
test7 (token)  
test8 (token)  
test9 (token)  
test10 (token)  



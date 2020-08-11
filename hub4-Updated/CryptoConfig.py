# Helper class to encrypt/decrypt a JSON object with a password and salt 
# It first generates the encryption key by hasing the password and salt
# The password and salt are read from a Python file in the code base
# https://nitratine.net/blog/post/encryption-and-decryption-in-python/

import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import PasswordStore   # our own secret module

class CryptoConfig():
    # keep two variables, password and salt, in a file named PasswordStore.py
    hash_key = None    
    fer_net = None
    debug = False
    
    def __init__(self, debug=False):
        self.debug = debug
        bypassword = PasswordStore.app_config_password.encode('utf-8')   # Convert to bytes
        bysalt = PasswordStore.app_config_salt.encode('utf-8')           # recommend: use a key from os.urandom(16), of type bytes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=bysalt,
            iterations=100000,
            backend=default_backend()
        )
        self.hash_key = base64.urlsafe_b64encode (kdf.derive(bypassword))   # "Can only use kdf once" (=?)
        self.fer_net = Fernet (self.hash_key)
        '''
        if self.debug:
            print ("hash key from your password and salt:")
            print (self.hash_key)
            print (type(self.hash_key))
            print()
        '''

    # encrypt a json object
    # jpayload : a json object
    # returns : a Python string
    def encrypt_json (self, jpayload):    
        return self.encrypt_str(json.dumps(jpayload).encode('utf-8'))    # encode converts it to byte string


    # decrypt a Python string payload and return a json object
    # payload : a Python string
    # returns : a json object
    def decrypt_json (self, payload):    
        if self.debug:
            #payload =  'deliberate_tampering, only for testing'
            #print (payload)
            print ('decrypting...')
        try:
            decrypted = self.decrypt_str(payload.encode('utf-8'))    # encode converts it to byte string 
            return  json.loads (decrypted.decode('utf-8'))
        except Exception as e:
            print ('_ERROR: ', str(e))   
            return None
        
            
    # encrypt a string payload using the stored hash as key
    # payload: a byte string
    # returns: a Python string, ready for transmission/storage
    def encrypt_str (self, payload):    
        try:
            encrypted = self.fer_net.encrypt (payload)
            '''
            if self.debug:        
                print ("encrypted message:")
                print (encrypted)
                print (type(encrypted))
                print()
            '''
            return (encrypted.decode('utf-8'))  
        except Exception as e:
                print ('Encrypting error:')
                print (str(e))
                return None

      
    # decrypt the message using the stored hash as key
    def decrypt_str (self, encrypted_payload):
        try:
            decrypted = self.fer_net.decrypt (encrypted_payload)
            '''
            if self.debug:      
                print ('decrypted:')
                print (decrypted)
                print (type(decrypted))
                print()
            '''
            return (decrypted)
        except Exception as e:
                print ('Decrypting error:')
                print (str(e))
                return None            
#------------------------------------------------------------------------      
# UNIT TEST
#------------------------------------------------------------------------

if (__name__ == '__main__'):
    jmessage = {"name" : "ramrom", "age":25, "city": "Coimbatore"} 
    print ("secret message:")
    print (jmessage)
    print()
    
    crypto = CryptoConfig (debug=True)
    encrypted = crypto.encrypt_json (jmessage)
    decrypted = crypto.decrypt_json (encrypted)
    
    print ("recovered message:")
    print (decrypted)
    print()    
    if (jmessage == decrypted):
        print ("message verified OK.")
    else:
        print ("Message verification failed.")    

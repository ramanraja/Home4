# new: self-serializing model objects; tree hierarchy of objects

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from random import randint
from datetime import datetime
import json

app = Flask (__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Hub6.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# enable this to see the internal queries
#app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy (app)

current_user = 'Anonymous'

def dprint (*args):
    #app.logger.info (*args)
    print (*args)
#----------------------------------------------------------------------------------------------------
# models
#----------------------------------------------------------------------------------------------------

class Device (db.Model): 
    __tablename__ = 'device'  # this line is optional
    device_id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False) 
    fallback_id = db.Column(db.String(32), unique=True, nullable=True)
    mac = db.Column(db.String(24), unique=True)
    ip = db.Column(db.String(24))
    hardware_type = db.Column(db.String(32), default='Generic') 
    num_relays = db.Column(db.Integer, default=1)
    num_sensors = db.Column(db.Integer, default=0) 
    enabled = db.Column(db.Boolean, default=True)
    RSSI = db.Column(db.Integer, default=0)  # maximum is 100%
    signal = db.Column(db.Integer, default=0) # dBm
    relsens = db.relationship ('Relsen', backref='controller')  # TODO: use back_populates
    stat = db.relationship ('Status', backref='controller')  # TODO: can you remove this list of stat objects?
    
    def get_attached_relsen_ids (self): # only relsen IDs, as a list
        relsen_ids = []
        for rs in self.relsens:
            relsen_ids.append(rs.relsen_id)
        return (relsen_ids)
        
    def get_attached_relsens (self):    # complete relsen objects, as a list
        rels = []
        for rs in self.relsens:
            rels.append(rs.toJSON())
        return (rels)
                
    def get_device_config (self):
        jdevice_config = {
            'device_id': self.device_id,
            'hardware_type': self.hardware_type, 
            'num_relays': self.num_relays,
            'num_sensors': self.num_sensors,
            'enabled': self.enabled,
        }
        return (jdevice_config)        

    def get_device_specs (self):  # config and technical specs
        jdev_specs = self.get_device_config()
        jdev_specs['relsen_count'] = len(self.relsens)  # must be = num_relays+num_sensors
        jdev_specs['mac'] = self.mac
        jdev_specs['ip'] = self.ip
        jdev_specs['RSSI'] = self.RSSI
        jdev_specs['signal'] = self.signal
        jdev_specs['fallback_id'] = self.fallback_id
        return (jdev_specs)  
        
    def toJSON (self):             # config and dump the entire set of relsens 
        jdevice = self.get_device_config()
        jdevice['relsens'] = []
        for rs in self.relsens:
            jdevice['relsens'].append (rs.toJSON())
        return (jdevice)    
                
    def __repr__(self):
        return ('<{}.{}>'.format (self.device_id, self.fallback_id))
#----------------------------------------------------------------------------------------------------

# NOTE: Combination of device_id + relsen_id must be unique        
class Relsen (db.Model): 
    __tablename__ = 'relsen'
    rowid = db.Column(db.Integer, primary_key=True) # built-in autoincrement field 
    device_id = db.Column(db.String(16), db.ForeignKey ('device.device_id'), nullable=False) 
    relsen_id = db.Column(db.String(32), nullable=False)       # 'POWER1', 'A0'
    relsen_name = db.Column(db.String(32), default='Light')    # 'Hall light'
    relsen_type = db.Column(db.String(32), default='Generic')  # 'bulb', 'Temperature', 'Light'
    room_name = db.Column(db.String(32))    # 'guest room'
    room_type = db.Column(db.String(32))    # 'bed room'
    group_name = db.Column(db.String(32))   # 'ground floor'
    schedule = db.Column(db.String(256))    # JSON
    repeat = db.Column(db.Boolean)   
    
    def toJSON (self):
        jrelsen = {
            'device_id': self.device_id,
            'relsen_id': self.relsen_id,
            'relsen_name': self.relsen_name,
            'relsen_type': self.relsen_type,
            'room_name': self.room_name,
            'room_type': self.room_type,
            'group_name': self.group_name,
            'repeat': self.repeat
        }
        if self.schedule :
            jrelsen.update(json.loads(self.schedule))  # merge the two json objects
        else:
            jrelsen['schedule'] = []        # create a 'schedule' node and add an empty array
        return (jrelsen)
     
    def __repr__(self):
        return ('<{}.{}>'.format (self.device_id, self.relsen_id))
        
#----------------------------------------------------------------------------------------------------

class Status (db.Model):  # TODO: store realtime data and events in database
    __tablename__ = 'status'
    rowid = db.Column(db.Integer, primary_key=True) # built-in autoincrement field 
    device_id = db.Column(db.String(16), db.ForeignKey ('device.device_id'), nullable=False) 
    time_stamp = db.Column(db.DateTime(timezone=True), default=datetime.now)  # db.func.current_timestamp())  
    relay_status = db.Column(db.String(24))  # array within JSON
    sensor_values = db.Column(db.String(32)) # JSON
    event_type = db.Column(db.String(16))    # autonomous, command, response, event, health, info, error 
    online = db.Column(db.Boolean)   

    def __repr__(self):
        OL = 'Offline'
        if self.online: 
            OL='Online'
        return ('<{}.{}({})>'.format (self.rowid, self.device_id, OL))
        
#----------------------------------------------------------------------------------------------------
# helper methods    
#----------------------------------------------------------------------------------------------------

def insert_device (device_id, fallback_id=None, mac=None, ip=None, 
                hardware_type="Generic", num_relays=1, num_sensors=0, 
                enabled=True):
    if (not device_id or len(device_id)==0):
        dprint ('Invalid device_id')
        return False
    # check for existing device (device_id must be unique)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if dev: 
        dprint ('Device ID already exists: {}'.format(device_id))
        return False
    # check for existing device (fallback_id must be unique)
    if (fallback_id):
        fb = Device.query.filter_by (fallback_id=fallback_id).first() 
        if fb: 
            dprint ('Falback ID already exists: {}'.format(fallback_id))
            return False   
    dev = Device ( 
        device_id = device_id, 
        fallback_id = fallback_id, 
        mac = mac,
        ip = ip,
        hardware_type = hardware_type, 
        num_relays = num_relays,   
        num_sensors = num_sensors,
        enabled = enabled) 
    db.session.add (dev) 
    db.session.commit()   
    dprint ('Added device: {}'.format(dev))
    return True   
    
        
def update_device (jdevice):
    print (jdevice)
    device_id = jdevice.get('device_id') or None
    if (not device_id or len(device_id)==0):
        return ({'error' : 'Invalid device_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'error' : 'device_id does not exist'})
    fallback_id =  jdevice.get ('fallback_id') or None
    # fallback_id must be a unique non-empty string
    if (fallback_id and len (fallback_id) > 0) : 
        fb = Device.query.filter_by (fallback_id=fallback_id).first() 
        if fb: 
            return ({'error' : 'fallback_id already exists'})
        dev.fallback_id = fallback_id
    mac = jdevice.get('mac') or None    
    if (mac): dev.mac = mac
    ip = jdevice.get('ip') or None    
    if (ip): dev.ip = ip
    hardware_type = jdevice.get('hardware_type') or None    
    if (hardware_type): dev.hardware_type = hardware_type
    num_relays = jdevice.get('num_relays') or -1    
    if (num_relays >= 0): dev.num_relays = num_relays   
    num_sensors = jdevice.get('num_sensors') or -1    
    if (num_sensors >= 0): dev.num_sensors = num_sensors
    print(jdevice.get('enabled'))
    ####enab = jdevice.get('enabled') or None   # TODO: understand this!
    if 'enabled' in jdevice:
         dev.enabled = jdevice.get('enabled') 
    db.session.commit()   
    return ({'result' : 'successfully updated device'})
 
    
def insert_relsen (device_id, relsen_id, 
                relsen_name=None, relsen_type=None, 
                room_name=None, room_type=None, group_name=None,
                schedule=None, repeat=False):
    # check for existance of device (device_id must preexist)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        dprint ('Unknown device ID: {}'.format(device_id))
        return False
    for rel in dev.relsens:  # combination of (device_id+relsen_id) must be unique
        if (rel.relsen_id==relsen_id):
            dprint ('{}.{} already exists'.format(device_id, relsen_id))
            return False
    rs = Relsen ( 
        controller = dev,
        relsen_id = relsen_id, 
        relsen_name = relsen_name,
        relsen_type = relsen_type,
        room_name = room_name,
        room_type = room_type,
        group_name = group_name,
        schedule = schedule,   # LHS is the DB column name; RHS is a stringified json object (which has 'schedule' as the key)
        repeat = repeat) 
    db.session.add (rs) 
    db.session.commit()    
    dprint ('Added relay: {}'.format(rs))
    return True   
    

def update_relsen (jrelsen):
    device_id = jrelsen.get('device_id') or None        
    if (not device_id or len(device_id)==0):
        return ({'error' : 'Invalid device_id'})
    relsen_id = jrelsen.get('relsen_id') or None 
    if (not relsen_id or len(relsen_id)==0):
        return ({'error' : 'Invalid relsen_id'})
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        return ({'error' : 'device_id does not exist'})
    rs = Relsen.query.filter_by (device_id=device_id, relsen_id=relsen_id).first() 
    if (not rs):
        return ({'error' : 'relsen_id does not exist'})
    relsen_name = jrelsen.get('relsen_name') or None 
    if (relsen_name):  rs.relsen_name = relsen_name
    relsen_type = jrelsen.get('relsen_type') or None 
    if (relsen_type):  rs.relsen_type = relsen_type
    room_name = jrelsen.get('room_name') or None 
    if (room_name):  rs.room_name = room_name
    room_type = jrelsen.get('room_type') or None 
    if (room_type):  rs.room_type = room_type
    
    group_name = jrelsen.get('group_name') or None    
    if (group_name):  rs.group_name = group_name
    
    schedule = jrelsen.get('schedule') or None 
    if (schedule):  rs.schedule = schedule   # it must be a string (stringified json with 'schdule' as the key)
    ###repe = jrelsen.get('repeat') or None # TODO: understand this!
    if 'repeat' in jrelsen:
         rs.repeat = jrelsen.get('repeat') 
    db.session.commit()    
    return ({'result' : 'successfully updated relsen'})
        
        
def insert_status (device_id, relay_status=None, sensor_values=None,    # time_stamp=None, 
                event_type=None, online=True): 
    # check for existance of device (device_id must already exist)
    dev = Device.query.filter_by (device_id=device_id).first() 
    if not dev: 
        dprint ('Unknown device ID: {}'.format(device_id))
        return False
    st = Status ( 
        controller = dev,
        relay_status = relay_status,  
        sensor_values = sensor_values,
        event_type = event_type,
        online = online) 
    db.session.add (st) 
    db.session.commit()   
    dprint ('Added status: {}'.format(st))
    return True   
    
# There is no need for update_status()
#----------------------------------------------------------------------------------------
# Upatate routes
#----------------------------------------------------------------------------------------

@app.route ('/update/device', methods =['GET', 'POST'])
def update_device_route():
    if (request.method=='GET'):
        return ({'error':'POST the new Device values as JSON'})
    if (not request.json):
        return ({'error':'invalid Device data'})
    return (update_device(request.json))
    
    
@app.route('/update/relsen', methods =['GET', 'POST']) 
def update_relsen_route():
    if (request.method=='GET'):
        return ({'error':'POST the new Relsen values as JSON'})
    if (not request.json):
        return ({'error':'invalid Relsen data'})
    return (update_relsen(request.json))

#----------------------------------------------------------------------------------------
# Housekeeping routes
#----------------------------------------------------------------------------------------

@app.route('/random', methods =['GET']) 
def random (): 
    return ({'random' : randint(0, 10000)})

      
@app.route ('/')      
@app.route ('/menu')
def home ():
    return (render_template('menu.html'))
    
    
@app.route('/test', methods =['GET']) 
def test (): 
    return (render_template('tester.html'))
    
    
@app.route('/create/db')
def create_test_db():
    dprint ('Deleting the old database...')
    db.drop_all()     # to avoid violating the unique value constraints        
    dprint ('Creating a test database...')
    db.create_all()       
    #return (add_test_data())
    return ({'result': 'Hub DB created'})  
      
      
@app.route('/delete/db')
def delete_test_db ():
    dprint ('{} is deleting the Hub database...'.format(current_user))
    db.drop_all()      
    return ({'result': 'Test DB removed'})


@app.route ('/remove/devices')  
def remove_all_devices ():
    dprint(remove_all_status()) # this is needed for dependency constraint
    dprint(remove_all_relays())
    dprint ('{} is removing all device records...'.format(current_user))    
    devs = Device.query.all()
    dprint ('{} records found.'.format(len(devs)))
    for d in devs:
        db.session.delete(d)
    db.session.commit()
    return ({'result': 'All device records removed.'})
        

@app.route ('/remove/relays') 
def remove_all_relays ():
    dprint ('{} is removing all relays/sensors...'.format(current_user))    
    rel = Relsen.query.all()
    dprint ('{} records found.'.format(len(rel)))
    for r in rel:
        db.session.delete(r)
    db.session.commit()
    return ({'result': 'All relays removed.'})
            

@app.route ('/remove/status')
def remove_all_status ():
    dprint ('{} is removing all status data...'.format(current_user))    
    sta = Status.query.all()
    dprint ('{} records found.'.format(len(sta)))
    for s in sta:
        db.session.delete(s)
    db.session.commit()
    return ({'result': 'All status data removed.'})
    
#---------------------------------------------------------------------------------------------------
# types
#---------------------------------------------------------------------------------------------------
    
@app.route('/list/rooms', methods =['GET'])      
def list_all_rooms():
    relsens = db.session.query(Relsen.room_name).distinct()  # all() 
    retval = [] 
    for rs in relsens: 
        retval.append (rs.room_name)  
    return ({'room_names': retval}) 
    
@app.route('/list/room/types', methods =['GET'])  
def list_all_room_types():
    relsens = db.session.query(Relsen.room_type).distinct()  # all() 
    retval = [] 
    for rs in relsens: 
        retval.append (rs.room_type)  
    return ({'room_types': retval}) 
    
@app.route('/list/hardware/types', methods =['GET'])  
def list_all_hardware_types(): 
    devs = db.session.query(Device.hardware_type).distinct()
    retval = [] 
    for d in devs: 
        retval.append (d.hardware_type)  
    return ({'hardware_types': retval}) 
    
@app.route('/list/relsen/types', methods =['GET'])  
def list_all_relsen_types():
    rels = db.session.query(Relsen.relsen_type).distinct()
    retval = [] 
    for r in rels: 
        retval.append (r.relsen_type)  
    return ({'relsen_types': retval}) 
        
#---------------------------------------------------------------------------------------------------
# dump
#---------------------------------------------------------------------------------------------------

#------------------------------------ All Devices ------------------------------------------------------
# only ids
@app.route('/get/devices', methods =['GET']) 
@app.route('/get/device/list', methods =['GET']) 
def list_all_devices(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})     

# full dump of all devices, including associated relsens, as a list
@app.route('/dump/devices', methods =['GET']) 
def dump_all_devices(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.toJSON()) 
    return ({'devices': retval})  
        
# full dump of all devices, including associated relsens, as a tree
@app.route('/dump/device/tree', methods =['GET']) 
def dump_all_device_tree(): 
    devs = Device.query.all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.toJSON()
    return (retval) 
            
# config and technical specs as a list       
@app.route('/dump/device/specs', methods =['GET']) 
def dump_device_specs(): 
    devs = Device.query.all()
    retval = [] 
    for d in devs: 
        retval.append(d.get_device_specs())  
    return ({'devices': retval})

# config and technical specs as a tree            
@app.route('/dump/device/spec/tree', methods =['GET']) 
def dump_device_spec_tree(): 
    devs = Device.query.all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = (d.get_device_specs())  
    return (retval) 
                
#------------------------------------ Active/inactive Devices ------------------------------------------------------

# only enabled ids
@app.route('/get/active/devices', methods=['GET'])      
def get_active_devices():    
    devs = Device.query.filter_by(enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})   
        
# only disabled ids        
@app.route('/get/inactive/devices', methods=['GET'])      
def get_inactive_devices():    
    devs = Device.query.filter_by(enabled=False).all()
    retval = [] 
    for d in devs: 
        retval.append(d.device_id) 
    return ({'devices': retval})      
            
#------------------------------------ Only for Active Devices ------------------------------------------------------
            
# all device json data as a list
@app.route('/dump/active/devices', methods =['GET']) 
def dump_active_devices(): 
    devs = Device.query.filter_by (enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append (d.toJSON())
    return ({'devices': retval}) 
        
# all device json data as a tree
@app.route('/dump/active/device/tree', methods =['GET']) 
def dump_active_device_tree(): 
    devs = Device.query.filter_by (enabled=True).all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.toJSON()
    return (retval) 
            
# technical specs            
@app.route('/dump/active/device/specs', methods =['GET']) 
def dump_active_device_specs(): 
    devs = Device.query.filter_by(enabled=True).all()
    retval = [] 
    for d in devs: 
        retval.append(d.get_device_specs())  
    return ({'devices': retval}) 
            
# specs as a tree            
@app.route('/dump/active/device/spec/tree', methods =['GET']) 
def dump_active_device_spec_tree(): 
    devs = Device.query.filter_by(enabled=True).all()
    retval = {} 
    for d in devs: 
        retval[d.device_id] = d.get_device_specs() 
    return (retval) 

#---------------------- filter a particular device --------------------------------------------

# dump a particular device along with its contained relsens
@app.route('/get/device/details', methods =['GET']) 
def get_device_details(): 
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'error' : 'invalid device_id'})
    return (dev.toJSON())    
    
# only config fields
@app.route('/get/device/config', methods =['GET']) 
def get_device_config ():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'error' : 'invalid device_id'})
    return (dev.get_device_config()) 

# technical specs
@app.route('/get/device/specs', methods =['GET']) 
def get_device_specs ():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'error' : 'invalid device_id'})
    return (dev.get_device_specs()) 

#-----------------------------------------------------------------------------------------------------------
# Relsens
#-----------------------------------------------------------------------------------------------------------

#------------------only the ids ---------------------------------------------------------------------

# all device_id and relsen_id, as a list      
@app.route('/get/relsens', methods =['GET']) 
@app.route('/get/relsen/list', methods =['GET']) 
def list_all_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}  
        retval.append (jrelson)          
    return ({'relsens': retval})  
                    
# all device_id and relsen_id, as a tree structure
@app.route('/get/relsen/tree', methods =['GET']) 
def get_relsen_tree (): 
    relsens = Relsen.query.all()
    retval = {} 
    for rs in relsens: 
        devid = rs.device_id
        rsid = rs.relsen_id        
        if (devid not in retval):
            retval[devid] = []
        retval[devid].append (rsid)    
    return (retval) 
                        
# active device_id and relsen_id, as a list
@app.route('/get/active/relsens', methods =['GET']) 
def get_active_relsens (): 
    ##relsens = Relsen.query.filter_by (controller.enabled=True).all() # TODO: use back_populates
    relsens = Relsen.query.all()
    retval = [] 
    for rs in relsens: 
        if (rs.controller.enabled):
            jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}  
            retval.append (jrelson)          
    return ({'relsens': retval})   
                        
# active device_id and relsen_id, as a tree         
@app.route('/get/active/relsen/tree', methods =['GET']) 
def get_active_relsen_tree (): 
    relsens = Relsen.query.all()
    retval = {} 
    for rs in relsens: 
        if (rs.controller.enabled):
            devid = rs.device_id
            rsid = rs.relsen_id        
            if (devid not in retval):
                retval[devid] = []
            retval[devid].append (rsid)    
    return (retval)  

#-------------------------------------- complete relsen objects -------------------------------------------------------

# all - complete relsen objects as a list
@app.route('/dump/relsens', methods =['GET']) 
def dump_all_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        retval.append (rs.toJSON())          
    return ({'relsens': retval})     # all relsens are sibling nodes
    
# all - complete relsen objects as a tree
@app.route('/dump/relsen/tree', methods =['GET']) 
def dump_all_relsen_tree(): 
    rels = Relsen.query.all()
    retval = {} 
    for rs in rels: 
        devid = rs.device_id
        if (devid not in retval):
            retval[devid] = rs.toJSON()          
    return (retval)      
        
# active - complete relsen objects as a list
@app.route('/dump/active/relsens', methods =['GET']) 
def dump_active_relsens(): 
    rels = Relsen.query.all()
    retval = [] 
    for rs in rels: 
        if (rs.controller.enabled):
            retval.append (rs.toJSON())          
    return ({'relsens': retval})      
        
# active - complete relsen objects as a tree
@app.route('/dump/active/relsen/tree', methods =['GET']) 
def dump_active_relsen_tree(): 
    rels = Relsen.query.all()
    retval = {} 
    for rs in rels: 
        if (rs.controller.enabled):
            devid = rs.device_id
            if (devid not in retval):
                retval[devid] = rs.toJSON()         
    return (retval)  
    
#---------------------- filters ----------------------------------------------------------------------------
    
#------------------------- find one particular relsesn by id ----------------------------------------------

# JSON dump of the selected relsen
@app.route('/get/relsen/details', methods =['GET']) 
def get_relsen_details (): 
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    relid = request.args.get('relsen_id')
    if (not relid):
        return ({'error' : 'relsen_id is required'})
    rs = Relsen.query.filter_by(device_id=devid, relsen_id=relid).first()  
    if (not rs):
        return ({'error' : 'invalid device_id or relsen_id'})    
    return (rs.toJSON()) 
            
#----------------------------------------------------------------------------------------------------------------

# all relsens under a given device - only ids
@app.route('/get/attached/relsen/ids', methods=['GET']) 
def get_attached_relsen_ids():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'error' : 'invalid device_id'})
    retval = {
        'device_id' : devid,
        'relsens' : dev.get_attached_relsen_ids()
    }
    return (retval)
    
# all relsens under a given device - complete dump
@app.route('/get/attached/relsens', methods=['GET'])  # full relsen objects under this device
def get_attached_relsens():
    devid = request.args.get('device_id')
    if (not devid):
        return ({'error' : 'device_id is required'})
    dev = Device.query.filter_by (device_id=devid).first()
    if (not dev):
        return ({'error' : 'invalid device_id'})
    retval = {
        'device_id' : devid,
        'relsens' : dev.get_attached_relsens()
    }
    return (retval)
            
#------------------------------------------------------------------------------------------------------------
# filters
#------------------------------------------------------------------------------------------------------------

# ---------------------- by room ---------------------            
@app.route('/get/device/ids/of/room', methods=['GET'])       
def get_device_ids_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all() # room_name is accessible only through Relsen
    retval = set([])    # to avoid duplicates
    for rs in relsens: 
        retval.add (rs.device_id)   
    return ({'devices': list(retval)})  # set cannot be serialized
        
@app.route('/get/devices/of/room', methods=['GET'])       
def get_devices_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all()
    devices = set([])    # to avoid duplicates
    for rs in relsens: 
        devices.add (rs.controller)
    dprint (devices)
    dprint (type(devices))
    retval = []
    for d in devices:
        retval.append (d.toJSON())
    return ({'devices': retval})   
 
@app.route('/get/relsen/ids/of/room', methods=['GET'])      
def get_relsen_ids_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all()
    retval = [] 
    for rs in relsens: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id} 
        retval.append (jrelson)          
    return ({'relsens': retval}) 
    
@app.route('/get/relsens/of/room', methods=['GET'])     # TODO: return the complete relsen objects
def get_relsens_in_room():    
    room = request.args.get('room_name')
    if (not room):
        return ({'error' : 'room_name is required'})
    relsens = Relsen.query.filter_by (room_name=room).all()
    retval = [] 
    for rs in relsens: 
        retval.append (rs.toJSON())          
    return ({'relsens': retval}) 

# ---------------------- by room type -----------------
      
@app.route('/get/relsen/ids/of/room/type', methods=['GET'])      
def get_relsen_ids_of_room_type():    
    rtype = request.args.get('room_type')
    if (not rtype):
        return ({'error' : 'room_type is required'})
    relsens = Relsen.query.filter_by (room_type=rtype).all()
    retval = [] 
    for rs in relsens: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id} 
        retval.append (jrelson)          
    return ({'relsens': retval}) 
            
@app.route('/get/relsens/of/room/type', methods=['GET'])      
def get_relsens_of_room_type():    
    rtype = request.args.get('room_type')
    if (not rtype):
        return ({'error' : 'room_type is required'})
    relsens = Relsen.query.filter_by (room_type=rtype).all()
    retval = [] 
    for rs in relsens: 
        retval.append (rs.toJSON())          
    return ({'relsens': retval}) 
    
# ---------------------- by relsen type -----------------  
                
@app.route('/get/relsen/ids/of/type', methods =['GET']) 
def get_relsen_ids_of_type():
    type = request.args.get('relsen_type')
    if (not type):
        return ({'error' : 'relsen_type is required'})
    relsens = Relsen.query.filter_by (relsen_type=type).all()
    retval = [] 
    for rs in relsens: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}  
        retval.append (jrelson)  
    return ({'relsens': retval}) 


@app.route('/get/relsens/of/type', methods =['GET']) 
def get_relsens_of_type():
    type = request.args.get('relsen_type')
    if (not type):
        return ({'error' : 'relsen_type is required'})
    relsens = Relsen.query.filter_by (relsen_type=type).all()
    retval = [] 
    for rs in relsens: 
        retval.append (rs.toJSON())  
    return ({'relsens': retval}) 
    
# ---------------------- by group -----------------  
    
@app.route('/get/relsen/ids/of/group', methods =['GET']) 
def get_relsen_ids_of_group():
    grp = request.args.get('group_name')
    if (not grp):
        return ({'error' : 'group_name is required'})
    relsens = Relsen.query.filter_by (group_name=grp).all()
    retval = [] 
    for rs in relsens: 
        jrelson = {'device_id':rs.device_id, 'relson_id':rs.relsen_id}
        retval.append (jrelson) 
    return ({'relsens': retval}) 


@app.route('/get/relsens/of/group', methods =['GET']) 
def get_relsens_of_group():
    grp = request.args.get('group_name')
    if (not grp):
        return ({'error' : 'group_name is required'})
    relsens = Relsen.query.filter_by (group_name=grp).all()
    retval = [] 
    for rs in relsens: 
        retval.append (rs.toJSON()) 
    return ({'relsens': retval}) 
    
#-------------------------Status data ----------------------------------------------------------

@app.route('/get/last/status', methods =['GET'])  
def get_latest_status(): 
    return ({'place_holder':'not implemented'})  # TODO: this is to get the last known status from the
                                                 # DB, for troubleshooting/ autopsy
    
    
@app.route('/get/all/status', methods =['GET'])  # This can return a large number of records!
def get_all_status():                            # Need to include device id and relsen id also
    stat = Status.query.all()
    retval = [] 
    for s in stat: 
        jstatus = {'device_did' : s.device_id, 'time_stamp':s.time_stamp, 'online':s.online}
        jrel={"Relays":None}
        if (s.relay_status):
            jrel = json.loads(s.relay_status)
        jsen={"Sensors":None}
        if (s.sensor_values):
            jsen = {"Sensors":json.loads(s.sensor_values)}      
        jstatus.update (jrel)
        jstatus.update (jsen)
        retval.append (jstatus)      # TODO: map them one-on-one to the relsen_ids
    return ({'all_status': retval})
    
            
#---------------------------------------------------------------------------------------------------
# Test data
#---------------------------------------------------------------------------------------------------

@app.route('/add/minimal/data') 
def add_minimal_data():
    DEV1 = 'fan'
    DEV2 = 'portico'
    DEV3 = 'hydro'
    DEV4 = 'labs1'
    DEV5 = 'coffee'
    # TODO: all the following calls return False if they fail. Handle it!
    insert_device (device_id=DEV1, num_relays=1, enabled=True)
    insert_device (device_id=DEV2, num_relays=2, enabled=True)
    insert_device (device_id=DEV3, num_relays=2, enabled=True)
    insert_device (device_id=DEV4, num_relays=4, enabled=True)
    insert_device (device_id=DEV5, num_relays=2, enabled=False)
    insert_relsen (device_id=DEV1, relsen_id='POWER')
    insert_relsen (device_id=DEV2, relsen_id='POWER1')
    insert_relsen (device_id=DEV2, relsen_id='POWER2')
    insert_relsen (device_id=DEV3, relsen_id='POWER1')
    insert_relsen (device_id=DEV3, relsen_id='POWER2')
    insert_relsen (device_id=DEV4, relsen_id='POWER1')
    insert_relsen (device_id=DEV4, relsen_id='POWER2')
    insert_relsen (device_id=DEV4, relsen_id='POWER3')
    insert_relsen (device_id=DEV4, relsen_id='POWER4')
    insert_relsen (device_id=DEV5, relsen_id='POWER1')
    insert_relsen (device_id=DEV5, relsen_id='POWER2')    
    return ({'result': '5 Test devices added (if not existing)'})   
    

@app.route('/add/test/data') 
def add_test_data():    
    '''
    DEV1 = 'AA12345'
    DEV2 = 'BB45678'
    DEV3 = 'CC67890'
    '''
    DEV1 = 'fan'
    DEV2 = 'portico'
    DEV3 = 'hydro'    
    DEV4 = 'labs1'
    
    
    # TODO: all the following calls return False if they fail. Handle it!
    # device
    insert_device (device_id=DEV1, fallback_id='fb_DVES0BC870', mac='A2390BC870', ip='192.168.0.2',
                hardware_type="Generic", num_relays=1, num_sensors=1, enabled=True)
    insert_device (device_id=DEV2, fallback_id='fb_DVESBC8991', mac='B9034BC8991', ip='192.168.0.3',
                hardware_type="RND.MCU.AL2", num_relays=2, num_sensors=1, enabled=False)
    insert_device (device_id=DEV3, fallback_id='fb_DVES9021A8', mac='C0B5E59021A8', ip='192.168.0.4',
                hardware_type="Generic", num_relays=4, num_sensors=0, enabled=True)
    insert_device (device_id=DEV4, fallback_id='fb_DVES0C45A1', mac='FF34E0C45A1', ip='192.168.0.5',
                hardware_type="MCU.4.PIR.RAD.2R", num_relays=4, num_sensors=1, enabled=True)                
                
    # relsen
    sched1 = json.dumps({"schedule":[[6.30,7.0],[18.0,19.20]]})
    sched2 = json.dumps({"schedule":[[11.0,12.0],[13.0,14.50]]})
    sched3 = json.dumps({"schedule":[[10.0,15.10]]})
    sched4 = json.dumps({"schedule":[[9.0,12.0],[12.10,12.40],[16.0,18.30]]})

    insert_relsen (device_id=DEV1, relsen_id='POWER1', relsen_name='Guest fan', relsen_type='Fan', 
                room_name='Master bed room', room_type='Bed room', group_name='Ground floor',
                schedule=None, repeat=False)    
    insert_relsen (device_id=DEV1, relsen_id='SENSOR', relsen_name='Temperature', relsen_type='Temperature sensor', 
                room_name='Guest room', room_type='Bed room', group_name='Sensors',
                schedule=sched1, repeat=False)    
    insert_relsen (device_id=DEV1, relsen_id='SENSOR', relsen_name='Humidity', relsen_type='Humidity sensor', 
                room_name='Master bed room', room_type='Bed room', group_name='Sensors',
                schedule=None, repeat=False)   
    insert_relsen (device_id=DEV2, relsen_id='POWER1', relsen_name='Bed room fan', relsen_type='Fan', 
                room_name='Master bed room', room_type='Bed room', group_name='Ground floor',
                schedule=sched2, repeat=True)    
    insert_relsen (device_id=DEV2, relsen_id='POWER2', relsen_name='Bed room light', relsen_type='Tube light', 
                room_name='Master bed room', room_type='Bed room', group_name='Ground floor',
                schedule=sched3, repeat=True)    
    insert_relsen (device_id=DEV2, relsen_id='SENSOR', relsen_name='Garage door', relsen_type='Door sensor', 
                room_name='Garage', room_type='Garage', group_name='Sensors',
                schedule=None, repeat=False)                    
    insert_relsen (device_id=DEV3, relsen_id='POWER1', relsen_name='Bath light', relsen_type='Bulb', 
                room_name='Main bath room', room_type='Bath room', group_name='Ground floor',
                schedule=sched1, repeat=True)    
    insert_relsen (device_id=DEV3, relsen_id='POWER2', relsen_name='Corridor light', relsen_type='Bulb', 
                room_name='Varanda', room_type='Corridor', group_name='Ground floor',
                schedule=None, repeat=False)    
    insert_relsen (device_id=DEV3, relsen_id='POWER3', relsen_name='Sit out light', relsen_type='Flood light', 
                room_name='sit out', room_type='Balcony', group_name='First floor',
                schedule=None, repeat=False)     
    insert_relsen (device_id=DEV3, relsen_id='POWER4', relsen_name='Balcony light', relsen_type='Tube light', 
                room_name='sit out', room_type='Balcony', group_name='First floor',
                schedule=sched3, repeat=False)     
    insert_relsen (device_id=DEV4, relsen_id='POWER1', relsen_name='AC', relsen_type='Air conditioner', 
                room_name='Kids bed room', room_type='Bed room', group_name='First floor',
                schedule=sched1, repeat=True)   
    insert_relsen (device_id=DEV4, relsen_id='POWER2', relsen_name='Geyser', relsen_type='Water heater', 
                room_name='Kids bath room', room_type='Bath room', group_name='First floor',
                schedule=sched4, repeat=True)   
    insert_relsen (device_id=DEV4, relsen_id='POWER3', relsen_name='AC', relsen_type='Air conditioner', 
                room_name='Grandma\'s bed room', room_type='Bed room', group_name='Ground floor',
                schedule=sched4, repeat=True)   
    insert_relsen (device_id=DEV4, relsen_id='POWER4', relsen_name='Fan', relsen_type='Fan', 
                room_name='Grandma\'s bath room', room_type='Bath room', group_name='Ground floor',
                schedule=sched4, repeat=True)                 
    insert_relsen (device_id=DEV4, relsen_id='SENSOR', relsen_name='Garage door', relsen_type='Door sensor', 
                room_name='Garage', room_type='Basement', group_name='Sensors',
                schedule=None, repeat=False)       
    # status
    stat1 = json.dumps({"Relays":[1,0,1,0]})
    stat2 = json.dumps({"Relays":[1,0,1,0]})
    stat3 = json.dumps({"Relays":[1,0,1,0]})
    stat4 = json.dumps({"Relays":[1,0,1,0]})
    sensor1 = json.dumps({"Temperature":31.6, "Humidity":76.1})
    sensor2 = json.dumps({"Temperature":22.2, "Humidity":66.9})
    sensor3 = json.dumps({"Light":786})
    sensor4 = json.dumps({"Light":1022})
    sensor5 = json.dumps({"Garage door":"Open"})
    
    insert_status (device_id=DEV1, relay_status=stat1, event_type='Response', online=True)
    insert_status (device_id=DEV1, sensor_values=sensor1, event_type='Autonomous', online=True)
    insert_status (device_id=DEV2, relay_status=stat2, event_type='Event', online=True)
    insert_status (device_id=DEV3, relay_status=stat3, sensor_values=sensor2, event_type='Health', online=True)
    insert_status (device_id=DEV4, relay_status=stat4, sensor_values=sensor3, event_type='Health', online=True)
    insert_status (device_id=DEV4, sensor_values=sensor5, event_type='Event', online=True)
    return ({'result': '4 Test devices added (if not existing)'})   
    
@app.route('/simul/update/device') 
def simul_update_device():
    dev = Device.query.filter_by (device_id='portico').first()
    if (not dev):
        return {'error' : 'invalid device_id'}
    en = not(dev.enabled)  # toggle the current status
    jupdate = {'device_id' : 'portico', 'enabled' : en}
    update_device (jupdate)
    return {'result' : 'device portico updated'}
    
@app.route('/simul/update/relsen') 
def simul_update_relsen():
    rs = Relsen.query.filter_by (device_id='labs1', relsen_id='POWER1').first()
    if (not rs):
        return {'error' : 'invalid device_id or relsen_id'}
    jupdate = {
        'device_id':'labs1', 'relsen_id':'POWER1',
        'relsen_name':'Table fan', 'relsen_type': 'Fan',
        'room_name':'Grandpa\'s room', 'room_type': 'Dining room', 'group_name':'Basement',
        'schedule': json.dumps({"schedule":[[10.0,11.30]]}), 
        'repeat':False
    }
    update_relsen (jupdate)
    return {'result' : 'relsen labs1.POWER1 updated'}    
    
    
    


#-----------------------------------------------------------------------------------------

dprint ('\nThis is Database Developer') 
dprint ("Running Module: ", __name__)   
dprint ('Database: ', app.config['SQLALCHEMY_DATABASE_URI'])
app.run(debug=True)

'''----------------------------------------------------------------------------------------
list all the room names         (eg. Grandma's room, guest room)
list all room types             (eg. bed room, bath room)
list all relay/sensor types     (eg. tube light, fan, AC, CO2 sensor)

Filter:
list all active devices
list all inactive (disabled) devices
list all devices of type 'tube light'   - filter by device type
list all devices in 'guest room'        - filter by room name
list all devices in 'Bed room'          - filter by room type
list all devices in 'Ground floor'      - filter by location or group name
list all devices that are ON            - filter by device status (ON or OFF)
list all devices that are offline       - filter by network status (online or offline)
---------------------------------------------------------------------------------------- 
There are only two API calls using HTTP POST: <br/>
1) To enable/disable a device: <br/>
Make a POST request to  http://<server:port>/update/device  <br/>
Payload: <br/>
{ <br/>
  'device_id' : 'portico',  <br/>
  'enabled' : true  <br/>
} <br/>
 <br/>
2) To update a relsen object: <br/>
Make a POST request to  http://<server:port>/update/relsen  <br/>
Payload: <br/>
{ <br/>
  'device_id' : 'portico',  <br/>
  'relsen_id' : 'POWER2',  <br/>
  'relsen_name' : 'Bed room fan', <br/> 
  'relsen_type' : 'Fan',  <br/>
  'room_name' : 'Master bed room', <br/> 
  'room_type' : 'Bed room',  <br/>
  'group_name' : 'Ground floor', <br/>
  'schedule' : [[11.45,12.0],[13.0,14.30]]  <br/>
} <br/>
''' 
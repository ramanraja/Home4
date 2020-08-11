# Wrapper around MariaDB
# pip install mariadb
'''
NOTE: You must fetch the complete result set before querying again with the same connection
    because fetchone() can still leave many more rows in the cursor.
    
Parameterized SELECT statement:    
"SELECT device_id FROM deviceConfig WHERE device_id = %s;"    # NOTE: there are no single quotes around %s
cursor.execute (SQL_DEVICE_EXISTS, (device_id,))     # NOTE: even a single parameter has to be wrapped as a tuple

TODO: 
implement all other SQLs
get/set device schedule
Disable if(relay_count>num_relays) error check: there may be sensors which will not be counted within num_relays
Sending 'device offline' error message when the result set is empty is not right. There will always be some stale data in the DB; check
   if the last time stamp is more than 10 minutes old, and declare it offline.
'''

import json
import mariadb
from datetime import datetime
import PasswordStore
from MariaSql import *
from CryptoConfig import CryptoConfig


class MariaWrapper():
    debug = False
    connection = None
    cursor = None
    
    def __init__(self, debug=False):   
        self.debug = debug
        if self.debug:
            print ('Maria Wrapper V 2.0')
        
    def scheduleToString (self, schedule_list):
        # input is of the type [hour,min,hour,min]
        if len(schedule_list) < 4:   # the schedule can be empty
            return ('') 
        err = False
        if (schedule_list[0] < 0 or schedule_list[0] > 23): err = True
        if (schedule_list[1] < 0 or schedule_list[1] > 59): err = True
        if (schedule_list[2] < 0 or schedule_list[2] > 23): err = True
        if (schedule_list[3] < 0 or schedule_list[3] > 59): err = True
        if err:
            #raise Exception ('Invalid schedule time')
            return ({'error' : 'Invalid schedule time' })
        retstr = str(schedule_list)[1:-1]  # this removes the square brackets
        #print(retstr)
        return retstr
        
        
    def listToString (self, integer_list):
        # input is of the type [int,int,int]
        retstr =  str(integer_list)[1:-1]
        print(retstr)
        return retstr
        
        
    def stringToList (self, num_str):
        retarr = []
        if len(num_str)==0:
            return (retarr)
        sp = num_str.split(',')
        for n in sp:
            retarr.append(int(n))
        return (retarr)
                    
                    
    def connect (self, db="intof", host="localhost", port=3300):
        try:
            if self.cursor:
                self.cursor.close()          
            if self.connection:
                self.connection.close()      
            self.connection = mariadb.connect (user=PasswordStore.db_user, password=PasswordStore.db_password, 
                                              database=db, host=host, port=port)
            self.connection.autocommit = True  # this is the default, anyway
            self.cursor = self.connection.cursor()
            if (self.debug):
                print ('Connected to DB {}@{}:{}'.format (db,host,port))
        except Exception as e:
            self.connection = None
            err = 'Failed to connect to DB- {}'.format(str(e))
            print(err)
            raise Exception(err)     
            #return ({'error' : err})
        return  ({'result' : 'success'})
            
            
    def close (self):
        if self.cursor:
            self.cursor.close()    
        if self.connection:
            self.connection.close()
        if (self.debug):
            print ('DB Connection closed.')            
        return  ({'result' : 'success'}) 

                         
    def getTimeStamp (self):
        self.cursor.execute (SQL_GET_TIMESTAMP)
        ts = self.cursor.fetchall()[0][0]
        if (self.debug):
            print (ts)    
        return (ts.strftime('%Y-%m-%d %H:%M:%S'))        
        
        
    def listTables (self):
        self.cursor.execute (SQL_LIST_TABLES)
        tabs = self.cursor.fetchall()
        lis = []
        for t in tabs:
            lis.append (t[0])   # single column tuple    
        return ({'tables' : lis})        
        
        
    def createTables (self):     
        if (self.debug):
            print ('Creating tables..')         
        for sql in CREATE_TABLES:      
            self.cursor.execute (sql)
        self.initDeviceTypes()     
        self.initRoomTypes()
        return ({'result' : 'success'}) 

            
    def dropTables (self):      
        if (self.debug):
            print ('Dropping tables..')        
        for sql in DROP_TABLES:       
            self.cursor.execute (sql) 
        return ({'result' : 'success'}) 
            
            
    def initDeviceTypes (self):  # called automatically during create_tables
        self.insertDeviceTypes (DEVICE_TYPE_SEED)
        return ({'result' : 'success'}) 

        
    def insertDeviceTypes (self, jdev_types):   # this is the same as update_device_types()
        #if self.debug: print(jdev_types)
        self.cursor.execute (SQL_DELETE_DEVICE_TYPES) # clear the list first
        for dt in jdev_types['device_types']: 
            self.cursor.execute (SQL_INSERT_DEVICE_TYPE, (dt,))
        return ({'result' : 'success'}) 

                                 
    def getDeviceTypes (self):            
        self.cursor.execute (SQL_GET_DEVICE_TYPES)
        types = self.cursor.fetchall()
        lis = []
        for t in types:
            lis.append (t[0])   # single column tuple    
        return ({'device_types' : lis})
        
                     
    def initRoomTypes (self):   # called automatically during create_tables
        self.insertRoomTypes (ROOM_TYPE_SEED)
        return ({'result' : 'success'}) 

        
    def insertRoomTypes (self, jroom_types):   # this is the same as update_room_types()
        #if self.debug: print(jroom_types)
        self.cursor.execute (SQL_DELETE_ROOM_TYPES) # clear the list first
        for rt in jroom_types['room_types']: 
            self.cursor.execute (SQL_INSERT_ROOM_TYPE, (rt,))
        return ({'result' : 'success'}) 
            
            
    def getRoomTypes (self):            
        self.cursor.execute (SQL_GET_ROOM_TYPES)
        types = self.cursor.fetchall()
        lis = []
        for t in types:
            lis.append (t[0])   # single column tuple    
        return ({'room_types' : lis})
        
        
    def getHardwareTypes (self):  # never called explicitly; it is just a database SELECT UNIQUE method          
        self.cursor.execute (SQL_GET_HARDWARE_TYPES)
        types = self.cursor.fetchall()
        lis = []
        for t in types:
            lis.append (t[0])   # single column tuple    
        return ({'hardware_types' : lis})
                                 
                                 
    def insertAppConfig (self, japp_config):
        crypto = CryptoConfig (debug=False)
        encrypted_str = crypto.encrypt_json (japp_config['config_item']) 
        temp_config = {}
        temp_config['config_id'] = japp_config['config_id']
        temp_config['config_item'] =  encrypted_str  
        self.cursor.execute (SQL_INSERT_APP_CONFIG, temp_config)           
        return ({'result' : 'success'}) 

            
    def getAppConfig (self, jconfig_id):
        self.cursor.execute (SQL_GET_APP_CONFIG, jconfig_id)   
        conf = self.cursor.fetchall()
        retval = {}
        if conf and len(conf) >0:
            retval['config_id'] = conf[0][0]
            crypto = CryptoConfig (debug=False)
            retval['config_item'] = crypto.decrypt_json (conf[0][1]) 
            return retval    
        return ({'error' : 'config id not found'})
               
    
    # This is an internal method; returns True/False
    # It takes either a simple string or a JSON as input
    def deviceExists (self, dev_id):
        if isinstance(dev_id, str):
            self.cursor.execute (SQL_DEVICE_EXISTS, {'device_id':dev_id})
        else:
            self.cursor.execute (SQL_DEVICE_EXISTS, (dev_id)) 
        macs = self.cursor.fetchall()
        return (len(macs) > 0)   # boolean
        
        
    def getNumRelays (self, jdevice_id):
        self.cursor.execute (SQL_GET_NUM_RELAYS, jdevice_id)
        retval = {'device_id' : jdevice_id['device_id'], 'num_relays': 0}
        rows = self.cursor.fetchall()
        #if self.debug: print(rows)
        if len(rows)==0:
            return retval
        retval['num_relays'] = int(rows[0][0])
        return retval
        
                      
    # called by the device, to register itself with the hub
    def registerDevice (self, jmin_device):
        if not self.deviceExists (jmin_device['device_id']):
            self.cursor.execute (SQL_NEW_DEVICE, jmin_device)
            return ({'result':'success'})
        if self.debug: print ('Device already registered')
        return ({'error' : 'Device already registered'})
        
    
    # called by admin, to insert a fully provisioned device from the back end
    def directInsertDevice (self, jfull_device):
        if not self.deviceExists (jfull_device['device_id']):    
            self.cursor.execute (SQL_INSERT_DEVICE, jfull_device)    
            return ({'result':'success'})
        if self.debug: print ('Device already exists')
        return ({'error': 'Device already exists'})
            
                
    # called by mobile, before provisioning them
    def getNewDevices (self):
        self.cursor.execute (SQL_GET_NEW_DEVICES)
        devices = self.cursor.fetchall()
        lis = []
        for d in devices:
            new_device = {
                'device_id' : d[0], 
                'hardware_type' : d[1], 
                'num_relays' : d[2],
                'room_name' : d[3],
                'room_type' : d[4]
            }
            lis.append (new_device)
        return ({'new_devices' : lis})
        
        
    # to re-provision deactivated devices
    def getInactiveDevices (self):
        self.cursor.execute (SQL_GET_INACTIVE_DEVICES)
        devices = self.cursor.fetchall()
        lis = []
        for d in devices:
            inactive_device = {
                'device_id' : d[0], 
                'hardware_type' : d[1], 
                'num_relays' : d[2],
                'room_name' : d[3],
                'room_type' : d[4]                
            }
            lis.append (inactive_device)
        return ({'inactive_devices' : lis})
        
                
    def getActiveDevices (self):
        self.cursor.execute (SQL_GET_ACTIVE_DEVICES)
        devices = self.cursor.fetchall()
        lis = []
        for d in devices:
            active_device = {
                'device_id' : d[0], 
                'hardware_type' : d[1],
                'num_relays' : d[2],
                'room_name' : d[3],
                'room_type' : d[4]                   
            }
            lis.append (active_device)
        return ({'active_devices' : lis})
  
  
    # this is actually onboarding the device; the next step is to configure the relays
    def provisionDevice (self, jprov_params):
        MACID = jprov_params['device_id']
        if not self.deviceExists (MACID):
            #raise Exception ('Invalid device id')
            return ({'error' : 'invalid device id'})    
        self.cursor.execute (SQL_PROVISION_DEVICE, jprov_params)
        return ({'result':'success'})
    

    def insertDeviceStatus (self, jdevice_stat):
        self.cursor.execute (SQL_INSERT_DEVICE_STATUS, jdevice_stat)
        return ({'result':'success'})
            
        
    def getDeviceStatus (self, jdevice_id):
        self.cursor.execute (SQL_GET_DEVICE_STATUS, jdevice_id) # get the latest record
        dev_status = self.cursor.fetchall()
        if dev_status and len(dev_status)>0:
            retval = {
                'device_id': dev_status[0][0],
                'time_stamp': dev_status[0][1].strftime('%Y-%m-%d %H:%M:%S'),
                'relay_status': dev_status[0][2]
            }
        else:
            retval = {'error' : 'no device status'}
        return (retval)
    

    def insertDeviceData (self, jdevice_data):
        MACID = jdevice_data['device_id']
        if not self.deviceExists (MACID):
            #raise Exception ('Invalid device id')
            return ({'error' : 'invalid device id'})       
        jdevice_data['data'] = json.dumps(jdevice_data['data'] )
        #if self.debug: print(jdevice_data)
        self.cursor.execute (SQL_INSERT_DEVICE_DATA, jdevice_data)
        return ({'result':'success'})
        
  
    def getDeviceData (self, jdevice_id):
        self.cursor.execute (SQL_GET_DEVICE_DATA, jdevice_id)
        dd = self.cursor.fetchall()
        #if self.debug: print(dd)
        if dd and len(dd)>0:
            retval = {
                'device_id': dd[0][0],
                'time_stamp': dd[0][1].strftime('%Y-%m-%d %H:%M:%S'),
                'relay_status': dd[0][2],
                'data': json.loads (dd[0][3])  # .decode()
            }
        else:
            retval = {'error' : 'device offline'}
        return (retval)
    
            
    def getDeviceConfig (self, jdevice_id):  
        self.cursor.execute (SQL_GET_DEVICE_CONFIG3, jdevice_id)    
        devcon = self.cursor.fetchone()
        #print (devcon)
        retval = {}
        if devcon and len(devcon)>0:
            retval = {
                'device_id': devcon[0],
                'hardware_type': devcon[1], 
                'num_relays' : devcon[2],
                'room_name' : devcon[3],
                'room_type' : devcon[4],                   
                'device_config' : []
            }
            while devcon and len(devcon)>0:
                dc = { 'name' : devcon[5], 'type': devcon[6], 
                       'schedule' : self.stringToList(devcon[7]) }
                retval['device_config'].append (dc)
                devcon = self.cursor.fetchone() # get them one by one
        else:
            retval = {'device_id' : jdevice_id['device_id'], 'device_config' : []}
        return (retval)    
    
      
    # deviceConfig table does not have a unique key, so duplicate MAC ids are possible.
    # So, delete the existing records of a device and reinsert new values 
    def insertDeviceConfig (self, jdevice_conf):
        #if self.debug: print(jdevice_conf)
        MACID = jdevice_conf['device_id']
        if not self.deviceExists (MACID):
            #raise Exception ('Invalid device id')
            return ({'error' : 'invalid device id'})   
        
        # TODO: there may be sensors (non-relays) which will exceed num_relays count
        jresult = self.getNumRelays ({'device_id': MACID})
        relay_count = jresult['num_relays']
        #if self.debug: print ('relay_count: ', relay_count)
        if len (jdevice_conf['device_config']) > relay_count:
            e = 'Number of config items exceeds relay count ({})'.format(relay_count)
            #raise Exception(e)  # TODO: revisit
            return ({'error' : e})   
        
        # delete all the existing configuration rows; otherwise the new rows will just get added
        self.cursor.execute (SQL_DELETE_DEVICE_CONFIG, {'device_id' : MACID})
        self.cursor.execute (SQL_UPDATE_LOCATION, {'device_id' : MACID, 
                                                   'room_name' : jdevice_conf['room_name'],
                                                   'room_type' : jdevice_conf['room_type']
                                                   })
        
        for c in jdevice_conf['device_config']:
            c ['device_id'] = MACID  # MAC id needs to be added to every record in the config table
            c ['schedule'] = self.scheduleToString (c['schedule'])
            self.cursor.execute (SQL_INSERT_DEVICE_CONFIG2, c)
        return ({'result' : 'success'}) 
        

    def insertDeviceEvent (self, jdevice_event):
        jdevice_event['event_body'] = json.dumps (jdevice_event['event_body'])
        self.cursor.execute (SQL_INSERT_DEVICE_EVENT, jdevice_event)        
        return ({'result' : 'success'}) 


    def getDeviceEvent (self, jdevice_id):
        self.cursor.execute (SQL_GET_DEVICE_EVENT, jdevice_id)
        de = self.cursor.fetchall()
        #if self.debug: print(de)
        if de and len(de) >0:
            retval = {
                'device_id': de[0][0],
                'time_stamp': de[0][1].strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': de[0][2],
                'event_body': json.loads (de[0][3])  # .decode()
            }
        else:
            retval = {'device_id' : jdevice_id['device_id'], 'event_type': None, 'event_body':'{}'}
        return (retval)
        
        
    def deleteDevice (self, jdevice_conf):
        MACID = jdevice_conf['device_id']
        if not self.deviceExists (MACID):
            #raise Exception ('Invalid device id')
            return ({'error' : 'invalid device id'})   
        self.cursor.execute (SQL_DELETE_DEVICE_CONFIG, {'device_id' : MACID})
        self.cursor.execute (SQL_DELETE_DEVICE_DATA, {'device_id' : MACID})
        self.cursor.execute (SQL_DELETE_DEVICE_EVENT, {'device_id' : MACID})
        self.cursor.execute (SQL_DELETE_DEVICE, {'device_id' : MACID})
        return ({'result' : 'success'}) 
                    
        
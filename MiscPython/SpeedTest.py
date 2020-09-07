# Python based internet speed tester
# Ref => https://github.com/sivel/speedtest-cli/

# pin install speedtest-cli

'''--------------------------------------------------------
To invoke speed test from command line:
 First, activate the virtual environment where you installed the speedtest-cli
 > speedtest-cli -h
 > speedtest-cli  
 > speedtest-cli  --simple
---------------------------------------------------------'''

from datetime import datetime
from os import path
import speedtest 
import threading
import time
import sys

file_name = datetime.now().strftime ("%A.csv")
print ('Log file: ', file_name)
file_exists = False
if (path.exists(file_name)):
    print ('File already exists. Appending..')
    file_exists = True
log_file = open(file_name, "a+")
if not file_exists:
    log_file.write ('TIME,SERVER,UPLINK,DOWNLINK\n')
    log_file.flush()
print ('Connecting to speed test server...')

connected = False
while True:
    try:
        st = speedtest.Speedtest() 
        connected = True
        break
    except Exception as e:
        print ('ERROR: ', str(e))
        time.sleep (10)
    except KeyboardInterrupt:
        break;
                    
if not connected:
    print ('No network!')
    log_file.close()
    sys.exit(0)
      
print ('Performing speed test...')
while True:
    try:
        try:
            err = False
            st.download()
            st.upload()
            res = st.results.dict()
            print (res)
        except Exception as e:
            print ('ERROR: ', str(e))
            err = True
        if not err:
            ts = datetime.now().strftime ("%H:%M")
            up = 0.0
            if 'upload' in res:
                up = round(res['upload']/1024/1024, 1)
            down = 0.0    
            if 'download' in res:    
                down = round(res['download']/1024/1024, 1)
            server = 'NULL'
            if 'server' in res:
                if 'host' in res['server']:
                    server = res['server']['host']
            log_entry = "{},{},{},{}\n".format (ts,server,up,down)
            print(log_entry)
            print()
            log_file.write (log_entry)
            log_file.flush()
        time.sleep (15*60)  # 15 minutes interval
    except KeyboardInterrupt:
        break;

log_file.close()
print('Bye!')

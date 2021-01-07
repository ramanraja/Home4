MQTT to socketIO two way bridge.

Using a factory pattern, with lazy initialization of socketio and mqtt objects (without a global app object)
Keeps trying to connect to MQTT broker initially till it succeeds.  

NEW IN THIS VERSION: Device Simulator added; retry once before declaring a device offline.

Test:
> mosquitto_sub -t stat/#  -v
> mosquitto_pub -t stat/labs1/POWER1  -m  ON   (Note: POWER and ON/OFF must be in upper case)

To know the status of a device: 
> mosquitto_pub -t cmnd/labs1/POWER0  -m ""

To monitor the device:
> mosquitto_sub -t stat/labs1/+ -v

To know the status of all devices: 
> mosquitto_pub -t cmnd/tasmotas/POWER0  -m ""

Send the relay id and the command, which
can be ON, OFF or TOGGLE.
To operate a relay, send a command to the hub through the web socket.
Format of the command payload:
{
	"device_id" : "BACD01234",
	"relsen_id" : "POWER1",
	"action" : "on"
}
'action' field will be '"on", "off" or "toggle" 
The command is not case sensitive.

Format of the response from the Hub:
{
	"device_id" : "BACD01234",
	"relsen_id" : "POWER1",
	"status" : "ON"
}

The server first sends an ACK with an echo of the command. 
Then the actual status from the devic (if any) is sent.

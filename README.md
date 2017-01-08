# rflink2mqtt
Python script to send rflink data to MQTT with sensors decodage.

example with openHAB

Receive data:
```
Number I_Temp_bedroom 		"Bedroom temperature [%.1f °C]"	<temperature>	(G_Bedroom ,G_All_Sensors)	{ mqtt="<[mymosquitto:rflink/temperature/2df1:state:default]"}
```
Send data:
```
String rfLinkTx "[%s]" {mqtt=">[mymosquitto:rflink/tx:command:*:default]"}
rfLinkTx.sendCommand("10;EV1527;09d4c0;03;" + lamp1Buttonrflink.state + ";")
```

Help: https://community.openhab.org/t/rflink-binding/7863/14

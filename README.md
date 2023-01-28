# rflink2mqtt
Python script to send rflink data to MQTT with sensors decodage.

## Docker
I use this container as a gateway, between my rflink (connected to arduino mega) to my Home Assistant Swarm network.
I have 2 rflink:
- First connected thanks to ser2net to my Home Assistant instance (I use rflink module inside HA)
```
rflink -- USB --> container ser2net -- swarm-network --> Home Assistant (rflink module)
```
- Second (RTS compatible), connected to my dev rflink2mqtt:
```
rflink -- USB --> container rflink2mqtt -- swarm-network --> Home Assistant (MQTT module)
```
### use docker-compose.yml
```
docker-compose up
```
Use with login and password, please add variables MQTT_USERNAME and MQTT_PWD in docker-compose.yml
https://hub.docker.com/r/mickaelh51/rflink2mqtt
## Example with HomeAssistant

### Send data:
```
- platform: template
  covers:
    living_room_windows:
      friendly_name: "LR windows"
      open_cover:
        - service: mqtt.publish
          data:
            topic: 'rflink2/tx'
            payload: '10;RTS;00000;0;UP;'

```
## Example with openHAB
### Receive data:
```
Number I_Temp_bedroom 		"Bedroom temperature [%.1f °C]"	<temperature>	(G_Bedroom ,G_All_Sensors)	{ mqtt="<[mymosquitto:rflink/temperature/2df1:state:default]"}
```
### Send data:
```
String rfLinkTx "[%s]" {mqtt=">[mymosquitto:rflink/tx:command:*:default]"}
rfLinkTx.sendCommand("10;EV1527;09d4c0;03;" + lamp1Buttonrflink.state + ";")
```

## Help: 
- https://community.openhab.org/t/rflink-binding/7863/14
- https://github.com/aequitas/python-rflink

## Updates
- 28-01-2023: Add support login and password
- 30-12-2022: Update script with python 3.9
- 30-12-2022: Add script into docker container

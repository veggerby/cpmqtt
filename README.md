# cpmqtt

## thonny_scripts

* Er indtil videre kun testet med ESP32.
   * ***mqtt_broker_wip***: fungere nogenlunde med MQTTx fra laptop, men fejler med myMQTT Android App når der bliver sendt beskeder.
      * skal testes med ESP32 MQTTsimple.

## jupyter_notebooks

   - [x] MicroPython intro og opgaver
   - [ ] WIP: installation af thonny og opsætning til ESP32/pico W board
   - [x] Test af om board LED og enkelt ekstra opgave
   - [x] Test af udlæsning af data fra BME280

   - [ ] Intro til MQTT's virkemåde
   - [ ] test af MQTTx, der skal forbindes til en "frivillig" access point og broker. Subscribe og publish beskeder mellem pirater
   - [ ] intro til WiFi som access point og station
   - [ ] opsætning af egen broker på ESP32, test med MQTTx sammen med en med-pirat
   - [ ] opsætning af klient, der for binder til broker. Test publish og subscribe MQTTx. eventuelt ekstra opgaver med at sende data fra BME280
   - [ ] Intro Node-Red dashboard. sende målinger fra BME280 til dashboard

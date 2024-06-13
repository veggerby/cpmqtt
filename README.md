# cpmqtt

## thonny_scripts

 #### ***MQTTBroker Class - Test***:
 * [x] Kan håndtere MQTTx app forbinder til enheden
    * [x] Kan modtage beskeder fra MQTTx app
    * [ ] Kan sende beskeder til MQTTx app - ***fejler MQTTx afbryder forbindelsen***
 * [x] Kan håndtere Android App myMQTT forbinder til enheden
   * [x] Kan modtage beskeder fra Android App myMQTT
   * [x] Kan sende beskeder til Android App myMQTT
 * [x] Kan håndtere at ESP32 `uMQTT.robust` forbinder til enheden
   * [x] Kan modtage beskeder fra ESP32 `uMQTT.robust`
   * [x] Kan sende beskeder til ESP32 `uMQTT.robust` 

 #### ***mqtt klienter Ping/Pong - Test***:
 * [x] Kan forbinde til RPI Zero Broker
     * [x] sende beskeder
     * [x] modtage beskeder
 * [x] Kan forbinde til ESP32 Broker
     * [x] sende beskeder
     * [x] modtage beskeder

## jupyter_notebooks

   - [x] MicroPython intro og opgaver
      - [ ] Introduktion til loops
   - [ ] WIP: installation af thonny og opsætning til ESP32/pico W board
   - [x] Test af om board RGB LED
   - [x] Test af udlæsning af data fra BME280
   - [x] OLED Display
   - [x] RGB LED strip
   - [x] Steppermotor
   - [x] LED og formodstande

   - [ ] Intro til MQTT's virkemåde
   - [ ] test af MQTTx, der skal forbindes til en "frivillig" access point og broker. Subscribe og publish beskeder mellem pirater
   - [ ] intro til WiFi som access point og station
   - [ ] opsætning af egen broker på ESP32, test med MQTTx sammen med en med-pirat
   - [ ] opsætning af klient, der for binder til broker. Test publish og subscribe MQTTx. eventuelt ekstra opgaver med at sende data fra BME280
   - [ ] Intro Node-Red dashboard. sende målinger fra BME280 til dashboard

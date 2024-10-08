# cpmqtt

## MQTT Test

<details>
<summary>Click here</summary>

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

</details>

## Jupyter Notebooks Tutorials

<details>
<summary>Click here</summary>

- [x] MicroPython intro
- [x] MicroPython intro opgaver
- [ ] WIP: installation af VSCode, PyMakr og jupyter notebook
- [x] Test af inbygget RGB LED
- [x] RGB LED strip
- [ ] Test af udlæsning af data fra BME280
- [ ] OLED Display
- [ ] Steppermotor
- [ ] LED og formodstande

   - [ ] Intro til MQTT's virkemåde
   - [ ] test af MQTTx, der skal forbindes til en "frivillig" access point og broker. Subscribe og publish beskeder mellem pirater
   - [ ] intro til WiFi som access point og station
   - [ ] opsætning af egen broker på ESP32, test med MQTTx sammen med en med-pirat
   - [ ] opsætning af klient, der for binder til broker. Test publish og subscribe MQTTx. eventuelt ekstra opgaver med at sende data fra BME280
   - [ ] Intro Node-Red dashboard. sende målinger fra BME280 til dashboard

## mqttx-cli

Publish

```sh
mqttx pub -t topic -m the-message -q 1 -V 3.1.1
```

Subscribe

```sh
mqttx sub -t topic -q 1 -V 3.1.1
```
## ESP32-C3

Flash

```sh
brew install esptool
```

or

```sh
pip install esptool
```

Download image from <https://micropython.org/download/ESP32_GENERIC/>

Flash ESP32:

```sh
esptool.py --chip esp32 --port /dev/cu.usbserial-145230 erase_flash
esptool.py --chip esp32 --port /dev/cu.usbserial-145230 --baud 460800 write_flash -z 0x1000 ./esp32/ESP32_GENERIC-20240602-v1.23.0.bin
```

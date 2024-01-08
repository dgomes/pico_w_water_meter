# Water Meter Sensor

Monitor your water usage through an energy-efficient IoT device attached to your water provider meter (which happens to have a metal "butterfly wheel) like the JANZ JT400:

![Water Meter](media/jt400.jpg "Water Meter")

![Water Meter](media/fitted.jpg "All in place")


This project enables you to monitor the water usage of your household water usage through the use of a DIY water meter sensor built using:

- [Raspberry Pi Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [Inductive Proximity Sensor Detection Switch - TL-W5MC1](https://www.aliexpress.com/item/32973109912.html)
- [TI High-Speed CMOS Logic 14-Stage Binary Counter](https://www.ti.com/lit/ds/symlink/cd54hc4020.pdf)

The RPI Pico W is very flexible in terms of power requirements, but in my case, I use:

- 18650 Battery
- [18650 TP4056 Lithium Battery Charger Module With Protection](https://www.aliexpress.com/item/32930640893.html)
- [Mini Boost Module Step Up Board 5V](https://www.aliexpress.com/item/4000626913742.html) (to power the Inductive Proximity Sensor which states minimum 6V but actually works with 5V)

Just assemble everything :)

![Box with PCB and Battery inside](media/prototype.jpg "Prototype")


You can find the PCB source files (KiCAD) in the respective directory. ([PCB files](https://github.com/dgomes/pico_w_water_meter/tree/main/Water%20Meter%20PCB))

I designed a 3D-printed adapter for the Inductive Proximity Sensor to fit the JANZ JT400.  ([3Dadapter](https://github.com/dgomes/pico_w_water_meter/tree/main/3Dadapter))

The RPi Pico W is flashed with a micropython firmware and then you upload the project available in `src`

You must have an MQTT broker (e.g. Mosquitto)

The project automatically integrates with [Home Assistant](https://www.home-assistant.io)

# config.py

You will need to create an additional file called `config.py` that must include the variables:

```python
SSID = "myhome_network"
WIFI_PASSWORD = "blablabla" 

SERVER = "192.168.1.1"  #this is your MQTT Broker Address
USER = None #change this to your MQTT username, else leave None
PASSWORD = None #change this to your MQTT password, else leave None

```

# Powering

- Using a 18650 3.7v battery the sensor can run for 2 weeks
- Using a battery pack of 4 AA batteries the sensor can run for 4 weeks

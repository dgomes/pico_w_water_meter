"""Water Meter."""

import json
import logging
import time

import lowpower
import network
import ubinascii
from machine import ADC, Pin, reset, unique_id
from micropython import const
from umqtt.robust import MQTTClient

from config import BSSID, SERVER, SSID, WIFI_PASSWORD, USER, PASSWORD

logging.basicConfig(level=logging.DEBUG)

VERSION = const(1)
MAX_WIFI_RETRIES = const(10)
RESET_VALUE = const(2**13)
MAX_BATTERY = const(3.98)  # 4.2v - 0.280v is the diode drop

NAME = "Water Meter"
NAME_SLUG = "water_meter"

CLIENT_ID = ubinascii.hexlify(unique_id())
STATE_TOPIC = f"{NAME_SLUG}/sensor/{NAME_SLUG}_total/state"
TOTAL_TOPIC = f"{NAME_SLUG}/sensor/total_water_usage/state"
BATT_STATE_TOPIC = f"{NAME_SLUG}/sensor/{NAME_SLUG}_battery_level/state"
BATT_VOLTAGE_TOPIC = f"{NAME_SLUG}/sensor/{NAME_SLUG}_voltage/state"
AVAILABILITY_TOPIC = f"{NAME_SLUG}/status"
CMD_TOPIC = f"{NAME_SLUG}/cmd"
DORMANT_PIN_TOPIC = f"{NAME_SLUG}/dormant"

CMD_RESET = b"reset"
CMD_DISCOVERY = b"discovery"

##
##  https://www.ti.com/lit/ds/symlink/cd54hc4020.pd
##
## 1st Column
q12 = Pin(7, Pin.IN, Pin.PULL_DOWN)
q13 = Pin(8, Pin.IN, Pin.PULL_DOWN)
q14 = Pin(9, Pin.IN, Pin.PULL_DOWN)
q6 = Pin(10, Pin.IN, Pin.PULL_DOWN)
q5 = Pin(11, Pin.IN, Pin.PULL_DOWN)
q7 = Pin(12, Pin.IN, Pin.PULL_DOWN)
q4 = Pin(13, Pin.IN, Pin.PULL_DOWN)
# gnd
## 2nd Column
# vcc
q11 = Pin(2, Pin.IN, Pin.PULL_DOWN)
q10 = Pin(3, Pin.IN, Pin.PULL_DOWN)
q8 = Pin(4, Pin.IN, Pin.PULL_DOWN)
q9 = Pin(5, Pin.IN, Pin.PULL_DOWN)
mr = Pin(22, Pin.OUT, value=0)
# cp
q1 = Pin(6, Pin.IN, Pin.PULL_DOWN)


spms = Pin("WL_GPIO1", Pin.OUT)
led = Pin("LED", Pin.OUT)
wlan_pwr = Pin(23, Pin.OUT)
DORMANT_PIN = 11

reset_pin = Pin(21, Pin.IN, Pin.PULL_DOWN)
reset_flag = reset_pin.value()

ha_discovery_flag = False


def ha_discovery(mqtt_client):
    """Send MQTT messages for Home Assistant Discovery."""
    device = {
        "ids": CLIENT_ID,
        "name": NAME,
        "sw": f"dgomes v{VERSION}",
        "mdl": "pico W",
        "mf": "Raspberry Foundation",
    }

    sensors = {
        "water_meter_total": {
            "dev_cla": "water",
            "unit_of_meas": "L",
            "stat_cla": "total_increasing",
            "name": f"{NAME} Total",
            "ic": "mdi:pulse",
            "stat_t": STATE_TOPIC,
            "ent_cat": "diagnostic",
            "uniq_id": "PICOsensorwater_meter_total",
            "dev": device,
            "value_template": "{{ value_json.counter }}",
        },
        "water_meter_battery_level": {
            "dev_cla": "battery",
            "unit_of_meas": "%",
            "name": f"{NAME} Battery Level",
            "stat_t": STATE_TOPIC,
            "frc_upd": "true",
            "uniq_id": "PICOsensorwater_meter_battery_level",
            "dev": device,
            "value_template": "{{ value_json.battery_level }}",
        },
        "water_meter_voltage": {
            "dev_cla": "voltage",
            "stat_cla": "measurement",
            "unit_of_meas": "V",
            "name": f"{NAME} Voltage",
            "stat_t": STATE_TOPIC,
            "ent_cat": "diagnostic",
            "frc_upd": "true",
            "uniq_id": "PICOsensorwater_meter_voltage",
            "dev": device,
            "value_template": "{{ value_json.voltage }}",
        },
        "total_water_usage": {
            "dev_cla": "water",
            "unit_of_meas": "m³",
            "stat_cla": "total_increasing",
            "name": f"{NAME} Total Usage",
            "stat_t": STATE_TOPIC,
            "uniq_id": "PICOsensortotal_water_usage",
            "dev": device,
            "value_template": "{{ value_json.total }}",
        },
    }
    logging.info("HA Discovery")
    blink_n_times(3, period=0.2)
    for name, sensor in sensors.items():
        logging.debug("%s: %s", name, json.dumps(sensor))
        mqtt_client.publish(
            f"homeassistant/sensor/water_meter/{name}/config".encode(),
            json.dumps(sensor).encode(),
            True,
            1,
        )


def blink_n_times(n: int, period: float = 0.5):
    """Blink LED."""
    for _ in range(2 * n):
        # toggle LED
        led(not led())
        time.sleep(period)


def wait_for_wifi(wlan):
    """Wait for connectiong to Wifi."""
    wlan.connect(SSID, WIFI_PASSWORD)  # , bssid=BSSID)

    # Wait for connect or fail
    max_wait = MAX_WIFI_RETRIES
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:  # cyw43-driver/src/cyw43.h:
            break
        max_wait -= 1
        blink_n_times(2)

    if wlan.status() != 3:
        raise Exception("not connected")
    logging.debug("Connected!")


def read_counter():
    """Read cd54hc4020."""
    counter = (
        (q14.value() << 13)
        | (q13.value() << 12)
        | (q12.value() << 11)
        | (q11.value() << 10)
        | (q10.value() << 9)
        | (q9.value() << 8)
        | (q8.value() << 7)
        | (q7.value() << 6)
        | (q6.value() << 5)
        | (q5.value() << 4)
        | (q4.value() << 3)
        | q1.value()
    )
    logging.debug("Meter: %s Liter", counter)
    return counter


def mqtt_callback(topic: str, msg: str):
    """MQTT Callback handler."""
    global reset_flag, ha_discovery_flag, DORMANT_PIN
    logging.debug((topic, msg))
    if topic == CMD_TOPIC.encode():
        if msg == CMD_RESET:
            reset_flag = True
        if msg == CMD_DISCOVERY:
            ha_discovery_flag = True
    elif topic == DORMANT_PIN_TOPIC.encode():
        DORMANT_PIN = int(msg)


def measure_vsys():
    """Retrieve VSYS."""
    # https://forums.raspberrypi.com/viewtopic.php?p=2062568&sid=3b63feda7bb0465d6234551dd5286da2#p2062568
    Pin(25, Pin.OUT, value=1)
    Pin(29, Pin.IN, pull=None)
    reading = ADC(3).read_u16() * 9.9 / 2**16
    logging.debug("VSYS: %s Volt", reading)

    Pin(25, Pin.OUT, value=0, pull=Pin.PULL_DOWN)
    Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
    return reading


def main():
    """Fake a Main Loop through a reset at the end."""
    # Inital setup
    global reset_flag, ha_discovery_flag

    # Measure battery before anything wifi related
    battery = measure_vsys()

    # Connect to MQTT Server
    led.on()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wait_for_wifi(wlan)

        mqtt_client = MQTTClient(CLIENT_ID, SERVER, user=USER, password=PASSWORD, keepalive=30)
        mqtt_client.connect(clean_session=False)
        mqtt_client.set_callback(mqtt_callback)
        mqtt_client.subscribe(CMD_TOPIC.encode())
        mqtt_client.publish(AVAILABILITY_TOPIC.encode(), "online", True, 1)

        # read the meter
        meter = read_counter()
        if meter < 16 or ha_discovery_flag:
            ha_discovery(mqtt_client)
            ha_discovery_flag = False
        state = {
            "counter": meter / 10,
            "battery_level": int(100 * battery / MAX_BATTERY),
            "voltage": round(battery, 2),
            "total": meter * 0.0001,
        }
        # Publish meter information
        mqtt_client.publish(STATE_TOPIC.encode(), json.dumps(state).encode(), False, 1)

        # Before sleeping again
        mqtt_client.check_msg()
        mqtt_client.publish(AVAILABILITY_TOPIC.encode(), "offline", True, 1)

        logging.debug("Disconnect")
        mqtt_client.disconnect()
        wlan.disconnect()
    except Exception as e:
        logging.error(e)
        reset()

    led.off()
    wlan.active(False)
    wlan.deinit()
    time.sleep_us(100)
    wlan_pwr.low()

    if reset_flag or meter >= RESET_VALUE:
        mr.on()
        logging.info("RESET METER")
        time.sleep_us(100)
        reset_flag = False
        mr.off()

    spms.low()
    lowpower.dormant_with_modes({DORMANT_PIN: (lowpower.EDGE_LOW | lowpower.EDGE_HIGH)})

    reset()


if __name__ == "__main__":
    main()

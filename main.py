import json
import uasyncio
import time
from phew import connect_to_wifi, server
from machine import ADC, Pin, Timer

from relay import Relay

# Read the config
settings = json.load(open('config.json'))

# We need to create a lights object,
# so we can control it
lights = Relay(pin=settings["Relay_Pin"], mode=settings["Relay_Mode"])
rearm_timer = None


def arm(armed_state=None):
    armed_state = armed_state or settings["Armed"]
    settings["Armed"] = armed_state
    with open('config.json', 'w') as f:
        json.dump(settings, f)


@server.route("/lights_on")
def lights_on(request):
    lights.turn_on()
    return "", 200


@server.route("/lights_off")
def lights_off(request):
    lights.turn_off()
    global rearm_timer
    rearm_timer = Timer(period=12 * 60 * 60, mode=Timer.ONE_SHOT, callback=arm)
    return "", 200


@server.route("/ruok")
def ruok(request):
    return f"{lights.on}", 200


@server.route("/status")
def status(request):
    out = settings.copy()
    out["Lights"] = lights.on
    return json.dumps(out), 200


@server.route("/settings_update", methods=["POST", "GET"])
def settings_update(request):
    settings = request.data
    print(settings)
    # with open('config.json', 'w') as f:
    #     json.dump(settings, f)


@server.route("/arm")
def arm_sensor(request):
    arm(True)
    return "", 200


@server.route("/disarm")
def disarm_sensor(request):
    arm(False)
    return "", 200


@server.route("/")
def index(request):
    return "<h1>Hello, World!</h1>", 200


@server.catchall()
def catchall(request):
    return f"You've found the server!", 200


async def go_serve():
    server.run(host="0.0.0.0", port=80)


async def monitor():
    sensor = ADC(Pin(settings["Sensor_Pin"]))
    while True:
        # do thing
        if settings["Armed"]:
            current_light = sensor.read_u16()
            if current_light < settings["Light_Sense_Cutoff"] and lights.on:
                lights.turn_off()
            elif current_light > settings["Light_Sense_Cutoff"] and not lights.on:
                lights.turn_on()
        time.sleep_ms(500)


async def main():
    """ Set up both the server and the light level monitor"""
    uasyncio.create_task(go_serve())
    if settings["Sensor_Pin"] > 0:
        uasyncio.create_task(monitor())

    await uasyncio.sleep(10)


if __name__ == "__main__":
    ip = connect_to_wifi(settings["SSID"], settings["Password"])

    print(ip)

    time.sleep(2)
    server.run(host="0.0.0.0", port=80)

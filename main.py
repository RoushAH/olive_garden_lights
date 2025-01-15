import json
import uasyncio
import time
from phew import connect_to_wifi, server
from machine import ADC, Pin, Timer

from relay import Relay

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'text/html'
}

# Read the config
settings = json.load(open('config.json'))
armed = True

# We need to create a lights object,
# so we can control it
lights = Relay(pin=settings["Relay_Pin"], mode=settings["Relay_Mode"])
rearm_timer = None


def average_light(values):
    if len(values) < settings["Sense_Count"]:
        return int(sum(values) / len(values))
    values = values[-settings["Sense_Count"]:]
    return int(sum(values) / settings["Sense_Count"])


def arm(armed_state=None):
    global armed
    armed = armed_state or settings["Armed"]


@server.route("/lights_on")
def lights_on(request=None):
    lights.turn_on()

    response = server.Response(body=str(lights.on), status=200, headers=HEADERS)
    return response


@server.route("/lights_off")
def lights_off(request=None):
    global armed, rearm_timer

    lights.turn_off()
    armed = False
    rearm_timer = Timer(period=12 * 60 * 60, mode=Timer.ONE_SHOT, callback=arm)

    response = server.Response(body=str(lights.on), status=200, headers=HEADERS)
    return response


@server.route("/ruok")
def ruok(request):
    response = server.Response(body=str(lights.on), status=200, headers=HEADERS)
    return response


@server.route("/status")
def status(request):
    out = settings.copy()
    out["Lights"] = lights.on

    response = server.Response(body=json.dumps(out), status=200, headers=HEADERS)
    return response


@server.route("/settings_update", methods=["POST", "GET"])
def settings_update(request):
    global settings
    settings = request.data

    if "Lights" in settings:
        lights.set_state(settings.pop("Lights"))

    with open('config.json', 'w') as f:
        json.dump(settings, f)
    return status(request)


@server.route("/")
def index(request):
    response = server.Response(body="<h1>Hello, World!</h1>", status=200, headers=HEADERS)
    return response


@server.catchall()
def catchall(request):
    response = server.Response(body="You've found the server!", status=404, headers=HEADERS)
    return response


async def go_serve():
    server.run(host="0.0.0.0", port=80)


async def monitor():
    sensor = ADC(Pin(settings["Sensor_Pin"]))
    reads = []
    print(sensor, reads)
    cooldown = 0 # Prevent flickering when crossing the boundary of on to off
    fudge_factor = 1 + 0.01 * cooldown # To also smooth the curve
    while True:
        # do thing
        if armed:
            reads.append(sensor.read_u16())
            current_light = average_light(reads)
            if cooldown > 0:
                cooldown -= 1
            print(current_light)
            if current_light < settings["Light_Sensitivity"] and lights.on and cooldown == 0:
                lights.turn_off()
                cooldown = settings["Cooldown"]
            elif current_light > settings["Light_Sensitivity"] + fudge_factor and not lights.on and cooldown == 0:
                lights.turn_on()
                cooldown = settings["Cooldown"]
        time.sleep_ms(500)


async def debug_control():
    while True:
        if input("On?") == "y":
            lights.turn_on()
        else:
            lights.turn_off()
        time.sleep_ms(1500)


async def main():
    """ Set up both the server and the light level monitor"""
    # uasyncio.create_task(go_serve())
    if settings["Sensor_Pin"] > 0:
        uasyncio.create_task(monitor())
    else:
        uasyncio.create_task(debug_control())

    await uasyncio.sleep(10)


if __name__ == "__main__":
#     ip = connect_to_wifi(settings["SSID"], settings["Password"])
# 
#     print(ip)

    time.sleep(2)
    uasyncio.run(main())
    # server.run(host="0.0.0.0", port=80)

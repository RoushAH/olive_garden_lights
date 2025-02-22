import json
import uasyncio
import time
from phew import connect_to_wifi, server
from machine import ADC, Pin, Timer

from relay import Relay

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, contenttype',
    'Content-Type': 'text/html'
}

# Read the config
settings = json.load(open('config.json'))

armed = True
attempt_rearm = None  # timer to track how many seconds of 'daylight' to rearm sensor

# We need to create a lights object,
# so we can control it
lights = Relay(pin=settings["Relay_Pin"], mode=settings["Relay_Mode"])

reads = []


def average_light(values):
    if len(values) < settings["Sense_Count"]:
        return int(sum(values) / len(values))
    values = values[-settings["Sense_Count"]:]
    return int(sum(values) / settings["Sense_Count"])


@server.route("/lights_on")
def lights_on(request=None):
    lights.turn_on()

    response = server.Response(body=str(lights.on), status=200, headers=HEADERS)
    return response


@server.route("/lights_off")
def lights_off(request=None):
    global attempt_rearm

    lights.turn_off()
    attempt_rearm = settings["Attempt_Rearm"]

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
    out["Sensor_Value"] = reads[-1]

    response = server.Response(body=json.dumps(out), status=200, headers=HEADERS)
    return response


@server.route("/settings_update", methods=["OPTIONS"])
def settings_options(request):
    return server.Response(body="", status=200, headers=HEADERS)


@server.route("/settings_update", methods=["POST", "GET"])
def settings_update(request):
    update = False
    global settings, armed

    if "Lights" in request.data:
        lights.set_state(request.data["Lights"])
        if not request.data["Lights"]:
            global attempt_rearm
            attempt_rearm = settings["Attempt_Rearm"]

    if "Armed" in request.data:
        armed = request.data["Armed"]
        settings["Armed"] = armed
        update = True

    if "Light_Sensitivity" in request.data:
        settings["Light_Sensitivity"] = request.data["Light_Sensitivity"]
        update = True
    
#     if "Write_Me" in request.data:
#         update = True

    if update:
        with open('config.json', 'w') as f:
            json.dump(settings, f)

    return server.Response(body=json.dumps(settings), status=200, headers=HEADERS)


@server.route("/")
def index(request):
    response = server.Response(body="<h1>Hello, World!</h1>", status=200, headers=HEADERS)
    return response

# @server.route("/data")
# def data(request):
#     print("Tryint")
#     try:
#         print("got here")
#         with open("data.txt", "r") as f:
#             data = f.read()
#     except Exception as e:
#         data = str(e)
#     print(data)
#     response = server.Response(body = str(data), status=200, headers=HEADERS)
#     return response


@server.catchall()
def catchall(request):
    response = server.Response(body="You've found the server!", status=404, headers=HEADERS)
    return response

# def write_data(datum):
#     try:
#         with open('data.txt', 'a') as f:
#             output = f"{datum};\n"
#             f.write(output)
#     except Exception as e:
#         print(f"sad trombone\n{e}")

async def go_serve():
    # try:
    server.run(host="0.0.0.0", port=80)
    # except Exception as e:
    #     print(f"Server crash: {e}")


async def monitor():
    global armed, attempt_rearm, reads
    sensor = ADC(Pin(settings["Sensor_Pin"]))
    cooldown = 0  # Prevent flickering when crossing the boundary of on to off
    fudge_factor = 1 + 0.01 * cooldown  # To also smooth the curve
    count = 0
    while True:
        # do thing
        reads.append(sensor.read_u16())
        current_light = average_light(reads)
        if len(reads) > settings["Sense_Count"]:
            reads.pop(0)
        if cooldown > 0:
            cooldown -= 1
#         print(f"{current_light}: {reads}")
        # Now time to do the sensing.
        # Note about arming -- if attempt_rearm exists, then we are 'armed to the user but inactive'
        # First, if the light is too bright out, turn lights off, decrement or reset the disarm timer if necessary
        if current_light < settings["Light_Sensitivity"]:
            if lights.on and cooldown == 0 and armed:
                lights.turn_off()
                cooldown = settings["Cooldown"]
            elif attempt_rearm and attempt_rearm > 0:
                # Approaching rearming
                attempt_rearm -= 1
            elif not armed and attempt_rearm and attempt_rearm <= 0:
                armed = True
                attempt_rearm = None
        # Next, if the light is too dim, either turn on the lights if no reset timer
        # Or blank the reset timer if needed
        elif current_light > settings["Light_Sensitivity"] + fudge_factor:
            if not lights.on and cooldown == 0 and not attempt_rearm and armed:
                lights.turn_on()
                cooldown = settings["Cooldown"]
            elif attempt_rearm and attempt_rearm < settings["Attempt_Rearm"]:
                attempt_rearm = settings["Attempt_Rearm"]
#         count += 1
#         if count >= settings["write_time"]:
#             write_data(current_light)
#             count = 0
        await uasyncio.sleep(1)


async def debug_control():
    """ Simulate sensor response with user input"""
    while True:
        if input("On?") == "y":
            lights.turn_on()
        else:
            lights.turn_off()
        await uasyncio.sleep(2)


async def main():
    """ Set up both the server and the light level monitor"""
    uasyncio.create_task(go_serve())
    if settings["Sensor_Pin"] > 0:
        uasyncio.create_task(monitor())
    else:
        uasyncio.create_task(debug_control())

    await uasyncio.sleep(10)


if __name__ == "__main__":
    ip = connect_to_wifi(settings["SSID"], settings["Password"])

    print(ip)

    time.sleep(2)
    uasyncio.run(main())
    # server.run(host="0.0.0.0", port=80)

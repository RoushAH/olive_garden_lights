import json
from phew import connect_to_wifi, server

from relay import Relay

# Read the config
settings = json.load(open('config.json'))

# We need to create a lights object,
# so we can control it
lights = Relay()

# Set up server, first by connecting to wifi
connect_to_wifi(settings["SSID"], settings["Password"])

@server.route("/lights_on")
def lights_on():
    lights.turn_on()
    return "", 200

@server.route("/lights_off")
def lights_off():
    lights.turn_off()
    return "", 200

@server.route("/ruok")
def ruok():
    return lights.on, 200

server.run(host="0.0.0.0", port=80)
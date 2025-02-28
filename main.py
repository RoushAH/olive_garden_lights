import json
import uasyncio
import time
from phew import connect_to_wifi, server
from machine import ADC, Pin
from relay import Relay

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, contenttype',
    'Content-Type': 'application/json'
}


class LightController:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.settings = self.load_settings()
        self.armed = True
        self.attempt_rearm = None  # Timer to track rearming
        self.lights = Relay(pin=self.settings["Relay_Pin"], mode=self.settings["Relay_Mode"])
        self.reads = []

    def load_settings(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            print("Error loading config.json, using defaults.")
            return {
                "Relay_Pin": 19, "Relay_Mode": 0, "Sensor_Pin": 2,
                "Sense_Count": 10, "Light_Sensitivity": 5000, "Cooldown": 5,
                "Attempt_Rearm": 30, "SSID": "your_wifi", "Password": "your_password"
            }

    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def average_light(self):
        if not self.reads:
            return 0
        count = min(len(self.reads), self.settings["Sense_Count"])
        return sum(self.reads[-count:]) // count

    async def monitor(self):
        sensor = ADC(Pin(self.settings["Sensor_Pin"]))
        cooldown = 0
        while True:
            self.reads.append(sensor.read_u16())
            if len(self.reads) > self.settings["Sense_Count"]:
                self.reads.pop(0)

            current_light = self.average_light()
            if cooldown > 0:
                cooldown -= 1

            if current_light < self.settings["Light_Sensitivity"]:
                if self.lights.on and cooldown == 0 and self.armed:
                    self.lights.turn_off()
                    cooldown = self.settings["Cooldown"]
                elif self.attempt_rearm:
                    self.attempt_rearm -= 1
                    if self.attempt_rearm <= 0:
                        self.armed = True
                        self.attempt_rearm = None
            elif current_light > self.settings["Light_Sensitivity"]:
                if not self.lights.on and cooldown == 0 and not self.attempt_rearm and self.armed:
                    self.lights.turn_on()
                    cooldown = self.settings["Cooldown"]
                elif self.attempt_rearm:
                    self.attempt_rearm = self.settings["Attempt_Rearm"]

            await uasyncio.sleep(1)

    async def run_server(self):
        server.run(host="0.0.0.0", port=80)

    def make_response(self, body, status=200):
        return server.Response(body=json.dumps(body), status=status, headers=HEADERS)

    def setup_routes(self):
        @server.route("/lights_on")
        def lights_on(request=None):
            self.lights.turn_on()
            return self.make_response({"Lights": self.lights.on})

        @server.route("/lights_off")
        def lights_off(request=None):
            self.lights.turn_off()
            self.attempt_rearm = self.settings["Attempt_Rearm"]
            return self.make_response({"Lights": self.lights.on})

        @server.route("/ruok")
        def ruok(request):
            return self.make_response({"Lights": self.lights.on})

        @server.route("/values")
        def values(request):
            out = {"attempt_rearm": self.attempt_rearm or "off", "reads": self.reads}
            return self.make_response(out)

        @server.route("/status")
        def status(request):
            out = self.settings.copy()
            out["Lights"] = self.lights.on
            return self.make_response(out)

        @server.route("/settings_update", methods=["OPTIONS"])
        def settings_options(request):
            return self.make_response("")

        @server.route("/settings_update", methods=["POST"])
        def settings_update(request):
            data = request.data
            if "Lights" in data:
                self.lights.set_state(data["Lights"])
                if not data["Lights"]:
                    self.attempt_rearm = self.settings["Attempt_Rearm"]

            if "Armed" in data:
                self.armed = data["Armed"]
                self.settings["Armed"] = self.armed

            if "Light_Sensitivity" in data:
                self.settings["Light_Sensitivity"] = data["Light_Sensitivity"]

            self.save_settings()
            return self.make_response(self.settings)

        @server.route("/adjust", methods=["OPTIONS"])
        def adjust_options(request):
            return self.make_response("")

        @server.route("/adjust", methods=["GET"])
        def adjust(request):
            param = request.query.get("param")
            value = request.query.get("value")

            if not param or not value:
                return self.make_response(f"Please provide param from {[i for i in self.settings]} and value")

            if param not in self.settings:
                return self.make_response(f"Invalid parameter, not in {[i for i in self.settings]}", status=400)

            try:
                self.settings[param] = int(value) if value.isdigit() else value
                self.save_settings()
                return self.make_response(self.settings)
            except Exception as e:
                return self.make_response({"error": str(e)}, status=500)

        @server.route("/")
        def index(request):
            return server.Response(body="<h1>Hello, World!</h1>", status=200, headers=HEADERS)

        @server.catchall()
        def catchall(request):
            return server.Response(body="You've found the server!", status=404, headers=HEADERS)


    async def main(self):
        self.setup_routes()
        uasyncio.create_task(self.run_server())
        if self.settings["Sensor_Pin"] > 0:
            uasyncio.create_task(self.monitor())
        await uasyncio.sleep(10)  # This is just to make sure that both start before this coro exits


if __name__ == "__main__":
    controller = LightController()
    ip = connect_to_wifi(controller.settings["SSID"], controller.settings["Password"])
    print(f"Connected to WiFi. IP Address: {ip}\nWait 2s for job start", end="")
    for i in range(2):
        time.sleep(1)
        print(".", end="")
    print()
    uasyncio.run(controller.main())

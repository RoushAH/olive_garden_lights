import json


class Setting:
    def __init__(self, name, this_type, maximum=None, minimum=None):
        self.name = name
        self.type = this_type
        self.max = maximum
        self.min = minimum
        self.value = None

    def set_value(self, value):
        if self.type != str:
            try:
                value = self.type(value)
            except ValueError:
                print(f"Value of type {type(value)} is not {self.type}")
                return False
        if self.type in [float, int] and (value < self.min or value > self.max):
            print(f"Value out of range ({self.min}, {self.max})")
            return False
        self.value = value
        return True

    def __str__(self):
        return f"{self.name}: {str(self.value)}"


settings = [
    Setting("SSID", str),
    Setting("Password", str),
    Setting("Latitude", float, 90, -90),
    Setting("Longitude", float, 180, -180),
    Setting("Light_Sensitivity", int, 65535, 0),
    Setting("Relay_Pin", int, 40, 0),
    Setting("Relay_Mode", str),
    Setting("Sensor_Pin", int, 40, 0),
    Setting("Armed", bool),
    Setting("Sense_Count", int, 100, 0),
    Setting("Cooldown", int, 100, 0),
    Setting("Rearm_Timer", int, 60 * 60 * 6, 0)
]

for setting in settings:
    val = input(f"Enter value for {setting.name}: ")
    if not (setting.set_value(val)):
        val = input(f"Enter value for {setting.name}: ")

setting_vals = {x.name: x.value for x in settings}
setting_vals["Lights"] = False
print(json.dumps(setting_vals, indent=3))
with open("config.json", "w") as f:
    json.dump(setting_vals, f, indent=3)

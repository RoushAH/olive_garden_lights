import time
import json
from machine import ADC, Pin, Timer

settings = json.load(open('config.json'))
sensor = ADC(Pin(settings["Sensor_Pin"]))
file = "records.csv"

with open(file, 'w') as csvfile:
    csvfile.write("date, light\n")


def do_job(stime):
    light = sensor.read_u16()
    t = time.localtime(time.time())
    tstring = f"{t[0]}/{t[1]}/{t[2]} {t[3]}:{t[4]}:{t[5]}"
    print(f"{tstring}: \t{light}")

    with open(file, 'a') as c:
        c.write("{},{}\n".format(tstring, light))
    time.sleep(stime)

if __name__ == "__main__":
    print("Welcome to the historiser\nmeasuring time vs light over HISTORY!!!!")
    mins = int(input("How many minutes per cycle? "))

    period = mins * 60
    # period = mins

    print("Starting measurements...")
    do_job(period)
    # tim = Timer(period=period, mode=Timer.PERIODIC, callback=do_job)

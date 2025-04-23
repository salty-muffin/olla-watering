import json
from swimmer_dummy import Swimmer
import time
from machine_dummy import Pin

VALVE_PINS = [9, 8, 7, 6]
SWITCH_PINS = [5, 4, 3, 2]


def check_time_slot() -> bool:
    return True

def main(): 

    # setup
    # Open and read the JSON file
    print("importing settings")
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    
    # initialize sensors
    sensors = [Swimmer(pin) for pin in SWITCH_PINS]
    valves = [Pin(n, Pin.OUT) for n in VALVE_PINS]
    overfill_times = settings["overfill_time_per_valve_seconds"]

    while True:
        # update sensor data
        time_slot_ok = check_time_slot()

        if time_slot_ok:
            print("time slot okay, now starting watering program")
            # check if time its the right time slot to start the program
            for sensor, valve, overfill_time in zip(sensors, valves, overfill_times): 
                print(f"checking swimmer pin {sensor.pin_number}")
                olla_needs_filling = sensor.empty()
                if olla_needs_filling:
                    print("start filling")
                    valve.on()
                    while not sensor.full() and time.time() :

                    time.sleep(overfill_time)
                else:
                    valve.off() # starting 'extra fill time' and closing afterwards

        else:
            for sensor in sensors: 
                sensor.reset()
            for valve in valves: 
                valve.off()
            
            # sleep

                 

if __name__ == "__main__":
    main()



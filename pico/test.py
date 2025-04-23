from machine import Pin, Timer
import time

VALVE_PINS = [9, 8, 7, 6]
SWITCH_PINS = [5, 4, 3, 2]

led = Pin("LED", Pin.OUT)
valves = [Pin(n, Pin.OUT) for n in VALVE_PINS]
switches = [Pin(n, Pin.IN, Pin.PULL_UP) for n in SWITCH_PINS]

tim = Timer(-1)

active_valve = 0


def tick(timer):
    global active_valve, valves

    for index, valve in enumerate(valves):
        if index == active_valve:
            valve.on()
        else:
            valve.off()

    active_valve += 1
    if active_valve > len(valves) - 1:
        active_valve = 0


tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)


while True:
    if any([bool(switch.value()) for switch in switches]):
        led.on()
    else:
        led.off()

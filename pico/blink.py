from machine import Pin, Timer

led = Pin("LED", Pin.OUT)
tim = Timer(-1)


def tick(timer):
    global led
    led.toggle()


tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)

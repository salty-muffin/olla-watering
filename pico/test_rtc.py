from machine import Pin, RTC
import utime

# Initialize onboard LED (GP25)
led = Pin("LED", Pin.OUT)

# Initialize RTC
rtc = RTC()

# Optional: set a known starting time if you want all Picos to start with the same clock
# Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
rtc.datetime((2025, 4, 17, 3, 12, 0, 0, 0))  # Uncomment to sync manually

print("Starting LED blink loop based on RTC...")

while True:
    now = rtc.datetime()
    seconds = now[6]  # Index 6 is 'seconds'

    # LED ON for even seconds, OFF for odd seconds
    led.value(seconds % 2)

    # Sleep a little to avoid spamming the CPU
    utime.sleep_ms(1)

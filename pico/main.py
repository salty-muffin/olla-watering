import json
from swimmer import Swimmer
import time
from machine import Pin, RTC, Timer
import machine

VALVE_PINS = [9, 8, 7, 6]
SWIMMER_PINS = [5, 4, 3, 2]


def main():
    # Underclock the cpu
    machine.freq(48_000_000)
    print(f"CPU runs at {machine.freq()}Hz")

    # Setup
    led = Pin("LED", Pin.OUT)

    # Initialize timer for error blinking
    timer = Timer(-1)

    # Initialize RTC
    rtc = RTC()
    rtc.datetime((2025, 5, 1, 0, 0, 0, 0, 0))
    print(f"Time initialized: {rtc.datetime()}")

    def print_timestamp(*values) -> None:
        print(
            f"[{get_datetime_string(rtc.datetime())}]",
            *values,
        )

    def log_error(error: str, error_file="errors.log"):
        with open(error_file, "a") as file:
            file.write(f"[{get_datetime_string(rtc.datetime())}] {error}\n")

    # Open and read the JSON file
    print("Importing settings")
    try:
        with open("settings.json", "r") as file:
            settings = json.load(file)
        for key, value in settings.items():
            print(f"{key}: {value}")
    except (OSError, ValueError) as e:
        print(f"Error loading settings: {e}")
        log_error(str(e))
        error_blinking(led, timer)

    # Initialize swimmers & valves
    swimmers = [Swimmer(pin) for pin in SWIMMER_PINS]
    valves = [Pin(n, Pin.OUT) for n in VALVE_PINS]

    for valve in valves:
        valve.off()

    # Copy Settings for easier readability
    overfill_times_s = settings["overfill_time_per_valve_seconds"]
    max_fill_time_s = settings["max_fill_time_per_valve_seconds"]
    interval_ms = settings["interval_ms"]
    samples_empty = settings["samples_empty"]
    samples_full = settings["samples_full"]
    time_shift_h = settings["time_shift_hours"]
    time_slot_length_h = settings["time_slot_length_hours"]
    threshold = settings["threshold"]

    try:
        # Fill sensor data one full time
        led.on()
        starting_time = time.ticks_ms()
        full_cycle = interval_ms * max(samples_empty, samples_full)
        print_timestamp(f"Initializing sensor data stack for {full_cycle / 1000}s...")
        while time.ticks_diff(time.ticks_ms(), starting_time) < full_cycle:
            for swimmer in swimmers:
                swimmer.update()
            time.sleep_ms(10)
        led.off()

        # Loop
        sequence_index = len(swimmers)
        filling = False
        overfilling = False
        time_slot = False
        starting_time = time.ticks_ms()
        while True:
            # Start the sequence only at the beginning of the timeslot
            if check_time_slot(time_shift_h, time_slot_length_h, rtc.datetime()):
                if not time_slot:
                    print_timestamp("Time slot is now, starting watering program...")
                    sequence_index = 0
                    time_slot = True
            else:
                if time_slot:
                    time_slot = False

            # Update all swimmers
            updated = any([swimmer.update() for swimmer in swimmers])

            # Fill ollas if in sequence
            if updated and sequence_index < len(swimmers):
                try:
                    if not overfilling:
                        # Fill the current olla if it is empty
                        if not filling and swimmers[sequence_index].empty() < threshold:
                            print_timestamp(
                                f"Olla {sequence_index} is empty, start filling valve at pin {VALVE_PINS[sequence_index]} for max {max_fill_time_s[sequence_index]}s..."
                            )
                            valves[sequence_index].on()
                            filling = True
                            starting_time = time.ticks_ms()
                        # Skip it if it is still full
                        elif (
                            not filling and swimmers[sequence_index].full() >= threshold
                        ):
                            print_timestamp(f"Olla {sequence_index} is full")
                            sequence_index += 1
                        # Stop filling if it has been filled
                        elif filling and swimmers[sequence_index].full() >= threshold:
                            print_timestamp(
                                f"Filled olla {sequence_index} in {time.ticks_diff(time.ticks_ms(), starting_time) / 1000}s"
                            )
                            print_timestamp(
                                f"Now topping off for {overfill_times_s[sequence_index]}s"
                            )
                            filling = False
                            overfilling = True
                            starting_time = time.ticks_ms()
                        # or the maximum fill time has been reached
                        elif (
                            filling
                            and time.ticks_diff(time.ticks_ms(), starting_time) / 1000
                            >= max_fill_time_s[sequence_index]
                        ):
                            print_timestamp(
                                f"Filled olla {sequence_index} for the max fill time of {max_fill_time_s[sequence_index]}s"
                            )
                            valves[sequence_index].off()
                            filling = False
                            log_error(
                                f"Stopped filling olla {sequence_index} due to max fill time"
                            )
                            sequence_index += 1
                            error_blinking(led, timer, blocking=False)

                    # After filling, possibly top it off a bit longer
                    elif (
                        time.ticks_diff(time.ticks_ms(), starting_time) / 1000
                        >= overfill_times_s[sequence_index]
                    ):
                        print_timestamp(
                            f"Topped off olla {sequence_index} in {time.ticks_diff(time.ticks_ms(), starting_time) / 1000}s"
                        )
                        valves[sequence_index].off()
                        overfilling = False
                        sequence_index += 1
                except Exception as e:
                    print_timestamp(f"Error filling ollas: {e}")
                    for valve in valves:
                        valve.off()
                    log_error(str(e))
                    error_blinking(led, timer, blocking=False)

            # Shut all valves if sequence is over as a precaution
            if sequence_index == len(swimmers):
                print_timestamp(
                    "All ollas have been checked and are full, ending watering program for today"
                )
                for valve in valves:
                    valve.off()
                sequence_index += 1

            # Sleep a little bit in every loop to keep the cpu chill
            time.sleep_ms(10)
    except KeyboardInterrupt:
        print("Exiting...")
        for valve in valves:
            valve.off()
        raise SystemExit


def check_time_slot(
    time_shift_hours: float, time_slot_length_hours: float, now: tuple
) -> bool:
    """
    Check if the current time falls within a specified time slot.

    Args:
        time_shift_hours (float): The start hour of the time slot (offset from 0).
        time_slot_length_hours (float): The duration of the time slot in hours.
        now (tuple): A time tuple where the 5th element (index 4) represents the current hour.

    Returns:
        bool: True if the current time is within the time slot, False otherwise.
    """
    return time_shift_hours <= now[4] <= time_slot_length_hours + time_shift_hours


def error_blinking(led: Pin, timer: Timer, blocking=True) -> None:
    """
    Blinks the LED.

    Args:
        blocking (boolean): Should the blinking occur in the background
    """

    def tick(timer):
        led.toggle()

    timer.init(freq=1, mode=Timer.PERIODIC, callback=tick)

    if blocking:
        while True:
            time.sleep(1)


def log_error(error: str, error_file="errors.log"):
    with open(error_file, "a") as file:
        file.write(f"[{time.ticks_ms() / 1000}] {error}\n")


def zfl(s, width):
    # Pads the provided string with leading 0's to suit the specified 'chrs' length
    # Force # characters, fill with leading 0's
    return "{:0>{w}}".format(s, w=width)


def get_datetime_string(dt: tuple) -> str:
    year = zfl(str(dt[0]), 4)
    month = zfl(str(dt[1]), 2)
    day = zfl(str(dt[2]), 2)
    hour = zfl(str(dt[4]), 2)
    minute = zfl(str(dt[5]), 2)
    second = zfl(str(dt[6]), 2)

    return f"{year}/{month}/{day} {hour}:{minute}:{second}"


if __name__ == "__main__":
    main()

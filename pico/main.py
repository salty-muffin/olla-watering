import json
from swimmer import Swimmer
import time
from machine import Pin, RTC

VALVE_PINS = [9, 8, 7, 6]
SWIMMER_PINS = [5, 4, 3, 2]


def check_time_slot(
    time_shift_hours: float, time_slot_length_hours: float, now: tuple
) -> bool:
    return time_shift_hours <= now[4] <= time_slot_length_hours + time_shift_hours


def error_blinking(led: Pin, duration_s=-1) -> None:
    """
    Blinks the LED in an error pattern (0.1s on, 2s off) for a specified duration.

    Args:
        duration_s (float, optional): Duration in seconds to blink the LED.
            If negative (default: -1), the function will blink indefinitely.

    Returns:
        None

    Note:
        This function blocks execution until the duration is complete or indefinitely
        if duration_s is negative.
    """
    starting_time = time.ticks_ms()
    while (
        duration_s < 0
        or time.ticks_diff(time.ticks_ms(), starting_time) / 1000 > duration_s
    ):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(2)


def main():
    led = Pin("LED", Pin.OUT)

    # Open and read the JSON file
    print("Importing settings")
    try:
        with open("settings.json", "r") as file:
            settings = json.load(file)
        print(settings)
    except (OSError, ValueError) as e:
        print(f"Error loading settings: {e}")
        error_blinking(led)

    # Initialize swimmers
    swimmers = [Swimmer(pin) for pin in SWIMMER_PINS]
    valves = [Pin(n, Pin.OUT) for n in VALVE_PINS]
    overfill_times = settings["overfill_time_per_valve_seconds"]
    max_fill_time = settings["max_fill_time_per_valve_minutes"]

    # Initialize RTC
    rtc = RTC()
    rtc.datetime((2025, 5, 1, 0, 0, 0, 0, 0))

    # Fill sensor data one full time
    starting_time = time.ticks_ms()
    print("Initializing sensor data stack...")
    while time.ticks_diff(time.ticks_ms(), starting_time) < settings[
        "interval_ms"
    ] * max(settings["samples_empty"], settings["samples_full"]):
        for swimmer in swimmers:
            swimmer.update()
        time.sleep_ms(1)

    completed_fill = False
    while True:
        # Update swimmer data
        for swimmer in swimmers:
            swimmer.update()

        if (
            check_time_slot(
                settings["time_shift_hours"],
                settings["time_slot_length_hours"],
                rtc.datetime(),
            )
            and not completed_fill
        ):
            print(
                f"Check valid: {settings['time_shift_hours']} <= {rtc.datetime()} <= {settings['time_shift_hours'] + settings['time_slot_length_hours']}"
            )
            try:
                print("Time slot okay, now starting watering program...")

                # Check if its the right time slot to start the program
                for (
                    swimmer,
                    valve,
                    overfill_time,
                    max_fill_time,
                    swimmer_pin,
                    valve_pin,
                ) in zip(
                    swimmers,
                    valves,
                    overfill_times,
                    max_fill_time,
                    SWIMMER_PINS,
                    VALVE_PINS,
                ):
                    print(f"Checking swimmer at pin {swimmer_pin}")

                    empty, mean = swimmer.empty()
                    print(
                        f"Swimmer mean: {mean:.2f}, state: {'empty' if empty else 'full'}"
                    )
                    if empty:
                        print(
                            f"Is empty, start filling valve {valve_pin} for max {max_fill_time}min..."
                        )

                        valve.on()

                        # Wait until olla is full or over max filling time
                        starting_time = time.ticks_ms()
                        swimmer_state = swimmer.full()
                        # --- DEBUG
                        print(
                            swimmer_state[1],
                            not swimmer_state[0],
                            time.ticks_diff(time.ticks_ms(), starting_time)
                            / (1000 * 60)
                            < max_fill_time,
                            (
                                not swimmer.full()[0]
                                and time.ticks_diff(time.ticks_ms(), starting_time)
                                / (1000 * 60)
                                < max_fill_time
                            ),
                            time.ticks_diff(time.ticks_ms(), starting_time),
                            time.ticks_diff(time.ticks_ms(), starting_time)
                            / (1000 * 60),
                            max_fill_time,
                        )
                        # --- DEBUG
                        while not swimmer.full()[0] and (
                            time.ticks_diff(time.ticks_ms(), starting_time)
                            / (1000 * 60)
                            < max_fill_time
                        ):  # TODO: Fix conditional statement in this loop?
                            for swimmer in swimmers:
                                swimmer.update()
                            time.sleep_ms(1)

                        print(
                            f"Filled in {time.ticks_diff(time.ticks_ms(), starting_time) / (1000 * 60):.2f}min"
                        )

                        print(f"Starting overfill for {overfill_time}s")
                        # Starting extra fill time
                        starting_time = time.ticks_ms()
                        while (
                            time.ticks_diff(time.ticks_ms(), starting_time) / 1000
                            < overfill_time
                        ):
                            for swimmer in swimmers:
                                swimmer.update()
                            time.sleep_ms(1)

                        print("Closing valve")
                        # Close valve
                        valve.off()

                    completed_fill = True
            except Exception as e:
                print(f"Error filling ollas: {e}")
                error_blinking(led, 30)

        elif not check_time_slot(
            settings["time_shift_hours"],
            settings["time_slot_length_hours"],
            rtc.datetime(),
        ):
            print(
                f"Check invalid: {settings['time_shift_hours']} <= {rtc.datetime()} <= {settings['time_shift_hours'] + settings['time_slot_length_hours']}"
            )
            completed_fill = False

        for valve in valves:
            valve.off()

        time.sleep_ms(100)


if __name__ == "__main__":
    main()

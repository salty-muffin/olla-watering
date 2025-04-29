from machine import Pin
import time


def mean(l: list[float]) -> float:
    return sum(l) / len(l)


class Swimmer:
    """
    A class for water level detection using a floating sensor connected to a GPIO pin.

    The Swimmer monitors water levels by sampling a sensor at regular intervals.

    Attributes:
        pin_number (int): GPIO pin number where the sensor is connected
        interval_ms (int): Sampling interval in milliseconds
        samples_empty (int): Number of samples to consider when checking if empty
        samples_full (int): Number of samples to consider when checking if full
    """

    def __init__(
        self,
        pin_number: int,
        interval_ms=100,
        samples_empty=200,
        samples_full=20,
    ) -> None:
        self._pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self._interval = interval_ms
        self._samples_empty = samples_empty
        self._samples_full = samples_full

        # Initialize sample buffer with zeros
        self._samples = [0.0] * max(self._samples_empty, self._samples_full)
        self._last_sample_time = time.ticks_ms()
        self._average = 0.0

    def update(self) -> bool:
        """
        Take a new sensor reading if the sampling interval has elapsed.

        This method should be called frequently in the main loop.

        Returns:
            bool: True if a new sample was taken, False otherwise
        """
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self._last_sample_time) >= self._interval:
            # Remove oldest sample
            self._samples.pop(0)

            # Add new sample (sensor reading)
            self._samples.append(float(self._pin.value()))

            return True
        return False

    def empty(self) -> float:
        """
        Return the mean of the samples to check if the container is empty.

        Returns:
            float: mean of recent samples considered to check if empty
        """
        return mean(self._samples[-self._samples_empty : -1])

    def full(self) -> float:
        """
        Return the mean of the samples to check if the container is full.

        Returns:
            float: mean of recent samples considered to check if full
        """
        return mean(self._samples[-self._samples_full : -1])

    def reset(self) -> None:
        """
        Reset the state of the sensor.

        Returns:
            None
        """
        self._samples = [0.0] * max(self._samples_empty, self._samples_full)

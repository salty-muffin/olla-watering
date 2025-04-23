import time
import statistics


class Swimmer:
    """
    A class for water level detection using a floating sensor connected to a GPIO pin.

    The Swimmer monitors water levels by sampling a sensor at regular intervals and
    using statistical analysis to determine if a container is empty or full.

    Attributes:
        pin_number (int): GPIO pin number where the sensor is connected
        interval_ms (int): Sampling interval in milliseconds
        samples_empty (int): Number of samples to consider when checking if empty
        samples_full (int): Number of samples to consider when checking if full
        threshold_empty (float): Threshold below which the container is considered empty (0.0-1.0)
        threshold_full (float): Threshold above which the container is considered full (0.0-1.0)
    """

    def __init__(
        self,
        pin_number: int,
        interval_ms=100,
        samples_empty=200,
        samples_full=20,
        threshold_empty=0.1,
        threshold_full=0.9,
    ) -> None:
        self._interval = interval_ms
        self._samples_empty = samples_empty
        self._samples_full = samples_full
        self._threshold_empty = threshold_empty
        self._threshold_full = threshold_full

        # Initialize sample buffer with zeros
        self._samples = [0.0] * max(self._samples_empty, self._samples_full)
        self._last_sample_time = int(time.time() * 1000)
        self._average = 0.0

    def update(self) -> bool:
        """
        Take a new sensor reading if the sampling interval has elapsed.

        This method should be called frequently in the main loop.

        Returns:
            bool: True if a new sample was taken, False otherwise
        """
        current_time = int(time.time() * 1000)
        if current_time - self._last_sample_time >= self._interval:
            # Remove oldest sample
            self._samples.pop(0)

            # Add new sample (sensor reading)
            self._samples.append(0.0)

            return True
        return False

    def empty(self) -> tuple[bool, float]:
        """
        Check if the container is empty based on recent sensor readings.

        Returns:
            float: True if the mean of recent samples is below or equal to empty threshold
        """
        mean = statistics.fmean(self._samples[-self._samples_empty : -1])
        return (mean <= self._threshold_empty, mean)

    def full(self) -> tuple[bool, float]:
        """
        Check if the container is full based on recent sensor readings.

        Returns:
            float: True if the mean of recent samples is above or equal to full threshold
        """
        mean = statistics.fmean(self._samples[-self._samples_full : -1])
        return (mean >= self._threshold_full, mean)

    def reset(self) -> None:
        """
        Reset the state of the sensor.

        Returns:
            None
        """
        self._samples = [0.0] * max(self._samples_empty, self._samples_full)

from abc import ABC, abstractmethod
import hid
from typing import Iterable, Sequence


class BaseWheel(ABC):
    """Abstract Logitech wheel.

Sub-classes must provide:
VENDOR_ID:  int
PRODUCT_IDS: Iterable[int]
_led_report(bits: int) -> Sequence[int]
    """
    VENDOR_ID: int = 0x046d          # Logitech
    PRODUCT_IDS: Iterable[int] = ()

    def __init__(self) -> None:
        self._dev: hid.Device | None = None
        self._last_bits: int = -1    # cache to avoid spamming
        self._min_percent: float = 4.0
        self._max_percent: float = 84.0

    def connect(self) -> bool:
        for pid in self.PRODUCT_IDS:
            try:
                self._dev = hid.Device(self.VENDOR_ID, pid)
                self._post_connect_setup()
                return True
            except hid.HIDException:
                continue
        return False

    def leds_rpm(self, percent: float) -> None:
        bits = self._percent_to_bits(percent)
        if bits == self._last_bits or self._dev is None:
            return
        self._last_bits = bits
        self._dev.write(bytes(self._led_report(bits)))

    def set_percent_limits(self, minpercent: float, maxpercent:float) -> None:
        self._min_percent = minpercent
        self._max_percent = maxpercent

    def _post_connect_setup(self) -> None:
        pass

    @abstractmethod
    def _led_report(self, bits: int) -> Sequence[int]: ...

    # ---------- helpers ----------

    def _percent_to_bits(self, pct: float) -> int:
        return (
            0b11111 if pct > self._max_percent
            else 0b01111 if pct > self._min_percent + 3.0 *((self._max_percent - self._min_percent) / 4.0)
            else 0b00111 if pct > self._min_percent + 2.0 * ((self._max_percent - self._min_percent) / 4.0)
            else 0b00011 if pct > self._min_percent + ((self._max_percent - self._min_percent) / 4.0)
            else 0b00001 if pct > self._min_percent
            else 0
        )

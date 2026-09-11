import time
import logging
import usb

from display import USBDisplay
from monitor import MetricsMonitor

UPDATE_INTERVAL = 1

class DisplayController:
    """Orchestrates the monitor and the display."""

    def __init__(self, use_watts, use_fahrenheit, update_interval = UPDATE_INTERVAL):
        self.display = USBDisplay()
        self.monitor = MetricsMonitor(update_interval, use_watts)
        self.use_fahrenheit = use_fahrenheit
        self.update_interval = update_interval
        self.flag_byte = self._calc_flags(use_watts, use_fahrenheit)

    def _calc_flags(self, use_watts, use_fahrenheit):
        flag = 0b00000000
        if not use_watts: flag |= 0b00010000
        if use_fahrenheit: flag |= 0b00000001
        return flag

    def run(self):
        while True:
            try:
                if not self.display.connect():
                    time.sleep(5); continue

                while True:
                    temp = self.monitor.get_temp()
                    if self.use_fahrenheit: temp = (temp * 9/5) + 32

                    load = self.monitor.get_load()
                    self._update_ui(int(temp), int(load))
                    time.sleep(self.update_interval)

            except KeyboardInterrupt:
                logging.debug("Program shutting down (signal received).")
                self.display.close()
                break

            except usb.core.USBError as e:
                # Real USB failure
                logging.error(f"Device error: {e}. Reconnecting in 5s...")
                self.display.close()
                time.sleep(5)

            except Exception as e:
                # Non-USB error
                logging.error(f"Unexpected error: {e}")
                time.sleep(1)

    def _update_ui(self, temp, load):
        temp_limit = max(0, min(temp, 99))
        t_tens, t_unit = divmod(temp_limit, 10)

        load_limit = max(0, min(load, 999))
        l_hundreds, remainder = divmod(load_limit, 100)
        l_tens, l_unit = divmod(remainder, 10)
        
        report = [0x07, 0x00, t_tens, t_unit, self.flag_byte, l_hundreds, l_tens, l_unit] + [0x00] * 56
        self.display.send_report(report)
        
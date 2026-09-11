import logging
import os
import psutil
import time
import threading

CPU_WATTS_FILE = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"

class MetricsMonitor:
    """Handles data collection (CPU Temp, Load/Watts)."""

    def __init__(self, update_interval, use_watts=False, rapl_file=CPU_WATTS_FILE):
        self.use_watts = use_watts
        self.rapl_file = rapl_file
        self.update_interval = update_interval
        self.current_watts = 0
        
        if self.use_watts and os.path.exists(self.rapl_file):
            threading.Thread(
                target=self._watts_worker, 
                daemon=True
            ).start()


    def _watts_worker(self):
        error_count = 0
        MAX_ERRORS = 3

        while error_count <= MAX_ERRORS:
            try:
                with open(self.rapl_file, "r") as f:
                    t0 = int(f.read())

                start_time = time.time()

                # Wait for the defined interval
                time.sleep(self.update_interval)

                with open(self.rapl_file, "r") as f:
                    t1 = int(f.read())

                end_time = time.time()
                elapsed_time = end_time - start_time

                # (t1 - t0) is in microJoules. 
                # Divide by 1,000,000 to get Joules.
                # Divide by elapsed_time to get Watts (Joules per second).
                energy_joules = (t1 - t0) / 1_000_000
                self.current_watts = int(energy_joules / elapsed_time)

                error_count = 0

            except (FileNotFoundError, PermissionError, ValueError, OSError):
                self.current_watts = 0
                error_count += 1
                logging.error("Failed to read RAPL sensor")
                time.sleep(5)
        
        logging.error("RAPL sensor permanently unreachable. Stopping monitor.")


    def get_temp(self):
        temps = psutil.sensors_temperatures()
        coretemp = temps.get('coretemp')

        if coretemp:
            return int(coretemp[0].current)
        
        return 35


    def get_load(self):
        return self.current_watts if self.use_watts else int(psutil.cpu_percent())

import logging
import signal
import sys

from controller import DisplayController

def signal_handler(signum, frame):
    """Converts system stop signals (SIGTERM) into KeyboardInterrupt."""
    raise KeyboardInterrupt

# Register the signal handler during script initialization
signal.signal(signal.SIGTERM, signal_handler)

# Logging configuration: Only errors will be registered
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    # Initialize the controller that orchestrates everything
    app = DisplayController(use_watts=False, use_fahrenheit=False)
    app.run()

if __name__ == "__main__":
    main()
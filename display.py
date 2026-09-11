import usb.core
import usb.util
import logging
import time

class USBDisplay:
    """Handles the communication with the hardware display."""

    VENDOR_ID = 0x1a2c
    PRODUCT_ID = 0x4984
    ENDPOINT_VAL = 0x0307
    USB_TYPE_HOST_TO_DEVICE = 0x21
    USB_REQ_SET_REPORT = 0x09

    def __init__(self, heartbeat_interval=3.0):
        self.device = None
        self._last_sent_data = None
        self._last_send_time = 0.0
        self._heartbeat_interval = heartbeat_interval

    def connect(self):
        """Initializes USB connection and detaches kernel drivers."""
        self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
        if self.device is None:
            return False
        
        for i in range(2):
            try:
                if self.device.is_kernel_driver_active(i):
                    self.device.detach_kernel_driver(i)
            except usb.core.USBError as e:
                logging.error(f"Could not detach interface {i}: {e}")

        # Initialize the buffer and the timer
        self._last_sent_data = [0x00] * 64
        self._last_send_time = time.time()
        
        # Send initial configuration
        try:
            self.send_report([0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] + [0x00] * 56, force=True)
        except usb.core.USBError as e:
            logging.error(f"Initial handshake failed: {e}")
            self.close()
            return False
        
        return True

    def send_report(self, data, force=False):
        """Sends data to the display only if it has changed or heartbeat interval exceeded."""
        if not self.device:
            return
        
        current_time = time.time()
        time_since_last_send = current_time - self._last_send_time
        
        # Check if we need to send a heartbeat to keep the display active
        needs_heartbeat = time_since_last_send >= self._heartbeat_interval
        
        # Skip sending if data is identical and no heartbeat is needed
        if not force and not needs_heartbeat and self._last_sent_data == data:
            return

        try:
            self.device.ctrl_transfer(
                self.USB_TYPE_HOST_TO_DEVICE, 
                self.USB_REQ_SET_REPORT,
                self.ENDPOINT_VAL, 
                1, 
                data
            )
            # Update cache and timestamp using slice assignment to maintain object reference
            self._last_sent_data[:] = data
            self._last_send_time = current_time
            
        except usb.core.USBError as e:
            logging.error(f"Failed to send report: {e}")
            raise

    def close(self):
        """Releases USB resources."""
        if self.device:
            usb.util.dispose_resources(self.device)
            self.device = None
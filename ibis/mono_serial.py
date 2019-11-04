import serial

from .mono_protocol import MONOProtocol

class SerialMONOMaster(MONOProtocol):
    """
    A MONO bus master, sending and receiving frames using a serial port
    """
    
    def __init__(self, port, baudrate = 19200, bytesize = 8, parity = 'N',
                 stopbits = 1, timeout = 2.0, *args, **kwargs):
        """
        port:
        The serial port to use for communication
        """
        
        super().__init__(*args, **kwargs)
        
        self.port = port
        self.device = serial.Serial(
            self.port,
            baudrate = baudrate,
            bytesize = bytesize,
            parity = parity,
            stopbits = stopbits,
            timeout = timeout
        )
    
    def _send(self, frame):
        """
        Actually send the frame.
        This varies depending on implementation
        """
        
        self.device.write(frame)
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        
        return self.device.read(length)

    def __del__(self):
        self.device.close()

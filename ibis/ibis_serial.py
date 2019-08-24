import serial

from .ibis_protocol import IBISProtocol

class SerialIBISMaster(IBISProtocol):
    """
    An IBIS bus master, sending and receiving telegrams using a serial port
    """
    
    def __init__(self, port, baudrate = 1200, bytesize = 7, parity = 'E',
                 stopbits = 2, timeout = 2.0, *args, **kwargs):
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
    
    def _send(self, telegram):
        """
        Actually send the telegram.
        This varies depending on implementation
        """
        
        self.device.write(telegram)
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        
        return self.device.read(length)

    def __del__(self):
        self.device.close()

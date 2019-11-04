import socket

from .ibis_protocol import IBISProtocol

class TCPIBISMaster(IBISProtocol):
    """
    An IBIS master using TCP instead of serial
    """
    
    def __init__(self, host, port, timeout = 2.0, *args, **kwargs):
        """
        host:
        The hostname or IP to connect to
        
        port:
        The TCP port to use for communication
        
        timeout:
        The socket timeout in seconds
        """
        
        super().__init__(*args, **kwargs)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.socket.settimeout(timeout)
    
    def _send(self, telegram):
        """
        Actually send the telegram.
        This varies depending on implementation
        """
        
        self.socket.send(telegram)
    
    def _receive(self, length):
        """
        Actually receive data.
        This varies depending on implementation and needs to be overridden
        """
        
        return self.socket.recv(length)

    def __del__(self):
        self.socket.close()
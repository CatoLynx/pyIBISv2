"""
Main protocol library
"""

import math
import serial

class IBISMaster:
    """
    An IBIS bus master, sending and receiving telegrams.
    """
    
    def __init__(self, port, debug = False):
        """
        port:
        The serial port to use for communication
        
        debug:
        Whether to print the sent and received telegrams
        """
        
        self.port = port
        self.debug = debug
        self.device = serial.Serial(
            self.port,
            baudrate = 1200,
            bytesize = serial.SEVENBITS,
            parity = serial.PARITY_EVEN,
            stopbits = serial.STOPBITS_TWO,
            timeout = 2.0
        )
        
        # Simple telegram definitions
        self.DS001 = self._tg("l{:03d}")        # Line number, 1-4 digits
        self.DS001neu = self._tg("q{:0>4}")     # Line number, alphanumeric, 1-4 chars
        self.DS001a = self._tg("qE{:02d}")      # Line number symbol ID, 1-2 digit
        self.DS001b = self._tg("lF{:05d}")      # Radio
        self.DS001c = self._tg("lP{:03d}")      # Line tape reel position ID, 1-3 digit
        self.DS001d = self._tg("lC{:0>4}")      # Line number, alphanumeric, 1-4 chars
        self.DS001e = self._tg("lC{:0>8}")      # Line number, alphanumeric, 1-8 chars
        self.DS001f = self._tg("lB{:0>7}")      # Line number, alphanumeric, 1-7 chars
        self.DS002 = self._tg("k{:02d}")        # Course number, 1-2 digits
        self.DS002a = self._tg("k{:05d}")       # Train number, 1-5 digits
        self.DS003 = self._tg("z{:03d}")        # Destination text ID, 1-3 digit
        self.DS003b = self._tg("zR{:03d}")      # Destination ID for IMU, 1-3 digits
        self.DS003d = self._tg("zN{:03d}")      # Route number, 1-3 digits
        self.DS003e = self._tg("zP{:03d}")      # Destination tape reel position ID, 1-3 digit
        self.DS003f = self._tg("zN{:06d}")      # Route number, 1-6 digits
        self.DS003g = self._tg("zL{:04d}")      # Line number, 1-4 digits
        self.DS004 = self._tg("e{:06d}")        # Ticket validator attributes, 6 digits
        self.DS004a = self._tg("eA{:04d}")      # Additional ticket validator attributes, 4 digits
        self.DS004b = self._tg("eH{:07d}")      # Ticket validator stop number, 1-7 digits
        self.DS005 = self._tg("u{:04d}")        # Time, HHMM
        self.DS006 = self._tg("d{:05d}")        # Date, DDMMY
        self.DS007 = self._tg("w{:01d}")        # Train length, 1 digit
        self.DS009 = self._tg("v{: <16}")       # Next stop text, 16 characters
        self.DS009a = self._tg("v{: <20}")      # Next stop text, 20 characters
        self.DS009b = self._tg("v{: <24}")      # Next stop text, 24 characters
        self.DS010 = self._tg("x{:04d}")        # Line progress display stop ID, 1-4 digits
        self.DS010a = self._tg("xH{:04d}")      # Line progress display stop ID, 1-4 digits
        self.DS010b = self._tg("xI{:02d}")      # Line progress display stop ID, 1-2 digits
        self.DS010d = self._tg("xJ{:04d}")      # Year, YYYY
        self.DS010e = self._tg("xV{}{:03d}")    # Delay, +/-, 1-3 digits
    
    def debug_telegram(self, telegram, receive = False):
        """
        Print a telegram to standard output if the debug flag is set.
        
        telegram:
        The telegram to print
        
        receive:
        Whether to print the telegram as sent or received
        """
        
        if self.debug:
            action = "Received" if receive else "Sending"
            telegram_hex = " ".join("{:02X}".format(byte) for byte in telegram)
            telegram_ascii = "  ".join(chr(byte) for byte in telegram[:-2])
            print("{} telegram:\n{}\n{}\n"
                .format(action, telegram_ascii, telegram_hex))
    
    def process_special_characters(self, telegram):
        """
        Replace IBIS special characters and strip unsupported characters.
        
        telegram:
        The telegram as a string
        
        Returns:
        The processed telegram
        """
        
        telegram = telegram.replace("ä", "{")
        telegram = telegram.replace("ö", "|")
        telegram = telegram.replace("ü", "}")
        telegram = telegram.replace("ß", "~")
        telegram = telegram.replace("Ä", "[")
        telegram = telegram.replace("Ö", "\\")
        telegram = telegram.replace("Ü", "]")
        telegram = telegram.encode('ascii', errors = 'replace')
        return telegram
    
    def wrap_telegram(self, telegram):
        """
        Append the checksum and the end byte to the given telegram.
        
        telegram:
        The telegram (as a bytearray) to wrap
        
        Returns:
        The wrapped telegram (as a bytearray)
        """
        
        telegram.append(0x0D)
        checksum = 0x7F
        for byte in telegram:
            checksum ^= byte
        telegram.append(checksum)
        return telegram
    
    def send_telegram(self, telegram, reply_length = 0):
        """
        Send an arbitrary telegram. Checksum and end byte will be added.
        
        telegram:
        The telegram to send
        
        reply_length:
        How many bytes to expect as a reply
        
        Returns:
        The received telegram OR None
        """
        
        if type(telegram) is str:
            telegram = self.process_special_characters(telegram)
            telegram = bytearray(telegram)
        elif type(telegram) is bytes:
            telegram = bytearray(telegram)
        
        telegram = self.wrap_telegram(telegram)
        self.debug_telegram(telegram)
        self.device.write(telegram)
        if reply_length:
            reply = self.device.read(reply_length + 2)
            self.debug_telegram(reply, receive = True)
            reply = reply[:-2]
            return reply.decode('latin1')
    
    def vdv_hex(self, value):
        """
        Convert a numerical value into the VDV hexadecimal representation
        
        value:
        The value to convert (0 to 15) OR a VDV Hex value to convert back
        
        Returns:
        The VDV Hex value OR the integer for the VDV Hex value
        """
        
        vdvhex = "0123456789:;<=>?"
        if type(value) is int:
            return vdvhex[value]
        else:
            return vdvhex.index(value)
    
    def _tg(self, fmt, reply_length = 0):
        """
        Wrapper for simple telegrams with just variables
        
        fmt:
        The format string for the telegram
        
        reply_length:
        As in send_telegram
        """
        
        def _send(*args):
            return self.send_telegram(fmt.format(*args),
                reply_length = reply_length)
        
        return _send
    
    def DS003a(self, text):
        """
        Destination text
        
        text:
        The destination text
        """
        
        num_blocks = math.ceil(len(text) / 16)
        return self.send_telegram("zA{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*16)))
    
    def DS003c(self, text):
        """
        Next stop text
        
        text:
        The next stop text
        """
        
        num_blocks = math.ceil(len(text) / 4)
        return self.send_telegram("zI{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*4)))
    
    def DS004c(self, text):
        """
        Stop text for ticket validators / ticket vending machines
        
        text:
        The stop text
        """
        
        num_blocks = math.ceil(len(text) / 4)
        return self.send_telegram("eT{}{}"
            .format(self.vdv_hex(num_blocks), text.ljust(num_blocks*4)))
    
    def DS010c(self, stop_id):
        """
        Next stop ID for line progress display
        
        stop_id:
        The ID of the next stop, 1-2 digits
        """
        
        stop_id_high_nibble = stop_id >> 4
        stop_id_low_nibble = stop_id & 0x0F
        return self.send_telegram("xZ{}{}"
            .format(self.vdv_hex(stop_id_high_nibble),
                self.vdv_hex(stop_id_low_nibble)))
    
    def DS010f(self, stop_id, change_text):
        """
        Connection information for line progress display
        
        stop_id:
        The ID of the next stop, 1-2 digits
        
        change_text:
        Connection information
        """
        
        stop_id_high_nibble = stop_id >> 4
        stop_id_low_nibble = stop_id & 0x0F
        length_high_nibble = len(change_text) >> 4
        length_low_nibble = len(change_text) & 0x0F
        return self.send_telegram("xU{}{}{}{}{}"
            .format(self.vdv_hex(stop_id_high_nibble),
                self.vdv_hex(stop_id_low_nibble),
                self.vdv_hex(length_high_nibble),
                self.vdv_hex(length_low_nibble),
                change_text))
    
    def DS020(self, address):
        """
        Display status query
        Reply: DS120
        
        address:
        The address of the display
        """
        
        return self.parse_DS120(self.send_telegram("a{}"
            .format(self.vdv_hex(address)), reply_length = 2))
    
    def parse_DS120(self, telegram):
        if not telegram:
            return None
        status = telegram[1]
        statuses = {
            '0': 'ok',
            '1': 'displaying',
            '2': 'searching',
            '3': 'error',
            '6': 'input_implausible'
        }
        reply = {
            'status': statuses.get(status, status)
        }
        return reply
    
    def DS201(self, address):
        """
        Display version query
        Reply: DS1201
        
        address:
        The address of the display
        """
        
        return self.parse_DS1201(self.send_telegram("aV{}"
            .format(self.vdv_hex(address)), reply_length = 8))
    
    def parse_DS1201(self, telegram):
        if not telegram:
            return None
        version = telegram[2:]
        reply = {
            'version': version
        }
        return reply
    
    def DS021(self, address, text):
        """
        Destination text
        
        address:
        The address of the display
        
        text:
        The destination text
        """
        
        num_blocks = math.ceil(len(text) / 16)
        return self.send_telegram("aA{}{}{}"
            .format(self.vdv_hex(address),
                self.vdv_hex(num_blocks),
                text.ljust(num_blocks*16)))
    
    def DS021a(self, address, stop_id, stop_text, change_text):
        """
        Line progress display texts
        
        address:
        The address of the display
        
        stop_id:
        The ID of the stop to send data for
        
        stop_text:
        The name of the stop
        
        change_text:
        Connection information
        """
        
        data = "\x03{:02d}\x04{}\x05{}".format(
            stop_id, stop_text, change_text)
        num_blocks, remainder = divmod(len(data), 16)
        return self.send_telegram("aL{}{}{}{}"
            .format(self.vdv_hex(address),
                self.vdv_hex(num_blocks),
                self.vdv_hex(remainder),
                data))
    
    def DS060(self, direction):
        """
        Query locating device status
        Reply: DS160
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS160(self.send_telegram("o{}S"
            .format(direction), reply_length = 3))
    
    def parse_DS160(self, telegram):
        if not telegram:
            return None
        status = telegram[2]
        statuses = {
            '0': 'ok_no_information',
            '1': 'information_read',
            '2': 'new_information'
        }
        reply = {
            'status': statuses.get(status, status)
        }
        return reply
    
    def DS601(self, direction):
        """
        Query locating device version
        Reply: DS1601
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS1201(self.send_telegram("o{}V"
            .format(direction), reply_length = 18))
    
    def parse_DS1601(self, telegram):
        if not telegram:
            return None
        version = int(telegram[2:])
        reply = {
            'version': version
        }
        return reply
    
    def DS061(self, direction):
        """
        Query locating device data
        Reply: DS161
        
        direction:
        Either A, B or C
        """
        
        return self.parse_DS161(self.send_telegram("o{}D"
            .format(direction), reply_length = 10))
    
    def parse_DS161(self, telegram):
        if not telegram:
            return None
        beacon_id_vdvhex = telegram[2:]
        beacon_id = 0x00
        for n in range(8):
            char = beacon_id_vdvhex[n]
            beacon_id |= self.vdv_hex(char) << ((7 - n) * 4)
        reply = {
            'beacon_id': beacon_id
        }
        return reply
    
    def DS068(self, channel, radio_telegram_type, delay, reporting_point_id, hand, line_number, course_number, destination_id, train_length):
        """
        Send an LSA radio telegram
        """
        
        radio_telegram = "{}{}{:02d}{}{}{:0>4}{}{:03d}{:02d}{:03d}{}".format(
            self.vdv_hex(channel),
            self.vdv_hex(0),
            radio_telegram_type,
            self.vdv_hex(delay),
            self.vdv_hex(6), # Number of extra bytes
            reporting_point_id,
            self.vdv_hex(hand),
            line_number,
            course_number,
            destination_id,
            self.vdv_hex(train_length)
        )
        return self.parse_DS160(self.send_telegram("oFM{}{}"
            .format(self.vdv_hex(math.ceil(len(radio_telegram) / 2)),
                radio_telegram), reply_length = 3))

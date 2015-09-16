# coding=utf-8

"""


"""

import os
import sys
import socket
import zlib, base64

from handler import Handler


class AutmonHandler(Handler):
    """
    Implements the abstract Handler class, sending data to graphite
    """

    def __init__(self, config=None):
        """
        Create a new instance of the AutmonHandler class
        """
        # Initialize Handler
        Handler.__init__(self, config)

        # Initialize Data
        self.socket = None

        # Initialize Options
        self.proto = self.config.get('proto', 'tcp').lower().strip()
        if self.config.get('compress', 'False').strip() == 'True':
            self.compress = True
        else:
            self.compress = False

        try:
            self.host = (self.config['host'][0], int(self.config['host'][1]))
        except Exception, e:
            self.log.error("AutmonHandler: Host parameter is invaild. %s", e)

        if "standby" in self.config:
            try:
                self.standby = (self.config['standby'][0], int(self.config['standby'][1]))
            except Exception, e:
                self.log.error("AutmonHandler: Standby parameter is invaild. %s", e)

        self.timeout = int(self.config.get('timeout', 15))
        self.batch_size = int(self.config.get('batch', 5))
        self.max_backlog_multiplier = int(
            self.config.get('max_backlog_multiplier', 5))
        self.trim_backlog_multiplier = int(
            self.config.get('trim_backlog_multiplier', 4))
        self.metrics = []

        # Connect
        self._connect()

    def __del__(self):
        """
        Destroy instance of the AutmonHandler class
        """
        self._close()

    def process(self, metric):
        """
        Process a metric by sending it to graphite
        """
        # Append the data to the array as a string
        self.metrics.append(str(metric))
        if len(self.metrics) >= self.batch_size:
            self._send()

    def flush(self):
        """Flush metrics in queue"""
        self._send()
        
    def _compress_data(self, data):
        try:
            compressed = zlib.compress(data, 9)
        except Exception as e:
            self.log.debug("AutmonHandler: zlib compress error. " + e)
            raise

        try:
            encoded = base64.b64encode(compressed)
        except Exception as e:
            self.log.debug("AutmonHandler: b64encode error. " + e)
            raise

        return encoded

    def _send_data(self, data):
        """
        Try to send all data in buffer.
        """
        if self.compress:
            self.socket.sendall(self._compress_data(data))
        else:
            self.socket.sendall(data)

    def _send(self):
        """
        Send data to graphite. Data that can not be sent will be queued.
        """
        # Check to see if we have a valid socket. If not, try to connect.
        try:
            try:
                if self.socket is None:
                    self.log.debug("AutmonHandler: Socket is not connected. "
                                   "Reconnecting.")
                    self._connect()
                if self.socket is None:
                    self.log.debug("AutmonHandler: Reconnect failed.")
                else:
                    # Send data to socket
                    self._send_data('<EOF>'.join(self.metrics) + '<EOF>')
                    self.metrics = []
            except Exception:
                self._close()
                self.log.error("AutmonHandler: Error sending metrics.")
                raise
        finally:
            if len(self.metrics) >= (
                self.batch_size * self.max_backlog_multiplier):
                trim_offset = (self.batch_size
                               * self.trim_backlog_multiplier * -1)
                self.log.warn('AutmonHandler: Trimming backlog. Removing'
                              + ' oldest %d and keeping newest %d metrics',
                              len(self.metrics) - abs(trim_offset),
                              abs(trim_offset))
                self.metrics = self.metrics[trim_offset:]

    def _connect(self):
        """
        Connect to the graphite server
        """
        if (self.proto == 'udp'):
            stream = socket.SOCK_DGRAM
        else:
            stream = socket.SOCK_STREAM

        # Create socket
        self.socket = socket.socket(socket.AF_INET, stream)
        if socket is None:
            # Log Error
            self.log.error("AutmonHandler: Unable to create socket.")
            return
        # Set socket timeout
        self.socket.settimeout(self.timeout)
        # Connect to autmon server
        try:
            self.socket.connect(self.host)
            # Log
            self.log.debug("AutmonHandler: Established connection to "
                           "autmon server %s.",
                           self.host)
        except Exception, ex:
            # Close Socket
            self._close()
            # Log Error
            self.log.error("AutmonHandler: Failed to connect to %s. %s.",
                           self.host, ex)
            return

            # try:
                # self.socket.connect(self.standby)
                # # Log
                # self.log.debug("AutmonHandler: Established connection to "
                           # "autmon standby server %s.",
                           # self.standby)
            # except Exception, ex:
                # # Log Error
                # self.log.error("AutmonHandler: Failed to connect to %s. %s.",
                           # self.standby, ex)
                # # Close Socket
                # self._close()
                # return

    def _close(self):
        """
        Close the socket
        """
        if self.socket is not None:
            self.socket.close()
        self.socket = None

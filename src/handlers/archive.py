# coding=utf-8

"""
Write the collected stats to a locally stored log file. Rotate the log file
every night and remove after 7 days.
"""
import os
import sys
import logging
import logging.handlers

from handler import Handler


class ArchiveHandler(Handler):
    """
    Implements the Handler abstract class, archiving data to a log file
    """
    def __init__(self, config):
        """
        Create a new instance of the ArchiveHandler class
        """
        # Initialize Handler
        Handler.__init__(self, config)

        # Create Archive Logger
        self.archive = logging.getLogger('autmon')
        #self.archive = logging.getLogger('archive')
        #self.archive.setLevel(logging.DEBUG)
        #self.archive.propagate = False
        # Create Archive Log Formatter
        #formatter = logging.Formatter('%(message)s')
        # Create Archive Log Handler
        #handler = logging.handlers.RotatingFileHandler(
        #    filename=self.config['log_file'],
        #    mode=self.config.get('mode', None),
        #    maxBytes=int(self.config.get('maxBytes', 31457280)),
        #    backupCount=int(self.config.get('backupCount', 7)),
        #    encoding=self.config.get('encoding', None)
        #    )
        # handler = logging.handlers.TimedRotatingFileHandler(
            # filename=self.config['log_file'],
            # when='midnight',
            # interval=1,
            # backupCount=int(self.config.get('days', 7)),
            # encoding=self.config.get('encoding', None)
            # )
        #handler.setFormatter(formatter)
        #handler.setLevel(logging.DEBUG)
        #self.archive.addHandler(handler)

    def process(self, metric):
        """
        Send a Metric to the Archive.
        """
        # Archive Metric
        self.archive.info(str(metric).strip())

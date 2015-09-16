# coding=utf-8

import time
import datetime
import re
import json
import logging

from error import AutmonException


class Metric(object):

    _METRIC_TYPES = ['COUNTER', 'GAUGE', 'LOG']

    def __init__(self, host, path, value, timestamp=None, metric_type='LOG'):
        """
        Create new instance of the Metric class

        Takes:
            path=string: string the specifies the path of the metric
            value=[float|int]: the value to be submitted
            timestamp=[float|int]: the timestamp, in seconds since the epoch
            (as from time.time()) precision=int: the precision to apply.
            Generally the default (2) should work fine.
        """

        if (host is None or host == ''):
            raise AutmonException("Invalid parameter.")    
        
        # Validate the path, value and metric_type submitted
        if (path is None
            or value is None
            or metric_type not in self._METRIC_TYPES):
            raise AutmonException("Invalid parameter.")

        # If no timestamp was passed in, set it to the current time
        if timestamp is None:
            timestamp = int(time.time())
        else:
            # If the timestamp isn't an int, then make it one
            if not isinstance(timestamp, int):
                try:
                    timestamp = int(timestamp)
                except ValueError, e:
                    raise AutmonException("Invalid parameter: %s" % e)

        # check dictionary object
        if metric_type in self._METRIC_TYPES[2:3] \
            and not isinstance(value, dict):
            try:
                value = dict(value)
            except ValueError, e:
                raise AutmonException("Invalid parameter: %s" % e)

        self.path = path
        self.value = value
        self.timestamp = timestamp
        self.host = host
        self.metric_type = metric_type

    def __repr__(self):
        """
        Return the Metric as a string
        """
        if self.metric_type in self._METRIC_TYPES[0:2]:

            if not isinstance(self.precision, (int, long)):
                log = logging.getLogger('autmon')
                log.warn('Metric %s does not have a valid precision', self.path)
                self.precision = 0

            # Set the format string
            fstring = "%%s %%0.%if %%i\n" % self.precision

            # Return formated string
            return fstring % (self.path, self.value, self.timestamp)
            
        elif self.metric_type in self._METRIC_TYPES[2:3]:

            # 
            for name, value in self.value.items():
                if isinstance(value, datetime.datetime):
                    self.value[name] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.date):
                    try:
                        self.value[name] = value.strftime('%Y-%m-%d')
                    except ValueError, e:
                        raise AutmonException("Invalid parameter: %s" % e)

                # elif isinstance(value, datetime.time):
                    # self.value[name] = value.strftime('%H:%M:%S')

            value = {}
            value.update(DATA=self.value)
            value['HOST'] = self.host
            value['PATH'] = self.path
            value['TS'] = self.timestamp

            try:
                result = json.dumps(value)
            except ValueError, e:
                raise AutmonException("Invalid parameter: %s" % e)

            return result

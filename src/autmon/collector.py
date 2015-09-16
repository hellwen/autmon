# coding=utf-8

"""
The Collector class is a base class for all metric collectors.

Support Operating Systems:
* Aix
* Suse linux
* Windows

"""

import os
import socket
import platform
import logging
import traceback
import time
import re
import tempfile, stat

import configobj

from autmon.metric import Metric

# Detect the architecture of the system and set the counters for MAX_VALUES
# appropriately. Otherwise, rolling over counters will cause incorrect or
# negative values.
   
def get_hostname(config, method=None):
    """
    Returns a hostname as configured by the user
    """
    if 'hostname' in config:
        return config['hostname']

    if method is None:
        if 'host_method' in config:
            method = config['host_method']
        else:
            method = 'smart'

    # case insensitive method
    method = method.lower()

    if method in get_hostname.cached_results:
        return get_hostname.cached_results[method]

    if method == 'smart':
        hostname = get_hostname(config, 'fqdn_short')
        if hostname != 'localhost':
            get_hostname.cached_results[method] = hostname
            return hostname
        hostname = get_hostname(config, 'hostname_short')
        get_hostname.cached_results[method] = hostname
        return hostname

    if method == 'fqdn_short':
        hostname = socket.getfqdn().split('.')[0]
        get_hostname.cached_results[method] = hostname
        return hostname
        
    if method == 'hostname_short':
        hostname = socket.gethostname().split('.')[0]
        get_hostnamename.cached_results[method] = hostname
        return hostname

    if method == 'none':
        get_hostname.cached_results[method] = None
        return None

    raise NotImplementedError(config['hostname_method'])

get_hostname.cached_results = {}


def str_to_bool(value):
    """
    Converts string ('true', 'false') to bool
    """
    if isinstance(value, basestring):
        if value.strip().lower() == 'true':
            return True
        else:
            return False

    return value


class Collector(object):
    """
    The Collector class is a base class for all metric collectors.
    """

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """
        # Initialize Logger
        self.log = logging.getLogger('autmon')
        # Initialize Members
        self.name = name
        self.handlers = handlers
        # self.last_values = {}

        # Initialize config
        self.config = configobj.ConfigObj()

        # Check if default config is defined
        if self.get_default_config() is not None:
            # Merge default config
            self.config.merge(self.get_default_config())

        # Check for config file in config directory
        configfile = config['collectors'][self.name]['configfile']
        if os.path.exists(configfile):
            # Merge Collector config file
            self.config.merge(configobj.ConfigObj(configfile))

        # Merge default Collector config
        self.config.merge(config['collectors']['default'])

        if self.config['class'] in config['collectors']:
            # Merge Collector config section
            self.config.merge(config['collectors'][self.config['class']])

        # Check if Collector config section exists
        if self.name in config['collectors']:
            # Merge Collector config section
            self.config.merge(config['collectors'][self.name])

        # Handle some config file changes transparently
        if isinstance(self.config['byte_unit'], basestring):
            self.config['byte_unit'] = self.config['byte_unit'].split()

        self.config['enabled'] = str_to_bool(self.config['enabled'])

        self.config['measure_collector_time'] = str_to_bool(
            self.config['measure_collector_time'])

        self.collect_running = False

    """Determins OS Type using platform module"""
    def __getattr__(self, attr):
        if attr == "aix":
            return "Aix"
        elif attr == "win":
            return "Windows"
        elif attr == "suse":
            return "Suse"
        elif attr == "unknown_linux":
            return "Linux"
        elif attr == "unknown":
            return "unknown"
        else:
            raise AttributeError, attr

    def get_linux_type(self):
        """Uses various methods to determine Linux Type"""
        if platform.dist()[0].upper() == self.suse.upper():
            return self.suse
        else:
            return self.unknown_linux

    def get_os_type(self):
        if platform.system() == "AIX":
            return self.aix
        elif platform.system() == "Linux":
            return self.get_linux_type()
        elif platform.system() == "Windows":
            return self.win
        else:
            return self.unknown

    def get_default_config_help(self):
        """
        Returns the help text for the configuration options for this collector
        """
        return {
            'enabled': 'Enable collecting these metrics',
            'byte_unit': 'Default numeric output(s)',
            'measure_collector_time': 'Collect the collector run time in ms',
        }

    def get_default_config(self):
        """
        Return the default config for the collector
        """
        return {
            ### Defaults options for all Collectors

            # Uncomment and set to hardcode a hostname for the collector path
            # Keep in mind, periods are seperators in graphite
            # 'hostname': 'my_custom_hostname',

            # If you perfer to just use a different way of calculating the
            # hostname
            # Uncomment and set this to one of these values:
            # fqdn_short  = Default. Similar to hostname -s
            # fqdn        = hostname output
            # fqdn_rev    = hostname in reverse (com.example.www)
            # uname_short = Similar to uname -n, but only the first part
            # uname_rev   = uname -r in reverse (com.example.www)
            # 'hostname_method': 'fqdn_short',

            # All collectors are disabled by default
            'enabled': False,
            'path': self.name,

            # Path Prefix
            'path_prefix': 'servers',

            # Path Prefix for Virtual Machine metrics
            'instance_prefix': 'instances',

            # Path Suffix
            'path_suffix': '',

            # Default splay time (seconds)
            'splay': 1,

            # Default Poll Interval (seconds)
            'interval': 300,

            # Default Poll Timeout (seconds)
            'timeout': 300,

            # Default collector threading model
            'method': 'Sequential',

            # Default numeric output
            'byte_unit': 'byte',

            # Collect the collector run time in ms
            'measure_collector_time': False,
        }

    def get_stats_for_upload(self, config=None):
        if config is None:
            config = self.config

        stats = {}

        if 'enabled' in config:
            stats['enabled'] = config['enabled']
        else:
            stats['enabled'] = False

        if 'interval' in config:
            stats['interval'] = config['interval']

        return stats

    def get_schedule(self):
        """
        Return schedule for the collector
        """
        # Return a dict of tuples containing (collector function,
        # collector function args, splay, interval)
        return {self.name: (self._run,
                              None,
                              int(self.config['splay']),
                              int(self.config['interval']))}

    def get_path(self):
        """
        Get metric path.
        Instance indicates that this is a metric for a
            virtual machine and should have a different
            root prefix.
        """
        if 'path' in self.config:
            path = self.config['path']
        else:
            path = self.name

        return path

    def get_hostname(self):
        return get_hostname(self.config)

    def build_script(self, scriptfile):
        if self.get_os_type() == self.win:
            tempfh = tempfile.NamedTemporaryFile(delete=False, suffix=".bat")
        else:
            tempfh = tempfile.NamedTemporaryFile(delete=False, suffix=".sh")
          
        try:
            scriptfh = open(scriptfile)
            for l in scriptfh.readlines():
                re_str = "^.*\<\<BT\>\>(?P<param_name>.+)\<\<ET\>\>.*$"
                patt = re.compile(re_str)
                m = patt.match(l.strip())
                if m:
                    groupdict = m.groupdict()
                    param_name = groupdict['param_name'].lower()
                    if param_name in self.config:
                        rl = l.replace("<<BT>>" + groupdict['param_name'] + "<<ET>>", self.config[param_name])
                        tempfh.write(rl)
                    else:
                        self.log.error("Param(%s) not configureate.", param_name)
                        return False
                else:
                    tempfh.write(l)

            tempfh.flush()
            os.chmod(tempfh.name, stat.S_IRWXU)

            return tempfh.name
        finally:
            scriptfh.close()
            tempfh.close()
            
    def collect(self):
        """
        Default collector method
        """
        raise NotImplementedError()

    def publish(self, value, metric_type='LOG'):
        """
        Publish a metric with the given name
        """
        # Create Metric
        metric = Metric(host=self.get_hostname(), path=self.get_path()
            , value=value, timestamp=None, metric_type=metric_type)

        # Publish Metric
        self.publish_metric(metric)

    def publish_metric(self, metric):
        """
        Publish a Metric object
        """
        # Process Metric
        for handler in self.handlers:
            handler._process(metric)

    def _run(self):
        """
        Run the collector unless it's already running
        """
        if self.collect_running:
            return
        # Log
        self.log.debug("Collecting data from: %s(%s)", self.name, self.__class__.__name__)
        try:
            try:
                start_time = time.time()
                self.collect_running = True

                # Collect Data
                self.collect()

                end_time = time.time()

                if 'measure_collector_time' in self.config:
                    if self.config['measure_collector_time']:
                        metric_name = 'collector_time_ms'
                        metric_value = int((end_time - start_time) * 1000)
                        self.publish(metric_name, metric_value)

            except Exception:
                # Log Error
                self.log.error(traceback.format_exc())
        finally:
            self.collect_running = False
            # After collector run, invoke a flush
            # method on each handler.
            for handler in self.handlers:
                handler._flush()
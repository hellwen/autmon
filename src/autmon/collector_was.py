# coding=utf-8

"""
The Collector class is a base class for all metric collectors.

Support Operating Systems:
* Aix
* Suse linux
* Windows

"""
import os
import time
import json
import traceback
import subprocess

from autmon.collector import Collector

class WasCollector(Collector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """
        # Get Class Collector config
        try:
            class_config = config['collectors']['WasCollector']
        except KeyError:
            class_config = None
        super(WasCollector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)

    def get_default_config_help(self):
        """
        Returns the help text for the configuration options for this collector
        """
        return {
            'enabled': 'Enable collecting these metrics',
        }

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(WasCollector, self).get_default_config()
        config.update({
            'enabled': 'True',
        })
        return config


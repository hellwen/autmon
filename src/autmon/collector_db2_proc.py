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
import traceback

import sys
import ibm_db

from autmon.metric import Metric
from autmon.collector_db2 import DB2Collector
from autmon.error import AutmonException


class DB2ProcCollector(DB2Collector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """     
        try:
            class_config = config['collectors']['DB2ProcCollector']
        except KeyError:
            class_config = None
        super(DB2ProcCollector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)        

        self.procname = self.config['procname']
        self.params = self.config['params']

    def collect(self, conn):
        try:
            # reorgchk tables
            (stmt, param1, param2) = ibm_db.callproc(conn, self.procname, tuple(self.params))
            if stmt:
                result = ibm_db.fetch_assoc(stmt)
                while result != False:
                    if self.add_inst_name:
                        if ('INST' not in result.keys()):
                            result['INST'] = self.server_info['inst_name'].upper()
                        else:
                            result['INST'] = result['INST'].upper()

                    if self.add_db_name:
                        if ('DB' not in result.keys()):
                            result['DB'] = self.server_info['db_name'].upper()
                        else:
                            result['DB'] = result['DB'].upper()

                    self.publish(result)
                    result = ibm_db.fetch_assoc(stmt)
        except Exception:
            self.log.error(traceback.format_exc())        

        return True


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

import ibm_db

from autmon.collector_db2 import DB2Collector

class DB2SqlCollector(DB2Collector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """
        # Get Class Collector config
        try:
            class_config = config['collectors']['DB2SqlCollector']
        except KeyError:
            class_config = None
        super(DB2SqlCollector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)

        if 'filename' in self.config:
            scriptfile = os.path.abspath(os.path.join(self.config['configpath'], \
                self.config['filename']))
            # print scriptfile
            if not os.path.exists(scriptfile):
                self.log.error("Collect (%s) can't find script file(%s).", self.name, scriptfile)
                return None

            with open(scriptfile) as f:
                self.sql = " ".join(f.readlines())

    def collect(self, conn):
        sql = self.sql

        try:
            stmt = ibm_db.prepare(conn, sql)
            if ibm_db.execute(stmt):
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

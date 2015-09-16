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

from autmon.collector import Collector

class DB2Collector(Collector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """          
        # Get Class Collector config
        try:
            class_config = config['collectors']['DB2Collector']
        except KeyError:
            class_config = None
        super(DB2Collector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)

        databases = self.config['databases']
        if not isinstance(databases, list):
            databases = databases.split()
        self.databases = databases

        self.level = self.config['level']

        self.add_inst_name = False
        if self.config.get('add_inst_name', 'False').strip() == 'True':
            self.add_inst_name = True

        self.add_db_name = False
        if self.config.get('add_db_name', 'False').strip() == 'True':
            self.add_db_name = True

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(DB2Collector, self).get_default_config()
        config.update({
            'enabled': 'True',
            # instance or database
            'level': 'database',
            'add_inst_name': 'True',
            'add_db_name': 'True',
        })
        return config

    def get_server_info(self, conn):
        server_info = ibm_db.server_info(conn)

        dbms_name = server_info.DBMS_NAME
        dbms_ver = server_info.DBMS_VER
        inst_name = server_info.INST_NAME.upper()
        db_name = server_info.DB_NAME.upper()

        return dict(dbms_name=dbms_name
            , dbms_ver=dbms_ver
            , inst_name=inst_name
            , db_name=db_name
            )

    def connect_db(self, db, pconnect=True, trytimes=3):
        try:
            if pconnect:
                conn = ibm_db.pconnect(db, "", "")
            else:
                conn = ibm_db.connect(db, "", "")
        except Exception:
            if pconnect:
                self.log.error('Database persistent connect failted('
                    + str(trytimes) + '): ' + traceback.format_exc())
            else:
                self.log.error('Database connect failted('
                    + str(trytimes) + '): ' + traceback.format_exc())

        try:
            if ibm_db.active(conn):
                self.server_info = self.get_server_info(conn)
                return conn
        except Exception:
            pass

        if pconnect:
            self.log.error('Database persistent connect inactive(' + str(trytimes) + ')')
        else:
            self.log.error('Database connect inactive(' + str(trytimes) + ')')

        if trytimes > 0:
            try:
                ibm_db.close(conn)
            except Exception:
                pass
            self.log.info('Database connect try again(' + str(trytimes) + ')')
            trytimes -= 1
            return self.connect_db(db, pconnect=False, trytimes=trytimes)

        return False

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

                for db in self.databases:
                    conn = self.connect_db(db)
                    if not conn or not ibm_db.active(conn):
                        break

                    if self.level.upper() == 'INSTANCE':
                        self.collect(conn)
                        break
                    elif self.level.upper() == 'DATABASE':
                        self.collect(conn)

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

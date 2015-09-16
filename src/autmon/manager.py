# coding=utf-8

import os
import sys
import time
import logging
import traceback
import inspect

import socket

import configobj

# Path Fix
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../")))

from autmon.util import get_autmon_version

class Manager(object):
    """
    Manager class manage Autmon
    """

    def __init__(self, config):
        # Initialize Logging
        self.log = logging.getLogger('autmon')

        # Initialize Members
        self.config = config
        
    def load_config(self):
        """
        Load the full config
        """

        configfile = os.path.abspath(self.config['configfile'])
        config = configobj.ConfigObj(configfile)
        config['configfile'] = self.config['configfile']

        self.config = config

    def get_version(self):
        """
        Get Autmon current version
        """
        return get_autmon_version()

    def get_config(self, items):
        """
        Get Config
            items: handlers>AutmonHandler>host
        """
        self.load_config()
        
        print type(self.config)
        print self.config.items()
        
        pid_file = self.config['collectors']
        pid_file = self.config['collectors']['DB2SqlCollector']
        print pid_file
        collectors_config_path = self.config['server']['collectors_config_path']
        print collectors_config_path
        
        
        
        
        
        
        
        
        config = self.config
        for item in config.items():
            print item

        for item in items.split('>'):
            print item
            if item:
                config = config[item]

        return config

    def update_config(self, items, value):
        """
        Update Config
            items: handlers>AutmonHandler>host
        """
        config = self.config
        for item in items.split('>'):
            if item:
                config = config[item]
            config = value

        return value

    def get_collector(self, collector):
        """
        Get Collector
        """

    def update_collector(self, collector):
        """
        Update Collector
        """

    def schedule_collector(self, collector):
        """
        Schedule One Collector
        """

    def do_stop(self):
        """
        Stop Autmon
        """

    def do_start(self):
        """
        Start Autmon
        """

    def run(self):
        """
        Load handler and collector classes and then start collectors
        """

        # Set Running Flag
        self.running = True

        # Load handlers          
        self.load_handlers()

        # Load config
        self.load_config()

        # Load collectors
        collectors = self.load_collectors()

        # Setup Collectors
        for name, cls in collectors.items():
            # Initialize Collector
            c = self.init_collector(name, cls)
            # Schedule Collector
            self.schedule_collector(c)

        # Start main loop
        self.mainloop()

    def run_one(self, file):
        """
        Run given collector once and then exit
        """
        # Set Running Flag
        self.running = True

        # Load handlers
        self.load_handlers()

        # Load collectors
        collectors = self.load_collectors()

        # Setup Collectors
        for name, cls in collectors.items():
            # Initialize Collector
            c = self.init_collector(name, cls)

            # Schedule collector
            self.schedule_collector(c, False)

        # Start main loop
        self.mainloop(False)

    def mainloop(self, reload=True):

        # Start scheduler
        self.scheduler.start()

        # Log
        self.log.info('Started task scheduler.')

        # Initialize reload timer
        time_since_reload = 0

        # Main Loop
        while self.running:
            time.sleep(1)
            time_since_reload += 1

            # Check if its time to reload collectors
            if (reload
                    and time_since_reload
                    > int(self.config['server']['collectors_reload_interval'])):
                self.log.debug("Reloading config.")
                self.load_config()
                # Log
                self.log.debug("Reloading collectors.")
                # Load collectors
                collectors = self.load_collectors()
                # Setup any Collectors that were loaded
                for name, cls in collectors.items():
                    # Initialize Collector
                    c = self.init_collector(name, cls)
                    # Schedule Collector
                    self.schedule_collector(c)

                # Reset reload timer
                time_since_reload = 0

            # Is the queue empty and we won't attempt to reload it? Exit
            if not reload and len(self.scheduler.sched._queue) == 0:
                self.running = False

        # Log
        self.log.debug('Stopping task scheduler.')
        # Stop scheduler
        self.scheduler.stop()
        # Log
        self.log.info('Stopped task scheduler.')
        # Log
        self.log.debug("Exiting.")

    def stop(self):
        """
        Close all connections and terminate threads.
        """
        # Set Running Flag
        self.running = False

class SocketServer(object):

    def __init__(self, host, port):

        self.backlog = 5

        self.host = host
        self.port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(self.backlog)

        self.data = ''
        self.end_tag = '<EOF>'

    def reap(self):
        while True:
            try:
                result = os.waitpid(-1, os.WNOHANG)
                if not result[0]: break
            except:
                break
            print "Reaped child process %d" % result[0]


    def start(self):

        print "Parent at %d listening for connections" % os.getpid()

        while True:
            try:
                conn, addr = self.server.accept()
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()
                continue

            self.reap()

            try:
                pid = os.fork()
            except:
                print "BAD THING HAPPENED: fork failed"
                conn.close()
                continue

            if pid:
                conn.close()
                continue
            else:
                self.server.close()

                try:
                    print "Child from %s being handled by PID %d" % \
                        (conn.getpeername(), os.getpid())

                    while True:
                        data = conn.recv(4096)
                        if not data or data == '': break 

                        self.datafactory(data.strip())

                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    traceback.print_exc()

                try:
                    conn.close()
                except KeyboardInterrupt:
                    raise
                except:
                    traceback.print_exc()

                break


    def datafactory(self, data):

        jsons = self.getjsons(data) 

        storage = db_storage.Storage()
        storage.push(jsons)

    def getjsons(self, data):
        result = []

        self.data += data

        iend = self.data.find('}' + self.end_tag)
        while iend > 0:
            ibng = self.data.find('{')
            j = self.data[ibng:iend + 1]
            result.append(j)

            ibng = self.data.find('{', iend)
            if ibng > 0:
                self.data = self.data[ibng:]
            else:
                self.data = ''
                break

            iend = self.data.find('}' + self.end_tag)

        return result



if __name__ == '__main__':
    configfile = 'D:\autmon_repository\autmon\conf\autmon_nt.conf'
    config = configobj.ConfigObj(configfile)
    config['configfile'] = configfile

    # Initialize Server
    manager = Manager(config)

    print manager.get_config('handlers>AutmonHandler>host')
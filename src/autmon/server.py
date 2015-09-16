# coding=utf-8

import os
import sys
import time
import logging
import traceback
import inspect

import configobj

# Path Fix
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../")))

from autmon.collector import Collector

from handlers.handler import Handler
from autmon.scheduler import ThreadedScheduler
from autmon.scheduler import ThreadedWeekdayTask
from autmon.scheduler import method as scheduler_method
from autmon.util import load_class_from_name

class Server(object):
    """
    Server class loads and starts Handlers and Collectors
    """

    def __init__(self, config):
        # Initialize Logging
        self.log = logging.getLogger('autmon')

        # Initialize Members
        self.config = config
        self.running = False
        self.handlers = []
        self.modules = {}
        self.tasks = {}
        # Initialize Scheduler
        self.scheduler = ThreadedScheduler()

    def load_config(self):
        """
        Load the full config
        """

        configfile = os.path.abspath(self.config['configfile'])
        config = configobj.ConfigObj(configfile)
        config['configfile'] = self.config['configfile']

        self.config = config

    def load_handler(self, fqfn, fqcn):
        """
        Load Handler class named fqcn
        """
        # Load class
        fqname = 'handlers.' + fqfn + '.' + fqcn
        cls = load_class_from_name(fqname)
        # Check if cls is subclass of Handler
        if cls == Handler or not issubclass(cls, Handler):
            raise TypeError("%s is not a valid Handler" % fqcn)
        # Log
        self.log.debug("Loaded Handler: %s", fqcn)
        return cls

    def load_handlers(self):
        """
        Load handlers
        """
        for h in self.config['handlers'].sections:
            if h == 'default': continue

            try:
                if 'enabled' in self.config['handlers'][h].keys():
                    #if self.config['handlers'][h]['enabled'] == 'False':
                    if self.config['handlers'][h].get('enabled', 'False').strip() == 'False':
                        continue
                else:
                    self.log.debug("The %s not have enabled params", h)
                    continue

                # Load Handler Class
                if 'file_name' in self.config['handlers'][h].keys():
                    f = self.config['handlers'][h]['file_name']
                    cls = self.load_handler(f, h)
                else:
                    self.log.debug("The %s not have file_name params", h)
                    continue

                # Initialize Handler config
                handler_config = configobj.ConfigObj()
                # Merge default Handler default config
                handler_config.merge(self.config['handlers']['default'])
                # Check if Handler config exists
                if cls.__name__ in self.config['handlers']:
                    # Merge Handler config section
                    handler_config.merge(self.config['handlers'][cls.__name__])

                # Initialize Handler class
                self.handlers.append(cls(handler_config))

            except ImportError:
                # Log Error
                self.log.debug("Failed to load handler %s.%s. %s", f, h,
                               traceback.format_exc())
                continue

    def load_collectors(self):
        """
        Scan for collectors to load from path
        """
        # Initialize return value
        collectors = {}

        # Load all
        for c in self.config['collectors'].sections:
            if c == 'default': continue

            if 'enabled' in self.config['collectors'][c].keys():
                #if self.config['collectors'][c]['enabled'] == 'False':
                if self.config['collectors'][c].get('enabled', 'False').strip() == 'False':
                    continue
            else:
                self.log.debug("The %s not have enabled params", c)
                continue

            self.log.debug("Loading Collector: %s", c)

            configpath = os.path.join(self.config['server']['collectors_config_path'], c)
            configfile = os.path.join(configpath, c + ".conf")

            if os.path.exists(configfile):
                config = configobj.ConfigObj(os.path.abspath(configfile))
                # Add current collectors path to config file
                config['configpath'] = configpath
                config['configfile'] = configfile
                self.config['collectors'][c].merge(config)

                cls = self.config['collectors'][c]['class']

                if cls == "CMDCollector":
                    from autmon.collector_cmd import CMDCollector
                    collectors[c] = CMDCollector
                elif cls == "DB2SqlCollector":
                    from autmon.collector_db2_sql import DB2SqlCollector
                    collectors[c] = DB2SqlCollector
                elif cls == "DB2ProcCollector":
                    from autmon.collector_db2_proc import DB2ProcCollector
                    collectors[c] = DB2ProcCollector
                elif cls == "WasJythonCollector":
                    from autmon.collector_was_jpython import WasJythonCollector
                    collectors[c] = WasJythonCollector
            else:
                self.log.debug("Collector Config File Not found: %s(%s)", c, configfile)

        # Return Collector classes
        return collectors

    def init_collector(self, name, cls):
        """
        Initialize collector
        """
        collector = None
        try:
            # Initialize Collector
            collector = cls(name, self.config, self.handlers)
            # Log
            self.log.debug("Initialized Collector: %s(%s)", name, collector.__class__.__name__)
        except Exception:
            # Log error
            self.log.error("Failed to initialize Collector: %s(%s). %s",
                           name, cls, traceback.format_exc())

        # Return collector
        return collector

    def schedule_collector(self, c, interval_task=True):
        """
        Schedule collector
        """
        # Check collector is for realz
        if c is None:
            self.log.warn("Skipped loading invalid Collector: %s",
                          c.__class__.__name__)
            return

        if c.config['enabled'] != True:
            self.log.warn("Skipped loading disabled Collector: %s",
                          c.__class__.__name__)
            return

        # Get collector schedule
        for name, schedule in c.get_schedule().items():
            # Get scheduler args
            func, args, splay, interval = schedule

            # Check if Collecter with same name has already been scheduled
            if name in self.tasks:
                try:
                    self.scheduler.cancel(self.tasks[name])
                    # Log
                    self.log.debug("Canceled task: %s", name)
                except ValueError, e:
                    self.log.error("Canceled task not found: %s", e)

            method = scheduler_method.sequential

            if 'method' in c.config:
                if c.config['method'] == 'Threaded':
                    method = scheduler_method.threaded
                elif c.config['method'] == 'Forked':
                    method = scheduler_method.forked

            # Schedule Collector
            if interval_task and ('task_type' in c.config):
                if c.config['task_type'] == 'Interval':
                    task = self.scheduler.add_interval_task(func,
                                                            name,
                                                            splay,
                                                            interval,
                                                            method,
                                                            args,
                                                            None,
                                                            True)
                elif c.config['task_type'] == 'Weekday':
                    try:
                        weekdays = [int(a) for a in c.config['weekdays']]
                    except TypeError, e:
                        self.log.error("weekdays must be a sequence of numbers 1-7: %s", e)

                    try:
                        timeonday = [int(a) for a in c.config['timeonday']]
                    except TypeError, e:
                        self.log.error("timeonday must be a sequence of hour,minute: %s", e)

                    task = self.scheduler.add_daytime_task(func,
                                                            name,
                                                            weekdays,
                                                            None,
                                                            timeonday,
                                                            method,
                                                            args,
                                                            None)
                elif c.config['task_type'] == 'Monthday':
                    try:
                        monthdays = [int(a) for a in c.config['monthdays']]
                    except TypeError, e:
                        self.log.error("monthdays must be a sequence of numbers 1-31: %s", e)

                    try:
                        timeonday = [int(a) for a in c.config['timeonday']]
                    except TypeError, e:
                        self.log.error("timeonday must be a sequence of hour,minute: %s", e)

                    task = self.scheduler.add_daytime_task(func,
                                                            name,
                                                            None,
                                                            monthdays,
                                                            timeonday,
                                                            method,
                                                            args,
                                                            None)
            else:
                task = self.scheduler.add_single_task(func,
                                                      name,
                                                      splay,
                                                      method,
                                                      args,
                                                      None)

            # Log
            self.log.debug("Scheduled task: %s", name)
            # Add task to list
            self.tasks[name] = task

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

if __name__ == '__main__':
    configfile = '/db2fs/autmon/autmon/conf/autmon.conf'
    config = configobj.ConfigObj(configfile)
    config['configfile'] = configfile

    # Initialize Server
    server = Server(config)

    server.run_one('/db2fs/autmon/autmon/src/collectors')
    # server.run()

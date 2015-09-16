import os
import sys
import win32process
import win32event

import cx_Logging
import cx_Threads


class ServiceHandler(object):

    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self):
        cx_Logging.Error("creating handler instance")
        # Initialize Logging
        self.stopEvent = cx_Threads.Event()

    # called when the service is starting
    def Initialize(self, configFileName):
        configFilePath = os.path.dirname(configFileName)
        self.path = os.path.abspath(configFilePath)
        self.exe_name = 'autmon.exe'
        cx_Logging.Error("initializing: current work directory %s", self.path)

    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        cx_Logging.Error("running service...")

        try:
            # CreateProcess(appName, commandLine, processAttributes, 
            # threadAttributes, bInheritHandles, 
            # dwCreateionFlags, newEnvironment, currentDirectory, startupinfo)
            # 
            appName = os.path.join(self.path, self.exe_name)
            self.handle = win32process.CreateProcess(
                appName, '', None, None, 0,
                win32process.CREATE_NO_WINDOW,
                None, self.path, win32process.STARTUPINFO())
        except Exception, e:
            cx_Logging.Error("Autmon Invoke Error! %s", e)
            self.handle = None

        while self.handle:
            rc = win32event.WaitForSingleObject(self.handle[0], 300)
            if rc == 0:
                self.handle = None
                cx_Logging.Error("Autmon be stopped!")
                self.Stop()

        self.stopEvent.Wait()

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        cx_Logging.Error("stopping service...")
        if self.handle:
            win32process.TerminateProcess(self.handle[0], 0)
            cx_Logging.Error("Autmon stopped...")
        self.stopEvent.Set()

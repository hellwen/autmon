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

from autmon.collector_was import WasCollector

class WasJythonCollector(WasCollector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """
        # Get Class Collector config
        try:
            class_config = config['collectors']['WasJythonCollector']
        except KeyError:
            class_config = None
        super(WasJythonCollector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)

        self.was_servers = self.config['was_servers']
        self.was_conntype = self.config['was_conntype']
        self.was_host = self.config['was_host']
        self.was_port = self.config['was_port']
        self.was_user = self.config['was_user']
        self.was_password = self.config['was_password']
        
        if 'was_home' in self.config:
            self.was_home = os.path.abspath(self.config['was_home'])

        if 'was_profile_name' in self.config:
            self.was_profile_name = self.config['was_profile_name']

        if 'filename' in self.config:
            scriptfile = os.path.abspath(os.path.join(self.config['configpath'], \
                self.config['filename']))
            # print scriptfile
            if not os.path.exists(scriptfile):
                self.log.error("Collect (%s) can't find script file(%s).", self.name, scriptfile)
                return None

            self.scriptfile = scriptfile

        # initial params
        os_type = self.get_os_type()
        wsadmin_official_home = os.path.join(self.was_home, "profiles", self.was_profile_name)

        if os_type.upper() == 'WINDOWS':
            wsadmin_performance_home = wsadmin_official_home
            self.wsadmin_script = os.path.join(wsadmin_performance_home, 'bin', 'wsadmin.bat')
        else:
            wsadmin_performance_home = os.path.join(os.path.abspath("."), "..", "wsadmin")
            self.wsadmin_script = os.path.join(wsadmin_performance_home, 'bin', 'wsadmin.sh')

            # modify ssl.client.props user.root only in aix/linux at 2014-05-27
            ssl_cleint_props = os.path.join(wsadmin_performance_home, 'properties', 'ssl.client.props')
            self.modify_config_value(ssl_cleint_props, 'user.root=', wsadmin_official_home)
            # modify wsadmin.sh WAS_HOME only in aix/linux at 2014-05-28
            self.modify_config_value(self.wsadmin_script, 'WAS_HOME=', self.was_home)
            wsadmin_properties = os.path.join(wsadmin_performance_home, 'properties', 'wsadmin.properties')
            self.modify_config_value(wsadmin_properties, \
                'com.ibm.ws.scripting.traceFile=', \
                os.path.join(wsadmin_performance_home, 'logs', 'wsadmin.traceout'))
            self.modify_config_value(wsadmin_properties, \
                'com.ibm.ws.scripting.validationOutput=', \
                os.path.join(wsadmin_performance_home, 'logs', 'wsadmin.valout'))
            self.modify_config_value(wsadmin_properties, \
                'com.ibm.ws.scripting.classpath=', \
                os.path.join(self.was_home, 'optionalLibraries', 'jython', 'jython.jar'))            

    def modify_config_value(self, file, key, value):
        f = open(file, 'r+')
        try:
            news=[]
            for r in f:
                if r.startswith(key):
                    news.append(key + value + '\n')
                else:
                    news.append(r)
            f.seek(0)
            f.writelines(news)
        finally:
            f.flush()
            f.close()

    def collect(self):
        scriptfile = self.scriptfile

        # build wsadmin.sh command
        wsadmin_cmd = '"' + self.wsadmin_script + '" -lang jython '
        if self.was_conntype:
            wsadmin_cmd += ' -conntype ' + str(self.was_conntype)
        if self.was_host:
            wsadmin_cmd += ' -host ' + str(self.was_host)
        if self.was_port:
            wsadmin_cmd += ' -port ' + str(self.was_port)
        if self.was_user:
            wsadmin_cmd += ' -user ' + str(self.was_user)
        if self.was_password:
            wsadmin_cmd += ' -password ' + str(self.was_password)
        if not self.was_servers or self.was_servers == '*':
            wsadmin_cmd += ' -f ' + scriptfile
        else:
            wsadmin_cmd += ' -f ' + scriptfile + ' ' + self.was_servers
        # print wsadmin_cmd

        # execute wsadmin.sh
        p1 = subprocess.Popen(wsadmin_cmd, shell=True, stdout=subprocess.PIPE)
        result = p1.communicate()[0]

        for r in [ l for l in result.split('\n') if l != '']:
            # pass was tips
            if r.startswith('WAS'):
                continue

            # print r
            try:
                rl = eval(r.strip())
                # if isinstance(rl, List):
                # print rl
                self.publish(rl)
            except SyntaxError:
                continue

        return True

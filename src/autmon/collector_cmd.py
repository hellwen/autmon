# coding=utf-8

"""
The Collector class is a base class for all metric collectors.

Support Operating Systems:
* Aix
* Suse linux
* Windows

"""
import os
import re
import time
import subprocess

from autmon.collector import Collector
from autmon.error import AutmonException

class CMDCollector(Collector):

    def __init__(self, name, config, handlers):
        """
        Create a new instance of the Collector class
        """
        # Get Class Collector config
        try:
            class_config = config['collectors']['CMDCollector']
        except KeyError:
            class_config = None
        super(CMDCollector, self).__init__(name, config, handlers)
        if class_config:
            self.config.merge(class_config)

        # vars = self.config['env_vars']
        # if not isinstance(vars, list):
            # vars = vars.split()
        # for var in vars:
            # key, param = var.split(':')
            # os.putenv(key, self.config[param])

    def get_default_config_help(self):
        config_help = super(CMDCollector, self).get_default_config_help()
        config_help.update({
            'filesystems': "filesystems to examine",
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(CMDCollector, self).get_default_config()
        config.update({
            'enabled': 'True',
            'fs': ',',
            'timeout': 300,
        })
        return config

    def collect(self):
        os_type = self.get_os_type()
        title = self.config['title']
        if not isinstance(title, list):
            title = title.split()

        for k in self.config.sections:
            if os_type.upper() == self.config[k]['platform'].upper():
                scriptfile = os.path.abspath(os.path.join(self.config['configpath'], \
                    self.config[k]['filename']))
                # print scriptfile
                if not os.path.exists(scriptfile):
                    self.log.error("Collect (%s) can't find script file(platform:%s, file:%s).", self.name, os_type, scriptfile)
                    return None

                if 'fs' in self.config.keys():
                    fs = self.config['fs']

                try:
                    newf = self.build_script(scriptfile)
                    if os.path.exists(newf):
                        try:
                            # p1 = subprocess.Popen(newf, shell=True, stdout=subprocess.PIPE)
                            # counterfile = p1.communicate()[0]

                            t1 = time.time()
                            if os_type.upper() != "WINDOWS":
                                p1 = subprocess.Popen(newf, shell=True, stdout=subprocess.PIPE, bufsize=10000, close_fds=True)
                            else:
                                p1 = subprocess.Popen(newf, shell=True, stdout=subprocess.PIPE, bufsize=10000)

                            while p1.poll() is None:
                                time.sleep(0.1)
                                t2 = time.time()
                                if (t2 - t1) >= int(self.config['timeout']):
                                    p1.terminate()
                                    raise ScriptException("timeout")

                            counterfile = p1.stdout
                            
                            re_str = "^" + fs.join([ "(?P<" + t + ">.+)" for t in title]) + "$"
                            patt = re.compile(re_str)
                            # for r in [ l for l in counterfile.split('\n') if l != '']:
                            for r in counterfile:
                                if r is None or r == "":
                                    continue
                                # print r.strip()
                                m = patt.match(r.strip())
                                if m:
                                    groupdict = m.groupdict()
                                    self.publish(groupdict)
                            
                            if p1.stdin:
                                p1.stdin.close()
                                
                            if p1.stdout:
                                p1.stdout.close()
                                
                            if p1.stderr:
                                p1.stderr.close()

                            try:
                                p1.kill()
                            except OSError:
                                pass
                        except Exception as e:
                            self.log.error("Script(%s) result error(%s)", scriptfile, e)
                finally:
                    if os.path.exists(newf):
                        os.remove(newf)

        return True

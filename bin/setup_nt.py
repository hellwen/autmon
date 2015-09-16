# A very simple setup script to create a single executable
#
# hello.py is a very simple "Hello, world" type script which also displays the
# environment in which the script runs
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the script without Python

import sys
from cx_Freeze import setup, Executable

executables = [
        Executable("autmon",
            targetName = "autmon.exe",
            compress = True
            ),
        Executable("config.py",
            base = "Win32Service",
            targetName = "autmon_service.exe"
            ),
]

buildOptions = dict(
        build_exe = "..\\autmon\\bin",
        compressed = True,
        include_files = [("..\\conf\\autmon_nt.conf", "..\\conf\\autmon.conf")
            , "..\\log\\"
            , "..\\db2cli\\"
            , ("AutmonStart.bat", "../AutmonStart.bat")
            , ("AutmonStop.bat", "../AutmonStop.bat")
            , ("AutmonJobRestart.bat", "../AutmonJobRestart.bat")
            , ("AutmonQuery.bat", "../AutmonQuery.bat")
            , ("InstallService.bat", "../InstallService.bat")
            , ("UnInstallService.bat", "../UnInstallService.bat")
            ],
        includes = ["ibm_db", "ibm_db_dbi", "autmon_service"
            , "handlers.archive"
            , "handlers.autmon"
            ],
        path = sys.path + ["..\\src"],
            )

setup(
        name = "autmon",
        version = "1.8",
        description = "autmon python modules",
        options = dict(build_exe = buildOptions),
        executables = executables)

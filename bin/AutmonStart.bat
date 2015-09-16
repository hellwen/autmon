@echo off

color 0B

set svc_name=AutmonService

net start %svc_name%

set current_script="%~dp0\AutmonJobRestart.bat"

schtasks /delete /tn "autmon" /F > nul
schtasks /create /tn "autmon" /mo 10 /sc minute /st 00:00:00 /ru "NT AUTHORITY\SYSTEM" /tr "%current_script%"

@pause > nul

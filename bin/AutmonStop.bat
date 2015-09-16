@echo off

color 0B

set svc_name=AutmonService

net stop %svc_name%

schtasks /delete /tn "autmon" /F

@pause > nul

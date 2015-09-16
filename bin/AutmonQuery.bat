@echo off

color 0B

set svc_name=AutmonService

sc query %svc_name%

@pause > nul

#!/bin/sh

# get absolute path
name=${0#.\/}
if [ "${name}" == "-ksh" ]; then
    echo "usage error. please use sh *.sh or *.sh"
    return 1
elif [ "${name##*\/}" == "$name" ]; then
    location=`pwd`
elif [ "${name%%\/*}" == "" ]; then
    location=${name%\/*}
else
    location="`pwd`/${name%\/*}"
fi

AUTMON_WSADMIN_HOME=${location%\/*}
export AUTMON_WSADMIN_HOME

WAS_HOME=/usr/IBM/WebSphere/AppServer
export WAS_HOME

. ${AUTMON_WSADMIN_HOME}/bin/setupCmdLine.sh

${WAS_HOME}/bin/wsadmin.sh "$@"

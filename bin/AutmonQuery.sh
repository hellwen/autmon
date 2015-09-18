#!/bin/ksh

# get absolute path
if [ "${0##*\/}" == "$0" ]; then
    location=`pwd`
elif [ "${0%%\/*}" == "" ]; then
    location=${0%\/*}
else
    location="`pwd`/${0%\/*}"
fi

autmon_path="${location}"
pid_f="${autmon_path}/log/autmon.pid"

# if running
if [ -f $pid_f ]; then
    pid=`cat $pid_f`
    ps -ef | grep -v $$ | grep -i $pid
fi

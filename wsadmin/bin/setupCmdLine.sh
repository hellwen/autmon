#!/bin/sh
# @(#) 1.21 CFG/ws/code/profile.templates/src/bin/setupCmdLine.sh, WAS.config.base, WAS61.CFG, cf230901.19 5/8/06 13:29:35 [3/24/09 12:16:26]

# Modified by Hellwen.wu
WAS_USER_SCRIPT="${AUTMON_WSADMIN_HOME}/bin/setupCmdLine.sh"
export WAS_USER_SCRIPT

USER_INSTALL_ROOT="${AUTMON_WSADMIN_HOME}"
JAVA_HOME="${WAS_HOME}/java"

#ulimit -n 10000

OSGI_INSTALL="-Dosgi.install.area=$WAS_HOME"
OSGI_CFG="-Dosgi.configuration.area=$USER_INSTALL_ROOT/configuration"
                                                                                                                             
ITP_LOC="$WAS_HOME"/deploytool/itp
CONFIG_ROOT="$USER_INSTALL_ROOT"/config

CLIENTSAS=-Dcom.ibm.CORBA.ConfigURL=file:"$USER_INSTALL_ROOT"/properties/sas.client.props
STDINCLIENTSAS=-Dcom.ibm.CORBA.ConfigURL=file:"$USER_INSTALL_ROOT"/properties/sas.stdinclient.props
SERVERSAS=-Dcom.ibm.CORBA.ConfigURL=file:"$USER_INSTALL_ROOT"/properties/sas.server.props
CLIENTSOAP=-Dcom.ibm.SOAP.ConfigURL=file:"$USER_INSTALL_ROOT"/properties/soap.client.props
JAASSOAP=-Djava.security.auth.login.config="$USER_INSTALL_ROOT"/properties/wsjaas_client.conf
CLIENT_CONNECTOR_INSTALL_ROOT="$USER_INSTALL_ROOT"/installedConnectors
CLIENTSSL=-Dcom.ibm.SSL.ConfigURL=file:"$USER_INSTALL_ROOT"/properties/ssl.client.props
WAS_LOGGING="-Djava.util.logging.manager=com.ibm.ws.bootstrap.WsLogManager -Djava.util.logging.configureByServer=true"

QUALIFYNAMES=-qualifyHomeName
PATH="$JAVA_HOME"/ibm_bin:"$JAVA_HOME"/bin/:"$JAVA_HOME"/jre/bin:$PATH
WAS_EXT_DIRS="$JAVA_HOME"/lib:"$WAS_HOME"/classes:"$WAS_HOME"/lib:"$WAS_HOME"/installedChannels:"$WAS_HOME"/lib/ext:"$WAS_HOME"/web/help:"$ITP_LOC"/plugins/com.ibm.etools.ejbdeploy/runtime
WAS_CLASSPATH="$WAS_HOME"/properties:"$WAS_HOME"/lib/startup.jar:"$WAS_HOME"/lib/bootstrap.jar:"$WAS_HOME"/lib/j2ee.jar:"$WAS_HOME"/lib/lmproxy.jar:"$WAS_HOME"/lib/urlprotocols.jar:"$JAVA_HOME"/lib/tools.jar

PLATFORM=`/bin/uname`
case $PLATFORM in

  AIX)

    WAS_LIBPATH="$WAS_HOME"/bin
    NLSPATH=/usr/lib/nls/msg/%L/%N:/usr/lib/nls/msg/en_US/%N:${NLSPATH:=}
#    WAS_BOOTCLASSPATH=
    ;;

  Linux)

    WAS_LIBPATH="$WAS_HOME"/bin
    NLSPATH=/usr/lib/locale/%L/LC_MESSAGES/%N:${NLSPATH:=}
    JAVA_HIGH_ZIPFDS=200
#    WAS_BOOTCLASSPATH=
    ;;

  SunOS)

    if [ "$LANG" = "" ]
    then
       LANG=C
       export LANG
    fi
    WAS_LIBPATH="$WAS_HOME"/bin
    NLSPATH=/usr/lib/locale/%L/LC_MESSAGES/%N:${NLSPATH:=}
#    WAS_BOOTCLASSPATH=
    ;;

  HP-UX)

    WAS_LIBPATH="$WAS_HOME"/bin
    NLSPATH=/usr/lib/nls/msg/%L/%N:${NLSPATH:=}
#    WAS_BOOTCLASSPATH=
    ;;

  *)

    WAS_LIBPATH="$WAS_HOME"/bin
    NLSPATH=/usr/lib/locale/%L/LC_MESSAGES/%N:${NLSPATH:=}
#    WAS_BOOTCLASSPATH=
    ;;

esac

export PATH WAS_HOME WAS_CELL WAS_NODE JAVA_HOME ITP_LOC CLIENTSAS CLIENTSSL STDINCLIENTSAS SERVERSAS CLIENTSOAP CLIENT_CONNECTOR_INSTALL_ROOT WAS_LOGGING QUALIFYNAMES WAS_EXT_DIRS WAS_CLASSPATH CONFIG_ROOT NLSPATH JAVA_HIGH_ZIPFDS WAS_LIBPATH OSGI_INSTALL OSGI_CFG


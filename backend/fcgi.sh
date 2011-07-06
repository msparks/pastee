#!/bin/sh
# Customized init script using Debian's start-stop-daemon.
#
# This script is used to start and stop the Pastee backend's FCGI processes. It
# creates a fcgi.sock Unix socket file in .../backend/run/, to be accessed by
# any FCGI-supporting webserver (nginx, Apache, lighttpd, etc).
#
# Based off of the Debian init script for Django:
#   https://code.djangoproject.com/wiki/InitdScriptForDebian

set -e

#### CONFIGURATION

# Please make sure this is NOT root.
# local user preferred, www-data accepted
RUN_AS=$USER

# Maximum requests before FastCGI process respawns.
MAXREQUESTS=1000

# Run method (threaded or prefork).
METHOD=prefork

# Hard limit on number of process / threads.
MAXCHILDREN=6

#### END CONFIGURATION

cd `dirname $0`
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DESC="Pastee backend"
MANAGE_PY=$PWD/manage.py
RUNFILES_PATH=$PWD/run
mkdir -p $RUNFILES_PATH
chown -R $RUN_AS:$RUN_AS $RUNFILES_PATH

#
#       Function that starts the daemon/service.
#
d_start()
{
  pidfile=$RUNFILES_PATH/fcgi.pid
  if [ -f $pidfile ]; then
    echo "$DESC is already running (pidfile: $pidfile)"
  else
    start-stop-daemon --start --quiet \
      --pidfile $RUNFILES_PATH/fcgi.pid \
      --chuid $RUN_AS --exec /usr/bin/env -- python \
      $MANAGE_PY runfcgi \
      protocol=fcgi method=$METHOD maxrequests=$MAXREQUESTS \
      maxchildren=$MAXCHILDREN \
      socket=$RUNFILES_PATH/fcgi.sock \
      pidfile=$RUNFILES_PATH/fcgi.pid \
      && echo "$DESC started" \
      || echo "Problem starting $DESC"
    chmod 400 $RUNFILES_PATH/fcgi.pid

    # NOTE(ms): This allows anyone to write to your FCGI socket. You may want
    # to tweak this setting and chown the socket to another user (like the user
    # your webserver runs under).
    chmod 777 $RUNFILES_PATH/fcgi.sock
  fi
}

#
#       Function that stops the daemon/service.
#
d_stop() {
    # Killing all Django FastCGI processes running
  pidfile=$RUNFILES_PATH/fcgi.pid
  start-stop-daemon --stop --quiet --pidfile $pidfile \
    && echo "$DESC stopped" \
    || echo "$DESC is not running"
  if [ -f $pidfile ]; then
    rm -f $pidfile
  fi
}

ACTION="$1"
case "$ACTION" in
  start)
    d_start
    ;;

  stop)
    d_stop
    ;;

  restart|force-reload)
    d_stop
    sleep 1
    d_start
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|force-reload}" >&2
    exit 3
    ;;
esac

exit 0

O#! /bin/sh
# /home/pi/Project2/pushover
#
### BEGIN INIT INFO
# Provides:          pushover
# Required-Start:    $remote_fs $network $time
# Required-Stop:     $time
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Send Pushover notifications on boot / shutdown.
# Description:       This will send a Pushover notification when the Raspberry Pi boots and shuts down.
### END INIT INFO

# Some things that run always
touch /var/lock/pushover

TOKEN="Put personal token here"
USER="Put personal key here"
DIST=`hostname`
SOUND=gamelan

# Carry out specific functions when asked to by the system
case "$1" in
  start)
echo "Starting script pushover "
curl -s -o /dev/null \
  --data-urlencode "sound=$SOUND" \
  --data-urlencode "token=$TOKEN" \
  --data-urlencode "user=$USER" \
  --data-urlencode "message=Raspberry Pi ($DIST) has just booted." \
  https://api.pushover.net/1/messages
;;
  stop)
echo "Stopping script pushover"
curl -s -o /dev/null \
  --data-urlencode "sound=$SOUND" \
  --data-urlencode "token=$TOKEN" \
  --data-urlencode "user=$USER" \
  --data-urlencode "message=Raspberry Pi ($DIST) is shutting down!" \
  https://api.pushover.net/1/messages
;;
  *)
echo "Usage: /home/pi/Project2/pushover {start|stop}"
exit 1
;;
esac

exit 0


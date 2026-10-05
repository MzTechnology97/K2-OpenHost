#!/bin/sh
# Benchmark helper (RAM only): switch the three bridges between variants.
#   switch.sh orig                   the user's /tmp/k2-openhost-dual-bridge.py
#   switch.sh new [k2oh-bridge args] the instrumented bridge, e.g. --chunk 256
# Same pid files as the user's bridges (/tmp/k2bridgeN.pid), so k2oh-ctl's
# bridges.sh keeps working on whatever is running.
DIR=/tmp/k2oh-bench
uart() { case $1 in 0) echo ttyS2;; 1) echo ttyS3;; 2) echo ttyS5;; esac; }
running() { ps w | grep -c "[/]dev/ttyGS[0-2] /dev/ttyS"; }

for i in 0 1 2; do
	[ -f /tmp/k2bridge$i.pid ] && kill -TERM "$(cat /tmp/k2bridge$i.pid)" 2>/dev/null
done
n=0
while [ "$(running)" -gt 0 ] && [ $n -lt 30 ]; do sleep 0.1; n=$((n + 1)); done
[ "$(running)" -eq 0 ] || { echo "old bridges still running" >&2; exit 1; }
rm -f /tmp/k2oh-bridge/ttyGS*.json

variant=$1
shift
for i in 0 1 2; do
	if [ "$variant" = orig ]; then
		start-stop-daemon -S -b -m -p /tmp/k2bridge$i.pid -x /usr/bin/python3 -- \
			/tmp/k2-openhost-dual-bridge.py /dev/ttyGS$i /dev/$(uart $i)
	else
		start-stop-daemon -S -b -m -p /tmp/k2bridge$i.pid -x /usr/bin/python3 -- \
			$DIR/k2oh-bridge "$@" /dev/ttyGS$i /dev/$(uart $i)
	fi
done
sleep 0.5
[ "$(running)" -eq 3 ] && echo "bridges: $variant $*"

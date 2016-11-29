#!/bin/bash
set -e
set -x

rm -f /etc/udev/rules.d/75-waggle-cameras.rules
cp 75-waggle-cameras.rules /etc/udev/rules.d/


set +x
echo "run: udevadm control --reload-rules"
echo "     udevadm trigger --subsystem-match=tty --action=add"

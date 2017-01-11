#!/bin/bash
set -e
set -x

rm -f /etc/udev/rules.d/75-waggle-microphone.rules
cp 75-waggle-microphone.rules /etc/udev/rules.d/


set +x
echo "run: udevadm control --reload-rules"
echo "     udevadm trigger --subsystem-match=sound --action=add"

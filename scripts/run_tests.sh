#!/bin/bash

if [[ ! -e /home/waggle/continue_test && ! -e /home/waggle/finish_test ]]; then
  touch /home/waggle/start_test
fi
sudo /bin/systemctl start waggle-test.service

sleep 2

systemctl status waggle-test --no-pager
while [ $? -eq 0 ]; do
  sleep 2
  systemctl status waggle-test --no-pager
done

#!/bin/bash

# Determine root and alternate boot medium root device paths
. /usr/lib/waggle/core/scripts/detect_disk_devices.sh

run_tests() {
  /usr/lib/waggle/guestnode/scripts/test_node.sh \
    > /home/waggle/test_node_GN_${CURRENT_DISK_DEVICE_TYPE}.log
}

generate_report() {
  # Retrieve the eMMC test log
  cp /media/test/home/waggle/test_node_GN_${OTHER_DISK_DEVICE_TYPE}.log /home/waggle/
  sync
}

mount | grep '/media/test' && true
if [ $? -eq 1 ]; then
  mount "${OTHER_DISK_DEVICE}p2" /media/test
fi

start_file=/home/waggle/start_test
continue_file=/home/waggle/continue_test
finish_file=/home/waggle/finish_test
if [ -e ${start_file} ] ; then
  run_tests
  touch /media/test${continue_file}
  sync
  rm ${start_file}
elif [ -e ${continue_file} ]; then
  run_tests
  touch /media/test${finish_file}
  sync
  if [ "${CURRENT_DISK_DEVICE_TYPE}" == "MMC" ]; then
    touch /media/test${finish_file}
    sync
  elif [ "${CURRENT_DISK_DEVICE_TYPE}" == "SD" ]; then
    generate_report
  fi
  rm ${continue_file}
elif [ -e ${finish_file} ]; then
  generate_report
  rm ${finish_file}
fi
echo "Finished"

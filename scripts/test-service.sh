#!/bin/bash

# Determine root and alternate boot medium root device paths
. /usr/lib/waggle/core/scripts/detect_disk_devices.sh

run_tests() {
  /usr/lib/waggle/guestnode/scripts/test_node.sh \
    > /home/waggle/test_node_${ODROID_MODEL}_${CURRENT_DISK_DEVICE_TYPE}.log
}

generate_report() {
  # Retrieve the eMMC test log
  cp /media/test/home/waggle/test_node_XU3_${OTHER_DISK_DEVICE_TYPE}.log /home/waggle/

  scp /home/waggle/test_node_*.log -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node waggle@10.31.81.10:
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
  rm ${start_file}
  if [ "${CURRENT_DISK_DEVICE_TYPE}" == "SD" ]; then
    touch /media/test${continue_file}
  else
    touch /media/test${finish_file}
  fi
elif [ -e ${continue_file} ]; then
  run_tests
  rm ${continue_file}
  touch /media/test${finish_file}
elif [ -e ${finish_file} ]; then
  generate_report
  rm ${finish_file}
fi
echo "Finished"

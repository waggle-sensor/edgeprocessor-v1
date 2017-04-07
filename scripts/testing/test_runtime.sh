#!/bin/bash

set +e

print_result() {
  local test_description=$1
  local result=$2
  local optional=$3
  local software=$4
  local pretext=""
  local posttext=""
  if [ $result == 0 ]; then
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;32m[PASS][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;32m[PASS][0;30;37m ${test_description}"
    fi
  elif [[ ! -z ${optional+x} && $optional == 1 ]]; then
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;33m[FAIL][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;33m[FAIL][0;30;37m ${test_description}"
    fi
  else
    if [[ ! -z ${software+x} && $software == 1 ]]; then
      echo "[0;30;31m[FAIL][0;30;37m [0;30;34m${test_description}[0;30;37m"
    else
      echo "[0;30;31m[FAIL][0;30;37m ${test_description}"
    fi
  fi
}

cat /etc/waggle/node_id | egrep '[0-9a-f]{16}' && true
print_result "Node ID Set" $? 0 1

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
. /usr/lib/waggle/core/scripts/detect_disk_devices.sh
cat /etc/hostname | fgrep "${MAC_STRING}${CURRENT_DISK_DEVICE_TYPE}" && true
print_result "Hostname Set" $? 0 1

units=("waggle-heartbeat" "waggle-core.target" "waggle-platform.target" \
       "waggle-image-producer" "waggle-image-exporter" "rabbitmq-server")
for unit in ${units[@]}; do
  systemctl status $unit | fgrep 'Active: active' && true
  print_result "$unit Service" $? 0 1
done

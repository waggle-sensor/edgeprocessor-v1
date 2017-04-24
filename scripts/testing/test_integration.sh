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

devices=('0d8c:013c' '05a3:9830' '05a3:9520')
device_names=('Microphone' 'Top Camera' 'Bottom Camera')
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  lsusb | grep $device
  print_result "$device_name USB Device Exists" $? 1
done

devices=('waggle_microphone' 'waggle_cam_top' 'waggle_cam_bottom')
device_names=('Microphone' 'Top Camera' 'Bottom Camera')
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  ls /dev/$device
  print_result "$device_name Device Symlink Exists" $? 1
done

devices=('waggle_cam_top' 'waggle_cam_bottom')
device_names=('Top Camera' 'Bottom Camera')
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  # the camera should return an image that is at a bare minimum 1K in size
  expr $(fswebcam -d /dev/$device -S 5 -q - | wc -c) > 1000
  print_result "$device_name Device Image Capture" $? 1
done

#!/bin/bash

set +e

print_result() {
  local test_description=$1
  local result=$2
  local optional=$3
  if [ $result == 0 ]; then
    echo "[0;30;32m[PASS][0;30;37m $test_description"
  elif [[ ! -z ${optional+x} && $optional == 1 ]]; then
    echo "[0;30;33m[FAIL][0;30;37m $test_description"
  else
    echo "[0;30;31m[FAIL][0;30;37m $test_description"
  fi
}

shadow='root:$6$D3j0Te22$md6NULvJPliwvAhK2BlL96XCsJ0KdTnPqNdufDWgyU5k6Nc3M88qO64WCKKTLZry1GgKhGE95L5ZA1i2VFQGn.:17079:0:99999:7:::'
fgrep $shadow /etc/shadow
print_result "AoT Root Password Set" $?

keys=('from="10.31.81.0/24" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_guest_node_key')
echo ${keys[@]}
key_names=('AoT Guest Key')
for i in $(seq 0 `expr ${#keys[@]} - 1`); do
  key=${keys[i]}
  key_name=${key_names[i]}
  fgrep "$key" /home/waggle/.ssh/authorized_keys
  print_result "$key_name Auth" $?
done

grep '^sudo:x:27:$' /etc/group
print_result "sudo Disabled" $?

directories=("/etc/waggle" "/usr/lib/waggle" "/usr/lib/waggle/core" "/usr/lib/waggle/plugin_manager" "/usr/lib/waggle/nodecontroller" \
             "/usr/lib/waggle/SSL" "/usr/lib/waggle/SSL/guest" "/usr/lib/waggle/SSL/node" "/usr/lib/waggle/SSL/waggleca")
for dir in ${directories[@]}; do
  [ -e $dir ]
  print_result "$dir Directory" $?
done

perms=$(stat -c '%U %G %a' /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node)
[ "$perms" == "root root 600" ]
print_result "Guest Key Permissions" $?

ifconfig | fgrep "          inet addr:10.31.81.51  Bcast:10.31.81.255  Mask:255.255.255.0" && true
print_result "Built-in Ethernet IP Address" $?

line_count=$(cat /etc/ssh/sshd_config | fgrep -e 'ListenAddress 127.0.0.1' -e 'ListenAddress 10.31.81.51' | wc -l)
[ $line_count -eq 2 ]
print_result "sshd Listen Addresses" $?

cat /etc/ssh/sshd_config | fgrep 'PermitRootLogin no' && true
print_result "sshd No Root Login" $?

cat /etc/waggle/node_id | egrep '[0-9a-f]{16}' && true
print_result "Node ID Set" $?

. /usr/lib/waggle/core/scripts/detect_mac_address.sh
. /usr/lib/waggle/core/scripts/detect_disk_devices.sh

cat /etc/hostname | fgrep "${MAC_STRING}${CURRENT_DISK_DEVICE_TYPE}" && true
print_result "Hostname Set" $?

parted -s ${CURRENT_DISK_DEVICE}p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB' && true
print_result "SD Resize" $?

parted -s ${OTHER_DISK_DEVICE}p2 print | grep --color=never -e ext | awk '{print $3}' | egrep '15\.[0-9]GB' && true
print_result "Recovery to eMMC" $?

units=("waggle-epoch" "waggle-heartbeat")
for unit in ${units[@]}; do
  systemctl status $unit | fgrep 'Active: active (running)' && true
  print_result "$unit Service" $?
done

ssh -i /usr/lib/waggle/SSL/guest/id_rsa_waggle_aot_guest_node waggle@10.31.81.10 \
    -o "StrictHostKeyChecking no" -o "PasswordAuthentication no" -o "ConnectTimeout 2" /bin/date
print_result "ssh to NC" $?

devices=('0d8c:013c' '05a3:9830' '05a3:9520')
device_names=('Microphone' 'Top Camera' 'Bottom Camera')
for i in $(seq 0 `expr ${#devices[@]} - 1`); do
  device=${devices[i]}
  device_name=${device_names[i]}
  lsusb | grep $device && true
  print_result "$device_name USB Device" $? 1
done

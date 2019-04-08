#!/bin/bash
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# this will make sure that an empty eMMC card will get the waggle image
# and try to recover uSD to make the uSD 3 partitions
echo "recover me" > /wagglerw/do_recovery
touch /root/waggle_platform_starter

echo -e "10.31.81.10\tnodecontroller" >> /etc/hosts

# Restrict SSH connections to local port bindings and ethernet card subnet
sed -i 's/^#ListenAddress ::$/ListenAddress 127.0.0.1/' /etc/ssh/sshd_config
sed -i 's/^#ListenAddress 0.0.0.0$/ListenAddress 10.31.81.51/' /etc/ssh/sshd_config 

# disable all password authentication
sed -i 's/^#PasswordAuthentication yes$/PasswordAuthentication no/' /etc/ssh/sshd_config

if [ $(lsb_release -r | tr "\t" " " | sed "s/\ //g"  | cut -d ":" -f 2) = "16.04" ]; then
  # NetworkManager will try to manage any interfaces *not* listed in
  # /etc/network/interfaces, so just replace it with what we want
  cp ${script_dir}/../etc/network/interfaces /etc/network/interfaces
elif [ $(lsb_release -r | tr "\t" " " | sed "s/\ //g"  | cut -d ":" -f 2) = "18.04" ]; then
  # Ubuntu 18.04 uses netplan https://netplan.io/
  cp ${script_dir}/../etc/netplan/50-waggle.yaml /etc/netplan/50-waggle.yaml
fi

rm -rf /etc/sudoers.d/waggle*
cp ${script_dir}/../etc/sudoers.d/* /etc/sudoers.d/

echo > /home/waggle/.ssh/authorized_keys

# add AoT Edge Processor node cert to root authorized_keys files
mkdir -p /root/.ssh
chmod 744 /root/.ssh
echo "from=\"10.31.81.0/24\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_edge_processor_key" > /root/.ssh/authorized_keys
echo "from=\"10.31.81.0/24\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsYPMSrC6k33vqzulXSx8141ThfNKXiyFxwNxnudLCa0NuE1SZTMad2ottHIgA9ZawcSWOVkAlwkvufh4gjA8LVZYAVGYHHfU/+MyxhK0InI8+FHOPKAnpno1wsTRxU92xYAYIwAz0tFmhhIgnraBfkJAVKrdezE/9P6EmtKCiJs9At8FjpQPUamuXOy9/yyFOxb8DuDfYepr1M0u1vn8nTGjXUrj7BZ45VJq33nNIVu8ScEdCN1b6PlCzLVylRWnt8+A99VHwtVwt2vHmCZhMJa3XE7GqoFocpp8TxbxsnzSuEGMs3QzwR9vHZT9ICq6O8C1YOG6JSxuXupUUrHgd AoT_key" >> /root/.ssh/authorized_keys

# Updating path to ep scripts in /root/.bashrc
echo "PATH=$PATH:/usr/lib/waggle/edge_processor/scripts:/usr/lib/waggle/core/scripts" >> /root/.bashrc
echo "alias disks='blkid | sort -r'" >> /root/.bashrc

#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# this will make sure that an empty eMMC card will get the waggle image
touch /root/do_recovery

echo -e "10.31.81.10\tnodecontroller" >> /etc/hosts

# Restrict SSH connections to local port bindings and ethernet card subnet
sed -i 's/^#ListenAddress ::$/ListenAddress 127.0.0.1/' /etc/ssh/sshd_config
sed -i 's/^#ListenAddress 0.0.0.0$/ListenAddress 10.31.81.51/' /etc/ssh/sshd_config 

# NetworkManager will try to manage any interfaces *not* listed in
# /etc/network/interfaces, so just replace it with what we want
cp ${script_dir}/../etc/network/interfaces /etc/network/interfaces

rm -rf /etc/sudoers.d/waggle*
cp ${script_dir}/../etc/sudoers.d/* /etc/sudoers.d/

echo > /home/waggle/.ssh/authorized_keys

# add AoT guest node cert to root authorized_keys files
mkdir -p /root/.ssh
chmod 744 /root/.ssh
echo "from=\"10.31.81.0/24\" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4ohQv1Qksg2sLIqpvjJuZEsIkeLfbPusEaJQerRCqI71g8hwBkED3BBv5FehLcezTg+cFJFhf2vBGV5SbV0NzbouIM+n0lAr6+Ei/XYjO0B1juDm6cUmloD4HSzQWv+cSyNmb7aXjup7V0GP1DZH3zlmvwguhMUTDrWxQxDpoV28m72aZ4qPH7VmQIeN/JG3BF9b9F8P4myOPGuk5XTjY1rVG+1Tm2mxw0L3WuL6w3DsiUrvlXsGE72KcyFBDiFqOHIdnIYWXDLZz61KXctVLPVLMevwU0YyWg70F9pb0d2LZt7Ztp9GxXBRj5WnU9IClaRh58RsYGhPjdfGuoC3P AoT_guest_node_key" > /root/.ssh/authorized_keys


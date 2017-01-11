##Set up static /dev endpoints to access microphone##

The waggle-registered microphone will be recognized. To set up run install.sh script.

##Setup:##

```bash
sudo ./install.sh
```

After the above step, when the microphone is connected, the link __waggle_microphone__ indicates the microphone in the system under /dev. When use the microphone refer to the microphone name saved in __/etc/waggle/waggle_name_microphone__. For example - 
```bash
$ls -l /dev/waggle_microphone /etc/waggle/waggle_name_microphone
lrwxrwxrwx 1 root root 13 Dec  1 20:53 /dev/waggle_microphone -> snd/controlC1
-rw-r--r-- 1 root root 21 Dec  1 20:53 /etc/waggle/waggle_name_microphone

$cat /etc/waggle/waggle_name_microphone
USB PnP Sound Device
```
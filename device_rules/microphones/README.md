##Set up static /dev endpoints to access Cameras##

The two cameras, known as upward and downward cameras, need to be distinguished in order for the processors to properly handle data regarding their characteristics (e.g., orientation and direction). To set up run install.sh script.

##Setup:##

```bash
sudo ./install.sh
```

After the above steps, when cameras are connected,  they should be available for access at __/dev/waggle_top_cam__ and __/dev/waggle_bottom_cam__ respectively. The above two are symbolic links to the standard Linux ttyACMX naming scheming under /dev. For example - 
```bash
$ls -l /dev/waggle_coresense /dev/waggle_sysmon
lrwxrwxrwx 1 root root 7 Feb 29 11:30 /dev/waggle_coresense -> ttyACM0 
lrwxrwxrwx 1 root root 7 Feb 29 11:30 /dev/waggle_sysmon -> ttyACM1
```







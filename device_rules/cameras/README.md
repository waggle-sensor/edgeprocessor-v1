##Set up static /dev endpoints to access Cameras##

The two cameras, the upward and downward cameras, need to be distinguished in order for plugins to properly handle data regarding their physical characteristics (e.g., orientation, direction, lens). To set up run install.sh script.

##Setup:##

```bash
sudo ./install.sh
```

After the above steps, when cameras are connected, they should be available for access at __/dev/waggle_cam_idx_top__ and __/dev/waggle_cam_idx_bottom__ respectively. The above two are symbolic links to the standard Linux videoX naming scheming under /dev. For example - 
```bash
$ls -l /dev/waggle_cam_bottom /dev/waggle_cam_top
lrwxrwxrwx 1 root root 6 Dec  1 20:18 /dev/waggle_cam_bottom -> video0
lrwxrwxrwx 1 root root 6 Dec  1 20:18 /dev/waggle_cam_top -> video1
```
For openCV users refer to the files 'waggle_cam_idx_top' and 'waggle_cam_idx_bottom' under '/etc/waggle' to find out the index of the device. The files contain device number openCV can use to use the particular camera. For example index of the top camera is -
```bash
$ cat /etc/waggle/waggle_cam_idx_top
1

# in openCV (for Python)
top_cam_index = int(open('/etc/waggle/waggle_cam_idx_top', 'r').read())
device = cv2.VideoCapture(top_cam_index)
...
```





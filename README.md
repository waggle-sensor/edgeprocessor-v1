# edge_processor
configuration and services specific to the Guest Node

##Static Camera Device Names##

The two cameras, upward and downward, need to be distinguished in order for plugins to properly handle data regarding their physical characteristics (e.g., orientation, direction, lens). Udev rules are provided that map the system's device names for the standard AoT cameras in /dev to static names that identify their physical position on the node.

When the cameras are connected, they should be available for access at `/dev/waggle_cam_top` and `/dev/waggle_cam_bottom`. The above two are symbolic links to the standard Linux video# naming scheming under /dev. For example - 
```bash
$ ls -l /dev/waggle_cam_bottom /dev/waggle_cam_*
lrwxrwxrwx 1 root root 6 Dec  1 20:18 /dev/waggle_cam_bottom -> video0
lrwxrwxrwx 1 root root 6 Dec  1 20:18 /dev/waggle_cam_top -> video1
```
OpenCV uses the system video device indicies, so the files 'waggle_cam_top_idx' and 'waggle_cam_bottom_idx' under '/etc/waggle' are populated with the index of the associated device. For example, the index of the top camera is
```bash
$ cat /etc/waggle/waggle_cam_top_idx
1
```

Using OpenCV (for Python) one can reference the desired camera as follows:
```
top_camera_index = int(open('/etc/waggle/waggle_cam_top_idx', 'r').read())
device = cv2.VideoCapture(top_camera_index)
...
```

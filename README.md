# guestnode
configuration and services specific to the Guest Node

# Installation of OpenCL for Mali T-62X

The base Waggle image for Odroid XU4 (version 2.1.4) comes with kernel driver (version 10.1) for Mali T-628. 

* NOTE: To check if the system has kernel driver for the GPU
```bash
$ ls -l /dev/mali*
crwxrwxrwx 1 root root 10, 61 Feb 11  2016 /dev/mali0
```

To be able to use the GPU in applications or OpenCV OpenCL library needs to be installed. To install OpenCL library

```bash
cd ~
git clone https://github.com/mdrjr/5422_mali.git
cd 5422_mali
# change the version to r9 because the 10.1 version of the kernel driver is not compatible with r14, which is the latest
git checkout r9p0
cd fbdev
make
```

After the installation the libraries should appear under __/usr/lib/arm-linux-gnueabihf/mali-egl__.
```
$ ls -l /usr/lib/arm-linux-gnueabihf/mali-egl/
total 18140
-rw-r--r-- 1 root root       38 Jan  4 21:09 ld.so.conf
-rwxr-xr-x 1 root root     4862 Jan  5 23:11 libEGL.so
lrwxrwxrwx 1 root root        9 Jan  4 21:09 libEGL.so.1 -> libEGL.so
lrwxrwxrwx 1 root root        9 Jan  4 21:09 libEGL.so.1.4 -> libEGL.so
-rwxr-xr-x 1 root root     4862 Jan  5 23:11 libGLESv1_CM.so
lrwxrwxrwx 1 root root       15 Jan  4 21:09 libGLESv1_CM.so.1 -> libGLESv1_CM.so
lrwxrwxrwx 1 root root       15 Jan  4 21:09 libGLESv1_CM.so.1.1 -> libGLESv1_CM.so
-rwxr-xr-x 1 root root     4862 Jan  5 23:11 libGLESv2.so
lrwxrwxrwx 1 root root       12 Jan  4 21:09 libGLESv2.so.2 -> libGLESv2.so
lrwxrwxrwx 1 root root       12 Jan  4 21:09 libGLESv2.so.2.0 -> libGLESv2.so
-rwxr-xr-x 1 root root 18534752 Jan  5 23:11 libmali.so
-rwxr-xr-x 1 root root     4862 Jan  5 23:11 libOpenCL.so
lrwxrwxrwx 1 root root       12 Jan  4 21:09 libOpenCL.so.1 -> libOpenCL.so
lrwxrwxrwx 1 root root       12 Jan  4 21:09 libOpenCL.so.1.1 -> libOpenCL.so
```

<!--
waggle_topic=IGNORE
-->

# Libraries and Packages Support

We expect that many user-driven processors would actively use some notable libraries (e.g., OpenCV, Caffe, Tensorflow, and more) for intensive computation on image/audio processing. Moreover, some of the processors would need to utilize GPU cores to speed up the process. Waggle as a platform should, therefore, support such libraries and provide ways for the users to utilize the libraries. This document covers what libraries and tools are available on the Edge processor.

## OpenCV

We have supported OpenCV along with OpenCL libraries (via Dynamic load) since Waggle 2.8.0. As OpenCV 3.4.1 (Feb 2018) was released, Waggle 2.9.0 supports the latest version of OpenCV. In Waggle 2.9.0, we enabled video4linux library so that OpenCV VideoCapture supports v4l2 as a backend for video streaming.

Below is the cmake command we used. Note that we have installed `libv4l2-dev` prior to the cmake command. Note also that the path of the options may differ in your environment.

```
# To support libv4l2
apt-get install libv4l-dev

cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=/root/repo/opencv_contrib/modules \
      -D PYTHON3_EXECUTABLE=/usr/bin/python3 \
      -D PYTHON_INCLUDE_DIR=/usr/include/python3.5 \
      -D PYTHON_INCLUDE_DIR2=/usr/include/arm-linux-gnueabihf/python3.5m \
      -D PYTHON_LIBRARY=/usr/lib/arm-linux-gnueabihf/libpython3.5m.so \
      -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/local/lib/python3.5/dist-packages/numpy/core/include \
      -D WITH_FFMPEG=ON \
      -D WITH_LIBV4L=ON \
      -D WITH_OPENCL=ON \
      -D CPACK_BINARY_DEB:BOOL=ON ..
```
You will get something similar to...

```
-- General configuration for OpenCV 3.4.1 =====================================
--   Version control:               3.4.1
-- 
--   Extra modules:
--     Location (extra):            /root/repo/opencv_contrib/modules
--     Version control (extra):     3.4.1
-- 
--   Platform:
--     Timestamp:                   2018-02-28T20:28:07Z
--     Host:                        Linux 3.10.96-113 armv7l
--     CMake:                       3.5.1
--     CMake generator:             Unix Makefiles
--     CMake build tool:            /usr/bin/make
--     Configuration:               Release
-- 
--   CPU/HW features:
--     Baseline:
--       requested:                 DETECT
--       disabled:                  VFPV3 NEON
-- 
--   C/C++:
--     Built as dynamic libs?:      YES
--     C++ Compiler:                /usr/bin/c++  (ver 5.4.0)
--     C++ flags (Release):         -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-narrowing -Wno-delete-non-virtual-dtor -Wno-comment -fdiagnostics-show-option -pthread -fomit-frame-pointer -ffunction-sections -fdata-sections  -mfp16-format=ieee -fvisibility=hidden -fvisibility-inlines-hidden -O3 -DNDEBUG  -DNDEBUG
--     C++ flags (Debug):           -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-narrowing -Wno-delete-non-virtual-dtor -Wno-comment -fdiagnostics-show-option -pthread -fomit-frame-pointer -ffunction-sections -fdata-sections  -mfp16-format=ieee -fvisibility=hidden -fvisibility-inlines-hidden -g  -O0 -DDEBUG -D_DEBUG
--     C Compiler:                  /usr/bin/cc
--     C flags (Release):           -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wuninitialized -Winit-self -Wno-narrowing -Wno-comment -fdiagnostics-show-option -pthread -fomit-frame-pointer -ffunction-sections -fdata-sections  -mfp16-format=ieee -fvisibility=hidden -O3 -DNDEBUG  -DNDEBUG
--     C flags (Debug):             -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wuninitialized -Winit-self -Wno-narrowing -Wno-comment -fdiagnostics-show-option -pthread -fomit-frame-pointer -ffunction-sections -fdata-sections  -mfp16-format=ieee -fvisibility=hidden -g  -O0 -DDEBUG -D_DEBUG
--     Linker flags (Release):      
--     Linker flags (Debug):        
--     ccache:                      NO
--     Precompiled headers:         YES
--     Extra dependencies:          dl m pthread rt
--     3rdparty dependencies:
-- 
--   OpenCV modules:
--     To be built:                 aruco bgsegm bioinspired calib3d ccalib core datasets dnn dnn_objdetect dpm face features2d flann freetype fuzzy hfs highgui img_hash imgcodecs imgproc java_bindings_generator line_descriptor ml objdetect optflow phase_unwrapping photo plot python3 python_bindings_generator reg rgbd saliency shape stereo stitching structured_light superres surface_matching text tracking ts video videoio videostab xfeatures2d ximgproc xobjdetect xphoto
--     Disabled:                    js world
--     Disabled by dependency:      -
--     Unavailable:                 cnn_3dobj cudaarithm cudabgsegm cudacodec cudafeatures2d cudafilters cudaimgproc cudalegacy cudaobjdetect cudaoptflow cudastereo cudawarping cudev cvv dnn_modern hdf java matlab ovis python2 sfm viz
--     Applications:                tests perf_tests apps
--     Documentation:               NO
--     Non-free algorithms:         NO
-- 
--   GUI: 
--     GTK+:                        YES (ver 2.24.30)
--       GThread :                  YES (ver 2.48.2)
--       GtkGlExt:                  NO
--     VTK support:                 NO
-- 
--   Media I/O: 
--     ZLib:                        /usr/lib/arm-linux-gnueabihf/libz.so (ver 1.2.8)
--     JPEG:                        /usr/lib/arm-linux-gnueabihf/libjpeg.so (ver )
--     WEBP:                        build (ver encoder: 0x020e)
--     PNG:                         /usr/lib/arm-linux-gnueabihf/libpng.so (ver 1.2.54)
--     TIFF:                        /usr/lib/arm-linux-gnueabihf/libtiff.so (ver 42 / 4.0.6)
--     JPEG 2000:                   /usr/lib/arm-linux-gnueabihf/libjasper.so (ver 1.900.1)
--     OpenEXR:                     build (ver 1.7.1)
-- 
--   Video I/O:
--     DC1394:                      YES (ver 2.2.4)
--     FFMPEG:                      YES
--       avcodec:                   YES (ver 56.60.100)
--       avformat:                  YES (ver 56.40.101)
--       avutil:                    YES (ver 54.31.100)
--       swscale:                   YES (ver 3.1.101)
--       avresample:                NO
--     GStreamer:                   NO
--     libv4l/libv4l2:              1.10.0 / 1.10.0
--     v4l/v4l2:                    linux/videodev2.h
--     gPhoto2:                     NO
-- 
--   Parallel framework:            pthreads
-- 
--   Trace:                         YES (built-in)
-- 
--   Other third-party libraries:
--     Lapack:                      NO
--     Eigen:                       NO
--     Custom HAL:                  YES (carotene (ver 0.0.1))
--     Protobuf:                    build (3.5.1)
-- 
--   NVIDIA CUDA:                   NO
-- 
--   OpenCL:                        YES (no extra features)
--     Include path:                /root/repo/opencv/3rdparty/include/opencl/1.2
--     Link libraries:              Dynamic load
-- 
--   Python 3:
--     Interpreter:                 /usr/bin/python3 (ver 3.5.2)
--     Libraries:                   /usr/lib/arm-linux-gnueabihf/libpython3.5m.so (ver 3.5.2)
--     numpy:                       /usr/local/lib/python3.5/dist-packages/numpy/core/include (ver 1.14.1)
--     packages path:               lib/python3.5/dist-packages
-- 
--   Python (for build):            /usr/bin/python2.7
-- 
--   Java:                          
--     ant:                         NO
--     JNI:                         NO
--     Java wrappers:               NO
--     Java tests:                  NO
-- 
--   Matlab:                        NO
-- 
--   Install to:                    /usr/local
-- -----------------------------------------------------------------
-- 
-- Configuring done
-- Generating done
```

To compile and make package, do

1) `make -j8; make install` to compile and install OpenCV libraries into your system
2) `make package` to compile OpenCV libraries and package them into a debian package

From 3.4.1, OpenCV supports CNN models imported from Tensorflow and Caffe [check here](https://github.com/opencv/opencv/wiki/ChangeLog#version341). An example that uses Tensorflow model in OpenCV can be found [here](https://github.com/opencv/opencv/wiki/TensorFlow-Object-Detection-API). [Here](https://github.com/waggle-sensor/plugin_manager/tree/master/plugins/image_detector) shows Waggle image detection plugin that uses OpenCV DNN module.

## OpenCL

ODROID XU4 has Mali T628 GPU processor which has 4 processing units. OpenCL 1.2 for Mali T series is included in the linux package support such that it is supported from Waggle 2.9.0.
```
$ opencv_version -opencl
3.4.1
[ INFO:0] Initialize OpenCL runtime...
OpenCL Platforms: 
    ARM Platform
        iGPU: Mali-T628 (OpenCL 1.2 v1.r12p0-04rel0.03af15950392f3702b248717f4938b82)
        iGPU: Mali-T628 (OpenCL 1.2 v1.r12p0-04rel0.03af15950392f3702b248717f4938b82)
Current OpenCL device: 
    Type = iGPU
    Name = Mali-T628
    Version = OpenCL 1.2 v1.r12p0-04rel0.03af15950392f3702b248717f4938b82
    Driver version = 1.2
    Address bits = 64
    Compute units = 4
    Max work group size = 256
    Local memory size = 32 KB
    Max memory allocation size = 498 MB 386 KB
    Double support = Yes
    Host unified memory = Yes
    Device extensions:
        cl_khr_global_int32_base_atomics
        cl_khr_global_int32_extended_atomics
        cl_khr_local_int32_base_atomics
        cl_khr_local_int32_extended_atomics
        cl_khr_byte_addressable_store
        cl_khr_3d_image_writes
        cl_khr_fp64
        cl_khr_int64_base_atomics
        cl_khr_int64_extended_atomics
        cl_khr_fp16
        cl_khr_gl_sharing
        cl_khr_icd
        cl_khr_egl_event
        cl_khr_egl_image
        cl_arm_core_id
        cl_arm_printf
        cl_arm_thread_limit_hint
        cl_arm_non_uniform_work_group_size
        cl_arm_import_memory
    Has AMD Blas = No
    Has AMD Fft = No
    Preferred vector width char = 16
    Preferred vector width short = 8
    Preferred vector width int = 4
    Preferred vector width long = 2
    Preferred vector width float = 4
    Preferred vector width double = 2
```

## Tensorflow

Tensorflow is a tool that allows to run networks which requires high computation. One of the major uses of the tool is in image classification. Deep networks that are described and compiled in Tensorflow have provided significant accuracy on object detection and classification. Tensorflow 1.8.0 is added to Waggle 2.9.0 and can only be imported in Python3.5. At this moment, CUDA / OpenCL supports are _NOT_ available.

To compile and pakcage Tensorflow, do

_NOTE: The instructions below is based on [tensorflow-on-arm](https://github.com/lhelontra/tensorflow-on-arm) and details are available in the link. The license information is [here](https://github.com/lhelontra/tensorflow-on-arm/blob/master/LICENSE)_
```
# Copy pyconfig.h from target (ARMv7) to the host system
# For example,
$ mkdir -p /usr/include/arm-linux-gnueabihf/python3.5
$ scp TARGET_USERNAME@TARGET_URL:/usr/include/arm-linux-gnueabihf/python3.5/pyconfig.h /usr/include/arm-linux-gnueabihf/python3.5/pyconfig.h

$ git clone https://github.com/lhelontra/tensorflow-on-arm.git
$ cd tensorflow-on-arm/build_tensorflow
$ git checkout v1.8.0
$ ./build_tensorflow configs/rpi.conf
$ ls /tmp/tensorflow_pkg
tensorflow-1.8.0-cp35-none-any.whl
```

Note that the target system will need libstdc++6 6.X or higher as the cross toolchain used in this compilation is 6.3.1. Note also that Waggle 2.9.0 or higher already meets the requirement.

## Caffe

Will be accommodated in Waggle...

# 背景
最近需要在Android应用程序上使用OpenCV，官方提供的预编译库实在是太大了，有100多MB。因为我们只用到了OpenCV中有限的函数，于是决定从源码编译出一个轻量级的OpenCV安卓库。

# 安装依赖
- Android NDK
```
wget https://dl.google.com/android/repository/android-ndk-r19c-linux-x86_64.zip
unzip android-ndk-r19c-linux-x86_64.zip
export ANDROID_NDK=$(pwd)/android-ndk-r19c
```
- OpenCV源码
```
git clone https://github.com/opencv/opencv
```
# 编译
1，使用cmake进行构建

这次先编译静态库，命令如下：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/build$ cmake \
-DBUILD_opencv_ittnotify=OFF \
-DBUILD_ITT=OFF \
-DWITH_CUDA=OFF \
-DWITH_OPENCL=OFF \
-DWITH_OPENCLAMDFFT=OFF \
-DWITH_OPENCLAMDBLAS=OFF \
-DWITH_VA_INTEL=OFF \
-DCPU_BASELINE_DISABLE=ON \
-DENABLE_SSE=OFF \
-DENABLE_SSE2=OFF \
-DBUILD_TESTING=OFF \
-DBUILD_PERF_TESTS=OFF \
-DBUILD_TESTS=OFF \
-DCMAKE_BUILD_TYPE=RELEASE \
-DBUILD_EXAMPLES=OFF \
-DBUILD_DOCS=OFF \
-DBUILD_opencv_apps=OFF \
-DBUILD_SHARED_LIBS=OFF \
-DOpenCV_STATIC=ON \
-DWITH_1394=OFF \
-DWITH_ARITH_DEC=OFF \
-DWITH_ARITH_ENC=OFF \
-DWITH_CUBLAS=OFF \
-DWITH_CUFFT=OFF \
-DWITH_FFMPEG=OFF \
-DWITH_GDAL=OFF \
-DWITH_GSTREAMER=OFF \
-DWITH_GTK=OFF \
-DWITH_HALIDE=OFF \
-DWITH_JASPER=OFF \
-DWITH_NVCUVID=OFF \
-DWITH_OPENEXR=OFF \
-DWITH_PROTOBUF=OFF \
-DWITH_PTHREADS_PF=OFF \
-DWITH_QUIRC=OFF \
-DWITH_V4L=OFF \
-DWITH_WEBP=OFF \
-DBUILD_LIST=core,imgproc \
-DANDROID_NDK=/app/gemfield/android-ndk-r19c \
-DCMAKE_TOOLCHAIN_FILE=/app/gemfield/android-ndk-r19c/build/cmake/android.toolchain.cmake \
-DANDROID_NATIVE_API_LEVEL=android-21 \
-DBUILD_JAVA=ON \
-DBUILD_ANDROID_EXAMPLES=OFF \
-DBUILD_ANDROID_PROJECTS=OFF \
-DANDROID_STL=c++_shared \
-DANDROID_ABI=arm64-v8a \
-DBUILD_FAT_JAVA_LIB=ON \
-DCMAKE_INSTALL_PREFIX=/app/gemfield/opencv-4.4.0/opencv_v8 \
..
```
上述参数的简单说明：
```
NDK 通过cmake-toolchains(cmake工具链文件)支持 CMake。工具链文件是用于自定义交叉编译工具链行为的 CMake 文件。用于 NDK 的工具链文件位于 NDK目录下的<NDK>/build/cmake/android.toolchain.cmake，比如上面参数中的：
-DCMAKE_TOOLCHAIN_FILE=/app/gemfield/android-ndk-r19c/build/cmake/android.toolchain.cmake
DANDROID_ARM_NEON用来指定 armeabi-v7a 启用或停用 NEON。对其他 ABI 没有影响。对于 API 级别（minSdkVersion或ANDROID_PLATFORM）23 或更高级别，默认为 true，否则为 false。要强制 armeabi-v7a 始终使用 Neon 支持构建，请传递-DANDROID_ARM_NEON=TRUE ；
ANDROID_ABI，用来指定目标 ABI。
armeabi-v7a	
armeabi-v7a with NEON	与 -DANDROID_ABI=armeabi-v7a -DANDROID_ARM_NEON=ON 相同。
arm64-v8a	
x86	
x86_64
ANDROID_PLATFORM，指定应用或库所支持的最低 API 级别。此值对应于应用的minSdkVersion。当直接调用 CMake 时，此值默认为所使用的 NDK 支持的最低 API 级别。例如，对于 NDK r20，此值默认为 API 级别 16；
ANDROID_STL，指定要为此应用使用的 STL。默认情况下将使用 c++_static ：
值	Gemfield的解释
c++_shared	libc++ 的共享库变体
c++_static	libc++ 的静态库变体
无	不支持 C++ 标准库
系统	系统 STL
上述参数中使用了：-DANDROID_STL=c++_shared。
```

2，cmake输出的摘要

比如编译器用的是clang++、使用C++11标准等：
```
-- General configuration for OpenCV 4.4.0 =====================================
--   Platform:
--     Host:                        Linux 5.4.0-42-syszux x86_64
--     Target:                      Android 1 aarch64
--     CMake:                       3.16.3
--     CMake generator:             Unix Makefiles
--     CMake build tool:            /usr/bin/make
--     Configuration:               RELEASE
-- 
--   CPU/HW features:
--     Baseline:                    NEON FP16
--       disabled:                  ON SSE SSE2
-- 
--   C/C++:
--     Built as dynamic libs?:      NO
--     C++ standard:                11
--     C++ Compiler:                /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/bin/clang++  (ver 8.0)
--     C++ flags (Release):         -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -fno-addrsig -Wa,--noexecstack -Wformat -Werror=format-security -stdlib=libc++    -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Winconsistent-missing-override -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments    -fvisibility=hidden -fvisibility-inlines-hidden -O2 -DNDEBUG   -DNDEBUG
--     C++ flags (Debug):           -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -fno-addrsig -Wa,--noexecstack -Wformat -Werror=format-security -stdlib=libc++    -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Winconsistent-missing-override -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments    -fvisibility=hidden -fvisibility-inlines-hidden -O0 -fno-limit-debug-info   -DDEBUG -D_DEBUG
--     C Compiler:                  /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/bin/clang
--     C flags (Release):           -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -fno-addrsig -Wa,--noexecstack -Wformat -Werror=format-security    -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Winconsistent-missing-override -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments    -fvisibility=hidden -fvisibility-inlines-hidden -O2 -DNDEBUG   -DNDEBUG
--     C flags (Debug):             -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -fno-addrsig -Wa,--noexecstack -Wformat -Werror=format-security    -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Winconsistent-missing-override -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments    -fvisibility=hidden -fvisibility-inlines-hidden -O0 -fno-limit-debug-info   -DDEBUG -D_DEBUG
--     Linker flags (Release):      -Wl,--exclude-libs,libgcc.a -Wl,--exclude-libs,libatomic.a -Wl,--build-id -Wl,--warn-shared-textrel -Wl,--fatal-warnings -Wl,--no-undefined -Qunused-arguments -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now   -Wl,--as-needed  
--     Linker flags (Debug):        -Wl,--exclude-libs,libgcc.a -Wl,--exclude-libs,libatomic.a -Wl,--build-id -Wl,--warn-shared-textrel -Wl,--fatal-warnings -Wl,--no-undefined -Qunused-arguments -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now   -Wl,--as-needed  
--     Extra dependencies:          /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/libz.a dl m log
--     3rdparty dependencies:       libcpufeatures tegra_hal
-- 
--   OpenCV modules:
--     To be built:                 core imgproc
--     Disabled:                    world
--     Disabled by dependency:      calib3d features2d flann gapi highgui imgcodecs java_bindings_generator ml objdetect photo stitching video videoio
--     Unavailable:                 dnn java js python2 python3 ts
-- 
--   Android NDK:                   /app/gemfield/android-ndk-r19c (ver 19.2.5345600)
--     Android ABI:                 arm64-v8a
--     NDK toolchain:               aarch64-linux-android-clang
--     STL type:                    c++_shared
--     Native API level:            21
--   Android SDK:                   not used, projects are not built
-- 
--   Media I/O: 
--     ZLib:                        /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/libz.a (ver 1.2.7)
--     JPEG:                        build-libjpeg-turbo (ver 2.0.5-62)
--     PNG:                         build (ver 1.6.37)
--     TIFF:                        build (ver 42 - 4.0.10)
--     JPEG 2000:                   NO
--     HDR:                         YES
--     SUNRASTER:                   YES
--     PXM:                         YES
--     PFM:                         YES
-- 
-- 
--   Other third-party libraries:
--     Custom HAL:                  YES (carotene (ver 0.0.1))
-- 
--   Python (for build):            /usr/bin/python2.7
-- 
--   Java:                          export all functions
--     ant:                         NO
--     Java wrappers:               NO
--     Java tests:                  NO
-- 
--   Install to:                    /app/gemfield/opencv-4.4.0/opencv_v8
```
可以看到NDK默认是加上了debug flag "-g"的，哪怕是release。

3，编译的三方库和opencv的模块（就2个：core和imgproc）

如下所示：
```
3rdparty/libjpeg-turbo
3rdparty/libtiff
3rdparty/libpng
3rdparty/carotene
3rdparty/ade
modules/core
modules/imgproc
```
4，真正开始编译

使用make命令：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/build$ make VERBOSE=1
```
5，安装
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/build$ make install
将会安装在/app/gemfield/opencv-4.4.0/opencv_v8/目录下。有所需的头文件和编译好的静态库：

./sdk/native/staticlibs/arm64-v8a/libopencv_core.a
./sdk/native/staticlibs/arm64-v8a/libopencv_imgproc.a
./sdk/native/3rdparty/libs/arm64-v8a/libtegra_hal.a
./sdk/native/3rdparty/libs/arm64-v8a/liblibtiff.a
./sdk/native/3rdparty/libs/arm64-v8a/libcpufeatures.a
./sdk/native/3rdparty/libs/arm64-v8a/liblibpng.a
./sdk/native/3rdparty/libs/arm64-v8a/liblibjpeg-turbo.a
./sdk/native/3rdparty/libs/arm64-v8a/libade.a
```
这样编译出来的库的大小有50多MB，不符合Gemfield的初心。

降低库的大小
上述步骤编译出来的opencv库很大，一大原因是因为NDK默认加了debug flag导致的，另一大原因是没有strip符号导致的。

我们先手工去掉-g flag，使用如下的临时解决方案：
```
-DCMAKE_CXX_FLAGS_RELEASE=-g0
```
整体命令如下（注意，ANDROID_STL改为默认值，也就是static的了）：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/build$ cmake \
-DBUILD_opencv_ittnotify=OFF \
-DBUILD_ITT=OFF \
-DWITH_CUDA=OFF \
-DWITH_OPENCL=OFF \
-DWITH_OPENCLAMDFFT=OFF \
-DWITH_OPENCLAMDBLAS=OFF \
-DWITH_VA_INTEL=OFF \
-DCPU_BASELINE_DISABLE=ON \
-DENABLE_SSE=OFF \
-DENABLE_SSE2=OFF \
-DBUILD_TESTING=OFF \
-DBUILD_PERF_TESTS=OFF \
-DBUILD_TESTS=OFF \
-DCMAKE_BUILD_TYPE=RELEASE \
-DCMAKE_CXX_FLAGS_RELEASE=-g0 \
-DBUILD_EXAMPLES=OFF \
-DBUILD_DOCS=OFF \
-DBUILD_opencv_apps=OFF \
-DBUILD_SHARED_LIBS=ON \
-DOpenCV_STATIC=OFF \
-DWITH_1394=OFF \
-DWITH_ARITH_DEC=OFF \
-DWITH_ARITH_ENC=OFF \
-DWITH_CUBLAS=OFF \
-DWITH_CUFFT=OFF \
-DWITH_FFMPEG=OFF \
-DWITH_GDAL=OFF \
-DWITH_GSTREAMER=OFF \
-DWITH_GTK=OFF \
-DWITH_HALIDE=OFF \
-DWITH_JASPER=OFF \
-DWITH_NVCUVID=OFF \
-DWITH_OPENEXR=OFF \
-DWITH_PROTOBUF=OFF \
-DWITH_PTHREADS_PF=OFF \
-DWITH_QUIRC=OFF \
-DWITH_V4L=OFF \
-DWITH_WEBP=OFF \
-DBUILD_LIST=core,imgproc \
-DANDROID_NDK=/app/gemfield/android-ndk-r19c \
-DCMAKE_TOOLCHAIN_FILE=/app/gemfield/android-ndk-r19c/build/cmake/android.toolchain.cmake \
-DANDROID_NATIVE_API_LEVEL=android-21 \
-DBUILD_JAVA=ON \
-DBUILD_ANDROID_EXAMPLES=OFF \
-DBUILD_ANDROID_PROJECTS=OFF \
-DANDROID_ABI=arm64-v8a \
-DCMAKE_INSTALL_PREFIX=/app/gemfield/opencv-4.4.0/opencv_v8 \
..
```
编译好后，我们可以看到库的大小（这个章节Gemfield使用了共享库编译，静态库类似，不再重复）：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ find . -type f -name "lib*.so" -exec ls -lh {} \+
-rw-r--r-- 1 gemfield gemfield 8.9M 11月 19 18:39 ./sdk/native/libs/arm64-v8a/libopencv_core.so
-rw-r--r-- 1 gemfield gemfield 3.6M 11月 19 18:41 ./sdk/native/libs/arm64-v8a/libopencv_imgproc.so
```
再strip下：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/aarch64-linux-android/bin/strip ./sdk/native/libs/arm64-v8a/libopencv_core.so
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/aarch64-linux-android/bin/strip ./sdk/native/libs/arm64-v8a/libopencv_imgproc.so
```
看起来只有2、3个MB了：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ find . -type f -name lib*.so -exec ls -lh {} \+
-rw-r--r-- 1 gemfield gemfield 3.4M 11月 19 18:49 ./sdk/native/libs/arm64-v8a/libopencv_core.so
-rw-r--r-- 1 gemfield gemfield 2.9M 11月 19 18:49 ./sdk/native/libs/arm64-v8a/libopencv_imgproc.so
```
还可以看这两个共享库的依赖：
```
gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/arm-linux-androideabi/bin/readelf -a ./sdk/native/libs/arm64-v8a/libopencv_core.so | grep "Shared library:"
 0x0000000000000001 (NEEDED)             Shared library: [libdl.so]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so]
 0x0000000000000001 (NEEDED)             Shared library: [liblog.so]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so]

gemfield@ThinkPad-X1C:/app/gemfield/opencv-4.4.0/opencv_v8$ /app/gemfield/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/arm-linux-androideabi/bin/readelf -a ./sdk/native/libs/arm64-v8a/libopencv_imgproc.so | grep "Shared library:"
 0x0000000000000001 (NEEDED)             Shared library: [libopencv_core.so]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so]
```
当然，共享库是要包含在apk中的，会增加apk的大小，推荐使用静态库，自己酌情考虑吧。

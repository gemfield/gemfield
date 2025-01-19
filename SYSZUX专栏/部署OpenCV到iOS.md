# 背景
最近要把一个SBD算法从X86服务器上移植到iOS上，因为该算法的核心要义就是使用了OpenCV的几个API（你懂的，每个API背后就是几代人几十篇paper的辛劳）。

iOS开发可以使用swift和object-c，但是因为object-c可以混合C++的语法（美其名曰object-c++，注意不是一门新语言)，因此Gemfield选择使用object-c。反正主要算法都是使用C++写的，object-c无非就当作个胶水语言，一头是iOS上的各种SDK，另外一头是C++编写的算法。不过苹果的Objective-C语言语法奇丑无比，和苹果的硬件产品外观真是完全相反。真是奇怪，你苹果心里没有点数吗？赶紧罢黜object-c，独尊C++！

# xcode项目
在xcodeproj目录下，有如下的文件：
```
project.pbxproj
xcuserdata
project.xcworkspace
```
- pbxproj文件包含了xcode项目的各种配置信息，我们不直接修改这个文件，而是通过xcode IDE来配置；
- xcuserdata是xcode-user-data的缩写，存放的是用户自己的一些数据，比如当前项目的一些和个人操作相关的记录；
- project.xcworkspace目录就是workspace，这个比较复杂，以后再说。

在XCode的"Build Settings"中主要修改C++的标准，使用的标准库，以及最重要的一项："Apple Clang - Language"-->"Compile Source As"修改为"Objective-C++"，不然你的C++会报各种奇怪的头文件找不到的错误；另外，object-c中引用的C++头文件要放在object-c头文件的前面，否则也会报一些奇怪的错误，比如"Expected identifier"错误。

# 编译iOS版的OpenCV
Gemfield选择的是OpenCV仓库的master分支（opencv4.2+)。确保你的mac已经从商店下载安装了Xcode。

1, 克隆opencv仓库
```
git clone https://github.com/opencv/opencv.git
```
如果还想要额外的opencv module，可以再克隆opencv_contrib.git
```
git clone https://github.com/opencv/opencv_contrib.git
```
2，安装cmkae
```
brew install cmake
```
3，安装xcode的命令行工具
```
xcode-select --install
```
4，编译OpenCV的iOS framework

编译过程已经放在仓库中的build_framework.py脚本里了：
```
python opencv/platforms/ios/build_framework.py ios
```
这个python脚本内部调用了cmake命令来进行C++的编译（OpenCV现在已经是C++11的项目了）：
```
cmake -GXcode \
-DAPPLE_FRAMEWORK=ON \
-DCMAKE_INSTALL_PREFIX=install \
-DCMAKE_BUILD_TYPE=Release \
-DOPENCV_INCLUDE_INSTALL_PATH=include \
-DOPENCV_3P_LIB_INSTALL_PATH=lib/3rdparty \
-DIOS_ARCH=armv7 \
-DCMAKE_TOOLCHAIN_FILE=/Users/civilnet/github/opencv/platforms/ios/cmake/Toolchains/Toolchain-iPhoneOS_Xcode.cmake \
-DCPU_BASELINE=DETECT /Users/civilnet/github/opencv \
-DCMAKE_C_FLAGS=-fembed-bitcode \
-DCMAKE_CXX_FLAGS=-fembed-bitcode
```
如果还想同时编译opencv_contrib，可以使用--contrib参数：
```
python opencv/platforms/ios/build_framework.py ios --contrib opencv_contrib
```
如果还想裁剪掉一些module，可以使用--without参数：
```
python opencv/platforms/ios/build_framework.py ios --contrib opencv_contrib --without optflow
```
编译可是需要很长时间，一个重要的原因是默认会编译5种CPU架构的framework：iOS需要的armv7、armv7s、arm64和iPhone模拟器需要的i386、x86_64。如果不想编译这么多种架构的framework，可以像Gemfield一样使用--iphoneos_archs 和 --iphonesimulator_archs 参数。比如，在CivilNet，Gemfield只编译iOS的arm64和模拟器的x86_64：
```
python opencv/platforms/ios/build_framework.py ios --iphoneos_archs arm64 --iphonesimulator_archs x86_64
```

# 再深入OpenCV的iOS构建
1，OpenCV的内部模块
```
-- Processing WORLD modules...
--     module opencv_core...
--     module opencv_flann...
--     module opencv_imgproc...
--     module opencv_ml...
--     module opencv_photo...
--     module opencv_dnn...
-- Registering hook 'INIT_MODULE_SOURCES_opencv_dnn': /Users/civilnet/github/opencv/modules/dnn/cmake/hooks/INIT_MODULE_SOURCES_opencv_dnn.cmake
-- opencv_dnn: filter out ocl4dnn source code
-- opencv_dnn: filter out cuda4dnn source code
--     module opencv_features2d...
--     module opencv_gapi...
--     module opencv_imgcodecs...
--     module opencv_videoio...
--     module opencv_calib3d...
--     module opencv_highgui...
--     module opencv_objdetect...
--     module opencv_stitching...
--     module opencv_video...
```
2,编译arm架构的时候

编译arm架构framework的时候，一些x86的源文件就会被自动排除：
```
-- Excluding from source files list: modules/imgproc/src/corner.avx.cpp
-- Excluding from source files list: modules/imgproc/src/imgwarp.avx2.cpp
-- Excluding from source files list: modules/imgproc/src/imgwarp.sse4_1.cpp
-- Excluding from source files list: modules/imgproc/src/resize.avx2.cpp
-- Excluding from source files list: modules/imgproc/src/resize.sse4_1.cpp
-- Excluding from source files list: <BUILD>/modules/world/layers/layers_common.avx.cpp
-- Excluding from source files list: <BUILD>/modules/world/layers/layers_common.avx2.cpp
-- Excluding from source files list: <BUILD>/modules/world/layers/layers_common.avx512_skx.cpp
-- Excluding from source files list: modules/features2d/src/fast.avx2.cpp
```
3,编译信息汇总

注意，就像下面Video IO部分显示的那样，编译iOS的framework会依赖iOS的AVFoundation SDK（用于视频的IO）。其它还有：

- 编译的OpenCV模块：calib3d core dnn features2d flann gapi highgui imgcodecs imgproc ml objdetect photo stitching video videoio world；
- 依赖的三方库：libprotobuf libjpeg-turbo libwebp libpng zlib quirc
- 使用的编译工具：/Users/civilnet/github/ios/build/build-armv7-iphoneos/xcodebuild_wrapper；
- c++编译器：/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++；
- 依赖的iOS framework： Accelerate CoreGraphics QuartzCore AssetsLibrary UIKit ade
```
-- General configuration for OpenCV 4.2.0-dev =====================================
--   Version control:               unknown
-- 
--   Platform:
--     Timestamp:                   2020-02-18T11:42:03Z
--     Host:                        Darwin 19.2.0 x86_64
--     Target:                      iOS 8.0 armv7
--     CMake:                       3.16.4
--     CMake generator:             Xcode
--     CMake build tool:            /Users/civilnet/github/ios/build/build-armv7-iphoneos/xcodebuild_wrapper
--     Xcode:                       11.3.1
-- 
--   CPU/HW features:
--     Baseline:                    NEON
--       requested:                 DETECT
-- 
--   C/C++:
--     Built as dynamic libs?:      NO
--     C++ Compiler:                /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++  (ver 11.0.0.11000033)
--     C++ flags (Release):         -fembed-bitcode   -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments -Wno-semicolon-before-method-body  -fvisibility=hidden -fvisibility-inlines-hidden -O3 -DNDEBUG  -DNDEBUG
--     C++ flags (Debug):           -fembed-bitcode   -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments -Wno-semicolon-before-method-body  -fvisibility=hidden -fvisibility-inlines-hidden -g  -O0 -DDEBUG -D_DEBUG
--     C Compiler:                  /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang
--     C flags (Release):           -fembed-bitcode   -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments -Wno-semicolon-before-method-body  -fvisibility=hidden -fvisibility-inlines-hidden -O3 -DNDEBUG  -DNDEBUG
--     C flags (Debug):             -fembed-bitcode   -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor -Werror=address -Werror=sequence-point -Wformat -Werror=format-security -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wundef -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized -Winit-self -Wno-delete-non-virtual-dtor -Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments -Wno-semicolon-before-method-body  -fvisibility=hidden -fvisibility-inlines-hidden -g  -O0 -DDEBUG -D_DEBUG
--     Linker flags (Release):      
--     Linker flags (Debug):        
--     ccache:                      NO
--     Precompiled headers:         NO
--     Extra dependencies:          -framework Accelerate -framework CoreGraphics -framework QuartzCore -framework AssetsLibrary -framework UIKit ade
--     3rdparty dependencies:       libprotobuf libjpeg-turbo libwebp libpng zlib quirc
-- 
--   OpenCV modules:
--     To be built:                 calib3d core dnn features2d flann gapi highgui imgcodecs imgproc ml objdetect photo stitching video videoio world
--     Disabled:                    -
--     Disabled by dependency:      -
--     Unavailable:                 java js python2 python3 ts
--     Applications:                -
--     Documentation:               NO
--     Non-free algorithms:         NO
-- 
--   GUI: 
-- 
--   Media I/O: 
--     ZLib:                        build (ver 1.2.11)
--     JPEG:                        build-libjpeg-turbo (ver 2.0.2-62)
--     WEBP:                        build (ver encoder: 0x020e)
--     PNG:                         build (ver 1.6.37)
--     HDR:                         YES
--     SUNRASTER:                   YES
--     PXM:                         YES
--     PFM:                         YES
-- 
--   Video I/O:
--     AVFoundation:                YES
--     iOS capture:                 YES
-- 
--   Parallel framework:            GCD
-- 
--   Trace:                         YES (built-in)
-- 
--   Other third-party libraries:
--     Custom HAL:                  NO
--     Protobuf:                    build (3.5.1)
-- 
--   Python (for build):            NO
--   Install to:                    /Users/civilnet/github/ios/build/build-armv7-iphoneos/install
```
- 4,xcodebuild命令
```
xcodebuild IPHONEOS_DEPLOYMENT_TARGET=8.0 ARCHS=armv7 -sdk iphoneos -configuration Release -parallelizeTargets -jobs 4 -target ALL_BUILD build
```
需要编译的3rd party库文件：
```
libzip.a
liblibwebp.a
liblibjpeg-turbo.a
liblibprotobuf.a
liblibpng.a
libquirc.a
libade.a
```

5,编译源文件

使用clang来编译c和c++源文件：
```
/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang \
-x c -target armv7-apple-ios8.0 -fmessage-length=204 \
-fdiagnostics-show-note-include-stack -fmacro-backtrace-limit=0 \
-fcolor-diagnostics -Wno-trigraphs -fpascal-strings -O3 \
-Wno-missing-field-initializers -Wno-missing-prototypes \
-Wno-return-type -Wno-missing-braces -Wparentheses -Wswitch \
-Wno-unused-function -Wno-unused-label -Wno-unused-parameter \
-Wno-unused-variable -Wunused-value -Wno-empty-body -Wno-uninitialized \
-Wno-unknown-pragmas -Wno-shadow -Wno-four-char-constants -Wno-conversion \
-Wno-constant-conversion -Wno-int-conversion -Wno-bool-conversion -Wno-enum-conversion \
-Wno-float-conversion -Wno-non-literal-null-conversion -Wno-objc-literal-conversion \
-Wno-shorten-64-to-32 -Wpointer-sign -Wno-newline-eof -DCMAKE_INTDIR=\"Release-iphoneos\" \
-DZ_HAVE_UNISTD_H -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS13.2.sdk \
-fstrict-aliasing -Wdeprecated-declarations -Wno-sign-conversion \
-Wno-infinite-recursion -Wno-comma -Wno-block-capture-autoreleasing \
-Wno-strict-prototypes -Wno-semicolon-before-method-body -fembed-bitcode-marker \
-I/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/lib/Release/include \
-I/Users/civilnet/github/opencv/3rdparty/zlib \
-isystem /Users/civilnet/github/ios/build/build-armv7-iphoneos \
-I/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/DerivedSources-normal/armv7 \
-I/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/DerivedSources/armv7 \
-I/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/DerivedSources \
-Wmost -Wno-four-char-constants -Wno-unknown-pragmas \
-F/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/lib/Release \
-fembed-bitcode -fsigned-char -W -Wall -Werror=return-type -Werror=non-virtual-dtor \
-Werror=address -Werror=sequence-point -Wformat \
-Werror=format-security -Winit-self -Wpointer-arith -Wshadow -Wsign-promo -Wuninitialized \
-Winit-self -Wno-delete-non-virtual-dtor \
-Wno-unnamed-type-template-args -Wno-comment -fdiagnostics-show-option -Qunused-arguments \
-Wno-semicolon-before-method-body -fvisibility=hidden -fvisibility-inlines-hidden \
-Wno-shorten-64-to-32 -Wno-attributes -Wno-strict-prototypes -Wno-missing-prototypes \
-Wno-missing-declarations -Wno-shift-negative-value -Wno-undef -Wno-implicit-fallthrough \
-DNDEBUG -DNDEBUG -fPIC -MMD -MT dependencies \
-MF /Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/Objects-normal/armv7/adler32.d \
--serialize-diagnostics \
/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/Objects-normal/armv7/adler32.dia \
-c /Users/civilnet/github/opencv/3rdparty/zlib/adler32.c \
-o /Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/Objects-normal/armv7/adler32.o
```
6，使用libtool命令将.o文件打包为.a静态库
```
/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/libtool \
-static -arch_only armv7 -D \
-syslibroot /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS13.2.sdk \
-L/Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/lib/Release \
-filelist /Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/zlib/OpenCV.build/Release-iphoneos/zlib.build/Objects-normal/armv7/zlib.LinkFileList \
-o /Users/civilnet/github/ios/build/build-armv7-iphoneos/3rdparty/lib/Release/libzlib.a
```
7，要install的东西
```
Executing: cmake -DBUILD_TYPE=Release -P cmake_install.cmake
-- Install configuration: "Release"
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/include/opencv2/cvconfig.h
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/include/opencv2/opencv_modules.hpp
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/cmake/opencv4/OpenCVModules.cmake
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/cmake/opencv4/OpenCVModules-release.cmake
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/cmake/opencv4/OpenCVConfig-version.cmake
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/cmake/opencv4/OpenCVConfig.cmake
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/valgrind.supp
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/valgrind_3rdparty.supp
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libzlib.a
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/licenses/opencv4/zlib-README
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibjpeg-turbo.a
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/licenses/opencv4/libjpeg-turbo-README.ijg
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibwebp.a
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibpng.a
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/licenses/opencv4/libpng-LICENSE
......
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/lbpcascades/lbpcascade_frontalcatface.xml
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/lbpcascades/lbpcascade_frontalface.xml
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/lbpcascades/lbpcascade_frontalface_improved.xml
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/lbpcascades/lbpcascade_profileface.xml
-- Installing: /Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/share/opencv4/lbpcascades/lbpcascade_silverware.xml
```
8，merge .a库
```
Merging libraries:
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/libopencv_world.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibpng.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibwebp.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libquirc.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibprotobuf.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libade.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libzlib.a
	/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibjpeg-turbo.a
```
还是使用的libtool命令：
```
libtool -static \
-o /Users/civilnet/github/ios/build/build-armv7s-iphoneos/lib/Release/libopencv_merged.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/libopencv_world.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibpng.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibwebp.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libquirc.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibprotobuf.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libade.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/libzlib.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/install/lib/3rdparty/liblibjpeg-turbo.a
```
9，每种CPU架构都得独立从头到尾编译一次

因此编译时间巨长，默认一共5轮build。

第3轮build，DIOS_ARCH=arm64：
```

cmake -GXcode -DAPPLE_FRAMEWORK=ON -DCMAKE_INSTALL_PREFIX=install \
-DCMAKE_BUILD_TYPE=Release -DOPENCV_INCLUDE_INSTALL_PATH=include \
-DOPENCV_3P_LIB_INSTALL_PATH=lib/3rdparty \
-DIOS_ARCH=arm64 \
-DCMAKE_TOOLCHAIN_FILE=/Users/civilnet/github/opencv/platforms/ios/cmake/Toolchains/Toolchain-iPhoneOS_Xcode.cmake \
-DCPU_BASELINE=DETECT /Users/civilnet/github/opencv \
-DCMAKE_C_FLAGS=-fembed-bitcode \
-DCMAKE_CXX_FLAGS=-fembed-bitcode
```
第4轮build，DIOS_ARCH=i386：
```
cmake -GXcode -DAPPLE_FRAMEWORK=ON -DCMAKE_INSTALL_PREFIX=install \
-DCMAKE_BUILD_TYPE=Release -DOPENCV_INCLUDE_INSTALL_PATH=include \
-DOPENCV_3P_LIB_INSTALL_PATH=lib/3rdparty \
-DIOS_ARCH=i386 \
-DCMAKE_TOOLCHAIN_FILE=/Users/civilnet/github/opencv/platforms/ios/cmake/Toolchains/Toolchain-iPhoneSimulator_Xcode.cmake \
/Users/civilnet/github/opencv
```
第5轮build，DIOS_ARCH=x86_64：
```
cmake -GXcode -DAPPLE_FRAMEWORK=ON -DCMAKE_INSTALL_PREFIX=install \
-DCMAKE_BUILD_TYPE=Release -DOPENCV_INCLUDE_INSTALL_PATH=include \
-DOPENCV_3P_LIB_INSTALL_PATH=lib/3rdparty \
-DIOS_ARCH=x86_64 \
-DCMAKE_TOOLCHAIN_FILE=/Users/civilnet/github/opencv/platforms/ios/cmake/Toolchains/Toolchain-iPhoneSimulator_Xcode.cmake \
/Users/civilnet/github/opencv
```
# 生成OpenCV的iOS framework
最后使用lipo命令生成iOS framework
```
lipo -create \
/Users/civilnet/github/ios/build/build-armv7-iphoneos/lib/Release/libopencv_merged.a \
/Users/civilnet/github/ios/build/build-armv7s-iphoneos/lib/Release/libopencv_merged.a \
/Users/civilnet/github/ios/build/build-arm64-iphoneos/lib/Release/libopencv_merged.a \
/Users/civilnet/github/ios/build/build-i386-iphonesimulator/lib/Release/libopencv_merged.a \
/Users/civilnet/github/ios/build/build-x86_64-iphonesimulator/lib/Release/libopencv_merged.a \
-o /Users/civilnet/github/ios/opencv2.framework/Versions/A/opencv2
```
那么iOS framework是什么东西呢？简单来说，就是个sdk，包含了头文件和库文件。我们来看看opencv framework里包含了什么内容：
```
gemfield:~/github/ios/opencv2.framework$ ls -l
total 0
lrwxr-xr-x  1 civilnet  staff   24  2 18 21:17 Headers -> Versions/Current/Headers
lrwxr-xr-x  1 civilnet  staff   26  2 18 21:17 Resources -> Versions/Current/Resources
drwxr-xr-x  4 civilnet  staff  128  2 18 21:17 Versions
lrwxr-xr-x  1 civilnet  staff   24  2 18 21:17 opencv2 -> Versions/Current/opencv2
```
其中，Headers是头文件，Resources里是info.plist文件，opencv2就是.a库了：
```
gemfield:~/github/ios/opencv2.framework$ file opencv2 
opencv2: Mach-O universal binary with 5 architectures: [arm_v7:current ar archive] [arm_v7s] [i386] [x86_64] [arm64]
opencv2 (for architecture armv7):	current ar archive
opencv2 (for architecture armv7s):	current ar archive
opencv2 (for architecture i386):	current ar archive
opencv2 (for architecture x86_64):	current ar archive
opencv2 (for architecture arm64):	current ar archive
```

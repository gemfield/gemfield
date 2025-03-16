# 背景
众所周知，PyTorch项目作为一个C++工程，是基于CMake进行构建的。然而当你想基于CMake来构建PyTorch静态库时，你会发现：

- 静态编译相关的文档不全；
- CMake文件bug太多，其整体结构比较糟糕。

由于重构整体的CMake结构需要很多的人力，一时半会还看不到优雅的解决方案，因此在这里，Gemfield先写篇文章来说明PyTorch的静态编译如何进行，以及各种注意事项。本文基于目前最新的PyTorch 1.7（在最新的master分支上也没有问题）。

尤其是涉及到PyTorch静态编译重构的时候，还牵涉到代码的重新设计。举个例子，一些模块的注册机制是依赖全局对象初始化的，在静态库中，这样的初始化逻辑并不会被链接（因为你的程序并没有调用它），这就导致程序需要调用的内容并没有被初始化。而为了解决这个问题引入的-Wl,--no-whole-archive，又导致编译目标的体积变得极为庞大。当未来，若PyTorch官方仓库为静态编译进行重构优化后，本文也就过时了（进而会被迁移到Gemfield的颓垣废址专栏下）。

思绪再回来，本文以在Ubuntu 18.04 上进行目标为x86_64 Linux的构建为例，介绍使用CMake对PyTorch进行静态编译的2种最小尺度（这种最小尺度的定义是：不更改pytorch自身代码、不使用CMake文件中intern的开关、使得libtorch能够进行模型的前向推理、tensor的序列化反序列化、库尽可能小）：

- 最小尺度CPU版本；
- 最小尺度CUDA版本。

另外，在阅读本文前，我们需要熟悉下几个线性代数库的名字。
- BLAS (Basic Linear Algebra Subprograms)，是一个常见线性代数操作的API规范，偏向底层，主要内容有：向量相加、标量相乘、点积、线性组合、矩阵相乘等。
- LAPACK (Linear Algebra Package) 也是一个线性代数库的规范. 基于BLAS规范，不同于BLAS的底层，LAPACK定位于高层。LAPACK定义矩阵分解的一些操作，如LU、LLt、QR、SVD、Schur，用来解决诸如找到矩阵的特征值、找到矩阵奇异值、求解线性方程组这样的问题。

BLAS/LAPACK既然是API规范，就应该有相应的实现，常用的有这些：

- MKL，Intel Math Kernel Library。用于Intel处理器的(注意和MKL-DNN库的区别，MKL-DNN是英特尔的一个独立的神经网络库：MKL for Deep Neural Networks)；
- ATLAS，Automatically Tuned Linear Algebra Software，多平台的；
- OpenBLAS，多平台的；
- Accelerate，苹果macOS、iOS平台上的；
- Eigen，这个库只有头文件，实现了BLAS和一部分LAPACK，集成到了PyTorch项目的thirdparty下；
- cuBLAS，NVIDIA的BLAS实现，基于NVIDIA的GPU硬件（此外还有cuFFT、cuRAND, cuSPARSE等）；
- MAGMA，基于CUDA、HIP、 Intel Xeon Phi、OpenCL的BLAS/LAPACK实现；

还记得刚才提到过本文的目标是在Ubuntu 18.04上进行目标为x86_64 Linux的构建，这种情况下，我们必须要使用一个LAPACK实现：openblas、MKL或者Eigen。否则，运行时会报错：“gels : Lapack library not found in compile time”。本文使用MKL，并实验性质到介绍下如何使用Eigen。

# CMake编译开关
使用CMake进行构建时，我们主要是通过一些编译开关来决定要编译的模块。这些编译开关是在CMake文件中定义的变量，其值的来源主要有这几种：

- 默认值；
- 用户指定；
- 通过检测系统环境获得；
- 通过检测软件包的安装情况获得；
- 通过开关与开关之间的逻辑关系推导而来；

这些开关的值会影响：

- CMakeLists.txt中要添加的编译单元；
- 编译器、链接器的命令行参数；
- 代码中的ifdef宏；

下面是一些主要的编译开关的初始值，这些值初始值要么为OFF，要么为ON，要么为空。如下所示：

## 1，默认关闭的

- ATEN_NO_TEST，是否编译ATen test binaries；
- BUILD_BINARY，Build C++ binaries；
- BUILD_DOCS，Build Caffe2 documentation；
- BUILD_CAFFE2_MOBILE，Build libcaffe2 for mobile，也就是在libcaffe2和libtorch mobile中选择，目前已经废弃，默认使用libtorch mobile；
- CAFFE2_USE_MSVC_STATIC_RUNTIME，Using MSVC static runtime libraries；
- BUILD_TEST，Build C++ test binaries (need gtest and gbenchmark)；
- BUILD_STATIC_RUNTIME_BENCHMARK，Build C++ binaries for static runtime benchmarks (need gbenchmark)；
- BUILD_TENSOREXPR_BENCHMARK，Build C++ binaries for tensorexpr benchmarks (need gbenchmark)；
- BUILD_MOBILE_BENCHMARK，Build C++ test binaries for mobile (ARM) targets(need gtest and gbenchmark)；
- BUILD_MOBILE_TEST，Build C++ test binaries for mobile (ARM) targets(need gtest and gbenchmark)；
- BUILD_JNI，Build JNI bindings；
- BUILD_MOBILE_AUTOGRAD，Build autograd function in mobile build (正在开发中)；
- INSTALL_TEST，Install test binaries if BUILD_TEST is on；
- USE_CPP_CODE_COVERAGE，Compile C/C++ with code coverage flags；
- USE_ASAN，Use Address Sanitizer；
- USE_TSAN，Use Thread Sanitizer；
- CAFFE2_STATIC_LINK_CUDA，Statically link CUDA libraries；
- USE_STATIC_CUDNN，Use cuDNN static libraries；
- USE_KINETO，Use Kineto profiling library；
- USE_FAKELOWP，Use FakeLowp operators；
- USE_FFMPEG；
- USE_GFLAGS；
- USE_GLOG；
- USE_LEVELDB；
- USE_LITE_PROTO，Use lite protobuf instead of full；
- USE_LMDB；
- USE_PYTORCH_METAL，Use Metal for PyTorch iOS build；
- USE_NATIVE_ARCH，Use -march=native；
- USE_STATIC_NCCL；
- USE_SYSTEM_NCCL，Use system-wide NCCL；
- USE_NNAPI；
- USE_NVRTC，Use NVRTC. Only available if USE_CUDA is on；
- USE_OBSERVERS，Use observers module；
- USE_OPENCL；
- USE_OPENCV；
- USE_PROF，Use profiling；
- USE_REDIS;
- USE_ROCKSDB;
- USE_SNPE，使用高通的神经网络引擎；
- USE_SYSTEM_EIGEN_INSTALL，Use system Eigen instead of the one under third_party；
- USE_TENSORRT，Using Nvidia TensorRT library；
- USE_VULKAN，Use Vulkan GPU backend；
- USE_VULKAN_API，Use Vulkan GPU backend v2；
- USE_VULKAN_SHADERC_RUNTIME，Use Vulkan Shader compilation runtime(Needs shaderc lib)；
- USE_VULKAN_RELAXED_PRECISION，Use Vulkan relaxed precision(mediump)；
- USE_ZMQ；
- USE_ZSTD；
- USE_MKLDNN_CBLAS，Use CBLAS in MKLDNN；
- USE_TBB；
- HAVE_SOVERSION，Whether to add SOVERSION to the shared objects；
- USE_SYSTEM_LIBS，Use all available system-provided libraries；
- USE_SYSTEM_CPUINFO，Use system-provided cpuinfo；
- USE_SYSTEM_SLEEF，Use system-provided sleef；
- USE_SYSTEM_GLOO，Use system-provided gloo；
- USE_SYSTEM_FP16，Use system-provided fp16；
- USE_SYSTEM_PTHREADPOOL，Use system-provided pthreadpool；
- USE_SYSTEM_PSIMD，Use system-provided psimd；
- USE_SYSTEM_FXDIV，Use system-provided fxdiv；
- USE_SYSTEM_BENCHMARK，Use system-provided google benchmark；
- USE_SYSTEM_ONNX，Use system-provided onnx；
- USE_SYSTEM_XNNPACK，Use system-provided xnnpack。

## 2，默认打开的

- BUILD_CUSTOM_PROTOBUF，Build and use Caffe2's own protobuf under third_party；
- BUILD_PYTHON，Build Python binaries；
- BUILD_CAFFE2，Master flag to build Caffe2；
- BUILD_CAFFE2_OPS，Build Caffe2 operators；
- BUILD_SHARED_LIBS，Build libcaffe2.so；
- CAFFE2_LINK_LOCAL_PROTOBUF，If set, build protobuf inside libcaffe2.so；
- COLORIZE_OUTPUT，Colorize output during compilation；
- USE_CUDA；
- USE_CUDNN；
- USE_ROCM；
- USE_FBGEMM，Use FBGEMM (quantized 8-bit server operators)；
- USE_METAL，Use Metal for Caffe2 iOS build；
- USE_NCCL，须在UNIX上，且USE_CUDA 或USE_ROCM是打开的；
- USE_NNPACK；
- USE_NUMPY；
- USE_OPENMP，Use OpenMP for parallel code；
- USE_QNNPACK；Use QNNPACK (quantized 8-bit operators);
- USE_PYTORCH_QNNPACK，Use ATen/QNNPACK (quantized 8-bit operators)；
- USE_VULKAN_WRAPPER，Use Vulkan wrapper；
- USE_XNNPACK，
- USE_DISTRIBUTED；
- USE_MPI，Use MPI for Caffe2. Only available if USE_DISTRIBUTED is on；
- USE_GLOO，Only available if USE_DISTRIBUTED is on；
- USE_TENSORPIPE，Only available if USE_DISTRIBUTED is on；
- ONNX_ML，Enable traditional ONNX ML API；
- USE_NUMA；
- USE_VALGRIND；
- USE_MKLDNN；
- BUILDING_WITH_TORCH_LIBS，Tell cmake if Caffe2 is being built alongside torch libs。

## 3，默认为空的

- SELECTED_OP_LIST，Path to the yaml file that contains the list of operators to include for custom build. Include all operators by default；
- OP_DEPENDENCY，Path to the yaml file that contains the op dependency graph for custom build。

# CMake编译开关的平台修正
编译开关的初始值并不是一成不变的，即使没有用户的手工指定，那么CMake也会通过检测硬件环境、系统环境、包依赖来进行修改。比如下面这样：
## 1，操作系统修正

- USE_DISTRIBUTED，如果不是Linux/Win32，则关闭；
- USE_LIBUV，macOS上，且手工打开USE_DISTRIBUTED，则打开；
- USE_NUMA，如果不是Linux，则关闭；
- USE_VALGRIND，如果不是Linux，则关闭；
- USE_TENSORPIPE，如果是Windows，则关闭；
- USE_KINETO，如果是windows，则关闭；
- 如果是构建Android、iOS等移动平台上的libtorch，则：
```
  set(BUILD_PYTHON OFF)
  set(BUILD_CAFFE2_OPS OFF)
  set(USE_DISTRIBUTED OFF)
  set(FEATURE_TORCH_MOBILE ON)
  set(NO_API ON)
  set(USE_FBGEMM OFF)
  set(USE_QNNPACK OFF)
  set(INTERN_DISABLE_ONNX ON)
  set(INTERN_USE_EIGEN_BLAS ON)
  set(INTERN_DISABLE_MOBILE_INTERP ON)
```
## 2，CPU架构修正
```
    USE_MKLDNN，如果不是64位x86_64，则关闭；
    USE_FBGEMM，如果不是64位x86_64，则关闭；如果不支持AVX512指令集，则关闭；
    USE_KINETO，如果是手机平台，则关闭；
    USE_GLOO，如果不是64位x86_64，则关闭；
```
## 3，软件包依赖修正
```
    USE_DISTRIBUTED，在Windows上，如果找不到libuv，则关闭；
    USE_GLOO，在Windows上，如果找不到libuv，则关闭；
    USE_KINETO，如果没有USE_CUDA，则关闭；
    MKL相关，不再赘述；
    NNPACK家族相关的（(QNNPACK, PYTORCH_QNNPACK,  XNNPACK) ），不再赘述；
    USE_BLAS，会被相关依赖修正；
    USE_PTHREADPOOL，会被相关依赖修正；
    USE_LAPACK，如果LAPACK包不能被找到，则关闭；且运行时会导致出错：“gels : Lapack library not found in compile time”；
```
## 4，用户手工指令的修正

- 如果手工打开了USE_SYSTEM_LIBS，则：
```
  set(USE_SYSTEM_CPUINFO ON)
  set(USE_SYSTEM_SLEEF ON)
  set(USE_SYSTEM_GLOO ON)
  set(BUILD_CUSTOM_PROTOBUF OFF)
  set(USE_SYSTEM_EIGEN_INSTALL ON)
  set(USE_SYSTEM_FP16 ON)
  set(USE_SYSTEM_PTHREADPOOL ON)
  set(USE_SYSTEM_PSIMD ON)
  set(USE_SYSTEM_FXDIV ON)
  set(USE_SYSTEM_BENCHMARK ON)
  set(USE_SYSTEM_ONNX ON)
  set(USE_SYSTEM_XNNPACK ON)
```
- 如果设置环境变量BUILD_PYTORCH_MOBILE_WITH_HOST_TOOLCHAIN，则set(INTERN_BUILD_MOBILE ON)，而INTERN_BUILD_MOBILE一旦打开，则：
```
#只有编译caffe2 mobile的时候才是OFF，其它时候都是ON，也就是都会编译ATen的op
set(INTERN_BUILD_ATEN_OPS ON)

set(BUILD_PYTHON OFF)
set(BUILD_CAFFE2_OPS OFF)
set(USE_DISTRIBUTED OFF)
set(FEATURE_TORCH_MOBILE ON)
set(NO_API ON)
set(USE_FBGEMM OFF)
set(USE_QNNPACK OFF)
set(INTERN_DISABLE_ONNX ON)
set(INTERN_USE_EIGEN_BLAS ON)
set(INTERN_DISABLE_MOBILE_INTERP ON)
```
## 5，CMake的配置
CMake的过程中会对系统环境进行检查，主要用来检测：

- 是否支持AVX2（perfkernels有依赖）；
- 是否支持AVX512（fbgemm有依赖）；
- 寻找BLAS实现，如果目标是Mobile平台，使用Eigen；如果不是Mobile，则寻找MKL、openblas（找不到不会报错，但程序运行时会提示：gels : Lapack library not found in compile time）；
- Protobuf；
- python解释器；
- NNPACK（NNPACK backend 是x86-64）；
- OpenMP（是MKL-DNN的依赖）；
- NUMA；
- pybind11；
- CUDA；
- ONNX；
- MAGMA（基于GPU等设备的blas/lapack实现）；
- metal（苹果生态）；
- NEON（ARM生态，这里肯定是检测不到相关的硬件了）；
- MKL-DNN（Intel的深度学习库）；
- ATen parallel backend: NATIVE；
- Sleef（thirdparty下的三方库）；
- RT : /usr/lib/x86_64-linux-gnu/librt.so ；
- FFTW3 : /usr/lib/x86_64-linux-gnu/libfftw3.so；
- OpenSSL: /usr/lib/x86_64-linux-gnu/libcrypto.so；
- MPI；

CMake构建的时候会使用python脚本(tools/codegen/gen.py)生成一些cpp源文件，这个python脚本对yaml、dataclasses模块有依赖，因此，在开始编译前，你需要安装这些包：
```
root@gemfield:~# pip3 install setuptools
root@gemfield:~# pip3 install pyyaml
root@gemfield:~# pip3 install dataclasses
```
# PyTorch官方预编译动态库的编译选项
如果对官方编译的库所选用的编译开关感兴趣的话，可以使用如下的python命令获得这些信息：
```
>>> print(torch.__config__.show())
PyTorch built with:
  - GCC 7.3
  - C++ Version: 201402
  - Intel(R) Math Kernel Library Version 2020.0.1 Product Build 20200208 for Intel(R) 64 architecture applications
  - Intel(R) MKL-DNN v1.5.0 (Git Hash e2ac1fac44c5078ca927cb9b90e1b3066a0b2ed0)
  - OpenMP 201511 (a.k.a. OpenMP 4.5)
  - NNPACK is enabled
  - CPU capability usage: AVX2
  - CUDA Runtime 10.1
  - NVCC architecture flags: -gencode;arch=compute_37,code=sm_37;\
    -gencode;arch=compute_50,code=sm_50;\
    -gencode;arch=compute_60,code=sm_60;\
    -gencode;arch=compute_61,code=sm_61;\
    -gencode;arch=compute_70,code=sm_70;\
    -gencode;arch=compute_75,code=sm_75;\
    -gencode;arch=compute_37,code=compute_37
  - CuDNN 7.6.3
  - Magma 2.5.2
  - Build settings: BLAS=MKL, \
    BUILD_TYPE=Release, \
    CXX_FLAGS= -Wno-deprecated -fvisibility-inlines-hidden -DUSE_PTHREADPOOL -fopenmp \
    -DNDEBUG -DUSE_FBGEMM -DUSE_QNNPACK -DUSE_PYTORCH_QNNPACK -DUSE_XNNPACK \
    -DUSE_VULKAN_WRAPPER -O2 -fPIC -Wno-narrowing -Wall -Wextra -Werror=return-type \
    -Wno-missing-field-initializers -Wno-type-limits -Wno-array-bounds -Wno-unknown-pragmas \
    -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-function \
    -Wno-unused-result -Wno-unused-local-typedefs -Wno-strict-overflow -Wno-strict-aliasing \
    -Wno-error=deprecated-declarations -Wno-stringop-overflow -Wno-error=pedantic \
    -Wno-error=redundant-decls -Wno-error=old-style-cast -fdiagnostics-color=always \
    -faligned-new -Wno-unused-but-set-variable -Wno-maybe-uninitialized -fno-math-errno \
    -fno-trapping-math -Werror=format -Wno-stringop-overflow, \
    PERF_WITH_AVX=1, PERF_WITH_AVX2=1, PERF_WITH_AVX512=1, \
    USE_CUDA=ON, \
    USE_EXCEPTION_PTR=1, \
    USE_GFLAGS=OFF, USE_GLOG=OFF, \
    USE_MKL=ON, \
    USE_MKLDNN=ON, \
    USE_MPI=OFF, \
    USE_NCCL=ON, \
    USE_NNPACK=ON, \
    USE_OPENMP=ON, \
    USE_STATIC_DISPATCH=OFF
```
# 编译最小尺度的CPU版本静态库（MKL后端）
在这个最小尺度的CPU版本里，Gemfield将会选择MKL作为LAPACK的实现。此外，Gemfield将会首先禁用CUDA，这是自然而然的。其次Gemfield还要禁用caffe2（因为目的是编译libtorch），这会连带着禁用caffe2的op。整体要禁用的模块还有：

- caffe2；
- 可执行文件；
- python；
- test；
- numa；
- 分布式（DISTRIBUTED）；
- ROCM;
- GLOO；
- MPI；
- CUDA;

## 1，安装MKL
既然选择了MKL，第一步就是要安装它。MKL使用的是ISSL授权（Intel Simplified Software License）：
```
root@gemfield:~# wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB
root@gemfield:~# apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB
root@gemfield:~# echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mkl.list
root@gemfield:~# apt update
root@gemfield:~# apt install intel-mkl-64bit-2020.4-912
```
## 2，使用CMake构建
命令如下：
```
cmake \
-DCMAKE_VERBOSE_MAKEFILE:BOOL=1 \
-DUSE_CUDA=OFF \
-DBUILD_CAFFE2=OFF \
-DBUILD_PYTHON:BOOL=OFF \
-DBUILD_CAFFE2_OPS=OFF \
-DUSE_DISTRIBUTED=OFF \
-DBUILD_TEST=OFF \
-DBUILD_BINARY=OFF \
-DBUILD_MOBILE_BENCHMARK=0 \
-DBUILD_MOBILE_TEST=0 \
-DUSE_ROCM=OFF \
-DUSE_GLOO=OFF \
-DUSE_LEVELDB=OFF \
-DUSE_MPI:BOOL=OFF \
-DBUILD_CUSTOM_PROTOBUF:BOOL=OFF \
-DUSE_OPENMP:BOOL=OFF \
-DBUILD_SHARED_LIBS:BOOL=OFF \
-DCMAKE_BUILD_TYPE:STRING=Release \
-DPYTHON_EXECUTABLE:PATH=`which python3` \
-DCMAKE_INSTALL_PREFIX:PATH=../libtorch_cpu_mkl \
../pytorch
```
然后使用如下的命令进行编译：
```
cmake --build . --target install -- "-j8"
```
编译成功后，生成的静态库有（23个，其中一个是链接文件）：
```
lib/libprotobuf.a
lib/libsleef.a
lib/libclog.a
lib/libcpuinfo.a
lib/libnnpack.a
lib/libasmjit.a
lib/libmkldnn.a
lib/libpytorch_qnnpack.a
lib/libcaffe2_protos.a
lib/libprotobuf-lite.a
lib/libfbgemm.a
lib/libc10.a
lib/libpthreadpool.a
lib/libtorch_cpu.a
lib/libdnnl.a
lib/libqnnpack.a
lib/libprotoc.a
lib/libXNNPACK.a
lib/libtorch.a
lib/libonnx_proto.a
lib/libfmt.a
lib/libonnx.a
lib/libfoxi_loader.a
```
或者你也想编译Caffe2的话，就开启BUILD_CAFFE2编译开关：
```
cmake \
-DCMAKE_VERBOSE_MAKEFILE:BOOL=1 \
-DBUILD_CAFFE2=ON \
-DBUILD_CAFFE2_OPS=ON \
-DUSE_OPENMP=ON \
-DUSE_MKLDNN=ON \
-DUSE_GFLAGS=OFF \
-DUSE_GLOG=OFF \
-DUSE_CUDA=OFF \
-DBUILD_PYTHON:BOOL=OFF \
-DUSE_DISTRIBUTED=OFF \
-DBUILD_TEST=OFF \
-DBUILD_BINARY=OFF \
-DBUILD_MOBILE_BENCHMARK=0 \
-DBUILD_MOBILE_TEST=0 \
-DUSE_ROCM=OFF \
-DUSE_GLOO=OFF \
-DUSE_LEVELDB=OFF \
-DUSE_MPI:BOOL=OFF \
-DBUILD_SHARED_LIBS:BOOL=OFF \
-DCMAKE_BUILD_TYPE:STRING=Release \
-DPYTHON_EXECUTABLE:PATH=`which python3` \
-DCMAKE_INSTALL_PREFIX:PATH=../libtorch_cpu_caffe2 \
../pytorch
```
生成的静态库有26个，除了上面的非caffe2版本，还多出来了perfkernel模块生成的：
```
libCaffe2_perfkernels_avx.a
libCaffe2_perfkernels_avx2.a
libCaffe2_perfkernels_avx512.a
```
这三个库包含了如下的API，实现了一些FMA操作：
```
caffe2::EmbeddingLookupIdx_int32_t_float_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int32_t_float_float_true__avx2_fma
caffe2::EmbeddingLookupIdx_int32_t_half_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int32_t_half_float_true__avx2_fma
caffe2::EmbeddingLookupIdx_int32_t_uint8_t_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int32_t_uint8_t_float_true__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_float_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_float_float_true__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_half_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_half_float_true__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_uint8_t_float_false__avx2_fma
caffe2::EmbeddingLookupIdx_int64_t_uint8_t_float_true__avx2_fma
caffe2::EmbeddingLookup_int32_t_float_float_false__avx2_fma
caffe2::EmbeddingLookup_int32_t_float_float_true__avx2_fma
caffe2::EmbeddingLookup_int32_t_half_float_false__avx2_fma
caffe2::EmbeddingLookup_int32_t_half_float_true__avx2_fma
caffe2::EmbeddingLookup_int32_t_uint8_t_float_false__avx2_fma
caffe2::EmbeddingLookup_int32_t_uint8_t_float_true__avx2_fma
caffe2::EmbeddingLookup_int64_t_float_float_false__avx2_fma
caffe2::EmbeddingLookup_int64_t_float_float_true__avx2_fma
caffe2::EmbeddingLookup_int64_t_half_float_false__avx2_fma
caffe2::EmbeddingLookup_int64_t_half_float_true__avx2_fma
caffe2::EmbeddingLookup_int64_t_uint8_t_float_false__avx2_fma
caffe2::EmbeddingLookup_int64_t_uint8_t_float_true__avx2_fma
caffe2::Fused8BitRowwiseEmbeddingLookupIdx_int32_t_uint8_t_float_false__avx2_fma
caffe2::Fused8BitRowwiseEmbeddingLookupIdx_int64_t_uint8_t_float_false__avx2_fma
caffe2::Fused8BitRowwiseEmbeddingLookup_int32_t_uint8_t_float_false__avx2_fma
caffe2::Fused8BitRowwiseEmbeddingLookup_int64_t_uint8_t_float_false__avx2_fma
caffe2::TypedAxpy__avx2_fma
caffe2::TypedAxpy__avx_f16c
caffe2::TypedAxpyHalffloat__avx2_fma
caffe2::TypedAxpyHalffloat__avx_f16c
caffe2::TypedAxpy_uint8_float__avx2_fma
```
此外，SELECTED_OP_LIST可以减少要编译的OP，但本文不讨论——因为Gemfield编译的静态库要满足不同模型的推理。
## 3，使用pytorch静态库（MKL后端版本）
如何让自己的程序链接该静态库呢？由于MKL依赖openmp，因此编译的命令行参数要打开（-fopenmp ）。而PyTorch的代码又需要依赖以下的MKL静态库：
```
/opt/intel/mkl/lib/intel64/libmkl_intel_lp64.a
#/opt/intel/mkl/lib/intel64/libmkl_sequential.a
/opt/intel/mkl/lib/intel64/libmkl_gnu_thread.a
/opt/intel/mkl/lib/intel64/libmkl_core.a
```
以及依赖系统上的这几个共享库：
```
/usr/lib/x86_64-linux-gnu/libpthread.so
/usr/lib/x86_64-linux-gnu/libm.so
/usr/lib/x86_64-linux-gnu/libdl.so
```
因此你的程序需要链接这些库（除了链接pytorch那二十几个静态库外）才能完成编译。感觉很复杂是吧？忘记这些吧，使用我们开源的libdeepvac库吧。libdeepvac封装了libtorch，提供更简化的C++中使用PyTorch模型的方法。

# 编译最小尺度的CPU版本静态库（Eigen后端）
在这个最小尺度的CPU版本里，Gemfield将会选择Eigen来作为LAPACK的实现。使用Eigen来作为LAPACK实现的话，需要打开INTERN_USE_EIGEN_BLAS。看见INTERN前缀了吧，这提示我们不应该这样来使用这个开关。并且由于在PyTorch中，Eigen是为mobile平台而设计使用的，因此要想在x86_64 Linux使用，就需要改下pytorch仓库中的CMake文件：一共2处。
## 1，修改PyTorch的CMake文件
第一处，修改cmake/Dependencies.cmake：
```
#if(NOT INTERN_BUILD_MOBILE)
#  set(AT_MKL_ENABLED 0)
#  set(AT_MKL_MT 0)
#  set(USE_BLAS 1)
#  if(NOT (ATLAS_FOUND OR OpenBLAS_FOUND OR MKL_FOUND OR VECLIB_FOUND OR GENERIC_BLAS_FOUND))
#    message(WARNING "Preferred BLAS (" ${BLAS} ") cannot be found, now searching for a general BLAS library")
#    find_package(BLAS)
#    if(NOT BLAS_FOUND)
#      set(USE_BLAS 0)
#    endif()
#  endif()
#
#  if(MKL_FOUND)
#    add_definitions(-DTH_BLAS_MKL)
#    if("${MKL_THREADING}" STREQUAL "SEQ")
#      add_definitions(-DTH_BLAS_MKL_SEQ=1)
#    endif()
#    if(MSVC AND MKL_LIBRARIES MATCHES ".*libiomp5md\\.lib.*")
#      add_definitions(-D_OPENMP_NOFORCE_MANIFEST)
#      set(AT_MKL_MT 1)
#    endif()
#    set(AT_MKL_ENABLED 1)
#  endif()
if(INTERN_USE_EIGEN_BLAS)
  # Eigen BLAS for Mobile
  set(USE_BLAS 1)
  set(AT_MKL_ENABLED 0)
  include(${CMAKE_CURRENT_LIST_DIR}/External/EigenBLAS.cmake)
  list(APPEND Caffe2_DEPENDENCY_LIBS eigen_blas)
endif()
```
第二处，修改cmake/External/EigenBLAS.cmake：
```
root@gemfield:~# git diff cmake/External/EigenBLAS.cmake
......
 set(__EIGEN_BLAS_INCLUDED TRUE)
-
-if(NOT INTERN_BUILD_MOBILE OR NOT INTERN_USE_EIGEN_BLAS)
+if(NOT INTERN_USE_EIGEN_BLAS)
   return()
 endif()
```
此外，像MKL后端那样，Gemfield要照例禁用CUDA、caffe2、caffe2的op。

## 2，使用CMake进行构建
命令如下（注意开启了INTERN_USE_EIGEN_BLAS）：
```
cmake \
-DINTERN_USE_EIGEN_BLAS=ON \
-DCMAKE_VERBOSE_MAKEFILE:BOOL=1 \
-DBUILD_CAFFE2=OFF \
-DBUILD_CAFFE2_OPS=OFF \
-DBUILD_PYTHON:BOOL=OFF \
-DUSE_DISTRIBUTED=OFF \
-DBUILD_TEST=OFF \
-DBUILD_BINARY=OFF \
-DBUILD_MOBILE_BENCHMARK=0 \
-DBUILD_MOBILE_TEST=0 \
-DUSE_ROCM=OFF \
-DUSE_GLOO=OFF \
-DUSE_CUDA=OFF \
-DUSE_LEVELDB=OFF \
-DUSE_MPI:BOOL=OFF \
-DBUILD_CUSTOM_PROTOBUF:BOOL=OFF \
-DUSE_OPENMP:BOOL=OFF \
-DBUILD_SHARED_LIBS:BOOL=OFF \
-DCMAKE_BUILD_TYPE:STRING=Release \
-DPYTHON_EXECUTABLE:PATH=`which python3` \
-DCMAKE_INSTALL_PREFIX:PATH=../libtorch_cpu_eigen \
../pytorch
```
然后使用如下的命令进行编译：
```
cmake --build . --target install -- "-j8"
```
编译出来的静态库如下所示（24个，注意多出来libeigen_blas.a）：
```
lib/libprotobuf.a
lib/libsleef.a
lib/libclog.a
lib/libcpuinfo.a
lib/libeigen_blas.a
lib/libnnpack.a
lib/libasmjit.a
lib/libmkldnn.a
lib/libpytorch_qnnpack.a
lib/libcaffe2_protos.a
lib/libprotobuf-lite.a
lib/libfbgemm.a
lib/libc10.a
lib/libpthreadpool.a
lib/libtorch_cpu.a
lib/libdnnl.a
lib/libqnnpack.a
lib/libprotoc.a
lib/libXNNPACK.a
lib/libtorch.a
lib/libonnx_proto.a
lib/libfmt.a
lib/libonnx.a
lib/libfoxi_loader.a
```
## 3，使用pytorch静态库（Eigen后端版本）
和MKL后端不同，你的程序需要从链接MKL转而去链接libeigen_blas.a，更简单了。如果使用libdeepvac库的话，这都是无感的。

和MKL后端的静态库进行了下粗略的性能比较，在6核intel处理器的系统上，对20个目标进行CNN+LSTM的计算下，MKL版本消耗了11秒，而Eigen版本消耗了20秒。所以还是推荐使用MKL。

# 编译最小尺度的CUDA版本静态库（无MAGMA版本）
## 1，配置
相关的配置如下：

- 要编译CUDA版本，必须启用USE_CUDA；
- 另外，回落到CPU的时候，我们依然需要有对应的LAPACK实现，这里还是选择MKL，安装方法见前文；
- 还有一个地方需要注意：是否使用MAGMA。这里Gemfield先不使用。

## 2，CUDA架构
同CPU版本相比，编译CUDA版本的最大不同就是要指定CUDA架构（开普勒、麦克斯韦、帕斯卡、图灵、安培等）。要编译特定CUDA架构的目标，需要给NVCC编译器传递特定架构的号码，如7.0。特定架构的号码有两种情况：PTX和非PTX。比如7.0 和 7.0 PTX。

非PTX版本是实际的二进制文件，只能做到主版本号兼容。比如compute capability 3.0 的编译产物只能运行在compute-capability 3.x的架构上（开普勒架构），而不能运行在compute-capability 5.x (麦克斯韦) 或者 6.x (帕斯卡) 设备上。

而PTX版本编译出来的是JIT的中间代码，可以做到前向兼容——也就是旧设备的目标可以运行在新设备上。因为编译的时候可以指定多个架构号码，因此一个技巧就是，总是在最高的版本号上加上PTX，以获得前向兼容，比如：3.5;5.0;5.2;6.0;6.1;7.0;7.5;7.5+PTX。

另外，在不兼容的CUDA设备上运行你的程序会出现“no kernel image is available for execution on the device”错误。编译PyTorch的时候，这个CUDA架构号码来自三种方式：

- 自动检测本地机器上的设备号；
- 检测不到，则使用默认的一组；
- 用户通过TORCH_CUDA_ARCH_LIST环境变量指定。TORCH_CUDA_ARCH_LIST环境变量，比如TORCH_CUDA_ARCH_LIST="3.5 5.2 6.0 6.1+PTX"，决定了要编译的pytorch支持哪些cuda架构。支持的架构越多，最后的库越大；
```
#cuda9
export TORCH_CUDA_ARCH_LIST="3.5;5.0;5.2;6.0;6.1;7.0;7.0+PTX"

#cuda10
export TORCH_CUDA_ARCH_LIST="3.5;5.0;5.2;6.0;6.1;7.0;7.5;7.5+PTX"

#cuda11
export TORCH_CUDA_ARCH_LIST="3.5;5.0;5.2;6.0;6.1;7.0;7.5;8.0;8.0+PTX"

#cuda11.1
export TORCH_CUDA_ARCH_LIST="5.0;7.0;8.0;8.6;8.6+PTX"
```
一些市面上常见显卡的compute-capability号码如下所示：
![v2-44256bea8b73b823f8adf9c5cbc5f7fa_720w](https://github.com/user-attachments/assets/c75863ad-4076-4139-a4fb-eab07b98b649)


## 3，使用CMake进行构建
cmake命令如下（注意打开了USE_CUDA）：
```
cmake \
-DCMAKE_VERBOSE_MAKEFILE:BOOL=1 \
-DUSE_CUDA=ON \
-DBUILD_CAFFE2=OFF \
-DBUILD_CAFFE2_OPS=OFF \
-DUSE_DISTRIBUTED=OFF \
-DBUILD_TEST=OFF \
-DBUILD_BINARY=OFF \
-DBUILD_MOBILE_BENCHMARK=0 \
-DBUILD_MOBILE_TEST=0 \
-DUSE_ROCM=OFF \
-DUSE_GLOO=OFF \
-DUSE_LEVELDB=OFF \
-DUSE_MPI:BOOL=OFF \
-DBUILD_PYTHON:BOOL=OFF \
-DBUILD_CUSTOM_PROTOBUF:BOOL=OFF \
-DUSE_OPENMP:BOOL=OFF \
-DBUILD_SHARED_LIBS:BOOL=OFF \
-DCMAKE_BUILD_TYPE:STRING=Release \
-DPYTHON_EXECUTABLE:PATH=`which python3` \
-DCMAKE_INSTALL_PREFIX:PATH=../libtorch_cuda \
../pytorch
```
在CUDA版本中，CMake构建时还会检测：
```
    -- CUDA detected: 10.2 
    -- CUDA nvcc is: /usr/local/cuda/bin/nvcc 
    -- CUDA toolkit directory: /usr/local/cuda 
    -- cuDNN: v7.6.5  (include: /usr/include, library: /usr/lib/x86_64-linux-gnu/libcudnn.so) 
    -- Autodetected CUDA architecture(s): 3.5;5.0;5.2;6.0;6.1;7.0;7.5;7.5+PTX;
    -- Found CUDA with FP16 support, compiling with torch.cuda.HalfTensor;
```
然后使用如下的命令进行编译：
```
cmake --build . --target install -- "-j8"
```
编译出如下的静态库（26个）：
```
libasmjit.a
libc10.a
libc10_cuda.a
libcaffe2_protos.a
libclog.a
libcpuinfo.a
libdnnl.a
libfbgemm.a
libfmt.a
libfoxi_loader.a
libmkldnn.a
libnccl_static.a
libnnpack.a
libonnx.a
libonnx_proto.a
libprotobuf.a
libprotobuf-lite.a
libprotoc.a
libpthreadpool.a
libpytorch_qnnpack.a
libqnnpack.a
libsleef.a
libtorch.a
libtorch_cpu.a
libtorch_cuda.a
libXNNPACK.a
```
可以看到相比CPU版本多出了libtorch_cuda.a、 libc10_cuda.a、libnccl_static.a这3个静态库。
## 4，使用pytorch静态库（CUDA版本）
和CPU版本类似，但是区别是还要链接NVIDIA的cuda运行时的库（这部分是动态库）。此外，如果你的程序初始化的时候报错：“PyTorch is not linked with support for cuda devices”，说明你没有whole_archive c10_cuda.a静态库。

如果你编译自己程序的时候遇到了cannot find -lnvToolsExt、cannot find -lcudart这样的错误，你还需要设置下环境变量让链接器能够找到cuda运行时的库：
```
root@gemfield:~# export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/cuda-10.2/targets/x86_64-linux/lib/
```
总之，你如果使用了libdeepvac封装的话（需要打开USE_CUDA），就没有这么多问题了。
## 5，性能
做了一个快速的不严谨的推理性能测试。使用了cuda版本后，还是之前的那个系统，还是之前那个测试任务（对20个目标进行CNN+LSTM的计算下），CUDA版本消耗了不到一秒。
# 最后
在你使用pytorch静态库的时候，或多或少还会遇到一些问题。但是，何必自讨苦吃呢，使用我们封装了libtorch的libdeepvac库吧：
DeepVAC/libdeepvac

一个编译命令：
```
export TORCH_CUDA_ARCH_LIST="6.1;7.0;7.5;7.5+PTX"

cmake \
-DCMAKE_VERBOSE_MAKEFILE:BOOL=1 \
-DUSE_CUDA=ON \
-DUSE_OPENMP=ON \
-DBUILD_CAFFE2=ON \
-DBUILD_CAFFE2_OPS=ON \
-DUSE_DISTRIBUTED=OFF \
-DBUILD_TEST=OFF \
-DBUILD_BINARY=OFF \
-DBUILD_MOBILE_BENCHMARK=0 \
-DBUILD_MOBILE_TEST=0 \
-DUSE_ROCM=OFF \
-DUSE_GLOO=OFF \
-DUSE_LEVELDB=OFF \
-DUSE_MPI:BOOL=OFF \
-DBUILD_PYTHON:BOOL=OFF \
-DBUILD_CUSTOM_PROTOBUF:BOOL=OFF \
-DBUILD_SHARED_LIBS:BOOL=OFF \
-DCMAKE_BUILD_TYPE:STRING=Release \
-DPYTHON_EXECUTABLE:PATH=`which python3` \
-DCMAKE_INSTALL_PREFIX:PATH=../libtorch_cuda \
../pytorch
```

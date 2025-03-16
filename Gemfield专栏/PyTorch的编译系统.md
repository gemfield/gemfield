# 背景
本文以PyTorch 1.0为基础。PyTorch的编译首先是python风格的编译，使用了python的setuptools编译系统。以最基本的编译安装命令python setup.py install 为例，这一编译过程包含了如下几个主要阶段：
- 1，setup.py入口；
- 2，提前检查依赖项；
- 3，使用cmake生成Makefile；
- 4，Make命令——中间源文件的产生；
- 5，Make命令——编译三方库；
- 6，Make命令——生成静态库、动态库、可执行文件；
- 7，Make命令——拷贝文件到合适路径下；
- 8，setuptools之build_py；
- 9，setuptools之build_ext；
- 10，setuptools之install_lib。

# setup.py入口
pytorch的编译是从下面这条命令开始的：
```
python setup.py install 
```
这是典型的Python convention，使用python setuptools包中的setup函数来进行install。setup函数接收了几个关键的东西：
- 1，package的名字，从环境变量里取TORCH_PACKAGE_NAME的值，取不到的话就是"torch";
- 2，version，gemfield使用的时候版本为version = '1.1.0a0'；
- 3，ext_modules，用来指定使用C/C++编写的模块，这个不像普通的python模块那么容易找到规律。毕竟用C/C++的时候，你得指定源文件、编译的参数、头文件路径、链接库路径等（setuptools工具又不是神仙，它怎么猜的出）。所以使用ext_modules keyword参数来指定所有需要这样编译的模块，用一个list来描述，list中的每个元素是一个Extension实例，用来描述编译C++所需要的源文件、编译的参数、头文件路径、链接库路径等。PyTorch中，这样的ext_modules有：
```
torch._C （源文件为torch/csrc/stub.cpp，目的so为torch_python.so）
torch._dl（源文件为torch/csrc/dl.c）
torch._nvrtc （源文件为torch/csrc/nvrtc.cpp）
#以及3个caffe2扩展：
caffe2.python.caffe2_pybind11_state
caffe2.python.caffe2_pybind11_state_gpu
caffe2.python.caffe2_pybind11_state_hip
```
- 4，cmdclass，setup的操作参数，是一个字典：
```
'create_version_file': <class '__main__.create_version_file'>
'build': <class '__main__.build'>
'build_py': <class '__main__.build_py'>
'build_ext': <class '__main__.build_ext'>
'build_deps': <class '__main__.build_deps'>
'build_module': <class '__main__.build_module'>
'rebuild': <class '__main__.rebuild'>
'develop': <class '__main__.develop'>
'install': <class '__main__.install'>
'clean': <class '__main__.clean'>
'build_caffe2': <class '__main__.build_dep'>, 
'rebuild_caffe2': <class '__main__.rebuild_dep'
```
因为我们执行的是python setup.py install，所以这里将会调用__main__.install（中的run方法）。install所做的工作就是调用build_deps和install。Gemfield将在下面的章节中探讨。
- 5，packages，指定项目中python源代码的路径。通常使用find_packages() 默认在和setup.py同一目录下搜索各个含有 __init__.py的包；
- 6，entry_points使用python的机制来注册你的命令，比如在PyTorch的setup.py中，entry_points如下所示：
```
entry_points = {
    'console_scripts': [
        'convert-caffe2-to-onnx = caffe2.python.onnx.bin.conversion:caffe2_to_onnx',
        'convert-onnx-to-caffe2 = caffe2.python.onnx.bin.conversion:onnx_to_caffe2',
    ]
}
```
以convert-caffe2-to-onnx为例，setup.py会在PATH路径下生成convert-caffe2-to-onnx文件，这个文件的内容如下：
```
#!/root/miniconda3/bin/python3
# EASY-INSTALL-ENTRY-SCRIPT: 'torch==1.1.0a0+ffd6138','console_scripts','convert-caffe2-to-onnx'
__requires__ = 'torch==1.1.0a0+ffd6138'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('torch==1.1.0a0+ffd6138', 'console_scripts', 'convert-caffe2-to-onnx')()
    )
```
- 7，package_data，指定将什么文件打包到package里，使用这个参数一般是因为有些要打包的文件是动态生成的（也就是执行setup.py过程中生成的）。在PyTorch里，package_data主要是一些动态库和头文件。
# 提前检查依赖项
1，检查以下三方库的CMakeLists.txt:
```
"gloo", "CMakeLists.txt"
"pybind11", "CMakeLists.txt"
'cpuinfo', 'CMakeLists.txt'
'onnx', 'CMakeLists.txt'
'QNNPACK', 'CMakeLists.txt'
'fbgemm', 'CMakeLists.txt'
```

2，检查必备的python 包

检查yaml、typing是否能够import。

# 使用cmake生成Makefile
使用tools/build_pytorch_libs.sh脚本来编译。在默认情况下，PyTorch会使用下面的命令和环境变量来开始caffe2的编译：
```
#command
bash ../tools/build_pytorch_libs.sh --use-cuda --use-fbgemm --use-nnpack --use-mkldnn --use-qnnpack caffe2

#env
CUDNN_VERSION: 7.4.1.5
HOSTNAME: skyweb
NVIDIA_REQUIRE_CUDA: cuda>=9.0
......
PYTORCH_PYTHON_LIBRARY: /root/miniconda3/lib/libpython3.7m.so.1.0
PYTORCH_PYTHON_INCLUDE_DIR: /root/miniconda3/include/python3.7m
PYTORCH_BUILD_VERSION: 1.1.0a0+ffd6138
CMAKE_PREFIX_PATH: /root/miniconda3/lib/python3.7/site-packages
VERBOSE_SCRIPT: 1
```
这个命令会创建torch/lib/tmp_install目录，接着使用cmake工具生成Makefile：
```
cmake /home/gemfield/github/pytorch -DPYTHON_EXECUTABLE=/root/miniconda3/bin/python -DPYTHON_LIBRARY=/root/miniconda3/lib/libpython3.7m.so.1.0 -DPYTHON_INCLUDE_DIR=/root/miniconda3/include/python3.7m -DBUILDING_WITH_TORCH_LIBS=ON -DTORCH_BUILD_VERSION=1.1.0a0+ffd6138 -DCMAKE_BUILD_TYPE=Release -DBUILD_TORCH=ON -DBUILD_PYTHON=ON -DBUILD_SHARED_LIBS=ON -DBUILD_BINARY=OFF -DBUILD_TEST=ON -DINSTALL_TEST=ON -DBUILD_CAFFE2_OPS=ON -DONNX_NAMESPACE=onnx_torch -DUSE_CUDA=1 -DUSE_DISTRIBUTED=ON -DUSE_FBGEMM=1 -DUSE_NUMPY= -DNUMPY_INCLUDE_DIR= -DUSE_SYSTEM_NCCL=ON -DNCCL_INCLUDE_DIR=/usr/include -DNCCL_ROOT_DIR=/usr/ -DNCCL_SYSTEM_LIB=/usr/lib/x86_64-linux-gnu/libnccl.so.2.3.7 -DCAFFE2_STATIC_LINK_CUDA=0 -DUSE_ROCM=0 -DUSE_NNPACK=1 -DUSE_LEVELDB=OFF -DUSE_LMDB=OFF -DUSE_OPENCV=OFF -DUSE_QNNPACK=1 -DUSE_TENSORRT=OFF -DUSE_FFMPEG=OFF -DUSE_SYSTEM_EIGEN_INSTALL=OFF -DCUDNN_INCLUDE_DIR=/usr/include/ -DCUDNN_LIB_DIR=/usr/lib/x86_64-linux-gnu/ -DCUDNN_LIBRARY=/usr/lib/x86_64-linux-gnu/libcudnn.so.7 -DUSE_MKLDNN=1 -DNCCL_EXTERNAL=1 -DCMAKE_INSTALL_PREFIX=/home/gemfield/github/pytorch/torch/lib/tmp_install -DCMAKE_C_FLAGS= -DCMAKE_CXX_FLAGS= '-DCMAKE_EXE_LINKER_FLAGS= -Wl,-rpath,$ORIGIN ' '-DCMAKE_SHARED_LINKER_FLAGS= -Wl,-rpath,$ORIGIN ' -DTHD_SO_VERSION=1 -DCMAKE_PREFIX_PATH=/root/miniconda3/lib/python3.7/site-packages
```
cmake的关键configure信息如下（Makefile等配置信息会写到build目录下）：
```
-- General:
--   BLAS                  : MKL
--   CXX flags             :  -Wno-deprecated -fvisibility-inlines-hidden -fopenmp -DUSE_FBGEMM -O2 -fPIC -Wno-narrowing -Wall -Wextra -Wno-missing-field-initializers -Wno-type-limits -Wno-array-bounds -Wno-unknown-pragmas -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-function -Wno-unused-result -Wno-strict-overflow -Wno-strict-aliasing -Wno-error=deprecated-declarations -Wno-error=pedantic -Wno-error=redundant-decls -Wno-error=old-style-cast -Wno-unused-but-set-variable -Wno-maybe-uninitialized
--   Compile definitions   : TH_BLAS_MKL;ONNX_NAMESPACE=onnx_torch;USE_GCC_ATOMICS=1;HAVE_MMAP=1;_FILE_OFFSET_BITS=64;HAVE_SHM_OPEN=1;HAVE_SHM_UNLINK=1;HAVE_MALLOC_USABLE_SIZE=1
--   CMAKE_PREFIX_PATH     : /root/miniconda3/lib/python3.7/site-packages
......
--   Public Dependencies  : Threads::Threads;caffe2::mkl;caffe2::mkldnn
--   Private Dependencies : qnnpack;nnpack;cpuinfo;fbgemm;fp16;gloo;aten_op_header_gen;onnxifi_loader;rt;gcc_s;gcc;dl
```

# Make命令——中间源文件的产生
cmake生成Makefile后，编译系统接着调用make命令来进行编译和install：
```
make install -j24
```
这个编译过程一共产生两种文件（Linux上）：
- 1，根据模板生成源文件，包含cpp文件和Python 文件（大部分是UT）；
- 2，生成.o/.a文件 、动态库 .so文件、可执行文件。

1，ATen部分cpp文件：
```
third_party/protobuf/src/google/protobuf/compiler/js/well_known_types_embed.cc
build/aten/src/ATen/CPUByteType.cpp
build/aten/src/ATen/CPUByteType.h
build/aten/src/ATen/CPUCharType.cpp
build/aten/src/ATen/CPUCharType.h
build/aten/src/ATen/CPUDoubleType.cpp
build/aten/src/ATen/CPUDoubleType.h
build/aten/src/ATen/CPUFloatType.cpp
build/aten/src/ATen/CPUFloatType.h
build/aten/src/ATen/CPUGenerator.h
build/aten/src/ATen/CPUHalfType.cpp
build/aten/src/ATen/CPUHalfType.h
build/aten/src/ATen/CPUIntType.cpp
build/aten/src/ATen/CPUIntType.h
build/aten/src/ATen/CPULongType.cpp
build/aten/src/ATen/CPULongType.h
build/aten/src/ATen/CPUShortType.cpp
build/aten/src/ATen/CPUShortType.h
build/aten/src/ATen/Declarations.yaml
build/aten/src/ATen/Functions.h
build/aten/src/ATen/LegacyTHCPUByteDispatcher.cpp
build/aten/src/ATen/LegacyTHCPUByteDispatcher.h
build/aten/src/ATen/LegacyTHCPUCharDispatcher.cpp
build/aten/src/ATen/LegacyTHCPUCharDispatcher.h
build/aten/src/ATen/LegacyTHCPUDoubleDispatcher.cpp
build/aten/src/ATen/LegacyTHCPUDoubleDispatcher.h
......
build/include/sleef.h
build/sleef/src/libm/include/renameavx2.h
build/sleef/src/libm/include/renameavx2128.h
build/sleef/src/libm/include/renamefma4.h
build/sleef/src/libm/include/renamesse4.h
build/sleef/src/libm/include/renamesse2.h
build/sleef/src/libm/include/renamedsp128.h
build/sleef/src/libm/dispsse.c
```
2，torch部分cpp文件：
```
torch/csrc/nn/THNN.cpp
torch/csrc/nn/THCUNN.cpp
torch/csrc/autograd/generated/VariableType.h
torch/csrc/autograd/generated/VariableType_0.cpp
torch/csrc/autograd/generated/VariableType_1.cpp
torch/csrc/autograd/generated/VariableType_2.cpp
torch/csrc/autograd/generated/VariableType_3.cpp
torch/csrc/autograd/generated/VariableType_4.cpp
torch/csrc/autograd/generated/Functions.h
torch/csrc/autograd/generated/Functions.cpp
torch/csrc/autograd/generated/python_functions.h
torch/csrc/autograd/generated/python_functions.cpp
torch/csrc/autograd/generated/python_variable_methods.cpp
torch/csrc/autograd/generated/python_variable_methods_dispatch.h
torch/csrc/autograd/generated/python_torch_functions.cpp
torch/csrc/autograd/generated/python_torch_functions_dispatch.h
torch/csrc/autograd/generated/python_nn_functions.cpp
torch/csrc/autograd/generated/python_nn_functions.h
torch/csrc/autograd/generated/python_nn_functions_dispatch.h
torch/csrc/autograd/generated/variable_factories.h
torch/csrc/jit/generated/register_aten_ops_0.cpp
torch/csrc/jit/generated/register_aten_ops_1.cpp
torch/csrc/jit/generated/register_aten_ops_2.cpp
```
3，python文件部分：
```
contrib/aten/__init__.py
contrib/aten/docs/__init__.py
contrib/aten/docs/sample.py
contrib/aten/gen_op.py
contrib/cuda-convnet2/__init__.py
contrib/cuda-convnet2/convdata.py
......
python/helpers/train.py
......
python/layers/batch_lr_loss.py
python/layers/batch_mse_loss.py
python/layers/batch_normalization.py
python/layers/batch_sigmoid_cross_entropy_loss.py
python/layers/batch_softmax_loss.py
python/layers/blob_weighted_sum.py
......
python/modeling/net_modifier.py
......
python/onnx/backend.py
......
python/predictor/mobile_exporter.py
......
quantization/server/utils.py
```
# Make命令——编译三方库
在开始阶段会编译third_party目录下的依赖包（基本是facebook和谷歌公司贡献的）。
```
#Facebook开源的cpuinfo，检测cpu信息的
third_party/cpuinfo

#Facebook开源的神经网络模型交换格式，
#目前Pytorch、caffe2、ncnn、coreml等都可以对接
third_party/onnx

#FB (Facebook) + GEMM (General Matrix-Matrix Multiplication)
#Facebook开源的低精度高性能的矩阵运算库，目前作为caffe2 x86的量化运算符的backend。
third_party/fbgemm

#谷歌开源的benchmark库
third_party/benchmark

#谷歌开源的protobuf
third_party/protobuf

#谷歌开源的UT框架
third_party/googletest

#Facebook开源的面向移动平台的神经网络量化加速库
third_party/QNNPACK

#跨机器训练的通信库
third_party/gloo

#Intel开源的使用MKL-DNN做的神经网络加速库
third_party/ideep
```

# Make命令——生成静态库、动态库、可执行文件
编译过程中生成的.a文件：
```
lib/libprotobuf-lite.a
lib/libprotobuf.a
lib/libprotoc.a
lib/libclog.a
lib/libcpuinfo.a
lib/libqnnpack.a
lib/libcpuinfo_internals.a
lib/libpthreadpool.a
lib/libnnpack_reference_layers.a
lib/libnnpack.a
lib/libgtest.a
lib/libgtest_main.a
lib/libbenchmark.a
lib/libbenchmark_main.a
lib/libasmjit.a
lib/libfbgemm.a
lib/libgloo.a
lib/libgloo_cuda.a
lib/libgloo_builder.a
lib/libonnxifi_loader.a
lib/libonnx_proto.a
lib/libonnx.a
lib/libmkldnn.a
lib/libCaffe2_perfkernels_avx2.a
lib/libcaffe2_protos.a
lib/libsleef.a
lib/libCaffe2_perfkernels_avx.a
lib/libCaffe2_perfkernels_avx512.a
lib/libTHD.a
lib/libc10d.a
```
编译过程生成的可执行文件：
```
bin/js_embed
bin/protoc
bin/c10_TypeList_test
bin/c10_TensorTypeId_test
......
bin/c10_cuda_CUDATest
bin/mkrename
bin/mkdisp
bin/utility_ops_gpu_test
.....
bin/blob_gpu_test
bin/cuda_cudnn_test
bin/parallel_net_test
bin/operator_test
......
bin/test_jit
bin/test_api
......
bin/c10_utils_cpu_test
```

编译过程中生成的.so动态库：
```
lib/libonnxifi.so
lib/libonnxifi_dummy.so
lib/libc10.so
lib/libc10_cuda.so
lib/libcaffe2.so
lib/libcaffe2_gpu.so
python/caffe2_pybind11_state.cpython-37m-x86_64-linux-gnu.so
python/caffe2_pybind11_state_gpu.cpython-37m-x86_64-linux-gnu.so
lib/libshm.so
lib/libtorch.so
lib/libtorch_python.so
lib/libc10d_cuda_test.so
lib/libcaffe2_detectron_ops_gpu.so
lib/libcaffe2_module_test_dynamic.so
lib/libcaffe2_observers.so
```
其中：
1，lib/libc10.so由下列源文件编译生成：
```
c10/*.cpp
```
2，lib/libc10_cuda.so由下列源文件编译生成：
```
c10/cuda/CUDAStream.cpp
c10/cuda/impl/CUDAGuardImpl.cpp
c10/cuda/impl/CUDATest.cpp
```
3，lib/libshm.so由下列源文件编译生成：
```
torch/lib/libshm/core.cpp
```
4，lib/libcaffe2.so由下列源文件编译生成：
```
aten/*.cpp
caffe2/core/*.cpp
caffe2/operators/*.cpp
caffe2/utils/*.cpp
caffe2/onnx/*.cpp
caffe2/quantization/*.cpp
caffe2/sgd/*.cpp
...
```
5，lib/libcaffe2_gpu.so由下列源文件编译生成：
```
aten/src/TH/*
aten/src/THCUNN/*
aten/src/ATen/*
caffe2/operators/*.cu
caffe2/sgd/*cu
aten/src/ATen/cuda/*
aten/src/THC/*
aten/src/ATen/cudnn/*
caffe2/operators/*op_cudnn.cc
caffe2/operators/*_gpu.cc
...
```
6，caffe2_pybind11_state.cpython-37m-x86_64-linux-gnu.so由下列源文件编译生成：
```
caffe2/python/pybind_state.cc
caffe2/python/pybind_state_dlpack.cc
caffe2/python/pybind_state_nomni.cc
caffe2/python/pybind_state_registry.cc
caffe2/python/pybind_state_int8.cc
caffe2/python/pybind_state_ideep.cc
```
7，caffe2_pybind11_state_gpu.cpython-37m-x86_64-linux-gnu.so由下列源文件编译生成：
```
caffe2/python/pybind_state.cc
caffe2/python/pybind_state_dlpack.cc
caffe2/python/pybind_state_nomni.cc
caffe2/python/pybind_state_registry.cc
caffe2/python/pybind_state_int8.cc
caffe2/python/pybind_state_ideep.cc
caffe2/python/pybind_state_gpu.cc
```
8，lib/libtorch.so由下列源文件编译生成：
```
torch/csrc/autograd/*.cpp
torch/csrc/autograd/generated/*.cpp
torch/csrc/jit/*.cpp
torch/csrc/utils/*.cpp
torch/csrc/api/*.cpp
```
9，lib/libtorch_python.so由下列源文件编译生成：
```
torch/lib/THD/*.cpp
torch/lib/c10d/*.cpp
torch/csrc/*.cpp
torch/csrc/*.cpp
torch/csrc/autograd/generated/python_*.cpp
torch/csrc/autograd/python_*.cpp
torch/csrc/jit/*.cpp
torch/csrc/utils/*.cpp
torch/csrc/cuda/*.cpp
torch/csrc/distributed/*.cpp
```
注意libtorch_python.so编译的时候也需要链接libtorch.so文件。

# Make命令——拷贝文件到合适路径下
这一步的核心工作就是使用make install来将make过程中产生的文件：
```
pytorch/torch/lib/tmp_install/lib/libTHD.a 
pytorch/torch/lib/tmp_install/lib/libasmjit.a 
pytorch/torch/lib/tmp_install/lib/libc10.so 
pytorch/torch/lib/tmp_install/lib/libc10_cuda.so 
pytorch/torch/lib/tmp_install/lib/libc10d.a 
pytorch/torch/lib/tmp_install/lib/libcaffe2.so 
pytorch/torch/lib/tmp_install/lib/libcaffe2_detectron_ops_gpu.so 
pytorch/torch/lib/tmp_install/lib/libcaffe2_gpu.so 
pytorch/torch/lib/tmp_install/lib/libcaffe2_module_test_dynamic.so 
pytorch/torch/lib/tmp_install/lib/libcaffe2_observers.so 
pytorch/torch/lib/tmp_install/lib/libclog.a 
pytorch/torch/lib/tmp_install/lib/libcpuinfo.a 
pytorch/torch/lib/tmp_install/lib/libfbgemm.a 
pytorch/torch/lib/tmp_install/lib/libgloo.a 
pytorch/torch/lib/tmp_install/lib/libgloo_builder.a 
pytorch/torch/lib/tmp_install/lib/libgloo_cuda.a 
pytorch/torch/lib/tmp_install/lib/libmkldnn.a 
pytorch/torch/lib/tmp_install/lib/libnnpack.a 
pytorch/torch/lib/tmp_install/lib/libonnx.a 
pytorch/torch/lib/tmp_install/lib/libonnx_proto.a 
pytorch/torch/lib/tmp_install/lib/libonnxifi.so 
pytorch/torch/lib/tmp_install/lib/libonnxifi_dummy.so 
pytorch/torch/lib/tmp_install/lib/libonnxifi_loader.a 
pytorch/torch/lib/tmp_install/lib/libprotobuf-lite.a 
pytorch/torch/lib/tmp_install/lib/libprotobuf.a 
pytorch/torch/lib/tmp_install/lib/libprotoc.a 
pytorch/torch/lib/tmp_install/lib/libpthreadpool.a 
pytorch/torch/lib/tmp_install/lib/libqnnpack.a 
pytorch/torch/lib/tmp_install/lib/libshm.so 
pytorch/torch/lib/tmp_install/lib/libsleef.a 
pytorch/torch/lib/tmp_install/lib/libtorch.so 
pytorch/torch/lib/tmp_install/lib/libtorch.so.1 
pytorch/torch/lib/tmp_install/lib/libtorch_python.so 
pytorch/torch/lib/tmp_install/lib/pkgconfig 
pytorch/torch/lib/tmp_install/lib/python3.7
```
拷贝到pytorch/torch/lib目录下。使用的是rsync命令：
```
rsync -lptgoD -r /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libTHD.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libasmjit.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libc10.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libc10_cuda.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libc10d.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcaffe2.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcaffe2_detectron_ops_gpu.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcaffe2_gpu.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcaffe2_module_test_dynamic.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcaffe2_observers.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libclog.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libcpuinfo.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libfbgemm.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libgloo.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libgloo_builder.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libgloo_cuda.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libmkldnn.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libnnpack.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libonnx.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libonnx_proto.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libonnxifi.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libonnxifi_dummy.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libonnxifi_loader.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libprotobuf-lite.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libprotobuf.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libprotoc.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libpthreadpool.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libqnnpack.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libshm.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libsleef.a /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libtorch.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libtorch.so.1 /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/libtorch_python.so /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/pkgconfig /home/gemfield/github/pytorch/torch/lib/tmp_install/lib/python3.7 .
```
# setuptools之build_py
这个步骤就是来生成python的package的Python部分，在这个阶段，我们要做的工作主要就是拷贝文件到符合package目录规范的文件夹里：
- 1，拷贝一些cpp的header文件到build/lib.linux-x86_64-3.7；
- 2，拷贝一些py文件到build/lib.linux-x86_64-3.7；
- 3，拷贝一些可执行文件到build/lib.linux-x86_64-3.7；
- 4，拷贝一些cuda header文件到build/lib.linux-x86_64-3.7；
- 5，拷贝一些cmake文件到build/lib.linux-x86_64-3.7；
- 6，拷贝一些zip文件到build/lib.linux-x86_64-3.7；
- 7，拷贝一些so文件到build/lib.linux-x86_64-3.7：

动态库so文件比较重要，在build_py阶段拷贝到build/lib.linux-x86_64-3.7的so文件有：
```
torch/lib/libcaffe2_module_test_dynamic.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libtorch.so.1 -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libonnxifi_dummy.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libtorch.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libc10.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libshm.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libcaffe2_observers.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libonnxifi.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libcaffe2.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libtorch_python.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libcaffe2_gpu.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libc10_cuda.so -> build/lib.linux-x86_64-3.7/torch/lib
torch/lib/libcaffe2_detectron_ops_gpu.so -> build/lib.linux-x86_64-3.7/torch/lib
```
# setuptools之build_ext
这个步骤是用来编译python的c/c++扩展插件的。先拷贝两个共享库到合适的目录下：

1，拷贝caffe2_pybind11_state.cpython-37m-x86_64-linux-gnu.so 到 build/lib.linux-x86_64-3.7/caffe2/python/caffe2_pybind11_state.cpython-37m-x86_64-linux-gnu.so（位于build/lib.linux-x86_64-3.7/caffe2/目录下）；

2，拷贝caffe2_pybind11_state_gpu.cpython-37m-x86_64-linux-gnu.so到build/lib.linux-x86_64-3.7/caffe2/python/caffe2_pybind11_state_gpu.cpython-37m-x86_64-linux-gnu.so（位于build/lib.linux-x86_64-3.7/caffe2/目录下）。

# 编译torch._C模块：
使用c++11标准和_THP_CORE 、ONNX_NAMESPACE=onnx_torch宏，用torch/csrc/stub.cpp源文件，链接libshm.so、libtorch_python.so、libcaffe2_gpu.so生成_C.cpython-37m-x86_64-linux-gnu.so 扩展插件（位于build/lib.linux-x86_64-3.7/torch/目录下）：
```
gcc -pthread -B /root/miniconda3/compiler_compat -Wl,--sysroot=/ -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes -fPIC -I/root/miniconda3/include/python3.7m -c torch/csrc/stub.cpp -o build/temp.linux-x86_64-3.7/torch/csrc/stub.o -D_THP_CORE -DONNX_NAMESPACE=onnx_torch -std=c++11 -Wall -Wextra -Wno-strict-overflow -Wno-unused-parameter -Wno-missing-field-initializers -Wno-write-strings -Wno-unknown-pragmas -Wno-deprecated-declarations -fno-strict-aliasing -Wno-missing-braces
g++ -pthread -shared -B /root/miniconda3/compiler_compat -L/root/miniconda3/lib -Wl,-rpath=/root/miniconda3/lib -Wl,--no-as-needed -Wl,--sysroot=/ build/temp.linux-x86_64-3.7/torch/csrc/stub.o -L/home/gemfield/github/pytorch/torch/lib -L/usr/local/cuda/lib64 -lshm -ltorch_python -o build/lib.linux-x86_64-3.7/torch/_C.cpython-37m-x86_64-linux-gnu.so -Wl,--no-as-needed /home/gemfield/github/pytorch/torch/lib/libcaffe2_gpu.so -Wl,--as-needed -Wl,-rpath,$ORIGIN/lib
```

# 编译torch._dl模块：
使用torch/csrc/dl.c编译出_dl.cpython-37m-x86_64-linux-gnu.so扩展插件（位于build/lib.linux-x86_64-3.7/torch/目录下）：
```
gcc -pthread -B /root/miniconda3/compiler_compat -Wl,--sysroot=/ -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes -fPIC -I/root/miniconda3/include/python3.7m -c torch/csrc/dl.c -o build/temp.linux-x86_64-3.7/torch/csrc/dl.o
gcc -pthread -shared -B /root/miniconda3/compiler_compat -L/root/miniconda3/lib -Wl,-rpath=/root/miniconda3/lib -Wl,--no-as-needed -Wl,--sysroot=/ build/temp.linux-x86_64-3.7/torch/csrc/dl.o -o build/lib.linux-x86_64-3.7/torch/_dl.cpython-37m-x86_64-linux-gnu.so
```

# 编译torch._nvrtc模块：
使用c++11标准，用torch/csrc/nvrtc.cpp源文件和_THP_CORE、ONNX_NAMESPACE=onnx_torch宏，并且链接libcuda.so、 -libnvrtc.so库，从而生成_nvrtc.cpython-37m-x86_64-linux-gnu.so扩展插件（位于build/lib.linux-x86_64-3.7/torch/目录下）：
```
gcc -pthread -B /root/miniconda3/compiler_compat -Wl,--sysroot=/ -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes -fPIC -I/home/gemfield/github/pytorch -I/root/miniconda3/include/python3.7m -c torch/csrc/nvrtc.cpp -o build/temp.linux-x86_64-3.7/torch/csrc/nvrtc.o -D_THP_CORE -DONNX_NAMESPACE=onnx_torch -std=c++11 -Wall -Wextra -Wno-strict-overflow -Wno-unused-parameter -Wno-missing-field-initializers -Wno-write-strings -Wno-unknown-pragmas -Wno-deprecated-declarations -fno-strict-aliasing -Wno-missing-braces
g++ -pthread -shared -B /root/miniconda3/compiler_compat -L/root/miniconda3/lib -Wl,-rpath=/root/miniconda3/lib -Wl,--no-as-needed -Wl,--sysroot=/ build/temp.linux-x86_64-3.7/torch/csrc/nvrtc.o -L/home/gemfield/github/pytorch/torch/lib -L/usr/local/cuda/lib64 -L/usr/local/cuda/lib64/stubs -o build/lib.linux-x86_64-3.7/torch/_nvrtc.cpython-37m-x86_64-linux-gnu.so -Wl,-rpath,$ORIGIN/lib -Wl,--no-as-needed -lcuda -lnvrtc
```

# setuptools之install_lib
这一步完成了安装。

- 1，拷贝共享库到python lib路径下：
```
libcaffe2_module_test_dynamic.so -> python3.7/site-packages/torch/lib
libtorch.so.1 -> /root/miniconda3/lib/python3.7/site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libonnxifi_dummy.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libtorch.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libc10.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libshm.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libcaffe2_observers.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/torch_shm_manager -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libonnxifi.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libcaffe2.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libtorch_python.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libcaffe2_gpu.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libc10_cuda.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/lib/libcaffe2_detectron_ops_gpu.so -> */site-packages/torch/lib
build/lib.linux-x86_64-3.7/torch/_dl.cpython-37m-x86_64-linux-gnu.so -> */site-packages/torch
build/lib.linux-x86_64-3.7/torch/_C.cpython-37m-x86_64-linux-gnu.so -> */site-packages/torch
build/lib.linux-x86_64-3.7/torch/_nvrtc.cpython-37m-x86_64-linux-gnu.so -> */site-packages/torch
build/lib.linux-x86_64-3.7/caffe2/python/caffe2_pybind11_state_gpu.cpython-37m-x86_64-linux-gnu.so -> */site-packages/caffe2/python
build/lib.linux-x86_64-3.7/caffe2/python/caffe2_pybind11_state.cpython-37m-x86_64-linux-gnu.so -> */site-packages/caffe2/python
```

- 2，拷贝header文件到python路径下；
- 3，拷贝py文件到python路径下；
- 4，安装egg_info，也就是torch.egg-info：
```
running install_egg_info
running egg_info
writing torch.egg-info/PKG-INFO
writing dependency_links to torch.egg-info/dependency_links.txt
writing entry points to torch.egg-info/entry_points.txt
writing top-level names to torch.egg-info/top_level.txt
reading manifest file 'torch.egg-info/SOURCES.txt'
writing manifest file 'torch.egg-info/SOURCES.txt'
removing '/root/miniconda3/lib/python3.7/site-packages/torch-1.1.0a0+ffd6138-py3.7.egg-info' (and everything under it)
Copying torch.egg-info to /root/miniconda3/lib/python3.7/site-packages/torch-1.1.0a0+ffd6138-py3.7.egg-info
```

- 5，注册entry_points：
```
Installing convert-caffe2-to-onnx script to /root/miniconda3/bin
Installing convert-onnx-to-caffe2 script to /root/miniconda3/bin
```

# 庆祝
这之后，你就可以愉快的import torch了。让我们再次满怀喜悦的回忆下，import的torch是怎么得来的：
```
import torch
```
- 1，Python会找到sys.path中的torch目录，然后找到其中的__init__.py；
- 2，在这个文件中，会import torch._C，在Python3.7环境中，会加载torch目录中的_C.cpython-37m-x86_64-linux-gnu.so 动态扩展库；
- 3，_C.cpython-37m-x86_64-linux-gnu.so 动态库是由源文件torch/csrc/stub.cpp源文件，并且链接libtorch.so、libshm.so、libtorch_python.so、libcaffe2.so、libcaffe2_gpu.so、libc10_cuda.so、libc10.so生成的；当然不止这些库，还链接其它的三方库，这里gemfield只列出了由PyTorch仓库中编译出来的库。

另外，你也可以使用下面的命令佐证下：
```
gemfield@skyweb:~# ldd ./build/lib.linux-x86_64-3.7/torch/_C.cpython-37m-x86_64-linux-gnu.so | grep -i pytorch
        libshm.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libshm.so (0x00007f3f848c0000)
        libtorch_python.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libtorch_python.so (0x00007f3f83e55000)
        libcaffe2_gpu.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libcaffe2_gpu.so (0x00007f3f7263b000)
        libcaffe2.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libcaffe2.so (0x00007f3f6f57d000)
        libc10.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libc10.so (0x00007f3f6f34e000)
        libtorch.so.1 => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libtorch.so.1 (0x00007f3f6df54000)
        libc10_cuda.so => /home/gemfield/github/pytorch/./build/lib.linux-x86_64-3.7/torch/lib/libc10_cuda.so (0x00007f3f68d61000)
```
- 4，而这里列出来的libtorch.so、libshm.so、libtorch_python.so、libcaffe2.so、libcaffe2_gpu.so、libc10_cuda.so、libc10.so，已经由Gemfield在前文说明过了。

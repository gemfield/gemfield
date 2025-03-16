# 背景
如果你想使用PyTorch官方的预编译的Python包，按照官网的说法：“Commands to install from binaries via Conda or pip wheels are on our website: https://pytorch.org”， 然后使用如下命令：
```
conda install pytorch torchvision torchaudio cudatoolkit=11.0 -c pytorch
```
但是如果想要自己编译这个包该怎么办呢？按照官网的说法是：
```
#安装conda包
conda install numpy ninja pyyaml mkl mkl-include setuptools cmake cffi typing_extensions future six requests dataclasses
conda install -c pytorch magma-cuda110

#克隆pytorch仓库
git clone --recursive https://github.com/pytorch/pytorch
cd pytorch
# if you are updating an existing checkout
git submodule sync
git submodule update --init --recursive

#编译
export CMAKE_PREFIX_PATH=${CONDA_PREFIX:-"$(dirname $(which conda))/../"}
python setup.py install
```
一切看着都很完美，除了以下几个问题：

- 上面有些包（比如magma-cuda110）本来就是pytorch项目编译出来的，我们略过了它；
- 这样编译的包只适用于自己的硬件；
- 并没有说明如何编译输出和PyTorch官方一样的conda包。

那如何自己从零开始编译PyTorch的软件包呢？PyTorch的软件包有多种：conda的、pip的、Libtorch的，每个还有不同cuda版本的（或者cpu的），每个还分别有三大操作系统上的——从最主流的Linux到稍次的macOS再到最不入流的Windows。为了简化叙事，Gemfield就以在Ubuntu 20.04上进行Linux cuda11的conda包 + pip包为例，来讲述从零开始编译的步骤。有以下主要的步骤：

- 前期准备
- 制作基础Docker镜像
- 编译安装magma
- 编译pytorch conda包
- 上传conda包
- 编译pip包

# 前期准备

- 宿主机上克隆PyTorch仓库；
- 宿主机上克隆PyTorch builder仓库（pytorch/builder）；
- 宿主机上安装docker；
- 宿主机上安装Nvidia-docker；

详细步骤不再赘述。
# 准备基础Docker镜像
1，构建gemfield/conda-cuda-base

直接pull该镜像：
```
docker pull gemfield/cuda:11.0.3-cudnn8-devel-ubuntu20.04
```
该镜像的Dockerfile来自：
https://github.com/CivilNet/Gemfield/blob/master/dockerfiles/pytorch-dev/Dockerfile.cuda11.0-cudnn8-devel-ubuntu20.04​

# 编译安装magma
其实并不用编译，上述的镜像以及Dockerfile中都已经包含。但如果你想知道magma包是怎么来的，则使用如下4个步骤来编译尝试下：

1，运行Docker容器

在宿主机上：
```
docker run --rm -it -h gemfield \
    -e PACKAGE_TYPE=conda \
    -e DESIRED_CUDA=cu110 \
    -e DESIRED_PYTHON=3.8 \
    -e PYTORCH_BUILD_VERSION=1.8.0 \
    -e PYTORCH_BUILD_NUMBER=1 \
    -e OVERRIDE_PACKAGE_VERSION=1.8.0 \
    -e TORCH_CONDA_BUILD_FOLDER=pytorch-nightly \
    -v /gemfield/hostpv/gemfield/github/pytorch:/pytorch \
    -v /gemfield/hostpv/gemfield/github/builder:/builder \
    -v "$(pwd):/final_pkgs" \
    gemfield/cuda:11.0.3-cudnn8-devel-ubuntu20.04 bash
```
2，编译magma

在容器中：
```
root@gemfield:/builder# export DESIRED_CUDA=11.1
root@gemfield:/builder# export PACKAGE_NAME=magma-cuda111
root@gemfield:/builder# export CUDA_POINTER_ATTR_PATCH="     - cudaPointerAttributes.patch"
root@gemfield:/builder# export CUDA_ARCH_LIST="-gencode arch=compute_60,code=sm_60 -gencode arch=compute_61,code=sm_61 -gencode arch=compute_70,code=sm_70 -gencode arch=compute_75,code=sm_75 -gencode arch=compute_80,code=sm_80 -gencode arch=compute_86,code=sm_86"

root@gemfield:/builder# bash -x magma/build_magma.sh
```
3，上传magma

上传到conda仓库：
```
root@gemfield:/builder/magma# anaconda login
root@gemfield:/builder/magma# anaconda upload -u gemfield --force output/*/magma-cuda*.bz2
```
4，使用本地magma来安装

这里gemfield使用本地编译的tar.bz2包来安装：
```
root@gemfield:/builder/magma# conda install --offline /builder/magma/output/linux-64/magma-cuda111-2.5.2-1.tar.bz2
```
# 编译安装PyTorch
1，运行Docker容器

在宿主机上：
```
docker run --rm -it -h gemfield \
    -e PACKAGE_TYPE=conda \
    -e DESIRED_CUDA=cu110 \
    -e DESIRED_PYTHON=3.8 \
    -e PYTORCH_BUILD_VERSION=1.8.0 \
    -e PYTORCH_BUILD_NUMBER=1 \
    -e OVERRIDE_PACKAGE_VERSION=1.8.0 \
    -e TORCH_CONDA_BUILD_FOLDER=pytorch-nightly \
    -v /gemfield/hostpv/gemfield/github/pytorch:/pytorch \
    -v /gemfield/hostpv/gemfield/github/builder:/builder \
    -v "$(pwd):/final_pkgs" \
    gemfield/cuda:11.0.3-cudnn8-devel-ubuntu20.04 bash
```
2，编译pytorch

在当前的容器上，执行/builder/conda/build_pytorch.sh：
```
root@gemfield:/builder# /builder/conda/build_pytorch.sh
```
注意，这个脚本（连同其调用的脚本）需要改动如下地方：
```
#conda/switch_cuda_version.sh
export CUDNN_VERSION=$(ls /usr/lib/x86_64-linux-gnu/libcudnn.so.*|sort|tac | head -1 | rev | cut -d"." -f -3 | rev)

#conda/build_pytorch.sh
export ANACONDA_TOKEN="gemfield-is-a-civilnet-maintainer"
if [ -z "$ANACONDA_TOKEN" ]; then
    echo "ANACONDA_TOKEN is unset. Please set it in your environment before running this script";
    exit 1
fi
if [[ -z "$ANACONDA_USER" ]]; then
    ANACONDA_USER=gemfield
fi
```
注意，如果一个conda包分明已经安装好了，但conda build的时候还是报错：conda_build.exceptions.DependencyNeedsBuildingError: Unsatisfiable dependencies for platform linux-64: {'magma-cuda110'}。那说明你还需要添加channels：
```
conda config --add channels pytorch
```
3，build_pytorch.sh做了什么？

这个脚本的实质性工作如下：
```
export PYTORCH_GITHUB_ROOT_DIR=/pytorch
export PYTORCH_BUILD_STRING=py3.8_cuda11.0.221_cudnn8.0.5_0
export PYTORCH_MAGMA_CUDA_VERSION=110

conda build -c gemfield --python 3.8 --output-folder out_py3.8_cuda11.0.221_cudnn8.0.5_0_20210128 --no-test pytorch-nightly
```
你是不是看到了conda build命令？conda build的输入主要就是pytorch-nightly目录下的meta.yaml和build.sh，而build.sh的主要工作就是：
```
export TORCH_CUDA_ARCH_LIST="6.1;7.0;7.5;8.0"
export TORCH_NVCC_FLAGS="-Xfatbin -compress-all"
export NCCL_ROOT_DIR=/usr/local/cuda

export USE_STATIC_CUDNN=1
export USE_STATIC_NCCL=1

python setup.py install

#一些ELF方面的工作
patchelf *
```
其中，python setup.py install 范畴内的工作gemfield之前的专栏文章已经提到过，主要就是：

- 编译源文件，生成各种库；
- 将库、头文件、py文件拷贝至build/lib.linux-x86_64-3.8/torch；
- 再从build下拷贝至$PREFIX/lib/python3.8/site-packages/torch；
- 将py文件byte-compiling成pyc文件；

编译的中间产物就在/opt/conda/conda-bld/目录下，其实conda build命令最开始就会把pytorch仓库拷贝到/opt/conda/conda-bld/ 目录下：
```
Copying /pytorch to /opt/conda/conda-bld/pytorch_1611655446834/work/
```
而patchelf做的工作如下：
```
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/_dl.cpython-38-x86_64-linux-gnu.so to  $ORIGIN:$ORIGIN/lib:$ORIGIN/../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/_C.cpython-38-x86_64-linux-gnu.so to  $ORIGIN:$ORIGIN/lib:$ORIGIN/../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libtorch_python.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libtorch.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libtorch_global_deps.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libcaffe2_detectron_ops_gpu.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libtorch_cpu.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libtorch_cuda.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libcaffe2_observers.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libcaffe2_nvrtc.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libc10_cuda.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libshm.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libcaffe2_module_test_dynamic.so to  $ORIGIN:$ORIGIN/../../../..
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/lib/libc10.so to  $ORIGIN:$ORIGIN/../../../..
```
怎么设置的rpath呢？如下所示：
```
patchelf --set-rpath '$ORIGIN:$ORIGIN/lib:$ORIGIN/../../..' --force-rpath /opt/conda/conda-bld/pytorch_1611655446834/_h_env_placehold_place/lib/python3.8/site-packages/torch/_dl.cpython-38-x86_64-linux-gnu.so
Setting rpath of $PREFIX/lib/python3.8/site-packages/torch/_dl.cpython-38-x86_64-linux-gnu.so to  $ORIGIN:$ORIGIN/lib:$ORIGIN/../../..

patchelf --print-rpath /opt/conda/conda-bld/pytorch_1611655446834/_h_env_placehold_place/lib/python3.8/site-packages/torch/_dl.cpython-38-x86_64-linux-gnu.so
$ORIGIN:$ORIGIN/lib:$ORIGIN/../../..
```
最终编译成功的PyTorch的包存放于：
```
root@gemfield:/gemfield# find / -name "*pytorch*.tar.bz2" -exec ls -l {} \+
-rw-r--r-- 1 root root  731361865 1月  28 14:19 /builder/conda/out_py3.8_cuda11.0.221_cudnn8.0.5_0_20210128/linux-64/pytorch-1.8.0-py3.8_cuda11.0.221_cudnn8.0.5_0.tar.bz2
-rw-r--r-- 1 root root  731361865 1月  28 14:19 /opt/conda/pkgs/pytorch-1.8.0-py3.8_cuda11.0.221_cudnn8.0.5_0.tar.bz2
```
注意，这步里面如果cuda的TORCH_CUDA_ARCH_LIST过长的话，可能触发RIP相对寻址不到2GB之外内存地址的错误：“relocation truncated to fit: R_X86_64_GOTPCREL against undefined symbol `__gmon_start__”。这个时候有两种解决方法，最简单的方式就是TORCH_CUDA_ARCH_LIST取值变少点。

# 上传conda包
使用anaconda upload命令来上传：
```
root@gemfield:/builder# anaconda upload /opt/conda/pkgs/pytorch-1.8.0-py3.8_cuda11.0.221_cudnn8.0.5_0.tar.bz2
```

# 编译pip包(可选)
1，准备docker环境

使用如下命令把docker容器运行起来：
```
docker run -it --name gemfield_cuda -h gemfield_cuda \
    -v /gemfield/hostpv/gemfield/github/pytorch/:/pytorch \
    gemfield/cuda:11.0.3-cudnn8-devel-ubuntu20.04 bash      
```
注意需要mount宿主机上的pytorch仓库。另外构建gemfield/cuda:11.1.1-cudnn8-devel-ubuntu20.04的Dockerfile来自：
https://github.com/CivilNet/Gemfield/blob/master/dockerfiles/pytorch-dev/Dockerfile.cuda11.0-cudnn8-devel-ubuntu20.04​

2，构建PyTorch

在容器中，切换到/pytorch目录下开始使用pip3命令构建：
```
root@gemfield_cuda:/pytorch# export TORCH_CUDA_ARCH_LIST="6.1 7.0 7.5 8.0" 
root@gemfield_cuda:/pytorch# export CMAKE_PREFIX_PATH="$(dirname $(which conda))/../"
root@gemfield_cuda:/pytorch# python3 setup.py sdist build

#安装
root@gemfield_cuda:/pytorch# python3 setup.py install
```
3，使用以及问题

按照本文编译出来的PyTorch可能在使用的时候遇到Error 804的问题：“Error 804: forward compatibility was attempted on non supported HW”，如下所示：
```
>>> import torch
>>> torch.cuda.is_available()
/opt/conda/lib/python3.8/site-packages/torch/cuda/__init__.py:52: UserWarning: CUDA initialization: Unexpected error from cudaGetDeviceCount(). Did you run some cuda functions before calling NumCudaDevices() that might have already set an error? Error 804: forward compatibility was attempted on non supported HW (Triggered internally at  ../c10/cuda/CUDAFunctions.cpp:104.)
  return torch._C._cuda_getDeviceCount() > 0
```
这是因为以下原因：

- Nvidia driver不匹配cuda；
- 系统需要重启，以重新加载Nvidia driver；
- cuda的forward compatibility问题：参考 ：《Gemfield：PyTorch的CUDA错误：Error 804: forward compatibility was attempted on non supported HW》

# 总结
上述工作完成后，使用conda命令就能搜索到gemfield编译的PyTorch包了：
```
root@gemfield:/# conda search gemfield::pytorch
Loading channels: done
# Name                       Version           Build  Channel             
pytorch                        1.8.0 py3.8_cuda11.0.221_cudnn8.0.5_0  gemfield
```
然后使用下面的命令来安装：
```
root@gemfield:/opt/conda# conda install pytorch -c gemfield
```
然后使用：
```
>>> import torch
>>> x = torch.rand([2,2])
>>> x
tensor([[0.7748, 0.8391],
        [0.9441, 0.3184]])
>>> x.to('cuda:1')
tensor([[0.7748, 0.8391],
        [0.9441, 0.3184]], device='cuda:1')
>>> torch.__version__
'1.8.0'
>>> torch._C._show_config()
'PyTorch built with:\n  - GCC 9.3\n  - C++ Version: 201402\n  - Intel(R) Math Kernel Library Version 2020.0.2 Product Build 20200624 for Intel(R) 64 architecture applications\n  - Intel(R) MKL-DNN v1.7.0 (Git Hash 7aed236906b1f7a05c0917e5257a1af05e9ff683)\n  - OpenMP 201511 (a.k.a. OpenMP 4.5)\n  - NNPACK is enabled\n  - CPU capability usage: AVX2\n  - CUDA Runtime 11.0\n  - NVCC architecture flags: -gencode;arch=compute_61,code=sm_61;-gencode;arch=compute_70,code=sm_70;-gencode;arch=compute_75,code=sm_75;-gencode;arch=compute_80,code=sm_80\n  - CuDNN 8.0.5\n  - Magma 2.5.2\n  - Build settings: BLAS_INFO=mkl, BUILD_TYPE=Release, CUDA_VERSION=11.0, CUDNN_VERSION=8.0.5, CXX_COMPILER=/usr/bin/c++, CXX_FLAGS= -Wno-deprecated -fvisibility-inlines-hidden -DUSE_PTHREADPOOL -fopenmp -DNDEBUG -DUSE_KINETO -DUSE_FBGEMM -DUSE_QNNPACK -DUSE_PYTORCH_QNNPACK -DUSE_XNNPACK -O2 -fPIC -Wno-narrowing -Wall -Wextra -Werror=return-type -Wno-missing-field-initializers -Wno-type-limits -Wno-array-bounds -Wno-unknown-pragmas -Wno-sign-compare -Wno-unused-parameter -Wno-unused-variable -Wno-unused-function -Wno-unused-result -Wno-unused-local-typedefs -Wno-strict-overflow -Wno-strict-aliasing -Wno-error=deprecated-declarations -Wno-stringop-overflow -Wno-psabi -Wno-error=pedantic -Wno-error=redundant-decls -Wno-error=old-style-cast -fdiagnostics-color=always -faligned-new -Wno-unused-but-set-variable -Wno-maybe-uninitialized -fno-math-errno -fno-trapping-math -Werror=format -Werror=cast-function-type -Wno-stringop-overflow, LAPACK_INFO=mkl, PERF_WITH_AVX=1, PERF_WITH_AVX2=1, PERF_WITH_AVX512=1, TORCH_VERSION=1.8.0, USE_CUDA=ON, USE_CUDNN=ON, USE_EXCEPTION_PTR=1, USE_GFLAGS=OFF, USE_GLOG=OFF, USE_MKL=ON, USE_MKLDNN=ON, USE_MPI=OFF, USE_NCCL=ON, USE_NNPACK=ON, USE_OPENMP=ON, \n'
```


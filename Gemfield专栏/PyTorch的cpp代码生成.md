# 背景
PyTorch中有些C++代码是在编译PyTorch的过程中才创建出来的。这个创建过程是由python脚本完成的。那么为什么会有这个过程呢？主要有2种原因：1，可以复用很多代码的逻辑；2，根据配置渲染模板。
其实这种动态生成cpp代码的方式是比较落后的，在C++11、14、17的年代，这样的生成方式大部分可以由C++ template代替。Gemfield可能会择机改写目前这样的方式。

# ONNX proto的生成
这是三方库onnx中的：
```
gemfield@ThinkPad-X1C:~/github/pytorch$ python3 \
    /home/gemfield/github/pytorch/third_party/onnx/onnx/gen_proto.py \
    -p onnx_torch \
    -o /home/gemfield/github/pytorch/build/third_party/onnx/onnx \
    onnx
Processing /home/gemfield/github/pytorch/third_party/onnx/onnx/onnx.in.proto
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx_onnx_torch.proto
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx_onnx_torch.proto3
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx.pb.h
generating /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx_pb.py


gemfield@ThinkPad-X1C:~/github/pytorch$ python3 \
    /home/gemfield/github/pytorch/third_party/onnx/onnx/gen_proto.py \
    -p onnx_torch \
    -o /home/gemfield/github/pytorch/build/third_party/onnx/onnx \
    onnx-operators
Processing /home/gemfield/github/pytorch/third_party/onnx/onnx/onnx-operators.in.proto
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx-operators_onnx_torch.proto
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx-operators_onnx_torch.proto3
Writing /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx-operators.pb.h
generating /home/gemfield/github/pytorch/build/third_party/onnx/onnx/onnx_operators_pb.py
```
# PyTorch ATen代码的动态生成
这部分已经在专栏文章 Gemfield：PyTorch ATen代码的动态生成 中详细描述过了。简单来说，就是：
```
gemfield@ThinkPad-X1C:~/github/pytorch$ python3 \
/home/gemfield/github/pytorch/aten/src/ATen/gen.py \
--source-path /home/gemfield/github/pytorch/aten/src/ATen \
--install_dir /home/gemfield/github/pytorch/build/aten/src/ATen \
/home/gemfield/github/pytorch/aten/src/ATen/Declarations.cwrap \
/home/gemfield/github/pytorch/aten/src/THNN/generic/THNN.h \
/home/gemfield/github/pytorch/aten/src/THCUNN/generic/THCUNN.h \
/home/gemfield/github/pytorch/aten/src/ATen/nn.yaml \
/home/gemfield/github/pytorch/aten/src/ATen/native/native_functions.yaml
```
这个命令会生成以下文件：
```
gemfield@ThinkPad-X1C:~/github/pytorch$ ls -l /home/gemfield/github/pytorch/build/aten/src/ATen
总用量 9728
drwxrwxr-x 2 gemfield gemfield    4096 3月  16 09:13 core_tmp
-rw-rw-r-- 1 gemfield gemfield    8476 3月  16 09:13 CPUBoolType.cpp
-rw-rw-r-- 1 gemfield gemfield    2266 3月  16 09:13 CPUBoolType.h
......
-rw-rw-r-- 1 gemfield gemfield    1657 3月  16 09:13 CUDABoolType.cpp
-rw-rw-r-- 1 gemfield gemfield     827 3月  16 09:13 CUDABoolType.h
......
-rw-rw-r-- 1 gemfield gemfield  188888 3月  16 09:13 CUDAShortType.cpp
-rw-rw-r-- 1 gemfield gemfield   49331 3月  16 09:13 CUDAShortType.h
-rw-rw-r-- 1 gemfield gemfield 1409757 3月  16 09:13 Declarations.yaml
-rw-rw-r-- 1 gemfield gemfield     596 3月  16 09:13 ExtensionBackendRegistration.h
-rw-rw-r-- 1 gemfield gemfield  488123 3月  16 09:13 Functions.h
-rw-rw-r-- 1 gemfield gemfield     199 3月  16 09:13 LegacyTHCPUBoolDispatcher.cpp
-rw-rw-r-- 1 gemfield gemfield     239 3月  16 09:13 LegacyTHCPUBoolDispatcher.h
......
-rw-rw-r-- 1 gemfield gemfield     202 3月  16 09:13 LegacyTHCPUShortDispatcher.cpp
-rw-rw-r-- 1 gemfield gemfield     241 3月  16 09:13 LegacyTHCPUShortDispatcher.h
-rw-rw-r-- 1 gemfield gemfield     203 3月  16 09:13 LegacyTHCUDABoolDispatcher.cpp
-rw-rw-r-- 1 gemfield gemfield     241 3月  16 09:13 LegacyTHCUDABoolDispatcher.h
......
-rw-rw-r-- 1 gemfield gemfield     206 3月  16 09:13 LegacyTHCUDAShortDispatcher.cpp
-rw-rw-r-- 1 gemfield gemfield     243 3月  16 09:13 LegacyTHCUDAShortDispatcher.h
-rw-rw-r-- 1 gemfield gemfield     140 3月  16 09:13 LegacyTHDispatcher.cpp
-rw-rw-r-- 1 gemfield gemfield     333 3月  16 09:13 LegacyTHDispatcher.h
-rw-rw-r-- 1 gemfield gemfield     849 3月  16 09:13 LegacyTHFunctions.h
-rw-rw-r-- 1 gemfield gemfield     435 3月  16 09:13 MSNPUBoolType.cpp
-rw-rw-r-- 1 gemfield gemfield     354 3月  16 09:13 MSNPUBoolType.h
......
-rw-rw-r-- 1 gemfield gemfield  565480 3月  16 09:13 MSNPUType.cpp
-rw-rw-r-- 1 gemfield gemfield  191815 3月  16 09:13 MSNPUType.h
-rw-rw-r-- 1 gemfield gemfield  147261 3月  16 09:13 NativeFunctions.h
-rw-rw-r-- 1 gemfield gemfield    4314 3月  16 09:13 RegisterCPU.cpp
-rw-rw-r-- 1 gemfield gemfield     147 3月  16 09:13 RegisterCPU.h
-rw-rw-r-- 1 gemfield gemfield    2266 3月  16 09:13 RegisterCUDA.cpp
-rw-rw-r-- 1 gemfield gemfield     148 3月  16 09:13 RegisterCUDA.h
-rw-rw-r-- 1 gemfield gemfield    9238 3月  16 09:13 SparseCPUBoolType.cpp
-rw-rw-r-- 1 gemfield gemfield    3784 3月  16 09:13 SparseCPUBoolType.h
......
-rw-rw-r-- 1 gemfield gemfield    9286 3月  16 09:13 SparseCPUShortType.cpp
-rw-rw-r-- 1 gemfield gemfield    3786 3月  16 09:13 SparseCPUShortType.h
-rw-rw-r-- 1 gemfield gemfield    9437 3月  16 09:13 SparseCUDABoolType.cpp
-rw-rw-r-- 1 gemfield gemfield    3928 3月  16 09:13 SparseCUDABoolType.h
......
-rw-rw-r-- 1 gemfield gemfield  407809 3月  16 09:13 TypeDefault.cpp
-rw-rw-r-- 1 gemfield gemfield  199659 3月  16 09:13 TypeDefault.h
-rw-rw-r-- 1 gemfield gemfield  170316 3月  16 09:13 TypeExtendedInterface.h
......
-rw-rw-r-- 1 gemfield gemfield     348 3月  16 09:13 XLAShortType.h
-rw-rw-r-- 1 gemfield gemfield  558946 3月  16 09:13 XLAType.cpp
-rw-rw-r-- 1 gemfield gemfield  191809 3月  16 09:13 XLAType.h
```
# Caffe2 OP的转发逻辑
这部分会生成pytorch/build/caffe2/contrib/aten/aten_op.h文件，这里面定义了ATenOp这个class，用来将caffe2的operator来mapping到ATen上，这也是caffe2和pytorch共享代码的一个层面。生成cpp代码的命令如下：
```
gemfield@ThinkPad-X1C:~/github/pytorch$ python3 \
    /home/gemfield/github/pytorch/caffe2/contrib/aten/gen_op.py \
    --aten_root=/home/gemfield/github/pytorch/aten \
    --template_dir=/home/gemfield/github/pytorch/caffe2/contrib/aten \
    --yaml_dir=/home/gemfield/github/pytorch/build/aten/src/ATen \
    --install_dir=/home/gemfield/github/pytorch/build/caffe2/contrib/aten
Skipping _th_multinomial Because of Arg: Generator * (Generator*) 
Skipping _th_normal Because of Arg: Generator * (Generator*) 
Skipping _th_normal Because of Arg: Generator * (Generator*) 
Skipping _th_normal Because of Arg: Generator * (Generator*) 
......
```
# PyTorch Autograd代码的动态生成
这部分已经在专栏文章 Gemfield：PyTorch Autograd代码的动态生成 中详细描述过了。简单来说，就是：
```
# 依赖 tools/shared/cwrap_common.py,tools/shared/_utils_internal.py (by civilnet)

gemfield@ThinkPad-X1C:~/github/pytorch$ python3 tools/setup_helpers/generate_code.py \
        --declarations-path \
        /home/gemfield/github/pytorch/build/aten/src/ATen/Declarations.yaml \
        --nn-path aten/src/
Writing torch/csrc/nn/THNN.cpp
Writing torch/csrc/nn/THCUNN.cpp
WARNING: derivative ignored for _indices
WARNING: derivative ignored for _values
WARNING: derivative ignored for indices
Writing torch/csrc/autograd/generated/VariableType.h
WARNING: derivative ignored for _indices
WARNING: derivative ignored for indices
Writing torch/csrc/autograd/generated/VariableType_0.cpp
WARNING: derivative ignored for _values
Writing torch/csrc/autograd/generated/VariableType_1.cpp
Writing torch/csrc/autograd/generated/VariableType_2.cpp
Writing torch/csrc/autograd/generated/VariableType_3.cpp
Writing torch/csrc/autograd/generated/VariableType_4.cpp
WARNING: derivative ignored for _indices
WARNING: derivative ignored for _values
WARNING: derivative ignored for indices
Writing torch/csrc/autograd/generated/VariableTypeEverything.cpp
Writing torch/csrc/autograd/generated/Functions.h
Writing torch/csrc/autograd/generated/Functions.cpp
Writing torch/csrc/autograd/generated/python_functions.h
Writing torch/csrc/autograd/generated/python_functions.cpp
Writing torch/csrc/autograd/generated/python_variable_methods.cpp
Writing torch/csrc/autograd/generated/python_variable_methods_dispatch.h
Writing torch/csrc/autograd/generated/python_torch_functions.cpp
Writing torch/csrc/autograd/generated/python_torch_functions_dispatch.h
Writing torch/csrc/autograd/generated/python_nn_functions.cpp
Writing torch/csrc/autograd/generated/python_nn_functions.h
Writing torch/csrc/autograd/generated/python_nn_functions_dispatch.h
Writing torch/csrc/autograd/generated/variable_factories.h
Writing torch/csrc/jit/generated/register_aten_ops_0.cpp
Writing torch/csrc/jit/generated/register_aten_ops_1.cpp
Writing torch/csrc/jit/generated/register_aten_ops_2.cpp
```
# Python Interface生成
用来生成python3的interface，或者stub，可以用来做类型检查。简单来说，就是：
```
gemfield@ThinkPad-X1C:~/github/pytorch$ python3 -mtools.pyi.gen_pyi --declarations-path \
    /home/gemfield/github/pytorch/build/aten/src/ATen/Declarations.yaml
writing ./torch/__init__.pyi
```
# 把OP从Legacy的TH移植到ATen
目前（2019年），这个移植工作还没有结束。也就是还有少数的op残留在TH下。Gemfield简单介绍下如果要移植一个op，需要做什么工作。本文以AdaptiveMaxPooling2d 操作符的移植为例，这个op以前是定义在TH下的，现在则已经移植到了ATen native中了。首先要明白移植会涉及到哪些文件，这些文件是做什么的：
```
#删除
aten/src/THCUNN/SpatialAdaptiveMaxPooling.cu
aten/src/THCUNN/generic/SpatialAdaptiveMaxPooling.cu
aten/src/THNN/generic/SpatialAdaptiveMaxPooling.c

#新增
aten/src/ATen/native/AdaptiveMaxPooling2d.cpp
aten/src/ATen/native/cuda/AdaptiveMaxPooling2d.cu

#yaml配置文件
aten/src/ATen/native/native_functions.yaml
aten/src/ATen/nn.yaml

#更改CMake文件
ten/src/THCUNN/CMakeLists.txt

#更改dispatch文件
aten/src/ATen/native/LegacyNNDefinitions.cpp
aten/src/THCUNN/generic/THCUNN.h
aten/src/THNN/generic/THNN.h
aten/src/THNN/init.cpp
torch/nn/_functions/thnn/auto.py
```
## 删掉legacy的TH文件
移植AdaptiveMaxPooling2d op需要把旧的TH实现删掉：

1，删除ATen op的CPU实现
```
aten/src/THNN/generic/SpatialAdaptiveMaxPooling.c
```
2，删除ATen op的CUDA实现：
```
aten/src/THCUNN/SpatialAdaptiveMaxPooling.cu
aten/src/THCUNN/generic/SpatialAdaptiveMaxPooling.cu
```

## 新增ATen文件
AdaptiveMaxPooling2d op现在要实现在ATen native 下：

### 1，新增ATen op的CPU实现：

新增aten/src/ATen/native/AdaptiveMaxPooling2d.cpp文件，在此文件中，定义了如下函数，调用栈如下所示：
```
#forward
adaptive_max_pool2d_out_cpu  / adaptive_max_pool2d_cpu
|
V
adaptive_max_pool2d_out_cpu_template
|
V
adaptive_max_pool2d_out_frame / adaptive_max_pool2d_out_cpu_template
|
V
adaptive_max_pool2d_single_out_frame

#backward
adaptive_max_pool2d_backward_out_cpu / adaptive_max_pool2d_backward_cpu
|
V
adaptive_max_pool2d_backward_out_frame / adaptive_max_pool2d_backward_out_cpu_template
|
V
adaptive_max_pool2d_backward_single_out_frame
```
可以看到分别实现了AdaptiveMaxPooling2d的前向和反向。
### 2，新增ATen op的CUDA实现：
新增aten/src/ATen/native/cuda/AdaptiveMaxPooling2d.cu文件，在此文件中，定义了如下函数，调用栈如下所示：
```
adaptive_max_pool2d_out_cuda / adaptive_max_pool2d_cuda
|
V
adaptive_max_pool2d_out_cuda_template
|
V
adaptivemaxpool

adaptive_max_pool2d_backward_out_cuda / adaptive_max_pool2d_backward_cuda
|
V
adaptive_max_pool2d_backward_out_cuda_template
|
V
atomicadaptivemaxgradinput / adaptivemaxgradinput
```
可以看到分别实现了AdaptiveMaxPooling2d的前向和反向。
## 更改yaml配置文件
1，aten/src/ATen/native/native_functions.yaml

ATen的native函数是PyTorch目前主推的operator机制，作为对比，老旧的TH/THC函数（使用cwrap定义）将逐渐被ATen的native替代。ATen的native函数声明在native_functions.yaml文件中，然后实现在ATen/native目录下。移植AdaptiveMaxPooling2d op需要修改这个yaml文件：
```
-- func: adaptive_max_pool2d(Tensor self, int[2] output_size, *, Tensor(a!) output, Tensor(b!) indices) -> (Tensor(a!), Tensor(b!))
+- func: adaptive_max_pool2d(Tensor self, int[2] output_size, *, Tensor(a!) out, Tensor(b!) indices) -> (Tensor(a!), Tensor(b!))
   python_module: nn
+  dispatch:
+    CPU: adaptive_max_pool2d_out_cpu
+    CUDA: adaptive_max_pool2d_out_cuda
 
 # Return: (Tensor output, Tensor indices)
 - func: adaptive_max_pool2d(Tensor self, int[2] output_size) -> (Tensor, Tensor)
   python_module: nn
+  dispatch:
+    CPU: adaptive_max_pool2d_cpu
+    CUDA: adaptive_max_pool2d_cuda
 
 - func: adaptive_max_pool2d_backward(Tensor grad_output, Tensor self, Tensor indices, *, Tensor(a!) grad_input) -> Tensor(a!)
   python_module: nn
+  dispatch:
+    CPU: adaptive_max_pool2d_backward_out_cpu
+    CUDA: adaptive_max_pool2d_backward_out_cuda
 
 - func: adaptive_max_pool2d_backward(Tensor grad_output, Tensor self, Tensor indices) -> Tensor
   python_module: nn
+  dispatch:
+    CPU: adaptive_max_pool2d_backward_cpu
+    CUDA: adaptive_max_pool2d_backward_cuda
```
增加dispatch项，正好将函数的执行逻辑分发到了对应的ATen native的实现上。

2，aten/src/ATen/nn.yaml

该文件使用nn_parse进行解析，得到_thnn_前缀的函数的信息。这些信息会放入top env，在后续步骤中用于替换各template文件中的占位符，这是服务于老旧的TH体系的。移植AdaptiveMaxPooling2d op，将dispatch逻辑从这个nn.yaml中移除：
```
-- name: _thnn_adaptive_max_pool2d(Tensor self, IntArrayRef[2] output_size)
-  cname: SpatialAdaptiveMaxPooling
-  scalar_check:
-    output: 'false'
-    grad_input: 'false'
-
```

## 更改dispatch文件

1，aten/src/ATen/native/LegacyNNDefinitions.cpp

去掉以下函数的定义：
```
std::tuple<Tensor &,Tensor &> adaptive_max_pool2d_out(Tensor & output, Tensor & indices, const Tensor & self, IntArrayRef output_size) {
  return at::legacy::th::_thnn_adaptive_max_pool2d_forward_out(output, indices, self, output_size);
}

std::tuple<Tensor,Tensor> adaptive_max_pool2d(const Tensor & self, IntArrayRef output_size) {
  return at::legacy::th::_thnn_adaptive_max_pool2d_forward(self, output_size);
}

Tensor & adaptive_max_pool2d_backward_out(Tensor & grad_input, const Tensor & grad_output, const Tensor & self, const Tensor & indices) {
  return at::legacy::th::_thnn_adaptive_max_pool2d_backward_out(grad_input, grad_output, self, indices);
}

Tensor adaptive_max_pool2d_backward(const Tensor & grad_output, const Tensor & self, const Tensor & indices) {
  return at::legacy::th::_thnn_adaptive_max_pool2d_backward(grad_output, self, indices);
}
```

2，aten/src/THCUNN/generic/THCUNN.h

去掉以下函数的声明：
```
-THC_API void THNN_(SpatialAdaptiveMaxPooling_updateOutput)(
-                  THCState *state,
-                  THCTensor *input,
-                  THCTensor *output,
-                  THCIndexTensor *indices,
-                  int osizeW,
-                  int osizeH);
-
-THC_API void THNN_(SpatialAdaptiveMaxPooling_updateGradInput)(
-                  THCState *state,
-                  THCTensor *input,
-                  THCTensor *gradOutput,
-                  THCTensor *gradInput,
-                  THCIndexTensor *indices);
```

3，aten/src/THNN/generic/THNN.h

去掉以下函数的声明：
```
-TH_API void THNN_(SpatialAdaptiveMaxPooling_updateOutput)(
-          THNNState *state,
-          THTensor *input,
-          THTensor *output,
-          THIndexTensor *indices,
-          int osizeW, int osizeH);
-TH_API void THNN_(SpatialAdaptiveMaxPooling_updateGradInput)(
-          THNNState *state,
-          THTensor *input,
-          THTensor *gradOutput,
-          THTensor *gradInput,
-          THIndexTensor *indices);
```

4，torch/nn/_functions/thnn/auto.py

从exceptions数组中去掉SpatialAdaptiveMaxPooling：
```
def _generate_function_classes(scope_dict):
    global function_list, function_by_name
    function_list = parse_header(THNN_H_PATH)
    function_by_name = {fn.name: fn for fn in function_list}
    classes_to_generate = {fn.name.partition('_')[0] for fn in function_list}
    exceptions = {
        'Linear',
        'IndexLinear',
        'SpatialFullConvolution',
        'SpatialConvolutionMM',
        'TemporalConvolution',
        'SpatialAveragePooling',
        'SpatialMaxPooling',
        'SpatialDilatedMaxPooling',
        'SpatialMaxUnpooling',
-       'SpatialAdaptiveMaxPooling',
        'VolumetricAveragePooling',
        'VolumetricMaxPooling',
        'VolumetricMaxUnpooling',
......
```
# 总结
以上就是在编译PyTorch的过程中创建出来的cpp代码。这个创建过程是由python脚本完成的，主要有ONNX proto（三方库）、PyTorch ATen代码的动态生成、Caffe2 OP的转发逻辑、PyTorch Autograd代码的动态生成、Python Interface生成。

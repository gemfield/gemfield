# 背景
在使用PyTorch深度学习框架的时候，不管是训练还是测试，代码中引入PyTorch的第一句总是：
```
import torch
```
在Gemfield前述专栏文章里，我们已经得知，torch/csrc/stub.cpp链接libshm.so、libtorch_python.so、libcaffe2_gpu.so生成了_C.cpython-37m-x86_64-linux-gnu.so库，而像前述方式import torch的时候，按照python规范，会找到torch package目录下的__init__.py，在这个文件中进一步会调用：
```
from torch._C import *
```
其中torch._C就是_C.cpython-37m-x86_64-linux-gnu.so。因为（以Python3为例）按照Python规范，由于默认的引擎都是CPython，而CPython的C/C++扩展是一个共享库，并且这个共享库安装在PYTHONPATH目录下，并且文件名（不包含后缀）要和module的名字一样，并且这个共享库中要实现PyInit_modulename符号来作为import时候的逻辑入口。

对于PyTorch来说这个modulename 是_C，因此我们可以揣测，在torch/csrc/stub.cpp中一定实现了PyInit_C这个函数。是的，PyTorch就是这么做的，torch/csrc/stub.cpp中的代码就是下面这样：
```
#include <Python.h>

extern PyObject* initModule();
PyMODINIT_FUNC PyInit__C()
{
  return initModule();
}
```
本文将从initModule函数展开，全面阐述PyTorch框架的初始化工作。initModule就是PyTorch初始化时候的第一层调用栈了，因为所有的初始化工作都是在这个函数内完成的，内容比较多，gemfield将其划分为7部分：

# 1，torch._C的诞生：
这一步就是产生torch._C类，并在这个python类上面注册众多函数：
```
PyObject* initModule() {
  //openmp的设置
  THInferNumThreads();
  THPUtils_addPyMethodDefs(methods, TorchMethods);
  THPUtils_addPyMethodDefs(methods, DataLoaderMethods);
  THPUtils_addPyMethodDefs(methods, torch::autograd::python_functions());
  THPUtils_addPyMethodDefs(methods, torch::multiprocessing::python_functions());
  THPUtils_addPyMethodDefs(methods, THCPModule_methods());
  THPUtils_addPyMethodDefs(methods, THCUDNN_methods());
  THPUtils_addPyMethodDefs(methods, THDPModule_methods());
  THPUtils_addPyMethodDefs(methods, torch::distributed::c10d::python_functions());

  module = Py_InitModule("torch._C", methods.data());
  ......
}
```
其中TorchMethods注册了29个方法，都是THPModule_前缀的函数；DataLoaderMethods注册了4个方法，都是THPModule_前缀的函数；torch::autograd::python_functions注册了4个方法；torch::multiprocessing::python_functions注册了1个方法；THCPModule_methods注册了37个CUDA相关的函数，前缀都是THCPModule_；THCUDNN_methods注册了1个方法；THDPModule_methods注册了28个方法；torch::distributed::c10d::python_functions注册了1个方法。

总而言之，在这一小步，我们达到了这样一个里程碑，torch._C符号诞生，并且向torch._C注册了一百余个函数，涉及torch、dataloader、autograd、multiprocess、cuda、cudnn、distribute、c10d方面。

# 2，一些关键类型
以下代码先后初始化了torch._C._PtrWrapper、torch._C.Generator（含5个方法）、FatalError、torch.Size、torch.dtype、torch.iinfo、torch.layout、torch.device：
```
PyObject* initModule() {
  ......
  THPWrapper_init(module);
  THPGenerator_init(module);
  THPException_init(module);
  THPSize_init(module);
  THPDtype_init(module);
  THPDTypeInfo_init(module);
  THPLayout_init(module);
  THPDevice_init(module);
  THPVariable_initModule(module);
  THPFunction_initModule(module);
  THPEngine_initModule(module);
  ......
}
```
# 3，torch._C._TensorBase的诞生
Gemfield将以下三个初始化函数归为这一小节：
```
PyObject* initModule() {
  ......
  THPVariable_initModule(module);
  THPFunction_initModule(module);
  THPEngine_initModule(module);
  ......
}
```
为什么呢？因为地位太显赫了。

THPVariable_initModule(module) 创建了torch._C._TensorBase，这是一切Tensor的基类，在Gemfield的其它专栏文章里将单独解释；

THPFunction_initModule(module)创建了torch._C._FunctionBase，在torch/autograd/function.py中，以下两个类以torch._C._FunctionBase为基类：
```
class Function(with_metaclass(FunctionMeta, _C._FunctionBase, _ContextMethodMixin, _HookMixin))
class BackwardCFunction(_C._FunctionBase, _ContextMethodMixin, _HookMixin)
```
这个Function继承体系就构成了DAG的基础。

THPEngine_initModule(module)创建了torch._C._EngineBase，_EngineBase这个类负责动态图执行之前的preprocess，_EngineBase会将torch.autograd的backward之类的请求预处理后送给真正的Engine去执行。

# 4，pybind11绑定
这一小节的初始化内容都是和pybind11相关的：
```
PyObject* initModule() {
  ......
  // NOTE: We need to be able to access OperatorExportTypes from ONNX for use in
  // the export side of JIT, so this ONNX init needs to appear before the JIT
  // init.
  torch::onnx::initONNXBindings(module);
  torch::jit::initJITBindings(module);
  torch::autograd::initNNFunctions(module);
  torch::autograd::init_legacy_variable(module);
  torch::python::init_bindings(module);
  torch::cuda::initModule(module);
  ......
}
```
initONNXBindings是ONNX的python binding：torch._C._onnx.TensorProtoDataType和torch._C._onnx.OperatorExportTypes：
```
>>> dir(torch._C._onnx.TensorProtoDataType)
['BOOL', 'COMPLEX128', 'COMPLEX64', 'DOUBLE', 'FLOAT', 'FLOAT16', 'INT16', 'INT32', 'INT64', 'INT8', 'STRING', 'UINT16', 'UINT32', 'UINT64', 'UINT8', 'UNDEFINED', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__int__', '__le__', '__lt__', '__members__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', 'name']
>>> dir(torch._C._onnx.OperatorExportTypes)
['ONNX', 'ONNX_ATEN', 'ONNX_ATEN_FALLBACK', 'RAW', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__int__', '__le__', '__lt__', '__members__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', 'name']
```
initJITBindings则是通过pybind11往torch._C上注册了一堆和JIT相关的C++函数/对象；

initNNFunctions初始化了一个torch._C._nn 对象，并注册了一些nn相关的函数：
```
>>> dir(torch._C._nn)
['__doc__', '__loader__', '__name__', '__package__', '__spec__', '_parse_to', 'adaptive_avg_pool2d', 'adaptive_avg_pool3d', 'adaptive_max_pool2d', 'adaptive_max_pool3d', 'avg_pool2d', 'avg_pool3d', 'binary_cross_entropy', 'elu', 'elu_', \
'fractional_max_pool2d', 'glu', 'hardtanh', 'hardtanh_', 'l1_loss', 'leaky_relu', 'leaky_relu_', 'log_sigmoid', 'max_pool2d_with_indices', 'max_pool3d_with_indices', 'max_unpool2d', 'max_unpool3d', 'mse_loss', 'multi_margin_loss', \
'multilabel_margin_loss', 'nll_loss', 'nll_loss2d', 'reflection_pad1d', 'reflection_pad2d', 'replication_pad1d', 'replication_pad2d', 'replication_pad3d', 'rrelu_with_noise', 'rrelu_with_noise_', 'smooth_l1_loss', 'soft_margin_loss', \
'softplus', 'softshrink', 'thnn_conv2d', 'thnn_conv3d', 'thnn_conv_depthwise2d', 'thnn_conv_dilated2d', 'thnn_conv_dilated3d', 'thnn_conv_transpose2d', 'thnn_conv_transpose3d', 'upsample_bilinear2d', 'upsample_linear1d', 'upsample_nearest1d', \
'upsample_nearest2d', 'upsample_nearest3d', 'upsample_trilinear3d']
```
init_legacy_variable注册了torch._C._LegacyVariableBase：

>>> dir(torch._C._LegacyVariableBase)
['__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', \
'__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', \
'__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', \
'__setattr__', '__sizeof__', '__str__', '__subclasshook__']

_LegacyVariableBase类会派生出Variable类（该类的_execution_engine会初始化为torch._C._EngineBase）：
```
class Variable(with_metaclass(VariableMeta, torch._C._LegacyVariableBase))
```
init_bindings是通过pybind11往torch._C上注册一些函数，torch::cuda::initModule类似，也是通过pybind11往torch._C上注册一些函数，只不过内容是和cuda相关的。

# 5，在torch._C上注册StorageBase类
```
PyObject* initModule() {
  ......
  THPDoubleStorage_init(module);
  THPFloatStorage_init(module);
  THPHalfStorage_init(module);
  THPLongStorage_init(module);
  THPIntStorage_init(module);
  THPShortStorage_init(module);
  THPCharStorage_init(module);
  THPByteStorage_init(module);
  THCPDoubleStorage_init(module);
  THCPFloatStorage_init(module);
  THCPHalfStorage_init(module);
  THCPLongStorage_init(module);
  THCPIntStorage_init(module);
  THCPShortStorage_init(module);
  THCPCharStorage_init(module);
  THCPByteStorage_init(module);
  THCPStream_init(module);
  ......
}
```
这些初始化工作主要就是往torch._C上注册了以下类：
```
CudaByteStorageBase
CudaCharStorageBase
CudaDoubleStorageBase
CudaFloatStorageBase
CudaHalfStorageBase
CudaIntStorageBase
CudaLongStorageBase
CudaShortStorageBase

ByteStorageBase
CharStorageBase
DoubleStorageBase
FloatStorageBase
HalfStorageBase
IntStorageBase
LongStorageBase
ShortStorageBase
```

比如以FloatStorageBase为例的话，我们可以这样查看它注册的方法：
```
>>> dir(torch._C.FloatStorageBase)
['__class__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__le__', '__len__', '__lt__', \
'__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', '_cdata', '_expired', '_free_weak_ref', \
'_get_shared_fd', '_new_shared_fd', '_new_shared_filename', '_new_using_fd', '_new_using_filename', '_new_with_file', '_new_with_weak_ptr', '_set_cdata', '_set_from_file', '_share_fd_', \
'_share_filename_', '_shared_decref', '_shared_incref', '_weak_ref', '_write_file', 'copy_', 'data_ptr', 'element_size', 'fill_', 'from_buffer', 'from_file', 'is_pinned', 'is_shared', 'new', \
'resize_', 'size']
```
这些类会在python体系中被继承：
```
class FloatStorage(_C.FloatStorageBase, _StorageBase)
```
另外注意下这块代码使用了一些宏来复用不同storage的代码，如下所示：
```
aten/src/TH/THGenerateLongType.h:10:#define Real Long
aten/src/TH/THGenerateHalfType.h:10:#define Real Half
aten/src/TH/THGenerateIntType.h:10:#define Real Int
aten/src/TH/THGenerateFloatType.h:9:#define Real Float
aten/src/TH/THGenerateShortType.h:10:#define Real Short
aten/src/TH/THGenerateCharType.h:8:#define Real Char
aten/src/TH/THGenerateByteType.h:8:#define Real Byte
aten/src/TH/THGenerateDoubleType.h:9:#define Real Double
aten/src/THC/THCGenerateIntType.h:7:#define Real Int
aten/src/THC/THCGenerateLongType.h:7:#define Real Long
aten/src/THC/THCGenerateCharType.h:7:#define Real Char
aten/src/THC/THCGenerateFloatType.h:9:#define Real Float
aten/src/THC/THCGenerateDoubleType.h:7:#define Real Double
aten/src/THC/THCGenerateHalfType.h:9:#define Real Half
aten/src/THC/THCGenerateShortType.h:7:#define Real Short
aten/src/THC/THCGenerateByteType.h:7:#define Real Byte
```
# 6，ATen的初始化
本小节会进行ATen的global context的初始化，然后使用at::globalContext().defaultGenerator(at::kCPU)进行generator的初始化。

另外，PyTorch会根据编译环境和用户配置，然后向torch._C上注册一些flag。这些flag有has_cudnn、has_mkl、has_lapack、_GLIBCXX_USE_CXX11_ABI：
```
PyObject* initModule() {
  ......
  PyObject *has_cudnn = Py_True;
  set_module_attr("has_cudnn", has_cudnn);

  at::init();
  py::reinterpret_borrow<py::module>(module).def("_demangle", &c10::demangle);
  ::c10::Warning::set_warning_handler(&warning_handler);

  set_module_attr("has_mkl", at::hasMKL() ? Py_True : Py_False);
  set_module_attr("has_lapack", at::hasLAPACK() ? Py_True : Py_False);
  set_module_attr("_GLIBCXX_USE_CXX11_ABI", _GLIBCXX_USE_CXX11_ABI ? Py_True : Py_False);
  auto& defaultGenerator = at::globalContext().defaultGenerator(at::kCPU);
  THPDefaultGenerator = (THPGenerator*)THPGenerator_NewWithGenerator(defaultGenerator);
  set_module_attr("default_generator", (PyObject*)THPDefaultGenerator, /* incref= */ false);
```
# 7，torch._C._THNN和torch._C._THCUNN的初始化
PyTorch在这一小节里注册了torch._C._THNN和torch._C._THCUNN类：
```
PyObject* initModule() {
  ......
  torch::nn::init__THNN(module);
  torch::nn::init__THCUNN(module);
  ......
}
```
这两个类都拥有数量巨大的op函数，一个是CPU版的，一个是CUDA版的。

# initModule之后
在initModule()函数初始化完毕之后，import torch的初始化工作还没有结束。因为在这之后，python的初始化脚本还要调用以下2个API才算真正完成全部的初始化：
```
_C._initExtension(manager_path())
_C._init_names(list(torch._storage_classes))
```
其中主要的工作都是在_C._initExtension中，这个初始化做了以下的工作：
```
torch::utils::initializeLayouts();
torch::utils::initializeDtypes();
torch::tensors::initialize_python_bindings();

THPDoubleStorage_postInit(module);
THPFloatStorage_postInit(module);
THPHalfStorage_postInit(module);
THPLongStorage_postInit(module);
THPIntStorage_postInit(module);
THPShortStorage_postInit(module);
THPCharStorage_postInit(module);
THPByteStorage_postInit(module);
THPBoolStorage_postInit(module);
//定义在THPStorage_(postInit)函数中，因为THPStorage_会被宏替换THPDoubleStorage_ \
//THPFloatStorage_、THPHalfStorage_、THPLongStorage_......

THPAutograd_initFunctions();
```
最后的THPAutograd_initFunctions()则是初始化了torch的自动微分系统，这是PyTorch动态图框架的基础。

# 总结
在PyTorch的初始化阶段，（python）torch模块先后初始化产生torch._C、torch._C._TensorBase、pybind11绑定、torch._C.*StorageBase、torch._C._THNN、torch._C._THCUNN，并进行了ATen context的初始化。在initModule()结束之后，初始化工作还进行了_C._initExtension()的初始化。

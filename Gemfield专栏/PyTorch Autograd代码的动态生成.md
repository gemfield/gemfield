# 背景
在《Gemfield：PyTorch ATen代码的动态生成》 一文中，我们知道PyTorch的的代码主要由C10、ATen、torch三大部分组成的。其中：
- C10，来自于Caffe Tensor Library的缩写；
- ATen，来自于 A TENsor library for C++11的缩写，PyTorch的C++ tensor library，ATen部分有大量的代码是来声明和定义Tensor运算相关的逻辑的；
- Torch，pytorch的variable、autograd、jit、onnx、distribute、model接口、python接口等都在这里声明定义。其中，PyTorch会使用tools/setup_helpers/generate_code.py来动态生成Autograd、jit、variable相关的一些代码，这部分动态生成的逻辑会在本文阐述。这也可以看作是gemfield专栏文章Gemfield：PyTorch的编译系统的一部分。

# Autograd动态代码生成的入口
在编译期，Cmake脚本会在torch/CMakeLists.txt中调用以下命令：
```
python3 tools/setup_helpers/generate_code.py --declarations-path \ 
/home/gemfield/github/pytorch/build/aten/src/ATen/Declarations.yaml 
--nn-path aten/src/
```
其中，/home/gemfield/github/pytorch/build/aten/src/ATen/Declarations.yaml 在Gemfield：PyTorch ATen代码的动态生成 一文中已经提到过，这个yaml文件是ATen代码动态生成的时候产生的。

# 开始生成动态代码
整个代码的动态生成过程可以划分为3部分。
## 1，生成THNN/THCUNN.cwrap 和THNN/THCUNN.cpp
- a，先生成aten/src/THNN/generic/THNN.cwrap，这一步的输入是aten/src/THNN/generic/THNN.h；
- b，再生成aten/src/THNN/generic/THNN.cpp，这一步的输入是aten/src/THNN/generic/THNN.cwrap、tools/cwrap/plugins/templates/nn_tail.cpp；
- c，生成THCUNN.cwrap和THCUNN.cpp同理。

不过，THNN/THCUNN.cpp的作用是什么呢？用来创建Python binding！
在THNN.cpp中：
```
namespace torch { namespace nn {
static PyTypeObject thnn_type;
void init__THNN(PyObject* c_module) {
  ((PyObject*)&thnn_type)->ob_refcnt = 1;
  thnn_type.tp_flags = Py_TPFLAGS_DEFAULT;
  thnn_type.tp_methods = module_methods;
  thnn_type.tp_name = "torch._C._THNN";
  if (PyType_Ready(&thnn_type) < 0) {
    throw python_error();
  }
  PyObject* type_obj = (PyObject*)&thnn_type;
  Py_INCREF(type_obj);
  if (PyModule_AddObject(c_module, "_THNN", type_obj) < 0) {
    throw python_error();
  }
}
}}
```
在THCUNN.cpp中：
```
namespace torch { namespace nn {
static PyTypeObject thnn_type;
void init__THCUNN(PyObject* c_module) {
  ((PyObject*)&thnn_type)->ob_refcnt = 1;
  thnn_type.tp_flags = Py_TPFLAGS_DEFAULT;
  thnn_type.tp_methods = module_methods;
  thnn_type.tp_name = "torch._C._THCUNN";
  if (PyType_Ready(&thnn_type) < 0) {
    throw python_error();
  }
  PyObject* type_obj = (PyObject*)&thnn_type;
  Py_INCREF(type_obj);
  if (PyModule_AddObject(c_module, "_THCUNN", type_obj) < 0) {
    throw python_error();
  }
}
}}
```
init__THCUNN和init__THNN是在Pytorch的初始化阶段调用的，在PyTorch的初始化时期，initModule函数会调用到
```
PyObject* initModule() {
  ......
  module = Py_InitModule("torch._C", methods.data())
  ......
  torch::nn::init__THNN(module);
#ifdef USE_CUDA
  torch::nn::init__THCUNN(module);
#endif
}
```
回到本文的主题，我们可以看到init__THCUNN和init__THNN创建过程基本一样，主要的干货就是module_methods。THNN的module_methods是基于cpu实现的算法，而THCUNN的module_methods是对等的CUDA实现。module_methods中大概有几百个函数，这些实现的module_methods是（左边是cpu，右边是cuda，省掉了_updateOutput和_updateGradInput后缀。可见主要是type不一样，比如float和Half）：
```
                                                              > Abs
                                                              > AbsCriterion
                                                              > BCECriterion
                                                              > ClassNLLCriterion
                                                              > Col2Im
                                                              > DistKLDivCriterion
                                                              > DoubleAbs
DoubleAbsCriterion                                              DoubleAbsCriterion
DoubleBCECriterion                                              DoubleBCECriterion
DoubleClassNLLCriterion                                         DoubleClassNLLCriterion
DoubleCol2Im                                                    DoubleCol2Im
                                                              > DoubleDistKLDivCriterion
DoubleELU                                                       DoubleELU
DoubleFeatureLPPooling                                          DoubleFeatureLPPooling
DoubleGatedLinear                                               DoubleGatedLinear
DoubleHardTanh                                                  DoubleHardTanh
DoubleIm2Col                                                    DoubleIm2Col
DoubleIndexLinear                                               DoubleIndexLinear
                                                              > DoubleL1Cost
DoubleLeakyReLU                                                 DoubleLeakyReLU
DoubleLogSigmoid                                                DoubleLogSigmoid
                                                              > DoubleLookupTable
                                                              > DoubleLookupTableBag
                                                              > DoubleMarginCriterion
......
```
这些module_methods内部会转而调用Legacy的pytorch的算法实现，比如，在THNN.cpp中我们已经注册到 torch._C._THNN 中的FloatAbsCriterion_updateOutput会转而调用THNN_FloatAbsCriterion_updateOutput。是的，其它API都一样，所有的调用都会转而调用THNN_*的函数。THNN_*函数的函数名是通过在aten/src/THNN/THNN.h（或者aten/src/THCUNN/THCUNN.h）中定义的宏扩展得到的：
```
#define THNN_(NAME) TH_CONCAT_3(THNN_, Real, NAME)
或者
#define THNN_(NAME) TH_CONCAT_3(THNN_, CReal, NAME)
```
这些函数实际声明在了aten/src/THCUNN/generic/THCUNN.h和aten/src/THNN/generic/THNN.h文件中，而定义则分别是在aten/src/THNN/generic/*.c （没错，legacy PyTorch的C源文件）和aten/src/THCUNN/*.cu 文件中（没错，legacy PyTorch的cuda实现）。

总结下来，这一步生成THNN/THCUNN.cpp是用来作为某些Python API到legacy 的torch代码的中继。

## 2，生成autograd文件
这一步会在torch/csrc/autograd/generated 目录下生成一系列（十几个）C++头文件和源文件。这些文件构成了PyTorch Autograd子系统的基础。分阶段来讲：

第一步是生成VariableType类相关的头文件和源文件

这一步的输入是build/aten/src/ATen/Declarations.yaml和tools/autograd/templates目录下的2个模板文件VariableType.h、VariableType.cpp，输出是在torch/csrc/autograd/generated目录下产生下列7个文件：
```
VariableType.h
VariableType_0.cpp
VariableType_1.cpp
VariableType_2.cpp
VariableType_3.cpp
VariableType_4.cpp
VariableTypeEverything.cpp
```
其中cpp文件目前hardcode了5个：VariableType_0.cpp ～ VariableType_4.cpp，所有的函数被Hash到了这5个里面（为了加快编译速度而将一个文件拆分成了5个）。VariableTypeEverything.cpp文件包含了0～4所有的函数，是为了给人看的（并不参与编译）。

VariableType系列文件定义了VariableType类，该类继承了at::Type，就像在Gemfield：PyTorch ATen代码的动态生成 一文中介绍的那样，该类是Type继承体系的一个子类（类比于CUDATypeDefault、CPUTypeDefault等），同其它的子类最明显的区别是，VariableType实现了operators自动求微分的功能。  当一个Tensor具备autograd功能时（requires_grad=True)，也就是这个Tensor是个Variable，那么在进入dispatch前，首先要经历Variable到VariableType的分发——也就是Variable上的计算会首先转发到VariableType类上。

要实现一个operator的autograd功能，我们一般直接将它绑定一个反向实现来让其做到求微分。但是有一些函数不需要绑定这样的反向实现，这是因为以下两点中的任意一个：

1，这些函数不能求微分：

- 这个函数没有可以求微分的输入；
- 这个函数没有可以求微分的输出；
- 或者这个函数压根就不是处理类似数据的输入的；

2，这个函数不需要亲自做，因为这个函数的实现就是由一些其他可以求微分的函数组成的。

第二步是生成autograd函数

这一步的输入是tools/autograd/templates目录下的4个模板文件，Functions.h、Functions.cpp、python_functions.h、python_functions.cpp，输出是在torch/csrc/autograd/generated目录下产生下列4个文件
```
Functions.h
Functions.cpp
python_functions.h
python_functions.cpp
```
为ATen的各种operations产生求微分的函数，用C++的类来表示这个函数。在Functions.h/cpp会声明/定义大量的autograd::Function类的子类。这些抽象出来的类相当于graph中的顶点，用两个函数的pair来表示edge。python_functions.h/cpp是上面这些类的python bingding，这些python binding的初始化工作是在torch初始化的时候，由定义在torch/csrc/Module.cpp中定义的THPModule_initExtension函数（如下所示）调用
```
static PyObject * THPModule_initExtension(PyObject *_unused, PyObject *shm_manager_path)
{
  ......
  torch::utils::initializeLayouts();
  torch::utils::initializeDtypes();
  torch::tensors::initialize_python_bindings();
  std::string path = THPUtils_unpackString(shm_manager_path);
  libshm_init(path.c_str());

  auto module = THPObjectPtr(PyImport_ImportModule("torch"));
  if (!module) throw python_error();

  THPDoubleStorage_postInit(module);
  THPFloatStorage_postInit(module);
  THPHalfStorage_postInit(module);
  THPLongStorage_postInit(module);
  THPIntStorage_postInit(module);
  THPShortStorage_postInit(module);
  THPCharStorage_postInit(module);
  THPByteStorage_postInit(module);
  THPAutograd_initFunctions();
  ......
}
```
在torch/csrc/autograd/functions/init.cpp中定义的THPAutograd_initFunctions（如下所示）
```
void THPAutograd_initFunctions()
{
  THPObjectPtr module(PyModule_New("torch._C._functions"));
  ......
  generated::initialize_autogenerated_functions();

  auto c_module = THPObjectPtr(PyImport_ImportModule("torch._C"));
  if (!c_module) throw python_error();

  Py_INCREF(module);
  if (PyModule_AddObject(c_module, "_functions", module) < 0) {
    throw python_error();
  }
}
```
调用在这里生成的python_functions.cpp文件中的initialize_autogenerated_functions函数：
```
void initialize_autogenerated_functions() {
  static PyTypeObject AbsBackwardClass;
  addClass<AbsBackward>(AbsBackwardClass, "AbsBackward");
  static PyTypeObject AcosBackwardClass;
  addClass<AcosBackward>(AcosBackwardClass, "AcosBackward");
  static PyTypeObject AddBackward0Class;
  addClass<AddBackward0>(AddBackward0Class, "AddBackward0");
  static PyTypeObject AddBackward1Class;
  addClass<AddBackward1>(AddBackward1Class, "AddBackward1");
  ......
}
```
完成的python初始化。

第三步是生成torch._C._TensorBase的python binding

这一步的输入是tools/autograd/templates目录下的2个模板文件python_variable_methods.cpp、python_variable_methods_dispatch.h，输出是在torch/csrc/autograd/generated目录下产生下列2个文件：
```
python_variable_methods.cpp
python_variable_methods_dispatch.h
```
在python_variable_methods.cpp中实现了variable_methods：
```
PyMethodDef variable_methods[] = {
  {"__add__", (PyCFunction)THPVariable_add, METH_VARARGS | METH_KEYWORDS, NULL},
  {"__radd__", (PyCFunction)THPVariable_add, METH_VARARGS | METH_KEYWORDS, NULL},
  {"__iadd__", (PyCFunction)THPVariable_add_, METH_VARARGS | METH_KEYWORDS, NULL},
  ......
  {"transpose", (PyCFunction)THPVariable_transpose, METH_VARARGS | METH_KEYWORDS, NULL},
  {"transpose_", (PyCFunction)THPVariable_transpose_, METH_VARARGS | METH_KEYWORDS, NULL},
  ......
}
```
而这个variable_methods将在torch/csrc/autograd/python_variable.cpp中的THPVariable_initModule初始化函数里被注册到torch._C._TensorBase上：
```
bool THPVariable_initModule(PyObject *module)
{
  static std::vector<PyMethodDef> methods;
  THPUtils_addPyMethodDefs(methods, torch::autograd::variable_methods);
  THPUtils_addPyMethodDefs(methods, extra_methods);
  THPVariableType.tp_methods = methods.data();
  if (PyType_Ready(&THPVariableType) < 0)
    return false;
  Py_INCREF(&THPVariableType);
  PyModule_AddObject(module, "_TensorBase",   (PyObject *)&THPVariableType);
  torch::autograd::initTorchFunctions(module);
  return true;
}
```
而在python_variable_methods_dispatch.h中定义的inline dispatch函数则是将这些variable_methods的逻辑分发到Tensor类对应的方法上。

第四步是生成torch._C._VariableFunctions的python binding

这一步的输入是tools/autograd/templates目录下的2个模板文件python_torch_functions.cpp、python_torch_functions_dispatch.h，输出是在torch/csrc/autograd/generated目录下产生下列2个文件：
```
python_torch_functions.cpp
python_torch_functions_dispatch.h
```
这个注册过程和第三步类似，往torch._C._VariableFunctions上绑定了一堆torch函数。

第五步是生成torch._C._nn的python binding

这一步的输入是tools/autograd/templates目录下的3个模板文件python_nn_functions.cpp、python_nn_functions.h、python_nn_functions_dispatch.h，输出是在torch/csrc/autograd/generated目录下产生下列3个文件：
```
python_nn_functions.cpp
python_nn_functions_dispatch.h
python_nn_functions.h
```
这个注册过程和第三步类似，往torch._C._nn上绑定了一堆torch函数。

第六步是生成variable factories文件

这一步的输入是tools/autograd/templates目录下的variable_factories.h模板文件，输出是在torch/csrc/autograd/generated目录下产生下面的文件：
```
variable_factories.h
```
这里产生的C++ 函数用来封装了ATen tensor 的工厂方法，用来将一个tensor转换成可微分的Variable。

## 3，生成JIT相关的文件
这一步的输入是tools/jit/templates目录下的register_aten_ops.cpp模板，然后会在torch/csrc/autograd/generated 目录下生成以下文件：
```
register_aten_ops_0.cpp
register_aten_ops_1.cpp
register_aten_ops_2.cpp
```
注册函数签名到c++的map中，为JIT服务：
```
std::unordered_map<std::string, std::shared_ptr<Operator>> operators_by_sig;
std::unordered_map<const char*, std::shared_ptr<Operator>> operators_by_sig_literal;
```
# 总结
在本文中，gemfield描述了Python中Autograd的代码动态生成。Autograd中动态生成的代码主要有：
- 生成THNN/THCUNN.cpp，这里实现了对legacy PyTorch 函数的python绑定；
- 生成用于autograd的文件，这里实现了PyTorch的Tensor（0.4版本以前的Variable）的自动求微分功能；其中的关键有 Type继承体系中的VariableType类、autograd函数（图中的顶点，edge由pair来表示），以及torch._C._TensorBase、torch._C._VariableFunctions、torch._C._nn的函数绑定；
- 生成JIT相关的文件，主要是为JIT注册一些operator的mapping。

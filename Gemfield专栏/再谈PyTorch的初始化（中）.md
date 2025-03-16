# 背景
上篇文章已经谈到过，由于PyTorch的初始化工作量非常多，这个主题被Gemfield分为3篇文章：
- 再谈PyTorch的初始化（上）：介绍c++库main/initModule之前的初始化工作，主要就是global constructors；
- 再谈PyTorch的初始化（中）：介绍c++库main/initModule之后的初始化工作；
- 再谈PyTorch的初始化（下）：__init__.py中c++库之外的初始化工作。

在本篇文章中，gemfield主要介绍介绍c++库main/initModule之后的初始化工作，主要就是各种init调用，以及往python object上注册data和function属性，其实大部分内容已经在
《Gemfield：PyTorch的初始化​》介绍过了，本篇文章补充一些细节。

# THPEngine_initModule的初始化
THPEngine_initModule(module)创建了torch._C._EngineBase，Engine实现了从中间输出的variable的grad到root variable（用户创建的Variable）之间的反向传播:
```
bool THPEngine_initModule(PyObject *module)
{
  if (PyType_Ready(&THPEngineType) < 0)
    return false;
  Py_INCREF(&THPEngineType);
  PyModule_AddObject(module, "_ImperativeEngine", (PyObject *)&THPEngineType);
  set_default_engine_stub(get_python_engine);
  return true;
}
```
上面的初始化代码向torch._C中注册了_ImperativeEngine属性。在variable的python接口中（torch/autograd/variable.py），会以下面的方式使用_ImperativeEngine：
```
from torch._C import _ImperativeEngine as ImperativeEngine
Variable._execution_engine = ImperativeEngine()
```
除此之外，还需要注册默认的engine stub（其实就是返回初始化好的PythonEngine）：
```
static torch::autograd::python::PythonEngine engine;

std::atomic<EngineStub> engine_stub(get_base_engine);

void set_default_engine_stub(EngineStub stub) {
  engine_stub.store(stub);
}

static Engine& get_python_engine() {
  return engine;
}

set_default_engine_stub(get_python_engine);
```
如果Python是启用的话（当然了，毕竟是PyTorch嘛），那么base engine就是一个Python Engine。 

# THPFloatStorage_init 初始化
实际上，不止float，一共有下面这些data type的初始化：
```
THPDoubleStorage_init(module)
THPFloatStorage_init(module)
THPHalfStorage_init(module)
THPLongStorage_init(module)
THPIntStorage_init(module)
THPShortStorage_init(module)
THPCharStorage_init(module)
THPByteStorage_init(module)
THPBoolStorage_init(module)
```
以THPFloatStorage_init为例，除了向python模块注册符号外，还要额外执行注册copy function的动作：
```
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPByteStorageType, h, &THWStorage_(copyByte));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPCharStorageType, h, &THWStorage_(copyChar));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPShortStorageType, h, &THWStorage_(copyShort));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPIntStorageType, h, &THWStorage_(copyInt));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPLongStorageType, h, &THWStorage_(copyLong));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPHalfStorageType, h, &THWStorage_(copyHalf));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPFloatStorageType, h, &THWStorage_(copyFloat));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPDoubleStorageType, h, &THWStorage_(copyDouble));
THPInsertStorageCopyFunction<THPStorage, THPStorage>(&THPBoolStorageType, h, &THWStorage_(copyBool));
```

# initModule之后
在initModule函数调用完成之后，python环境中的torch module就包含了以下的符号：
```
'_C': <module 'torch._C' from '/usr/local/lib/python2.7/dist-packages/torch/_C.so'>
'layout': <type 'torch.layout'>
'Graph': <class 'torch._C.Graph'>
'Value': <class 'torch._C.Value'>
'Gradient': <class 'torch._C.Gradient'>
'dtype': <type 'torch.dtype'>
'Node': <class 'torch._C.Node'>
'Generator': <type 'torch._C.Generator'>
'ExecutionPlanState': <class 'torch._C.ExecutionPlanState'>
'default_generator': <torch._C.Generator object at 0x7f30d8737e10>
'FatalError': <class 'torch.FatalError'>
'iinfo': <type 'torch.iinfo'>
'IODescriptor': <class 'torch._C.IODescriptor'>
'_utils': <module 'torch._utils' from '/usr/local/lib/python2.7/dist-packages/torch/_utils.pyc'>
'set_grad_enabled': <built-in function set_grad_enabled>
'Block': <class 'torch._C.Block'>
'Argument': <class 'torch._C.Argument'>
'Future': <class 'torch._C.Future'>
'CompleteArgumentSpec': <class 'torch._C.CompleteArgumentSpec'>
'Use': <class 'torch._C.Use'>

'GraphExecutor': <class 'torch._C.GraphExecutor'>
'GraphExecutorState': <class 'torch._C.GraphExecutorState'>
'ArgumentSpec': <class 'torch._C.ArgumentSpec'>
'PyTorchFileWriter': <class 'torch._C.PyTorchFileWriter'>
'JITException': <class 'torch._C.JITException'>
'Code': <class 'torch._C.Code'>
'TracingState': <class 'torch._C.TracingState'>
'PyTorchFileReader': <class 'torch._C.PyTorchFileReader'>
'finfo': <type 'torch.finfo'>
'Size': <type 'torch.Size'>
'LoggerBase': <class 'torch._C.LoggerBase'>
'NoopLogger': <class 'torch._C.NoopLogger'>
'LockingLogger': <class 'torch._C.LockingLogger'>
'ExtraFilesMap': <class 'torch._C.ExtraFilesMap'>
'FunctionSchema': <class 'torch._C.FunctionSchema'>
'ScriptMethod': <class 'torch._C.ScriptMethod'>
'ScriptModule': <class 'torch._C.ScriptModule'>
'device': <type 'torch.device'>
'FileCheck': <class 'torch._C.FileCheck'>

'Type': <class 'torch._C.Type'>
'BoolType': <class 'torch._C.BoolType'>
'IntType': <class 'torch._C.IntType'>
'NumberType': <class 'torch._C.NumberType'>
'StringType': <class 'torch._C.StringType'>
'FloatType': <class 'torch._C.FloatType'>
'TupleType': <class 'torch._C.TupleType'>
'DictType': <class 'torch._C.DictType'>
'ListType': <class 'torch._C.ListType'>
'TensorType': <class 'torch._C.TensorType'>
'OptionalType': <class 'torch._C.OptionalType'>
'AggregationType': <class 'torch._C.AggregationType'>

'ByteStorageBase': <type 'torch._C.ByteStorageBase'>
'HalfStorageBase': <type 'torch._C.HalfStorageBase'>
'ShortStorageBase': <type 'torch._C.ShortStorageBase'>
'IntStorageBase': <type 'torch._C.IntStorageBase'>
'LongStorageBase': <type 'torch._C.LongStorageBase'>
'CharStorageBase': <type 'torch._C.CharStorageBase'>
'DoubleStorageBase': <type 'torch._C.DoubleStorageBase'>
'FloatStorageBase': <type 'torch._C.FloatStorageBase'>
'BoolStorageBase': <type 'torch._C.BoolStorageBase'>

'has_mkldnn': True
'has_openmp': True
'has_cuda': False
'has_mkl': False
'has_cudnn': False
'has_lapack': False
```
你会发现好多之前遇到过的符号，不过。。。为什么连tensor符号都没有呢？还有常用的、基础的torch.zeros等等符号也没有呢？别着急，initModule的工作虽然完成了，但整个__init__.py的初始化工作还未结束，这个将在下篇文章中介绍。

# torch中的__all__
我们知道，在python中，如果使用from gemfield_module import * 可以将gemfield_module中的所有符号导入，除了下划线开头的符号。而如果在gemfield_module中定义了__all__数组，那么将只能从gemfield_module模块中import出__all__数组中的符号。也就是说，__all__覆盖了前述import的默认行为。
在torch/__init__.py中，__all__是这么定义的：
```
__all__ = [
    'typename', 'is_tensor', 'is_storage', 'set_default_tensor_type',
    'set_rng_state', 'get_rng_state', 'manual_seed', 'initial_seed',
    'save', 'load', 'set_printoptions', 'chunk', 'split', 'stack', 'matmul',
    'no_grad', 'enable_grad', 'rand', 'randn',
    'DoubleStorage', 'FloatStorage', 'LongStorage', 'IntStorage',
    'ShortStorage', 'CharStorage', 'ByteStorage',
    'DoubleTensor', 'FloatTensor', 'LongTensor', 'IntTensor',
    'ShortTensor', 'CharTensor', 'ByteTensor', 'Tensor',
]

__all__ += [name for name in dir(_C) if name[0] != '_' and not name.endswith('Base')]
```
也就是说，先给__all__初始化一些默认要导出的符号，然后再加上torch._C上注册的符号（符号名字不能以下划线开头，并且不能以Base结尾）。这些就是torch模块中的public符号，初始化完成后，这些符号如下面所示：
```
'__all__': [
'typename'
'is_tensor'
'is_storage'
'set_default_tensor_type'
'set_rng_state'
'get_rng_state'
'manual_seed'
'initial_seed'
'save'
'load'
'set_printoptions'
'chunk'
'split'
'stack'
'matmul'
'no_grad'
'enable_grad'
'rand'
'randn'
'DoubleStorage'
'FloatStorage'
'LongStorage'
'IntStorage'
'ShortStorage'
'CharStorage'
'ByteStorage'
'DoubleTensor'
'FloatTensor'
'LongTensor'
'IntTensor'
'ShortTensor'
'CharTensor'
'ByteTensor'
'Tensor'
'AVG'
'AggregationType'
'Argument'
'ArgumentSpec'
'Block'
'BoolType'
'Code'
'CompleteArgumentSpec'
'DictType'
'ExecutionPlanState'
'ExtraFilesMap'
'FatalError'
'FileCheck'
'FloatType'
'FunctionSchema'
'Future'
'Generator'
'Gradient'
'Graph'
'GraphExecutor'
'GraphExecutorState'
'IODescriptor'
'IntType'
'JITException'
'ListType'
'LockingLogger'
'Node'
'NoopLogger'
'NumberType'
'OptionalType'
'PyTorchFileReader'
'PyTorchFileWriter'
'SUM'
'ScriptMethod'
'ScriptModule'
'Size'
'StringType'
'TensorType'
'TracingState'
'TupleType'
'Type'
'Use'
'Value'
'cpp'
'default_generator'
'device'
'dtype'
'finfo'
'fork'
'get_default_dtype'
'get_num_threads'
'has_cuda'
'has_cudnn'
'has_lapack'
'has_mkl'
'has_mkldnn'
'has_openmp'
'iinfo'
'import_ir_module'
'import_ir_module_from_buffer'
'is_anomaly_enabled'
'is_grad_enabled'
'layout'
'merge_type_from_type_comment'
'parse_ir'
'parse_type_comment'
'set_anomaly_enabled'
'set_flush_denormal'
'set_grad_enabled'
'set_num_threads'
'wait'
]
```
# 总结
Gemfield将PyTorch的初始化分为3个阶段，如下所示：
- 再谈PyTorch的初始化（上）：介绍c++库main/initModule之前的初始化工作，主要就是global constructors；
- 再谈PyTorch的初始化（中）：介绍c++库main/initModule之后的初始化工作；
- 再谈PyTorch的初始化（下）：__init__.py中c++库之外的初始化工作。

本篇文章为中篇，在本篇文章中，gemfield主要介绍c++库main/initModule被调用之后的初始化工作，主要就是围绕着torch._C符号，进行各种属性和函数的注册，使得python的符号和c++的符号mapping了起来。

# 背景
上篇文章已经谈到过，由于PyTorch的初始化工作量非常多，这个主题被Gemfield分为3篇文章：
- 再谈PyTorch的初始化（上）：介绍c++库main/initModule之前的初始化工作，主要就是global constructors；
- 再谈PyTorch的初始化（中）：介绍c++库main/initModule之后的初始化工作；
- 再谈PyTorch的初始化（下）：__init__.py中c++库之外的初始化工作。

在本篇文章中，gemfield主要介绍__init__.py中c++库之外的初始化工作，主要就是python中的各种import。

# 模型的save和load
从serialization.py中import出save和load函数：
```
from .serialization import save, load
```
序列化当然离不开python的pickle模块，在serialization.py中，有如下引用：
```
if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle
```
# Python中定义的Tensor类
在__init__.py中使用下面的语句将Tensor类 import出来：
```
from .tensor import Tensor
```
Tensor类可了不得，因为代表网络权重参数的类——Parameter类——就是Tensor的子类。Tensor类定义如下所示：
```
class Tensor(torch._C._TensorBase):
    def __deepcopy__(self, memo):
    def __reduce_ex__(self, proto):
    def __setstate__(self, state):
    def __repr__(self):
    def backward(self, gradient=None, retain_graph=None, create_graph=False):
        torch.autograd.backward(self, gradient, retain_graph, create_graph)
    def register_hook(self, hook):
    def reinforce(self, reward):
    def retain_grad(self):
    def is_pinned(self):
    def is_shared(self):
    def share_memory_(self):
    def stft(self, n_fft, hop_length=None, win_length=None, window=None,
             center=True, pad_mode='reflect', normalized=False, onesided=True):
    ......
```
# Python中定义的Storage类
在storage.py中定义的_StorageBase类如下所示：
```
class _StorageBase(object):
    is_cuda = False
    is_sparse = False
    def __str__(self):
    def __repr__(self):
    def __iter__(self):
    def __copy__(self):
    def __deepcopy__(self, memo):
    def __reduce__(self):
    def __sizeof__(self):
    def clone(self):
    def tolist(self):
    def cpu(self):
    def double(self):
    def float(self):
    def half(self):
    def long(self):
    def int(self):
    def short(self):
    def char(self):
    def byte(self):
    def bool(self):
    def pin_memory(self):
    def share_memory_(self):
    def _new_shared(cls, size):

def _load_from_bytes(b):
    return torch.load(io.BytesIO(b))

_StorageBase.type = _type
_StorageBase.cuda = _cuda
```
和C++中定义的StorageBase类一起，共同派生出了以下python中的class：
```
class DoubleStorage(_C.DoubleStorageBase, _StorageBase)
class FloatStorage(_C.FloatStorageBase, _StorageBase)
class HalfStorage(_C.HalfStorageBase, _StorageBase)
class LongStorage(_C.LongStorageBase, _StorageBase)
class IntStorage(_C.IntStorageBase, _StorageBase)
class ShortStorage(_C.ShortStorageBase, _StorageBase)
class CharStorage(_C.CharStorageBase, _StorageBase)
class ByteStorage(_C.ByteStorageBase, _StorageBase)
class BoolStorage(_C.BoolStorageBase, _StorageBase)
```
这9个Storage类可是一开始就定义在__all__符号中的。之后调用_C._init_names，输入的参数是这些Storage类的名字组成的list：
```
_C._init_names(list(torch._storage_classes))
```
Python中的_init_names调用的是C++中的THPModule_initNames，这个函数起的作用就是给这些Storage相关的python object一个tp_name，比如，HalfStorage类的tp_name就初始化为torch.HalfStorage，其它类型Storage类的tp_name如下所示，可以看到就是在前面加上了module的名字：
```
torch.HalfStorage
torch.CharStorage
torch.ShortStorage
torch.IntStorage
torch.LongStorage
torch.cuda.BoolStorage
torch.cuda.FloatStorage
torch.cuda.HalfStorage
torch.cuda.DoubleStorage
torch.cuda.LongStorage
torch.cuda.ByteStorage
torch.cuda.CharStorage
torch.FloatStorage
torch.cuda.ShortStorage
torch.DoubleStorage
torch.BoolStorage
torch.ByteStorage
torch.cuda.IntStorage
```
# _C._initExtension()
在初始化完Strorage的name后，PyTorch开始执行_initExtension调用。
```
# Shared memory manager needs to know the exact location of manager executable
_C._initExtension(manager_path())
```
_initExtension的调用内容还是比较多的，主要有：

## 1，torch::utils::initializeLayouts调用
顾名思义，用来初始化layout。除了添加torch.strided和torch.sparse_coo符号外，还初始化了layout_registry数组。layout_registry数组的每个元素为THPLayout实例（payload为at::Layout）：
```
THPLayout* layout_registry[static_cast<int>(at::Backend::NumOptions)] = {};
```
然后通过registerLayoutObject调用向layout_registry数组添加元素：
```
registerLayoutObject((THPLayout*)strided_layout, at::Backend::CPU);
registerLayoutObject((THPLayout*)strided_layout, at::Backend::CUDA);
registerLayoutObject((THPLayout*)strided_layout, at::Backend::MSNPU);
registerLayoutObject((THPLayout*)strided_layout, at::Backend::XLA);
registerLayoutObject((THPLayout*)sparse_coo_layout, at::Backend::SparseCPU);
registerLayoutObject((THPLayout*)sparse_coo_layout, at::Backend::SparseCUDA);
```
## 2， torch::utils::initializeDtypes调用
添加了以下python符号：
```
torch.uint8
torch.int8
torch.int16
torch.int32
torch.int64
torch.float16
torch.float32
torch.float64
torch.complex32
torch.complex64
torch.complex128
torch.bool
torch.qint8
```
并且初始化了dtype_registry数组：
```
THPDtype* dtype_registry[static_cast<int>(at::ScalarType::NumOptions)] = {};
```
并且通过torch::registerDtypeObject调用向dtype_registry数组添加元素。
## 3， torch::tensors::initialize_python_bindings调用
先使用initialize_aten_types调用来初始化tensor_types数组，数组的每个元素是PyTensorType实例，初始化每个实例的所有成员：
```
static std::vector<PyTensorType> tensor_types;
```
使用py_initialize_metaclass添加了python符号torch.tensortype；

对于前述的tensor_types vector，初始化里面的每一个python type元素（如torch.FloatTensor, torch.DoubleTensor等等）；然后将这些类型添加到其对应的python module上，像下面这样：
```
ByteTensor-->torch
CharTensor-->torch
DoubleTensor-->torch
FloatTensor-->torch
IntTensor-->torch
LongTensor-->torch
ShortTensor-->torch
HalfTensor-->torch
BoolTensor-->torch
ByteTensor-->torch.cuda
CharTensor-->torch.cuda
DoubleTensor-->torch.cuda
FloatTensor-->torch.cuda
IntTensor-->torch.cuda
LongTensor-->torch.cuda
ShortTensor-->torch.cuda
HalfTensor-->torch.cuda
BoolTensor-->torch.cuda
ByteTensor-->torch.sparse
CharTensor-->torch.sparse
DoubleTensor-->torch.sparse
FloatTensor-->torch.sparse
IntTensor-->torch.sparse
LongTensor-->torch.sparse
ShortTensor-->torch.sparse
ByteTensor-->torch.cuda.sparse
CharTensor-->torch.cuda.sparse
DoubleTensor-->torch.cuda.sparse
FloatTensor-->torch.cuda.sparse
IntTensor-->torch.cuda.sparse
LongTensor-->torch.cuda.sparse
ShortTensor-->torch.cuda.sparse
```
## 4，libshm_init调用
将字符串变量manager_executable_path的值初始化为/usr/local/lib/python2.7/dist-packages/torch/bin/torch_shm_manager。
## 5，THPDoubleStorage_postInit调用（一共9种Storage）
初始化了attype_to_py_storage_type和py_storage_type_to_attype表，这两个表分别是从ATen type到Python storage type的映射，以及Python storage type到ATen type的映射：
```
std::unordered_map<at::Type*, PyTypeObject*> attype_to_py_storage_type;
std::unordered_map<PyTypeObject*, at::Type*> py_storage_type_to_attype;
```
## 6，THPAutograd_initFunctions调用
用来初始化cpp_function_types表，这个表维护了从cpp类型的函数到python类型的映射：
```
static std::unordered_map<std::type_index, THPObjectPtr> cpp_function_types
```
这个表里存放的都是和autograd相关的函数的映射关系。
## from .functional import *
import出torch/functional.py中定义的函数：
```
'btriunpack',
'broadcast_tensors',
'btrifact',
'btrifact_with_info',
'cartesian_prod',
'chain_matmul',
'einsum',
'gesv',
'isfinite',
'isinf',
'lu',
'lu_unpack',
'norm',
'meshgrid',
'potrf',
'pstrf',
'potrs',
'split',
'stft',
'tensordot',
'trtrs',
'unique'
```
实例化torch._C._EngineBase，这个会执行THPEngine_new调用。

执行torch._C._autograd_init()，这个会执行C++中的THPAutograd_initExtension调用，初始化torch.autograd.ProfilerEvent符号。

执行c10d_init，检查torch.distributed符号是否ready。

# import torch.cuda
torch.cuda用来支持CUDA类型的tensor操作，这里面实现的function和CPU tensor是一样的，只不过背后是使用GPU来进行计算。通过torch.cuda.is_available()来判断当前平台是否支持CUDA计算。

# import torch.autograd
torch.autograd通过提供类和函数来实现任意scalar valued函数的自动微分计算。

# import torch.nn
导出Parameter类、DataParallel类以及下面的OP符号：
```
'Module', 'Linear', 'Conv1d', 'Conv2d', 'Conv3d', 'ConvTranspose1d',
'ConvTranspose2d', 'ConvTranspose3d', 'Threshold', 'ReLU', 'Hardtanh', 'ReLU6',
'Sigmoid', 'Tanh', 'Softmax', 'Softmax2d', 'LogSoftmax', 'ELU', 'SELU', 'CELU', 'GLU', 'Hardshrink',
'LeakyReLU', 'LogSigmoid', 'Softplus', 'Softshrink', 'PReLU', 'Softsign', 'Softmin',
'Tanhshrink', 'RReLU', 'L1Loss', 'NLLLoss', 'KLDivLoss', 'MSELoss', 'BCELoss', 'BCEWithLogitsLoss',
'NLLLoss2d', 'PoissonNLLLoss', 'CosineEmbeddingLoss', 'CTCLoss', 'HingeEmbeddingLoss', 'MarginRankingLoss',
'MultiLabelMarginLoss', 'MultiLabelSoftMarginLoss', 'MultiMarginLoss', 'SmoothL1Loss',
'SoftMarginLoss', 'CrossEntropyLoss', 'Container', 'Sequential', 'ModuleList', 'ModuleDict',
'ParameterList', 'ParameterDict', 'AvgPool1d', 'AvgPool2d', 'AvgPool3d', 'MaxPool1d', 'MaxPool2d',
'MaxPool3d', 'MaxUnpool1d', 'MaxUnpool2d', 'MaxUnpool3d', 'FractionalMaxPool2d', "FractionalMaxPool3d",
'LPPool1d', 'LPPool2d', 'LocalResponseNorm', 'BatchNorm1d', 'BatchNorm2d', 'BatchNorm3d', 'InstanceNorm1d',
'InstanceNorm2d', 'InstanceNorm3d', 'LayerNorm', 'GroupNorm', 'SyncBatchNorm',
'Dropout', 'Dropout2d', 'Dropout3d', 'AlphaDropout', 'FeatureAlphaDropout',
'ReflectionPad1d', 'ReflectionPad2d', 'ReplicationPad2d', 'ReplicationPad1d', 'ReplicationPad3d',
'CrossMapLRN2d', 'Embedding', 'EmbeddingBag', 'RNNBase', 'RNN', 'LSTM', 'GRU', 'RNNCellBase', 'RNNCell',
'LSTMCell', 'GRUCell', 'PixelShuffle', 'Upsample', 'UpsamplingNearest2d', 'UpsamplingBilinear2d',
'PairwiseDistance', 'AdaptiveMaxPool1d', 'AdaptiveMaxPool2d', 'AdaptiveMaxPool3d', 'AdaptiveAvgPool1d',
'AdaptiveAvgPool2d', 'AdaptiveAvgPool3d', 'TripletMarginLoss', 'ZeroPad2d', 'ConstantPad1d', 'ConstantPad2d',
'ConstantPad3d', 'Bilinear', 'CosineSimilarity', 'Unfold', 'Fold',
'AdaptiveLogSoftmaxWithLoss'
```
# import torch.optim
导出下列优化器：
```
Adadelta
Adagrad
Adam
SparseAdam
Adamax
ASGD
SGD
Rprop
RMSprop
Optimizer
LBFGS
lr_scheduler
```
# import torch.multiprocessing
调用multiprocessing_init，用来检查torch.multiprocessing符号是否ready。

torch.multiprocessing可以注册自定义的reducers, 使用共享内存来让不同的进程访问同样的data。一旦一个tensor/storage 被移动到shared_memory, 我们就可以将它发送到其它进程，这个过程不会产生新的copy。

# import torch.sparse
导出稀疏矩阵的 addmm、mm、sum计算函数。

# import torch.onnx
封装了onnx模块，比如export函数用来将PyTorch的模型转换为onnx格式。
# import torch.jit
PyTorch的JUST-IN-TIME编译器，区别于传统的eager模式（主要用来prototype、debug、train、experiment），JIT提供的script模式是为性能和部署而生的，那些DAG通过JIT被翻译成IR，从而解耦了模型（计算图），IR后续可以被各种backend使用。
# import torch.distributions
torch.distributions包含可参数化的概率分布和采样函数，这允许构建随机计算图和随机梯度估计器以进行优化，主要用于强化学习、无监督学习等领域。实现的函数有以下这些：
```
'Bernoulli',
'Beta',
'Binomial',
'Categorical',
'Cauchy',
'Chi2',
'Dirichlet',
'Distribution',
'Exponential',
'ExponentialFamily',
'FisherSnedecor',
'Gamma',
'Geometric',
'Gumbel',
'HalfCauchy',
'HalfNormal',
'Independent',
'Laplace',
'LogNormal',
'LogisticNormal',
'LowRankMultivariateNormal',
'Multinomial',
'MultivariateNormal',
'NegativeBinomial',
'Normal',
'OneHotCategorical',
'Pareto',
'RelaxedBernoulli',
'RelaxedOneHotCategorical',
'StudentT',
'Poisson',
'Uniform',
'Weibull',
'TransformedDistribution',
'biject_to',
'kl_divergence',
'register_kl',
'transform_to'
```
# import torch.backends.cuda
# import torch.backends.mkl
# import torch.backends.openmp
实现了is_available函数：
```
def is_available():
    return torch._C.has_openmp
```
使用了torch._C.has_* bool变量，这正是在https://zhuanlan.zhihu.com/p/63371853中介绍过的。

# from torch._ops import ops
通过定义_Ops类的load_library方法，实现了自定义op的动态加载。你可以使用下面的方法来加载自己编译的动态库：
```
torch.ops.load_library('path/to/libgemfield.so')
```
这样就可以将libgemfield.so 加载到当前进程的地址空间。背后使用的是python的ctypes库：
```
ctypes.CDLL(gemfield_library_path)
```
# import torch.quasirandom
实现了SobolEngine，这是用来产生Sobol 序列的引擎。Sobol 序列是准随机低差异序列的一个例子，最初由俄罗斯数学家Ilya M. Sobol 于1967年提出。
# 总结
在PyTorch的__init__.py初始化脚本中，除了c++库之外，还依次定义和初始化了以下内容：

- torch model的save和load方法；
- Python中的tensor类；
- Python中的storage类；
- _C._initExtension()的调用，初始化了layout_registry数组、dtype_registry数组、tensor_types数组、attype_to_py_storage_type表、py_storage_type_to_attype表、cpp_function_types表；
- python模块的import：
```
from .functional import *
import torch.cuda
import torch.autograd
from torch.autograd import no_grad, enable_grad, set_grad_enabled  # noqa: F401
import torch.nn
import torch.optim
import torch.multiprocessing
import torch.sparse
import torch.utils.backcompat
import torch.onnx
import torch.jit
import torch.random
import torch.distributions
import torch.testing
import torch.backends.cuda
import torch.backends.mkl
import torch.backends.openmp
from torch._ops import ops
import torch.quasirandom
```

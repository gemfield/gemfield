# 背景
import torch的初始化工作就是执行了torch/__init__.py文件。这个文件里的内容不可谓不丰富。其中占据初始化工作量95%以上的就是这句：
```
from torch._C import *
```
在之前的专栏文章中，Gemfield已经介绍了PyTorch的Python库的初始化入口及步骤：《Gemfield：PyTorch的初始化​》

一言以蔽之，这就是一个典型的C++共享库的初始化。然而，如果我们从C++共享库的视角再来审视这一初始化，步骤就绝非是前述专栏文章里提的那么简单了。很简单，初始化的第一阶段永远属于global变量(对于POD类型来说，实际上在编译出来的二进制文件中已经初始化完毕了）以及class中的static成员,特别的，对于C++程序/库来说，global的对象实例将会触发构造函数先于main函数来执行初始化逻辑。因此这次，在Gemfield本文中，将会从内存中初始化完毕之后的dict、array等内存视角来重新看待PyTorch的初始化——大量初始化工作发生在main()/initModule()调用之前。

由于这个初始化的工作量非常多，Gemfield的这个主题将分为3篇文章：
- 再谈PyTorch的初始化（上）：介绍c++库main/initModule之前的初始化工作，主要就是global constructors；
- 再谈PyTorch的初始化（中）：介绍c++库main/initModule之后的初始化工作；
- 再谈PyTorch的初始化（下）：__init__.py中c++库之外的初始化工作。

在本篇文章中，gemfield主要介绍c++库main/initModule之前的初始化工作，主要就是global constructors，以及class中的static成员（单例设计模式）。下面来一一介绍这个初始化过程中涉及到的PyTorch子系统。
# Registry系统的初始化
Registry系统的本质工作就是实现了从字符串（key）到对象（value）的mapping。Registry系统是C10模块的一个组件，在PyTorch中，通过如下定义的宏来定义各种Registry：
```
C10_DECLARE_REGISTRY
C10_DEFINE_REGISTRY
```
PyTorch目前一共定义了如下20余个Registry：
```
C10_DEFINE_REGISTRY(LegacyDeviceTypeInitRegistry,LegacyDeviceTypeInitInterface,LegacyDeviceTypeInitArgs)
C10_DEFINE_REGISTRY(VariableHooksRegistry,VariableHooksInterface,VariableHooksArgs)
C10_DEFINE_REGISTRY(ComplexHooksRegistry,ComplexHooksInterface,ComplexHooksArgs)
C10_DEFINE_REGISTRY(CUDAHooksRegistry, CUDAHooksInterface, CUDAHooksArgs)
C10_DEFINE_REGISTRY(HIPHooksRegistry, HIPHooksInterface, HIPHooksArgs)
C10_DEFINE_REGISTRY(FreeCudaMemoryCallbacksRegistry, FreeMemoryCallback);
C10_DEFINE_REGISTRY(C10FlagsRegistry, C10FlagParser, const string&);
C10_DEFINE_REGISTRY(BlobDeserializerRegistry, BlobDeserializerBase);
C10_DEFINE_REGISTRY(Caffe2DBRegistry, DB, const string&, Mode);
C10_DEFINE_REGISTRY(NetRegistry,NetBase,const std::shared_ptr<const NetDef>&,Workspace*);
C10_DEFINE_REGISTRY(C10OperatorRegistry,OperatorBase,const OperatorDef&,Workspace*);
C10_DEFINE_REGISTRY(CPUOperatorRegistry,OperatorBase,const OperatorDef&,Workspace*);
C10_DEFINE_REGISTRY(CUDAOperatorRegistry,OperatorBase,const OperatorDef&,Workspace*);
C10_DEFINE_REGISTRY(HIPOperatorRegistry,OperatorBase,const OperatorDef&,Workspace*);
C10_DEFINE_REGISTRY(GradientRegistry,GradientMakerBase,const OperatorDef&,const vector<GradientWrapper>&);
C10_DEFINE_REGISTRY(TransformRegistry, Transform);
C10_DEFINE_REGISTRY(IDEEPOperatorRegistry,OperatorBase,const OperatorDef&,Workspace*);
C10_DEFINE_REGISTRY(ConverterRegistry, Converter);
C10_DEFINE_REGISTRY(WorkspaceOptimizationPassRegistry,WorkspaceOptimizationPass,NNModule*,Workspace*);
C10_DEFINE_REGISTRY(OptimizationPassRegistry, OptimizationPass, NNModule*);
C10_DEFINE_REGISTRY(PybindAdditionRegistry, PybindAddition, py::module&);
C10_DEFINE_TYPED_REGISTRY(ContextRegistry,at::DeviceType,at::BaseContext,std::unique_ptr,at::Device);
C10_DEFINE_TYPED_REGISTRY(BlobSerializerRegistry,TypeIdentifier,BlobSerializerBase,std::unique_ptr);
C10_DEFINE_TYPED_REGISTRY(BlobFetcherRegistry,TypeIdentifier,BlobFetcherBase,std::unique_ptr);
C10_DEFINE_TYPED_REGISTRY(BlobFeederRegistry,caffe2::DeviceType,BlobFeederBase,std::unique_ptr);
C10_DEFINE_SHARED_REGISTRY(ThreadPoolRegistry, TaskThreadPoolBase, int,int, bool);
C10_DEFINE_SHARED_REGISTRY(TaskGraphRegistry,AsyncTaskGraphBase,ExecutorHelper*,const ExecutionOptions&);
```
然后为了向这些Registry注册各种东西，PyTorch另外定义了一些helper的宏，这些helper的宏通过global consturctor在main函数之前完成了对各种Registry的初始化。比如：
```
C10_DEFINE_bool(caffe2_report_cpu_memory_usage, false, "If set, print out detailed memory usage");
```
将会定义一个global的对象：
```
RegistererC10FlagsRegistry g_C10FlagsRegistry_caffe2_report_cpu_memory_usage
```
进而会调用::c10::Registerer的构造函数来进行初始化：
```
class Registerer {
 public:
  explicit Registerer(
      const SrcType& key,
      Registry<SrcType, ObjectPtrType, Args...>* registry,
      typename Registry<SrcType, ObjectPtrType, Args...>::Creator creator,
      const std::string& help_msg = "") {
    registry->Register(key, creator, help_msg);
  }
  ......
}
```
进而会调用registry->Register(key, creator, help_msg)，其中registry是RegistryName()函数中的static变量，意味着每种Registry在内存中只有一份registry实例。最终Register类函数的调用产生了key("caffe2_report_cpu_memory_usage")到value("RegistererC10FlagsRegistry::DefaultCreator<C10FlagParser_caffe2_report_cpu_memory_usage>")的mapping。
类似的，这样的Registry有：
```
LegacyDeviceTypeInitRegistry
VariableHooksRegistry
ComplexHooksRegistry
CUDAHooksRegistry
HIPHooksRegistry
FreeCudaMemoryCallbacksRegistry
C10FlagsRegistry
BlobDeserializerRegistry
Caffe2DBRegistry
NetRegistry
C10OperatorRegistry
CPUOperatorRegistry
CUDAOperatorRegistry
HIPOperatorRegistry
GradientRegistry
TransformRegistry
IDEEPOperatorRegistry
ConverterRegistry
WorkspaceOptimizationPassRegistry
OptimizationPassRegistry
PybindAdditionRegistry
ContextRegistry
BlobSerializerRegistry
BlobFetcherRegistry
BlobFeederRegistry
ThreadPoolRegistry
TaskGraphRegistry
```
像C10FlagsRegistry目前注册了67个key，而CPUOperatorRegistry目前注册了827个key，等等。

# LegacyDeviceTypeInitRegistry的初始化
作为Registry系统中的一个，这个Registry目前就注册了一个key（LegacyDeviceTypeInit）。LegacyDeviceTypeInitRegistry以“LegacyDeviceTypeInit”字符串为key，以RegistererLegacyDeviceTypeInitRegistry::DefaultCreator<LegacyDeviceTypeInit>为value，注册到new ::c10:: Registry<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs>()新建出来的registry里，mapping关系如此便建立起来了。mapping一旦建立后，以后就可以通过字符串LegacyDeviceTypeInit”来操作对象了，比如在getLegacyDeviceTypeInit()函数中就使用如下语句来操作LegacyDeviceTypeInitInterface实例：
```
LegacyDeviceTypeInitRegistry()->Create("LegacyDeviceTypeInit", LegacyDeviceTypeInitArgs{});
```
相关的macro如下所示：
```
C10_DECLARE_REGISTRY(LegacyDeviceTypeInitRegistry, LegacyDeviceTypeInitInterface, LegacyDeviceTypeInitArgs);
C10_DEFINE_REGISTRY(LegacyDeviceTypeInitRegistry, LegacyDeviceTypeInitInterface, LegacyDeviceTypeInitArgs)

//在ATen/Context.cpp中注册
REGISTER_LEGACY_TYPE_INIT(LegacyDeviceTypeInit);
```
宏展开后如下所示：
```
//声明
::c10::Registry<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs>* LegacyDeviceTypeInitRegistry(); 
typedef ::c10::Registerer<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs> RegistererLegacyDeviceTypeInitRegistry;

//定义
::c10::Registry<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs>* LegacyDeviceTypeInitRegistry() {
    static ::c10::Registry<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs>* registry = \
    new ::c10:: Registry<std::string, std::unique_ptr<LegacyDeviceTypeInitInterface>, LegacyDeviceTypeInitArgs>(); 
    return registry;
}

//注册
static RegistererLegacyDeviceTypeInitRegistry g_LegacyDeviceTypeInitRegistry0( "LegacyDeviceTypeInit", \
    LegacyDeviceTypeInitRegistry(), RegistererLegacyDeviceTypeInitRegistry::DefaultCreator<LegacyDeviceTypeInit>, \
    ::c10::demangle_type<LegacyDeviceTypeInit>());;
```

# g_device_type_registry的初始化
在前述的Registry系统里，和Device operator相关的是以下4个Registry：
```
CPUOperatorRegistry
CUDAOperatorRegistry
HIPOperatorRegistry
IDEEPOperatorRegistry
```
通过CAFFE_REGISTER_DEVICE_TYPE宏，这四个Registry会被放入到g_device_type_registry字典里，来和key（device type）mapping起来：
```
CAFFE_REGISTER_DEVICE_TYPE(CPU, CPUOperatorRegistry);
CAFFE_REGISTER_DEVICE_TYPE(CUDA, CUDAOperatorRegistry);
CAFFE_REGISTER_DEVICE_TYPE(HIP, HIPOperatorRegistry);
CAFFE_REGISTER_DEVICE_TYPE(DeviceType::IDEEP, IDEEPOperatorRegistry);
```
CAFFE_REGISTER_DEVICE_TYPE宏的定义如下：
```
#define CAFFE_REGISTER_DEVICE_TYPE(type, registry_function) \
  namespace {                                               \
  static DeviceTypeRegisterer C10_ANONYMOUS_VARIABLE(       \
      DeviceType)(type, &registry_function);                \
  }

//global consturctor
struct DeviceTypeRegisterer {
  explicit DeviceTypeRegisterer(DeviceType type, RegistryFunction func) {
    ......
    // Calling the registry function to get the actual registry pointer.
    gDeviceTypeRegistry()->emplace(type, func());
  }

std::map<DeviceType, OperatorRegistry*>* gDeviceTypeRegistry() {
  static std::map<DeviceType, OperatorRegistry*> g_device_type_registry;
  return &g_device_type_registry;
}
```
由于使用了global constructor，g_device_type_registry的初始化将在main之前完成，然后在Caffe2的operator系统里发挥作用。

# 内存分配器Allocator的初始化
这个模块也属于C10 core系统，使用了一样的手法，也即通过宏REGISTER_ALLOCATOR封装了global的对象的construct：
```
#define REGISTER_ALLOCATOR(t, f)                    \
  namespace {                                       \
  static AllocatorRegisterer<t> g_allocator_##d(f); \
  }
```
整个PyTorch共register了2个Allocator，cpu的和cuda的：
```
static DefaultCPUAllocator g_cpu_alloc;
REGISTER_ALLOCATOR(DeviceType::CPU, &g_cpu_alloc);

static DefaultCUDAAllocator g_cuda_alloc;
REGISTER_ALLOCATOR(CUDA, &g_cuda_alloc);
```
也因此会触发2次关于AllocatorRegisterer构造函数的调用，在AllocatorRegisterer的构造函数中，会调用void SetAllocator(at::DeviceType t, at::Allocator* alloc)，而这个函数是用来初始化这个global数组的：
```
at::Allocator* allocator_array[at::COMPILE_TIME_MAX_DEVICE_TYPES];
```
这个global数组的index就是DeviceType::CPU、CUDA等枚举值，而value就是g_cpu_alloc、g_cuda_alloc这样的global对象，分别定义了内存分配相关的allocator，比如CPU type对应的Allocator是posix_memalign()，CUDA type对应的是cudaMallocHost()等调用。

# Type id系统的初始化
type id就是一个C++ type的独一无二的id（一个数字），你需要使用CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE或者CAFFE_KNOWN_TYPE来为一个type注册一个type id，从而建立起来了一个id到数据类型的mapping,比如tensor的dtype的类型就使用了这个type id系统。这个系统属于C10子模块，在c10/util/typeid.h中，一共声明了如下的type id：
```
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(0, uint8_t)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(1, int8_t)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(2, int16_t)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(3, int)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(4, int64_t)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(5, at::Half)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(6, float)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(7, double)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(8, at::ComplexHalf)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(9, std::complex<float>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(10, std::complex<double>)
// 11 = undefined type id
//caffe2/core/tensor.h
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(12, Tensor)

CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(13, std::string)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(14, bool)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(15, uint16_t)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(16, char)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(17, std::unique_ptr<std::mutex>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(18, std::unique_ptr<std::atomic<bool>>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(19, std::vector<int32_t>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(20, std::vector<int64_t>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(21, std::vector<unsigned long>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(22, bool*)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(23, char*)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(24, int*)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(25, detail::_guard_long_unique<long>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(26,detail::_guard_long_unique<std::vector<long>>)
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(27, c10::qint8);
CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE(28, _CaffeHighestPreallocatedTypeId)
```
而在c10/util/typeid.cpp文件中，则定义了这些type id，注意，这个初始化是在main函数之前完成的：
```
CAFFE_DEFINE_PREALLOCATED_KNOWN_TYPE(0, uint8_t)
CAFFE_DEFINE_PREALLOCATED_KNOWN_TYPE(1, int8_t)
......
CAFFE_DEFINE_PREALLOCATED_KNOWN_TYPE(28, _CaffeHighestPreallocatedTypeId)
```
我们以typeid为6的float为例，其声明及定义（宏展开后）如下所示：
```
//声明
template <>
inline TypeIdentifier TypeIdentifier::Get<float>() {
    return TypeIdentifier(6);
}      
namespace detail {                      
    extern const TypeMetaData _typeMetaDataInstance_preallocated_6;      
}      
template <>  
inline const detail::TypeMetaData* TypeMeta::_typeMetaDataInstance<float>() noexcept {
    return &detail::_typeMetaDataInstance_preallocated_6);
}

//定义
namespace detail {     
    const TypeMetaData _typeMetaDataInstance_preallocated_6 = _makeTypeMetaDataInstance<float>(_typeName<float>("float"));
}
```
_makeTypeMetaDataInstance<float>调用就是产生了一个TypeMetaData的实例，而一个TypeMetaData实例就包含了一个Type的元信息（包含了这个Type的大小、如何new、如何placement new、如何copy、如何delete、如何placement delete）：
```
struct TypeMetaData final {
  ......
  size_t itemsize_;
  New* new_;
  PlacementNew* placementNew_;
  Copy* copy_;
  PlacementDelete* placementDelete_;
  Delete* delete_;
  TypeIdentifier id_;
  const char* name_;
};
```
在Type id系统中，一共定义了28个这样的TypeMetaData实例，在PyTorch中，通过Type mapping到对应的Id再mapping到对应的TypeMetaData实例，你在前述“typeid为6的float”的声明/定义中已经看到了这个mapping关系了。

除此之外， Types就必须使用CAFFE_KNOWN_TYPE()来注册一个type id。CAFFE_KNOWN_TYPE和前述的CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE的区别在于，CAFFE_DECLARE_PREALLOCATED_KNOWN_TYPE是那些被访问很频繁的type，并且id在编译期就确定好了，而CAFFE_KNOWN_TYPE是在运行时的初始化时期动态的分配一个id，用于自定义的type。PyTorch中目前使用CAFFE_KNOWN_TYPE注册有下面的type及其id：
```
CAFFE_KNOWN_TYPE(std::unique_ptr<StoreHandler>)
CAFFE_KNOWN_TYPE(detail::WorkspaceStack)
CAFFE_KNOWN_TYPE(std::unique_ptr<Counter<int64_t>>)
CAFFE_KNOWN_TYPE(detail::ScratchWorkspaces)
CAFFE_KNOWN_TYPE(std::unique_ptr<caffe2::IndexBase>)
CAFFE_KNOWN_TYPE(MapType64To64)
CAFFE_KNOWN_TYPE(MapType64To32)
CAFFE_KNOWN_TYPE(MapType32To32)
CAFFE_KNOWN_TYPE(MapType32To64)
CAFFE_KNOWN_TYPE(std::unique_ptr<dataset_ops::TreeCursor>)
CAFFE_KNOWN_TYPE(dataset_ops::TensorVectorPtr)
CAFFE_KNOWN_TYPE(dataset_ops::SharedTensorVectorPtr)
CAFFE_KNOWN_TYPE(std::unique_ptr<TextFileReaderInstance>)
CAFFE_KNOWN_TYPE(TimerInstance*)
CAFFE_KNOWN_TYPE(std::unique_ptr<caffe2::StatRegistry>)
CAFFE_KNOWN_TYPE(std::shared_ptr<Module>)
CAFFE_KNOWN_TYPE(Tensor<OpenCLContext>)
CAFFE_KNOWN_TYPE(::gloo::float16)
CAFFE_KNOWN_TYPE(std::shared_ptr<::gloo::Context>)
CAFFE_KNOWN_TYPE(std::shared_ptr<BlobsQueue>)
CAFFE_KNOWN_TYPE(RebatchingQueuePtr)
CAFFE_KNOWN_TYPE(db::DBReader)
CAFFE_KNOWN_TYPE(db::Cursor)
CAFFE_KNOWN_TYPE(WorkspaceTestFoo)
CAFFE_KNOWN_TYPE(int8::Int8TensorCPU)
CAFFE_KNOWN_TYPE(BlobTestFoo)
CAFFE_KNOWN_TYPE(BlobTestBar)
CAFFE_KNOWN_TYPE(BlobTestNonDefaultConstructible)
CAFFE_KNOWN_TYPE(DummyType)
CAFFE_KNOWN_TYPE(QTensor<CPUContext>)
CAFFE_KNOWN_TYPE(MPICommonWorldWrapper)
CAFFE_KNOWN_TYPE(Int8FCDNNLowPPackedWeightBlob)
CAFFE_KNOWN_TYPE(Int8ConvDNNLowPPackedWeightBlob)
CAFFE_KNOWN_TYPE(ideep::tensor)
CAFFE_KNOWN_TYPE(TypeMetaTestFoo)
CAFFE_KNOWN_TYPE(TypeMetaTestBar)
CAFFE_KNOWN_TYPE(ClassAllowAssignment)
CAFFE_KNOWN_TYPE(ClassNoAssignment)
```
如果一个type注册好了,你就可以通过调用 TypeMeta::Make<T>来创建一个对象来包含它的metadata（如构造函数、析构函数等），TypeMeta::Make<T>返回一个TypeMeta() object, 这是一个指向meta信息结构体的一个指针。
# 注册Tensor类型
如果要在PyTorch中注册一个新的tensor type, 那么在C10的头文件c10/core/TensorTypeIdRegistration.h中使用C10_DECLARE_TENSOR_TYPE(MY_TENSOR)来声明这个新的Tensor类型，而在源文件c10/core/TensorTypeIdRegistration.cpp中使用C10_DEFINE_TENSOR_TYPE(MY_TENSOR)来定义这个新的Tensor类型。目前C10中已经定义了如下12种Tensor：
```
//声明
C10_DECLARE_TENSOR_TYPE(UndefinedTensorId);
C10_DECLARE_TENSOR_TYPE(CPUTensorId); // PyTorch/Caffe2 supported
C10_DECLARE_TENSOR_TYPE(CUDATensorId); // PyTorch/Caffe2 supported
C10_DECLARE_TENSOR_TYPE(SparseCPUTensorId); // PyTorch only
C10_DECLARE_TENSOR_TYPE(SparseCUDATensorId); // PyTorch only
C10_DECLARE_TENSOR_TYPE(MKLDNNTensorId); // Caffe2 only
C10_DECLARE_TENSOR_TYPE(OpenGLTensorId); // Caffe2 only
C10_DECLARE_TENSOR_TYPE(OpenCLTensorId); // Caffe2 only
C10_DECLARE_TENSOR_TYPE(IDEEPTensorId); // Caffe2 only
C10_DECLARE_TENSOR_TYPE(HIPTensorId); // PyTorch/Caffe2 supported
C10_DECLARE_TENSOR_TYPE(SparseHIPTensorId); // PyTorch only
C10_DECLARE_TENSOR_TYPE(MSNPUTensorId); // PyTorch only
C10_DECLARE_TENSOR_TYPE(XLATensorId); // PyTorch only

//定义
C10_DEFINE_TENSOR_TYPE(UndefinedTensorId);
C10_DEFINE_TENSOR_TYPE(CPUTensorId);
C10_DEFINE_TENSOR_TYPE(CUDATensorId);
C10_DEFINE_TENSOR_TYPE(SparseCPUTensorId);
C10_DEFINE_TENSOR_TYPE(SparseCUDATensorId);
C10_DEFINE_TENSOR_TYPE(MKLDNNTensorId);
C10_DEFINE_TENSOR_TYPE(OpenGLTensorId);
C10_DEFINE_TENSOR_TYPE(OpenCLTensorId);
C10_DEFINE_TENSOR_TYPE(IDEEPTensorId);
C10_DEFINE_TENSOR_TYPE(HIPTensorId);
C10_DEFINE_TENSOR_TYPE(SparseHIPTensorId);
C10_DEFINE_TENSOR_TYPE(MSNPUTensorId);
C10_DEFINE_TENSOR_TYPE(XLATensorId);
```
以CPUTensorId为例，宏展开后可见其定义如下：
```
::c10::TensorTypeId CPUTensorId() {
    static ::c10::TensorTypeIdRegistrar registration_raii;
    return registration_raii.id(); 
}

//TensorTypeIdRegistrar的构造如下：
TensorTypeIdRegistrar::TensorTypeIdRegistrar() : id_(TensorTypeIds::singleton().createAndRegister()) {}
```
注册的本质就是往TensorTypeIdRegistry实例中维护的std::unordered_set<c10::TensorTypeId> registeredTypeIds_里放入tensor type的id。

# device_guard_impl_registry数组的初始化
device_guard_impl_registry数组存放的是DeviceGuardImplInterface的实例，DeviceGuardImplInterface是OOP中的接口，提供了RAII class 通过DeviceGuard来实现device和stream的切换。每种不同的设备, 比如CUDA和HIP,都需要继承并且实现这个接口，然后将其实现注册到device_guard_impl_registry数组中。PyTorch中有以下设备上的DeviceGuard的实现：
```
C10_REGISTER_GUARD_IMPL(CPU, CPUGuardImpl);
C10_REGISTER_GUARD_IMPL(CUDA, at::cuda::HIPGuardImplMasqueradingAsCUDA);
C10_REGISTER_GUARD_IMPL(CUDA, CUDAGuardImpl);
C10_REGISTER_GUARD_IMPL(MSNPU, MSNPUGuardImpl);
```
以CPU的实现为例，C10_REGISTER_GUARD_IMPL(CPU, CPUGuardImpl)宏展开后如下所示：
```
struct CPUGuardImpl final : public c10::impl::DeviceGuardImplInterface{
    ......
}
#global construct init
static ::c10::impl::DeviceGuardImplRegistrar g_DeviceType0(::c10::DeviceType::CPU, new CPUGuardImpl());
```
global的instance的constructor会执行下面的初始化逻辑：
```
DeviceGuardImplRegistrar::DeviceGuardImplRegistrar(DeviceType type, const DeviceGuardImplInterface* impl) {
  device_guard_impl_registry[static_cast<size_t>(type)].store(impl);
}
```
没错，初始化了device_guard_impl_registry这个数组，device的type为这个数组的index，相应的value就是DeviceGuardImplInterface在每种设备上的具体实现（其子类）。

# THVector table的初始化
这个table是用来将对应的op转发到某个实现上（取决于当前这个平台支持什么指令集），这个初始化也是沿用了global construct的方式，借助THVectorDispatch.cpp中定义的宏：static THVector_(startup) THVector_(g_startup)，PyTorch在global作用域中共定义了8个：
```
//宏static THVector_(startup) THVector_(g_startup)展开后

static THFloatVector_startup THFloatVector_g_startup;
static THDoubleVector_startup THDoubleVector_g_startup;
static THByteVector_startup THByteVector_g_startup;
static THCharVector_startup THCharVector_g_startup;
static THShortVector_startup THShortVector_g_startup;
static THIntVector_startup THIntVector_g_startup;
static THLongVector_startup THLongVector_g_startup;
static THHalfVector_startup THHalfVector_g_startup;
```
以THFloatVector_startup为例，其constructor的初始化逻辑如下：
```
struct THFloatVector_startup {
  THFloatVector_startup() {
    uint32_t hostSimdExts = detectHostSIMDExtensions();
    INIT_DISPATCH_PTR(fill);
    INIT_DISPATCH_PTR(cadd);
    INIT_DISPATCH_PTR(adds);
    INIT_DISPATCH_PTR(cmul);
    INIT_DISPATCH_PTR(muls);
    INIT_DISPATCH_PTR(cdiv);
    INIT_DISPATCH_PTR(divs);
    INIT_DISPATCH_PTR(normal_fill);

#if defined(TH_REAL_IS_FLOAT) || defined(TH_REAL_IS_DOUBLE)
    INIT_DISPATCH_PTR(sigmoid);
#endif
  }
};
```
看起来里面有规律的使用了INIT_DISPATCH_PTR宏，以INIT_DISPATCH_PTR(sigmoid)为例，其展开后如下所示：
```
do { 
    size_t i; 
    for (i = 0; i < sizeof(THFloatVector_sigmoid_DISPATCHTABLE) / sizeof(FunctionDescription); ++i) {
        THFloatVector_sigmoid_DISPATCHPTR = reinterpret_cast<decltype(THFloatVector_sigmoid_DISPATCHPTR)>(THFloatVector_sigmoid_DISPATCHTABLE[i].function); 
        if (THFloatVector_sigmoid_DISPATCHTABLE[i].supportedSimdExt & hostSimdExts) { 
            break; 
        } 
    } 
} while(0);
```
构造函数中初始化了dispatch tables。
```
typedef struct FunctionDescription
{
  void *function;
  uint32_t supportedSimdExt;
} FunctionDescription;
```
一个THVector table（比如THFloatVector_sigmoid_DISPATCHTABLE）会有多个FunctionDescription的实例，在PyTorch的初始化阶段，通过cpuid调用拿到当前cpu支持的SIMD指令集选项，再和FunctionDescription实例中的supportedSimdExt字段的值进行比对，如果支持的话，当前FunctionDescription实例中的function指向的函数就会被选中，并且赋值给THFloatVector_sigmoid_DISPATCHPTR，而table中后续的实例将不再做比对。这就是初始化的工作，对应的，在运行时，sigmoid运算符就会通过THFloatVector_sigmoid调用找到THFloatVector_sigmoid_DISPATCHPTR，如下所示：
```
void THFloatVector_sigmoid(float *y, const float *x, const ptrdiff_t n) {
    THFloatVector_sigmoid_DISPATCHPTR(y, x, n);
}
```
在TH下，如上面展示的那样，一共有8种data类型，每个里面有9种op，因此这里一共初始化了72个dispatchptr。
# CopyBytesFunction表的初始化
Tensor的数据需要在设备与设备之间拷贝，拷贝的方法因设备而异，在PyTorch的C10系统中定义了一个global的g_copy_bytes三维数组，用来维护设备与copy function的mapping关系，如下所示：
```
static CopyBytesFunction g_copy_bytes[2][COMPILE_TIME_MAX_DEVICE_TYPES]
                                     [COMPILE_TIME_MAX_DEVICE_TYPES];
```
这个三维数组的第一维表示是同步（0）还是异步（1），第二维表示copy的源设备，第三维表示copy的目的设备，g_copy_bytes三维数组通过如下7个宏进行初始化：
```
REGISTER_COPY_BYTES_FUNCTION(DeviceType::CUDA,DeviceType::CUDA,caffe2::CUDAContext::CopyBytesSync,caffe2::CUDAContext::CopyBytesAsync);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::CUDA,DeviceType::CPU,caffe2::CUDAContext::CopyBytesSync,caffe2::CUDAContext::CopyBytesAsync);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::CPU,DeviceType::CUDA,caffe2::CUDAContext::CopyBytesSync,caffe2::CUDAContext::CopyBytesAsync);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::CPU,DeviceType::CPU,caffe2::CopyBytesWrapper);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::IDEEP,DeviceType::CPU,CopyBytesWrapper);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::CPU,DeviceType::IDEEP,CopyBytesWrapper);
REGISTER_COPY_BYTES_FUNCTION(DeviceType::IDEEP,DeviceType::IDEEP,CopyBytesWrapper);
```
这就实现了数据可以从cuda到cpu、从cpu到cuda、从cuda到cuda、从cpu到cpu的拷贝。宏展开后如下所示：
```
#define REGISTER_COPY_BYTES_FUNCTION(from, to, ...)           \
  namespace {                                                 \
  static _CopyBytesFunctionRegisterer C10_ANONYMOUS_VARIABLE( \
      g_copy_function)(from, to, __VA_ARGS__);                \
  }

_CopyBytesFunctionRegisterer::_CopyBytesFunctionRegisterer(
    DeviceType fromType,
    DeviceType toType,
    CopyBytesFunction func_sync,
    CopyBytesFunction func_async) {
  auto from = static_cast<int>(fromType);
  auto to = static_cast<int>(toType);
  if (!func_async) {
    // default to the sync function
    func_async = func_sync;
  }
  g_copy_bytes[0][from][to] = func_sync;
  g_copy_bytes[1][from][to] = func_async;
}
```
如此通过global constructor便初始化完成了g_copy_bytes数组。

# Caffe2 OpSchemaRegistry的初始化
OpSchemaRegistry维护了一个map：
```
static CaffeMap<string, OpSchema> map
```
key是op name，value是OpSchema的实例。而OpSchema维护了关于一个op应该有的所有信息（包括输入输出参数，前向要执行的函数等）——这也就意味着，使用一个name即可通过OpSchemaRegistry中的map找到对应的OpSchema。 

要往OpSchemaRegistry中注册一个OpSchema，通常使用OPERATOR_SCHEMA宏，并且可以在后面追加OpSchema的成员函数。假如要注册gemfield_op，有2个输入1个输出，则注册的时候可以这么写：
```
OPERATOR_SCHEMA(gemfield_op).NumInputs(2).NumOutputs(1)
```
之后，OpSchemaRegistry中的map就多了一个gemfield_op及其schema组成的 pair。

# ATen中Type继承体系的初始化
这块的初始化有点区别，它不是global constructor，而是class中的static成员函数。众所周知，static成员函数是在main之前就要执行一次进行初始化的。通过使用static的成员函数，下面的这些Type类实现了单例模式：
```
struct TensorType : public Type 
struct NumberType : public Type 
struct SingleElementType : public Type 
struct DictType : public Type 
struct TupleType : public Type 
struct BoolType : public Type 
struct StringType : public Type 
struct NoneType : public Type 
struct GeneratorType : public Type 
struct DeviceObjType : public Type 
struct VarType : public Type 
struct ClassType : public Type

struct FutureType : public SingleElementType<TypeKind::FutureType, FutureType> 
struct ListType : public SingleElementType<TypeKind::ListType, ListType> 
struct OptionalType: public SingleElementType<TypeKind::OptionalType, OptionalType> 

struct FloatType : public NumberType 
struct IntType : public NumberType 

struct AutogradZeroTensorType : public TensorType 
struct DimensionedTensorType : public TensorType 
struct CompleteTensorType : public DimensionedTensorType 
```
它们都new了自己的一个实例，并由std::shared_ptr智能指针管理起来。
```
struct TypeExtendedInterface : public Type
struct TypeDefault : public TypeExtendedInterface
struct CPUTypeDefault : public TypeDefault
struct CUDATypeDefault : public TypeDefault
struct UndefinedType final : public TypeDefault 
struct VariableType final : public at::TypeDefault
```
在专栏文章https://zhuanlan.zhihu.com/p/55966063 中已经提到过了，CPUTypeDefault和CUDATypeDefault又有多个派生的子类，共同构成了Type继承体系。

# C10 dispatcher table的初始化
在PyTorch中，我们使用C10_REGISTER_CAFFE2_OPERATOR_CPU和C10_REGISTER_CAFFE2_OPERATOR_CUDA宏来将一些caffe2的operator注册到c10 dispatcher中。一个operator对应一个kernel，用下面的方式来定义一个kernel：
```
class my_kernel_cpu final : public c10::OperatorKernel {
  public:
    Tensor operator()(Tensor a, Tensor b) {...}
};
```
宏C10_REGISTER_CAFFE2_OPERATOR_*展开后为
```
static auto registry = c10::RegisterOperators().op(
    "my_op", c10::kernel<my_kernel_cpu(), c10::dispatchKey(CPUTensorId())
);
```
居然使用了RegisterOperators的构造函数来注册，那估计肯定是要用析构函数来取消注册。构造函数如下：
```
class OperatorRegistrar {
public:
  explicit OperatorRegistrar(FunctionSchema&& schema, c10::optional<TensorTypeId> dispatch_key, KernelFunction* kernel, KernelCacheCreatorFunction&& cache_creator)
  : op_(Dispatcher::singleton().registerSchema(std::move(schema))), dispatch_key_(std::move(dispatch_key)), has_kernel_(kernel != nullptr), owns_registration_(true) {

    if (has_kernel_) {
      if (dispatch_key_.has_value()) {
        Dispatcher::singleton().registerKernel(op_, *dispatch_key_, kernel, std::move(cache_creator));
      } else {
        Dispatcher::singleton().registerFallbackKernel(op_, kernel, std::move(cache_creator));
      }
    }
  }
```
Dispatcher类里维护了一个DispatchTable类实例，而DispatchTable类中维护了一个ThreadsafeOperatorTable_ 类实例，而后者又维护了一个LeftRight<ska::flat_hash_map<TensorTypeId, DispatchTableEntry>> map_，这是一个线程安全的hash table。

使用这个宏注册的caffe2 op有BBoxTransform、BoxWithNMSLimit、GenerateProposals、InferenceLSTM、LayerNorm、RoIAlign等。

# CodeTemplate的global construct
CodeTemplate实现了简单的模板引擎，在PyTorch的初始化阶段，我们定义了如下的template：
```
static jit::CodeTemplate event_template;
static auto dim_calc;
static auto type_declarations_template;
static auto cpu_compilation_unit_template;
static auto type_declarations_template;
static auto cuda_compilation_unit_template;
auto scalar_operators_source;
auto _ntuple_ops;
```

# VariableTypeRegistry及at::globalContext的初始化
使用VariableTypeRegistry的global construct来进行type_to_variable_type表的初始化（这是一个vector)，构造函数如下所示：
```
struct VariableTypeRegistry {
  VariableTypeRegistry() {
    auto& context = at::globalContext();
    for (int p = 0; p < static_cast<int>(Backend::NumOptions); ++p) {
      for (int s = 0; s < static_cast<int>(ScalarType::NumOptions); ++s) {
        auto baseType = context.getNonVariableTypeRaw(static_cast<Backend>(p), static_cast<ScalarType>(s));
        if (baseType && baseType->backend() != Backend::Undefined) {
          register_variable_type_for(baseType);
        }
      }
    }
  }
};
```
其中的at::globalContext()调用顺便初始化了globalContext_，包括generator_registry数组，以及更重要的register_cpu_types调用。register_cpu_types调用：
```
void register_cpu_types(Context * context) {
  context->registerType(Backend::CPU, ScalarType::Bool, new CPUBoolType());
  context->registerType(Backend::CPU, ScalarType::Byte, new CPUByteType());
  context->registerType(Backend::CPU, ScalarType::Char, new CPUCharType());
  context->registerType(Backend::CPU, ScalarType::Double, new CPUDoubleType());
  context->registerType(Backend::CPU, ScalarType::Float, new CPUFloatType());
  context->registerType(Backend::CPU, ScalarType::Int, new CPUIntType());
  context->registerType(Backend::CPU, ScalarType::Long, new CPULongType());
  context->registerType(Backend::CPU, ScalarType::Short, new CPUShortType());
  context->registerType(Backend::CPU, ScalarType::Half, new CPUHalfType());
  context->registerType(Backend::CPU, ScalarType::QInt8, new CPUQInt8Type());
  context->registerType(Backend::SparseCPU, ScalarType::Bool, new SparseCPUBoolType());
  context->registerType(Backend::SparseCPU, ScalarType::Byte, new SparseCPUByteType());
  context->registerType(Backend::SparseCPU, ScalarType::Char, new SparseCPUCharType());
  context->registerType(Backend::SparseCPU, ScalarType::Double, new SparseCPUDoubleType());
  context->registerType(Backend::SparseCPU, ScalarType::Float, new SparseCPUFloatType());
  context->registerType(Backend::SparseCPU, ScalarType::Int, new SparseCPUIntType());
  context->registerType(Backend::SparseCPU, ScalarType::Long, new SparseCPULongType());
  context->registerType(Backend::SparseCPU, ScalarType::Short, new SparseCPUShortType());
  context->registerType(Backend::SparseCPU, ScalarType::QInt8, new SparseCPUQInt8Type());
  context->registerType(Backend::MSNPU, ScalarType::Bool, new MSNPUBoolType());
  context->registerType(Backend::MSNPU, ScalarType::Byte, new MSNPUByteType());
  context->registerType(Backend::MSNPU, ScalarType::Char, new MSNPUCharType());
  context->registerType(Backend::MSNPU, ScalarType::Double, new MSNPUDoubleType());
  context->registerType(Backend::MSNPU, ScalarType::Float, new MSNPUFloatType());
  context->registerType(Backend::MSNPU, ScalarType::Int, new MSNPUIntType());
  context->registerType(Backend::MSNPU, ScalarType::Long, new MSNPULongType());
  context->registerType(Backend::MSNPU, ScalarType::Short, new MSNPUShortType());
  context->registerType(Backend::MSNPU, ScalarType::Half, new MSNPUHalfType());
  context->registerType(Backend::MSNPU, ScalarType::QInt8, new MSNPUQInt8Type());
  context->registerType(Backend::XLA, ScalarType::Bool, new XLABoolType());
  context->registerType(Backend::XLA, ScalarType::Byte, new XLAByteType());
  context->registerType(Backend::XLA, ScalarType::Char, new XLACharType());
  context->registerType(Backend::XLA, ScalarType::Double, new XLADoubleType());
  context->registerType(Backend::XLA, ScalarType::Float, new XLAFloatType());
  context->registerType(Backend::XLA, ScalarType::Int, new XLAIntType());
  context->registerType(Backend::XLA, ScalarType::Long, new XLALongType());
  context->registerType(Backend::XLA, ScalarType::Short, new XLAShortType());
  context->registerType(Backend::XLA, ScalarType::Half, new XLAHalfType());
  context->registerType(Backend::XLA, ScalarType::QInt8, new XLAQInt8Type());
  context->registerType(Backend::Undefined, ScalarType::Undefined, new UndefinedType());
}
```
registerType实现如下：
```
void registerType(Backend b, ScalarType s, Type* t) {
  globalLegacyTypeDispatch().registerType(b, s,
    LegacyTypeDispatch::TypeUniquePtr{t, LegacyTypeDeleter([](Type* p) { delete p; }) });
}
```
LegacyTypeDispatch实例中维护了一个type_registry二维数组，很简单，就是一组backend和scalar对应一个type；一个registerType调用除了向这个二维数组中添加一个元素外，还通过VariableHooksRegistry向type_to_variable_type添加了id到type的mapping：
```
void VariableHooks::registerVariableTypeFor(at::LegacyTypeDispatch* context, at::Backend backend, at::ScalarType scalar_type) const {
  auto* baseType = context->getNonVariableTypeRaw(backend, scalar_type);
  register_variable_type_for(static_cast<at::TypeExtendedInterface*>(baseType));
}
```
# JIT operator的初始化
目前JIT operator和C10 operator是分开的，因为它俩的功能不是完全一样。以后可能将JIT operator拆分，其中一部分和C10 operator复用。要注册一个自定义的JIT operator，需要使用createOperator调用，这个函数接收2个参数：第一个参数是一个name/schema，第二个参数是一个implementation。

如果第一个参数仅指定了函数名（比如gem::field)，那么schema就会从这个函数定义推导出来；如果第一个参数指定的不是一个函数名，那么就是schema，这种情况下要指定完整的schema，比如‘gem::field(Tensor a, double b) -> Tensor’，这种情况下，schema仍然需要从函数定义中推到出来，来和这里指定的做个校验检查。

第二个参数是函数实现，类型是一个函数指针或者functor（包含lambda对象）。这个函数可以接收任意参数的输入（类型只能是PyTorch JIT backend支持类型的一个子集），并且返回一个或者一个tuple的type。比如：
```
createOperator(
   "gem::field(float a, Tensor b)",
   [](float a, at::Tensor b) { return a + b; });
```
调用createOperator进行注册的过程中，主要的工作量都是在调用parseSchema，这个函数会进行lexer词法分析。为什么说主要工作量是在调用parseSchema呢？是因为整个初始化阶段JIT模块会有1825次parseSchema调用（当前），下面给出了一些schema的样子：
```
aten::get_device(Tensor self) -> int
aten::storage_offset(Tensor self) -> int
aten::is_contiguous(Tensor self) -> bool
aten::__and__(Tensor self, Tensor other) -> Tensor
aten::__and__(Tensor self, Scalar other) -> Tensor
aten::__iand__(Tensor(a!) self, Tensor other) -> Tensor(a!)
aten::__iand__(Tensor(a!) self, Scalar other) -> Tensor(a!)
aten::_adaptive_avg_pool2d_backward(Tensor grad_output, Tensor self) -> Tensor
aten::_baddbmm_mkl_(Tensor(a!) self, Tensor batch1, Tensor batch2, *, Scalar beta=1, Scalar alpha=1) -> Tensor(a!)
aten::_batch_norm_impl_index_backward(int impl_index, Tensor input, Tensor grad_output, Tensor? weight, Tensor? running_mean, Tensor? running_var, Tensor? save_mean, Tensor? save_var_transform, bool train, float eps, bool[3] output_mask) -> (Tensor, Tensor, Tensor)
```
在JIT模块的operator注册完毕后，PyTorch的初始化就将进入main阶段了，对于PyTorch的python的插件来说，就是stub.cpp文件中的init_C函数调用了，Gemfield将会在下一篇文章中介绍。

# REGISTER_DISPATCH
REGISTER_DISPATCH宏在编译期的时候根据device的不同自动展开不同的注册方法。以CPU的设备为例，REGISTER_DISPATCH会展开为：

REGISTER_ARCH_DISPATCH，并随着cmake系统分三次展开（三个编译单元），分别是default、avx、avx2,如下所示：
```
REGISTER_ARCH_DISPATCH(name, DEFAULT, fn)
REGISTER_ARCH_DISPATCH(name, AVX, fn)
REGISTER_ARCH_DISPATCH(name, AVX2, fn)
#展开为
DispatchStub<decltype(fn), struct name>::DEFAULT = *_kernel;
DispatchStub<decltype(fn), struct name>::AVX = *_kernel;
DispatchStub<decltype(fn), struct name>::AVX2 = *_kernel;
```
在运行的时候，通过choose_cpu_impl()依次判断pytorch是否使用AVX2、AVX编译的，如果都不是则使用DEFAULT。

另外，上述*_kernel函数对应的有以下几十个：
```
REGISTER_DISPATCH(pdist_forward_stub, &pdist_forward_kernel_impl);
REGISTER_DISPATCH(pdist_backward_stub, &pdist_backward_kernel_impl);
REGISTER_DISPATCH(cdist_stub, &cdist_kernel_impl);
REGISTER_DISPATCH(cdist_backward_stub, &cdist_backward_kernel_impl);
REGISTER_DISPATCH(index_stub, &index_kernel);
REGISTER_DISPATCH(index_put_stub, &index_put_kernel);
REGISTER_DISPATCH(std_var_stub, &std_var_kernel_cuda);
REGISTER_DISPATCH(sum_stub, &sum_kernel_cuda);
REGISTER_DISPATCH(prod_stub, &prod_kernel_cuda);
REGISTER_DISPATCH(mean_stub, &mean_kernel_cuda);
REGISTER_DISPATCH(norm_stub, &norm_kernel_cuda);
REGISTER_DISPATCH(and_stub, &and_kernel_cuda);
REGISTER_DISPATCH(or_stub, &or_kernel_cuda);
REGISTER_DISPATCH(max_values_stub, &max_values_kernel_cuda);
REGISTER_DISPATCH(min_values_stub, &min_values_kernel_cuda);
REGISTER_DISPATCH(threshold_stub, &threshold_kernel);
REGISTER_DISPATCH(add_stub, &add_kernel_cuda);
REGISTER_DISPATCH(sub_stub, &sub_kernel_cuda);
REGISTER_DISPATCH(div_stub, &div_kernel_cuda);
REGISTER_DISPATCH(mul_stub, &mul_kernel_cuda);
REGISTER_DISPATCH(cross_stub, &cross_kernel_impl);
REGISTER_DISPATCH(index_stub, &index_kernel);
REGISTER_DISPATCH(index_put_stub, &index_put_kernel);
REGISTER_DISPATCH(max_kernel, &max_kernel_impl);
REGISTER_DISPATCH(min_kernel, &min_kernel_impl);
REGISTER_DISPATCH(cross_stub, &cross_kernel_impl);
REGISTER_DISPATCH(grid_sampler_2d_cpu_kernel, &grid_sampler_2d_cpu_kernel_impl);
REGISTER_DISPATCH(grid_sampler_2d_backward_cpu_kernel, &grid_sampler_2d_backward_cpu_kernel_impl);
REGISTER_DISPATCH(softmax_lastdim_kernel, &softmax_lastdim_kernel_impl);
REGISTER_DISPATCH(log_softmax_lastdim_kernel, &log_softmax_lastdim_kernel_impl);
REGISTER_DISPATCH(softmax_backward_lastdim_kernel,&softmax_backward_lastdim_kernel_impl);
REGISTER_DISPATCH(log_softmax_backward_lastdim_kernel,&log_softmax_backward_lastdim_kernel_impl);
REGISTER_DISPATCH(copy_kernel_same_type, &copy_kernel_same_type_impl);
REGISTER_DISPATCH(copy_kernel_cast, &copy_kernel_cast_impl);
REGISTER_DISPATCH(sum_stub, &sum_kernel_impl);
REGISTER_DISPATCH(std_var_stub, &std_var_kernel_impl);
REGISTER_DISPATCH(prod_stub, &prod_kernel_impl);
REGISTER_DISPATCH(mean_stub, &mean_kernel_impl);
REGISTER_DISPATCH(norm_stub, &norm_kernel_tensor_iterator_impl);
REGISTER_DISPATCH(and_stub, &and_kernel_impl);
REGISTER_DISPATCH(or_stub, &or_kernel_impl);
REGISTER_DISPATCH(min_values_stub, &min_values_kernel_impl);
REGISTER_DISPATCH(max_values_stub, &max_values_kernel_impl);
REGISTER_DISPATCH(add_stub, &add_kernel);
REGISTER_DISPATCH(sub_stub, &sub_kernel);
REGISTER_DISPATCH(mul_stub, &mul_kernel);
REGISTER_DISPATCH(div_stub, &div_kernel);
REGISTER_DISPATCH(threshold_stub, &threshold_kernel);
REGISTER_DISPATCH(rsqrt_stub, &rsqrt_kernel)
REGISTER_DISPATCH(sigmoid_stub, &sigmoid_kernel)
REGISTER_DISPATCH(bernoulli_mkl_stub, &bernoulli_mkl_kernel);
REGISTER_DISPATCH(abs_stub, &abs_kernel);
REGISTER_DISPATCH(frac_stub, &frac_kernel);
REGISTER_DISPATCH(reciprocal_stub, &reciprocal_kernel);
REGISTER_DISPATCH(neg_stub, &neg_kernel);
REGISTER_DISPATCH(pdist_forward_stub, &pdist_forward_kernel_impl);
REGISTER_DISPATCH(pdist_backward_stub, &pdist_backward_kernel_impl);
REGISTER_DISPATCH(cdist_stub, &cdist_kernel_impl);
REGISTER_DISPATCH(cdist_backward_stub, &cdist_backward_kernel_impl);
###
REGISTER_DISPATCH(acos_stub, &acos_kernel)
REGISTER_DISPATCH(asin_stub, &asin_kernel)
REGISTER_DISPATCH(atan_stub, &atan_kernel)
REGISTER_DISPATCH(ceil_stub, &ceil_kernel)
REGISTER_DISPATCH(cos_stub, &cos_kernel)
REGISTER_DISPATCH(erf_stub, &erf_kernel)
REGISTER_DISPATCH(erfc_stub, &erfc_kernel)
REGISTER_DISPATCH(exp_stub, &exp_kernel)
REGISTER_DISPATCH(expm1_stub, &expm1_kernel)
REGISTER_DISPATCH(floor_stub, &floor_kernel)
REGISTER_DISPATCH(log_stub, &log_kernel)
REGISTER_DISPATCH(log10_stub, &log10_kernel)
REGISTER_DISPATCH(log1p_stub, &log1p_kernel)
REGISTER_DISPATCH(log2_stub, &log2_kernel)
REGISTER_DISPATCH(round_stub, &round_kernel)
REGISTER_DISPATCH(sin_stub, &sin_kernel)
REGISTER_DISPATCH(sqrt_stub, &sqrt_kernel)
REGISTER_DISPATCH(tan_stub, &tan_kernel)
REGISTER_DISPATCH(tanh_stub, &tanh_kernel)
REGISTER_DISPATCH(trunc_stub, &trunc_kernel)
```
以 REGISTER_DISPATCH(add_stub, &add_kernel) 为例，在CPU设备上的AVX2编译单元中，会展开为如下形式：
```
template <> decltype(&add_kernel) DispatchStub<decltype(&add_kernel), struct add_stub>::AVX2 = &add_kernel;
```
从上面的展开式中可以看到注册了add_kernel函数，这个函数实现在了aten/src/ATen/native/cpu/BinaryOpsKernel.cpp文件中。

在PyTorch的运行中，tensor之间的加法会调用到add_stub，并被分发到上述定义的add_kernel函数上：
```
void add_kernel(TensorIterator& iter, Scalar alpha_scalar) {
  std::cout<<"gemfield call "<<__FILE__<<":"<<__LINE__<<":"<<__FUNCTION__<<std::endl;
  AT_DISPATCH_ALL_TYPES(iter.dtype(), "add_cpu", [&]() {
    auto alpha = alpha_scalar.to<scalar_t>();
    auto alpha_vec = Vec256<scalar_t>(alpha);
    binary_kernel_vec(iter,
      [=](scalar_t a, scalar_t b) -> scalar_t { return a + alpha * b; },
      [=](Vec256<scalar_t> a, Vec256<scalar_t> b) {
        return vec256::fmadd(b, alpha_vec, a);
      });
  });
}
```
# 总结
Gemfield将PyTorch的初始化分为3个阶段，如下所示：
- 再谈PyTorch的初始化（上）：介绍c++库main/initModule之前的初始化工作，主要就是global constructors；
- 再谈PyTorch的初始化（中）：介绍c++库main/initModule之后的初始化工作；
- 再谈PyTorch的初始化（下）：__init__.py中c++库之外的初始化工作。

本篇文章为上篇，在本篇文章中，gemfield主要介绍c++库main/initModule之前的初始化工作，主要就是global constructors，以及class中的static成员（单例设计模式）。共涉及到PyTorch中以下子系统：
- 1，Registry系统的初始化；
- 2，LegacyDeviceTypeInitRegistry的初始化；
- 3，g_device_type_registry的初始化；
- 4，内存分配器Allocator的初始化；
- 5，Type id系统的初始化；
- 6，注册Tensor类型；
- 7，device_guard_impl_registry数组的初始化；
- 8，THVector table的初始化；
- 9，CopyBytesFunction表的初始化；
- 10，Caffe2 OpSchemaRegistry的初始化；
- 11，ATen中Type继承体系的初始化；
- 12，C10 dispatcher table的初始化；
- 13，CodeTemplate的global construct；
- 14，VariableTypeRegistry及at::globalContext的初始化；
- 15，JIT operator的初始化；
- 16，REGISTER_DISPATCH。

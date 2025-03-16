# 背景

(本文基于PyTorch 1.0）

我们知道PyTorch的的代码主要由C10、ATen、torch三大部分组成的。其中：

1，C10，来自于Caffe Tensor Library的缩写。这里存放的都是最基础的Tensor库的代码，可以运行在服务端和移动端。PyTorch目前正在将代码从ATen/core目录下迁移到C10中。C10的代码有一些特殊性，体现在这里的代码除了服务端外还要运行在移动端，因此编译后的二进制文件大小也很关键，因此C10目前存放的都是最核心、精简的、基础的Tensor函数和接口。

C10目前最具代表性的一个class就是TensorImpl了，它实现了Tensor的最基础框架。继承者和使用者有：
```
Variable的Variable::Impl
SparseTensorImpl
detail::make_tensor<TensorImpl>(storage_impl, CUDATensorId(), false)
Tensor(c10::intrusive_ptr<TensorImpl, UndefinedTensorImpl> tensor_impl)
c10::make_intrusive<at::TensorImpl, at::UndefinedTensorImpl>
```
值得一提的是，C10中还使用/修改了来自llvm的SmallVector，在vector元素比较少的时候用以代替std::vector，用以提升性能; 

2，ATen，来自于 A TENsor library for C++11的缩写；PyTorch的C++ tensor library。ATen部分有大量的代码是来声明和定义Tensor运算相关的逻辑的，除此之外，PyTorch还使用了aten/src/ATen/gen.py来动态生成一些ATen相关的代码。ATen基于C10，Gemfield本文讨论的正是这部分；

3，Torch，部分代码仍然在使用以前的快要进入历史博物馆的Torch开源项目，比如具有下面这些文件名格式的文件：
```
TH* = TorcH
THC* = TorcH Cuda
THCS* = TorcH Cuda Sparse (now defunct)
THCUNN* = TorcH CUda Neural Network (see cunn)
THD* = TorcH Distributed
THNN* = TorcH Neural Network
THS* = TorcH Sparse (now defunct)
THP* = TorcH Python
```
PyTorch会使用tools/setup_helpers/generate_code.py来动态生成Torch层面相关的一些代码，这部分动态生成的逻辑将不在本文阐述，你可以关注Gemfield专栏的后续文章。

4，Gemfield在本文将讨论ATen部分动态生成的代码

这也可以看作是gemfield专栏文章Gemfield：PyTorch的编译系统的一部分。

# ATen动态代码生成的入口
在编译期，Cmake脚本会在cmake/Codegen.cmake中检测BUILD_ATEN_MOBILE标志（该标志在编译Android和iOS的时候会设置为True，否则是False），如果该标志为False的话，才会运行gen.py（也就是说，gen.py生成了ATen模块的一部分源代码）：这正好说明了，gen.py生成的代码是为Server端准备的。
```
  SET(GEN_COMMAND
      ${PYCMD} ${CMAKE_CURRENT_LIST_DIR}/../aten/src/ATen/gen.py
      --source-path ${CMAKE_CURRENT_LIST_DIR}/../aten/src/ATen
      --install_dir ${CMAKE_BINARY_DIR}/aten/src/ATen
      ${GEN_ROCM_FLAG}
      ${cwrap_files}
  )

  EXECUTE_PROCESS(
      COMMAND ${GEN_COMMAND}
        --output-dependencies ${CMAKE_BINARY_DIR}/aten/src/ATen/generated_cpp.txt
        --install_dir ${CMAKE_BINARY_DIR}/aten/src/ATen
      RESULT_VARIABLE RETURN_VALUE
  )
```
展开就是
```
python3 pytorch/aten/src/ATen/gen.py
--source-path pytorch/aten/src/ATen
--install_dir pytorch/build/aten/src/ATen 
pytorch/aten/src/ATen/Declarations.cwrap 
pytorch/aten/src/THNN/generic/THNN.h 
pytorch/aten/src/THCUNN/generic/THCUNN.h 
pytorch/aten/src/ATen/nn.yaml 
pytorch/aten/src/ATen/native/native_functions.yaml
--output-dependencies pytorch/aten/src/ATen/generated_cpp.txt
```
那么什么样的代码是server端需要而移动端又不能要的呢？（不妨猜测下）

上述gen.py的命令会被执行两次，第一次是带output-dependencies参数的，第二次则不带。区别是，前者仅仅会把要生成的文件的文件名写入以下三个文件：
```
build/aten/src/ATen/generated_cpp.txt-cuda
build/aten/src/ATen/generated_cpp.txt-core
build/aten/src/ATen/generated_cpp.txt
```
 举例，在generated_cpp.txt-core文件中，有以下内容： 
```
gemfield@ubuntu:~/github/pytorch$ cat ./build/aten/src/ATen/generated_cpp.txt-core 
/home/gemfield/github/pytorch/build/aten/src/ATen/core_tmp/Tensor.h;/home/gemfield/github/pytorch/build/aten/src/ATen/core_tmp/TensorMethods.h;/home/gemfield/github/pytorch/build/aten/src/ATen/core_tmp/Type.h;
```
第二次不带output-dependencies参数，则动态代码生成逻辑会真正的去生成那些文件：
```
build/aten/src/ATen/CPUByteType.cpp
build/aten/src/ATen/CPUByteType.h
......
build/aten/src/ATen/CPUShortType.cpp
build/aten/src/ATen/CPUShortType.h
build/aten/src/ATen/Declarations.yaml
build/aten/src/ATen/ExtensionBackendRegistration.h
build/aten/src/ATen/Functions.h
build/aten/src/ATen/LegacyTHCPUByteDispatcher.cpp
build/aten/src/ATen/LegacyTHCPUByteDispatcher.h
......
build/aten/src/ATen/LegacyTHDispatcher.cpp
build/aten/src/ATen/LegacyTHDispatcher.h
build/aten/src/ATen/LegacyTHFunctions.h
build/aten/src/ATen/MSNPUType.cpp
build/aten/src/ATen/MSNPUType.h
build/aten/src/ATen/NativeFunctions.h
build/aten/src/ATen/RegisterCPU.cpp
build/aten/src/ATen/RegisterCPU.h
......
build/aten/src/ATen/SparseCPUShortType.cpp
build/aten/src/ATen/SparseCPUShortType.h
build/aten/src/ATen/TypeDefault.cpp
build/aten/src/ATen/TypeDefault.h
build/aten/src/ATen/TypeExtendedInterface.h
build/aten/src/ATen/XLAType.cpp
build/aten/src/ATen/XLAType.h
```
以及CUDA backend的：
```
build/aten/src/ATen/CUDAByteType.cpp;
build/aten/src/ATen/CUDAByteType.h;
......
build/aten/src/ATen/CUDAShortType.cpp
build/aten/src/ATen/CUDAShortType.h
build/aten/src/ATen/LegacyTHCUDAByteDispatcher.cpp
build/aten/src/ATen/LegacyTHCUDAByteDispatcher.h
......
build/aten/src/ATen/RegisterCUDA.cpp
build/aten/src/ATen/RegisterCUDA.h
......
build/aten/src/ATen/SparseCUDAShortType.cpp
build/aten/src/ATen/SparseCUDAShortType.h
```

# ATen动态代码如何生成
在cmake的调用过程中，gen.py从命令行上接收的参数除了source-path、install_dir、output-dependencies之外，就是files：
```
/home/gemfield/github/pytorch/aten/src/ATen/Declarations.cwrap
/home/gemfield/github/pytorch/aten/src/THNN/generic/THNN.h
/home/gemfield/github/pytorch/aten/src/THCUNN/generic/THCUNN.h
/home/gemfield/github/pytorch/aten/src/ATen/nn.yaml
/home/gemfield/github/pytorch/aten/src/ATen/native/native_functions.yaml
```
这些files被划分了cwrap_files、nn_files、native_files；

## cwrap_files
```
/home/gemfield/github/pytorch/aten/src/ATen/Declarations.cwrap
```
cwrap_files是包含了大量的"[["和"]]"括起来的yaml结构体，使用cwrap_parser进行解析。得到的信息主要是_th_前缀的函数，这些都是TH Tensor的函数。这些信息会放入top env，在后续步骤中用于替换各template文件中的占位符。另外，经过后续脚本的处理，还会以yaml形式写入torch/share/ATen/Declarations.yaml文件中。
## nn_files
```
/home/gemfield/github/pytorch/aten/src/THNN/generic/THNN.h
/home/gemfield/github/pytorch/aten/src/THCUNN/generic/THCUNN.h
/home/gemfield/github/pytorch/aten/src/ATen/nn.yaml
```
使用nn_parse进行解析，得到_thnn_前缀的函数的信息。这些信息会放入top env，在后续步骤中用于替换各template文件中的占位符。另外，经过后续脚本的处理，还会以yaml形式写入torch/share/ATen/Declarations.yaml文件中。
## native_files
```
/home/gemfield/github/pytorch/aten/src/ATen/native/native_functions.yaml
```
使用native_parse进行解析，得到的是modern PyTorch（区别于老旧的Torch）的一些正统函数的信息。这些信息会放入top env，在后续步骤中用于替换template中的占位符。另外，经过后续脚本的处理，还会以yaml形式写入torch/share/ATen/Declarations.yaml文件中。

所有解析完的信息会放入python list里（当然含有很多嵌套的list和dict），也就是屡次提到的top env。

解析完legacy的cwrap_files、nn_files和modern的native_files后，我们得到了top env信息，下面就要开始使用各个template文件结合top env来渲染出真正的源文件了。这个渲染过程分10步：
## 1，生成CPUGenerator.h、CUDAGenerator.h
输入为模板文件aten/src/ATen/templates/GeneratorDerived.h：
```
#pragma once
//${generated_comment}
#include <$header>
#include <ATen/core/Generator.h>
namespace at {
class Context;
struct ${name}Generator : public Generator {
  CAFFE2_API ${name}Generator(Context * context);
  CAFFE2_API virtual ~${name}Generator();
  CAFFE2_API virtual ${name}Generator& copy(const Generator& from) override;
  CAFFE2_API virtual ${name}Generator& free() override;
  CAFFE2_API virtual uint64_t seed() override;
  CAFFE2_API virtual uint64_t initialSeed() override;
  CAFFE2_API virtual ${name}Generator& manualSeed(uint64_t seed) override;
  CAFFE2_API virtual ${name}Generator& manualSeedAll(uint64_t seed) override;
  CAFFE2_API virtual void * unsafeGetTH() override;
public:
  Context * context;
  ${th_generator}
};
}
```
输出为$INSTALL_DIR/CPUGenerator.h和$INSTALL_DIR/CUDAGenerator.h，会把其中的${name}替换为CPU或CUDA；${th_generator}替换为THGenerator * generator; 或者空；$header替换为TH/TH.h或THC/THC.h。
## 2，生成build/aten/src/ATen/Declarations.yaml（同时会被拷贝到torch/share/ATen/Declarations.yaml）

这是根据cwrap_files、nn_files、native_files解析出来的信息生成的。Declarations.yaml会在Torch模块的动态代码生成过程中被使用。
## 3，生成Type继承体系的源文件
首先的一个问题是：Type继承体系是什么样子呢？

Type的整个继承体系是这样的，Type类派生出了TypeExtendedInterface类，TypeExtendedInterface类又派生出了TypeDefault类。TypeDefault又派生出了CUDATypeDefault、CPUTypeDefault、VariableType（这个实现了autograd功能）、UndefinedType等（以后还会扩展）。其中，根据density和scaler type的不同，CUDATypeDefault派生出了下面这些类：
```
CUDAIntType 
CUDAShortType 
SparseCUDACharType 
CUDADoubleType 
CUDAByteType 
CUDACharType 
SparseCUDAByteType 
CUDAFloatType 
SparseCUDALongType 
CUDALongType 
CUDAHalfType 
SparseCUDAShortType 
SparseCUDADoubleType 
SparseCUDAIntType 
SparseCUDAFloatType
```
CPUTypeDefault派生除了下面这些类：
```
SparseCPUShortType
CPUFloatType
CPUHalfType
CPUDoubleType
CPUByteType
SparseCPUFloatType
SparseCPUIntType
SparseCPUDoubleType
CPUCharType
SparseCPUByteType
CPUIntType
CPULongType
SparseCPULongType
SparseCPUCharType
CPUShortType
```
你看到了什么？这些Type拥有不同的device、layout（stride还是sparse）、dtype。欢迎认识Type继承体系建立起来的Tensor运算分发机制。

那其次的这个问题的答案就清楚了：Type继承体系的作用是什么呢？

Type类里声明了426个纯虚函数；TypeExtendedInterface除了继承之外额外声明了1287个纯虚函数；而TypeDefault类继承了这些函数，并实现了部分函数（在不同的device上拥有共同的逻辑），正如default这一名字的含义一样。而TypeDefault没有实现的部分，将被30个具体的子类分别实现。所有PyTorch中的op函数，都将由Tensor接口dispatch到Type家族（比如使用detail::infer_type函数可以得到一个Tensor对应的Type，继而使用Type继承体系中相应的子类的函数调用）——不是落在TypeDefault上，就是30个具体的子类上，再由Type家族转发到具体的kernel实现上——这些kernel有legacy的TH/THC实现或是modern的native实现。

更具体来说，这个分发机制是2级/3级，Gemfield来一一说来：
- 1，第一级分发是根据一个Tensor的是device type （cpu或者cuda）和 layout（stride或者sparse，靠Type继承体系中的虚函数实现的；
- 2，第二级分发是根据一个Tensor的dtype（int、float等），在程序运行过程中靠switch语句实现的（宏AT_DISPATCH_ALL_TYPES展开），因为对int和float等不同dtype的tensor的计算方法是不一样的，然后转发到具体的kernel实现上；
- 3，当一个Tensor具备autograd功能时（requires_grad=True)，也就是这个Tensor是个Variable，那么在进入上面的2级分发前，首先要经历Variable到VariableType的分发——VariableType也是Type继承体系中的一个子类哦。

最后一个问题是：这30个具体的类都是Type，那它们之间的区别是什么呢？

在aten/src/ATen/core/Type.h（该文件是由模板Type.h生成）中定义了Type类，这个类主要就是声明了一大堆和tensor相关的纯虚函数；接着是TypeExtendedInterface.h中定义的TypeExtendedInterface类继承了Type类，和Type类一样，TypeExtendedInterface继续扩展了更多的纯虚函数（由模板中的${pure_virtual_extended_type_method_declarations}根据parser得到的信息生成的），这些扩充的纯虚函数拥有下面这样的格式：
```
virtual ${return_type} ${method_prefix_derived}${api_name}(${type_method_formals}) const = 0;
//和
virtual ${return_type} ${api_name}(${type_method_formals}) const = 0;
```
接着是TypeDefault.h中定义的TypeDefault类，它继承了TypeExtendedInterface类。和父类们一样，TypeDefault又扩充了一堆函数（也是由模板中的${type_method_declarations}生成的，这些扩充的函数拥有下面这样的格式：
```
${return_type} ${api_name}(${type_method_formals}) const override;
```
TypeDefault类派生出了CUDATypeDefault、CPUTypeDefault。由上文得知，CUDATypeDefault和CPUTypeDefault将会分别派生出15个具体的类，这些类所在的30个头文件就是根据TypeDerived.h、TypeDerived.cpp、SparseTypeDerived.cpp这三个模板文件生成的。

Type继承体系中头文件对应的输入的模板是./aten/src/ATen/templates/TypeDerived.h：
```
#pragma once

// ${generated_comment}

#include <ATen/CPUTypeDefault.h>
#include <ATen/Context.h>
#include <ATen/CheckGenerator.h>

$extra_cuda_headers

#ifdef _MSC_VER
#ifdef Type
#undef Type
#endif
#endif

namespace at {

struct ${Type} final : public ${DenseBackend}TypeDefault {
  explicit ${Type}();
  virtual ScalarType scalarType() const override;
  virtual caffe2::TypeMeta typeMeta() const override;
  virtual Backend backend() const override;
  virtual const char * toString() const override;
  virtual size_t elementSizeInBytes() const override;
  virtual TypeID ID() const override;

  // example
  // virtual Tensor * add(Tensor & a, Tensor & b) override;
  ${type_derived_method_declarations}
};

} // namespace at
```
根据density是dense还是sparse、backend是CPU还是CUDA、scalar_types是 Byte/Char/Long/Double/Float/Int/Short/Half（sparse没有Half），我们可以从这一个模板文件生成30个不同的头文件。它们是：
```
CPUByteType.h
CPUCharType.h
CPUDoubleType.h
CPUFloatType.h
CPUHalfType.h
CPUIntType.h
CPULongType.h
CPUShortType.h
CUDAByteType.h
CUDACharType.h
CUDADoubleType.h
CUDAFloatType.h
CUDAHalfType.h
CUDAIntType.h
CUDALongType.h
CUDAShortType.h
SparseCPUByteType.h
SparseCPUCharType.h
SparseCPUDoubleType.h
SparseCPUFloatType.h
SparseCPUIntType.h
SparseCPULongType.h
SparseCPUShortType.h
SparseCUDAByteType.h
SparseCUDACharType.h
SparseCUDADoubleType.h
SparseCUDAFloatType.h
SparseCUDAIntType.h
SparseCUDALongType.h
SparseCUDAShortType.h
```
其中，${type_derived_method_declarations}将会被替换为一大堆函数声明。CUDA比CPU的多很多、Sparse的比dense的少很多。如果backend和density都一样，则不同的scalar_types之间的头文件的${type_derived_method_declarations}将是一样的。

Type继承体系中cpp实现文件对应的输入模板文件是aten/src/ATen/templates/TypeDerived.cpp（Dense的）和aten/src/ATen/templates/SparseTypeDerived.cpp（Sparse的）。这两个模板文件基本一样：
```
#define __STDC_FORMAT_MACROS

#include <ATen/${Type}.h>

// ${generated_comment}

$th_headers
$storage_tensor_headers
#include <ATen/${Generator}.h>
#include <c10/core/Allocator.h>
......
${type_derived_method_definitions}
}
```
输出则是30个cpp：
```
CPUByteType.cpp
CPUCharType.cpp
CPUDoubleType.cpp
CPUFloatType.cpp
CPUHalfType.cpp
CPUIntType.cpp
CPULongType.cpp
CPUShortType.cpp
CUDAByteType.cpp
CUDACharType.cpp
CUDADoubleType.cpp
CUDAFloatType.cpp
CUDAHalfType.cpp
CUDAIntType.cpp
CUDALongType.cpp
CUDAShortType.cpp
SparseCPUByteType.cpp
SparseCPUCharType.cpp
SparseCPUDoubleType.cpp
SparseCPUFloatType.cpp
SparseCPUIntType.cpp
SparseCPULongType.cpp
SparseCPUShortType.cpp
SparseCUDAByteType.cpp
SparseCUDACharType.cpp
SparseCUDADoubleType.cpp
SparseCUDAFloatType.cpp
SparseCUDAIntType.cpp
SparseCUDALongType.cpp
SparseCUDAShortType.cpp
```

## 4，生成legacy TH dispatcher

根据模板LegacyTHDispatcherDerived.cpp：
```
#include "ATen/${Dispatcher}.h"

// ${generated_comment}

namespace at {

${Dispatcher}::${Dispatcher}()
  : LegacyTHDispatcher(${Backend}TensorId()) {}

}
```
和LegacyTHDispatcherDerived.h：
```
#pragma once

// ${generated_comment}

#include "ATen/LegacyTHDispatcher.h"

namespace at {

struct ${Dispatcher} final : public LegacyTHDispatcher {
  explicit ${Dispatcher}();

};

} // namespace at
```
生成以下的class 类：
```
LegacyTHCPUByteDispatcher
LegacyTHCPUCharDispatcher
LegacyTHCPUDoubleDispatcher
LegacyTHCPUFloatDispatcher
LegacyTHCPUHalfDispatcher
LegacyTHCPUIntDispatcher
LegacyTHCPULongDispatcher
LegacyTHCPUShortDispatcher
LegacyTHCUDAByteDispatcher
LegacyTHCUDACharDispatcher
LegacyTHCUDADoubleDispatcher
LegacyTHCUDAFloatDispatcher
LegacyTHCUDAHalfDispatcher
LegacyTHCUDAIntDispatcher
LegacyTHCUDALongDispatcher
LegacyTHCUDAShortDispatcher
```
## 5，生成Type.h、Tensor.h、TensorMethods.h
根据模板Type.h、Tensor.h、TensorMethods.h生成源文件Type.h、Tensor.h、TensorMethods.h，其中Type.h在上文已经提到过。Tensor.h模板中就是一个 ${tensor_method_declarations}占位符，该占位符将由下面的语句结合实际的env来替换：
```
${return_type} ${api_name}(${method_formals_with_defaults})${const_mark}
```
而TensorMethods.h模板中就是一个${tensor_method_definitions}占位符，该占位符将由下面的语句结合实际的env来替换：
```
inline ${return_type} Tensor::${api_name}(${method_formals})${const_mark} {
    return type().${api_name}(${method_actuals});
}
```
可见Tensor.h负责声明Tensor类，而TensorMethods.h负责inline实现Tensor类的一些方法。这样一来，Tensor类的函数就通过tensor的种类和dispatcher的中继，进而调用到了Type继承体系的代码。

## 6，生成TypeExtendedInterface.h、TypeDefault.h、TypeDefault.cpp
根据模板TypeExtendedInterface.h、TypeDefault.h、TypeDefault.cpp生成源文件TypeExtendedInterface.h、TypeDefault.h、TypeDefault.cpp。上文已经提到过了。

## 7，生成LegacyTHDispatcher.h、LegacyTHDispatcher.cpp
根据模板LegacyTHDispatcher.h和LegacyTHDispatcher.cpp生成，对于这两者来说，模板里也没啥要替换的。
```
#pragma once

// ${generated_comment}

#include <c10/core/TensorTypeIdRegistration.h>

namespace at {

struct CAFFE2_API LegacyTHDispatcher {
  explicit LegacyTHDispatcher(TensorTypeId type_id)
      : type_id_(type_id) {}

  virtual ~LegacyTHDispatcher() {}

protected:
  TensorTypeId type_id_;
};

} // namespace th
```
## 8，生成RegisterCPU.h、RegisterCPU.cpp、RegisterCUDA.h、RegisterCUDA.cpp
其中，register_cpu_types、register_cuda_types会被hooks调用，完成Type继承体系的初始化和注册：
```
#cpu
void register_cpu_types(Context * context) {
  context->registerType(Backend::CPU, ScalarType::Byte, new CPUByteType());
  context->registerType(Backend::CPU, ScalarType::Char, new CPUCharType());
  context->registerType(Backend::CPU, ScalarType::Double, new CPUDoubleType());
  context->registerType(Backend::CPU, ScalarType::Float, new CPUFloatType());
  context->registerType(Backend::CPU, ScalarType::Int, new CPUIntType());
  context->registerType(Backend::CPU, ScalarType::Long, new CPULongType());
  context->registerType(Backend::CPU, ScalarType::Short, new CPUShortType());
  context->registerType(Backend::CPU, ScalarType::Half, new CPUHalfType());
  context->registerType(Backend::SparseCPU, ScalarType::Byte, new SparseCPUByteType());
  context->registerType(Backend::SparseCPU, ScalarType::Char, new SparseCPUCharType());
  context->registerType(Backend::SparseCPU, ScalarType::Double, new SparseCPUDoubleType());
  context->registerType(Backend::SparseCPU, ScalarType::Float, new SparseCPUFloatType());
  context->registerType(Backend::SparseCPU, ScalarType::Int, new SparseCPUIntType());
  context->registerType(Backend::SparseCPU, ScalarType::Long, new SparseCPULongType());
  context->registerType(Backend::SparseCPU, ScalarType::Short, new SparseCPUShortType());
  context->registerType(Backend::MSNPU, ScalarType::Byte, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Char, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Double, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Float, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Int, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Long, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Short, new MSNPUType());
  context->registerType(Backend::MSNPU, ScalarType::Half, new MSNPUType());
  context->registerType(Backend::XLA, ScalarType::Byte, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Char, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Double, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Float, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Int, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Long, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Short, new XLAType());
  context->registerType(Backend::XLA, ScalarType::Half, new XLAType());
  context->registerType(Backend::Undefined, ScalarType::Undefined, new UndefinedType());
}
#cuda
void register_cuda_types(Context * context) {
  context->registerType(Backend::CUDA, ScalarType::Byte, new CUDAByteType());
  context->registerType(Backend::CUDA, ScalarType::Char, new CUDACharType());
  context->registerType(Backend::CUDA, ScalarType::Double, new CUDADoubleType());
  context->registerType(Backend::CUDA, ScalarType::Float, new CUDAFloatType());
  context->registerType(Backend::CUDA, ScalarType::Int, new CUDAIntType());
  context->registerType(Backend::CUDA, ScalarType::Long, new CUDALongType());
  context->registerType(Backend::CUDA, ScalarType::Short, new CUDAShortType());
  context->registerType(Backend::CUDA, ScalarType::Half, new CUDAHalfType());
  context->registerType(Backend::SparseCUDA, ScalarType::Byte, new SparseCUDAByteType());
  context->registerType(Backend::SparseCUDA, ScalarType::Char, new SparseCUDACharType());
  context->registerType(Backend::SparseCUDA, ScalarType::Double, new SparseCUDADoubleType());
  context->registerType(Backend::SparseCUDA, ScalarType::Float, new SparseCUDAFloatType());
  context->registerType(Backend::SparseCUDA, ScalarType::Int, new SparseCUDAIntType());
  context->registerType(Backend::SparseCUDA, ScalarType::Long, new SparseCUDALongType());
  context->registerType(Backend::SparseCUDA, ScalarType::Short, new SparseCUDAShortType());
}
```
Context类中实现的registerType如下所示：
```
void registerType(Backend b, ScalarType s, Type* t) {
  globalLegacyTypeDispatch().registerType(b, s,
    LegacyTypeDispatch::TypeUniquePtr{t, LegacyTypeDeleter([](Type* p) { delete p; }) });
}
```
其是通过LegacyTypeDispatch类里的2维数组type_registry完成的mapping。
## 9，生成Functions.h、LegacyTHFunctions.h
Functions.h是legacy的TH代码的函数声明，在未来，这部分将要重写为modern的native函数。

## 10，生成NativeFunctions.h
根据模板NativeFunctions.h生成源文件NativeFunctions.h，其中占位符 ${native_function_declarations}将由下面的内容替换（真正的内容来自于native_functions.yaml）：
```
CAFFE2_API ${return_type} ${native_type_method_dispatch}(${formals_with_defaults});
```
这个文件声明了所有的native函数。ATen的native函数才是PyTorch的函数应该有的样子，区别于历史上老旧的TH/THC cwrap函数。目前PyTorch这部分的迁移工作还未结束，有些老旧的来自Torch历史博物馆的TH/THC函数仍然在使用中。 Native 函数都会被声明在native_functions.yaml中，然后实现在aten/src/ATen/native/目录下的cpp文件中。

native函数可以通过C++和Python接口调用。在C++中，可以通过Tensor类的方法和at namespace中的函数来进行访问；在Python中，可以通过Variable类或者torch._C._FunctionBase来访问。

# 总结
在本文中，gemfield描述了Python中ATen的代码动态生成。ATen中动态生成的代码主要有：
- 1，Type继承体系，包含头文件和源文件；Type继承体系/家族是联系Tensor op 与 legacy的TH/现代的native kernel函数之间的纽带；Type继承体系维护了2/3级分发机制。
- 2，Declarations.yaml，会被Torch模块动态生成代码调用；
- 3，生成Tensor类；
- 4，生成Type家族注册初始化的代码；
- 5，生成legacy的TH/THC的kernel的声明；
- 6，生成modern PyTorch的native kernel的声明。

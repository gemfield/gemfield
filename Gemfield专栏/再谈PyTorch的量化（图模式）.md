# 背景
在Gemfield：PyTorch的量化一文中，Gemfield介绍了PyTorch目前的三种量化：

- 后训练动态量化；
- 后训练静态量化；
- 量化感知训练。

只是，但凡在一线实践过PyTorch量化，就会发现一些问题——一些不便之处。尤其是对于静态量化和量化感知训练，这些不便之处有：

- 需要手工插入QuantStub和DeQuantStub，否则会报错（如果使用DeepVAC的话，这一步可忽略）：
```
RuntimeError: Could not run 'quantized::some_operator' with arguments from the 'CPU' backend...
```
- 需要手工调用fuse_modules() API来对模块进行合并，且必须手工指定要合并的模块的名字（如果使用DeepVAC的话，这一步可忽略）；
- Functionals在量化王国里没有被当作一等公民，比如functional.conv2d、functional.linear都不会被量化（如果使用的是QAT，DeepVAC并没有解决这个问题）；
- 一些Add、cat这样的操作需要额外手工使用FloatFunctional来包装，否则运行会报错（如果使用的是QAT，DeepVAC并没有解决这个问题）：
```
RuntimeError: Could not run 'aten::add.Tensor' with arguments from the 'QuantizedCPU' backend. 
This could be because the operator doesn't exist for this backend, 
or was omitted during the selective/custom build process (if using custom build). 
If you are a CivilNet employee using DeepVAC, 
please visit https://github.com/deepvac/deepvac for possible resolutions. 
'aten::add.Tensor' is only available for these backends: 
[CPU, CUDA, MkldnnCPU, SparseCPU, SparseCUDA, Meta, BackendSelect, Named, 
AutogradOther, AutogradCPU, AutogradCUDA, AutogradXLA, AutogradNestedTensor, 
UNKNOWN_TENSOR_TYPE_ID, AutogradPrivateUse1, AutogradPrivateUse2, AutogradPrivateUse3, 
Tracer, Autocast, Batched, VmapMode].
```
那这些种种不便之处该怎么解决呢？实际上，在PyTorch 1.8 版本中，一种称之为GRAPH MODE（图模式）的量化功能正在开发中（之前的量化模式称之为Eager模式中的量化），一旦发布便可以解决上述的问题。

# 动态量化
在GRAPH MODE中，要动态量化自己的模型，一定要先trace或者script。

## 1，trace或者script模型
```
script_model = torch.jit.script(float_model).eval()

#或者
traced_model = torch.jit.trace(float_model, gemfield_input).eval()
```
## 2，动态量化
```
from torch.quantization import quantize_dynamic_jit, per_channel_dynamic_qconfig

qconfig_dict = {'': per_channel_dynamic_qconfig}
quantized_model = quantize_dynamic_jit(traced_model, qconfig_dict)
```
这样就完成了。
# 静态量化
在GRAPH MODE中，要静态量化自己的模型，一定要先trace或者script。
## 1，trace或者script模型
```
script_model = torch.jit.script(float_model)

#或者
traced_model = torch.jit.trace(float_model, gemfield_input)
```
## 2，准备qconfig
```
from torch.quantization import get_default_qconfig, quantize_jit

qconfig = get_default_qconfig('fbgemm')
qconfig_dict = {'': qconfig}
```
## 3，准备定标材料
定标材料需要dataloader和calibrate函数：
```
data_loader = torch.utils.data.DataLoader(dataset, batch_size=train_batch_size, sampler=gemfield_sampler)

def calibrate(model, data_loader):
    model.eval()
    with torch.no_grad():
        for sample, target in data_loader:
            model(sample)
```
dataloader就是torch.utils.data.DataLoader，calibrate函数基本都像上面这样实现。

## 4，静态量化
一个API调用即可：
```
quantized_model = quantize_jit(
    civilnet_model, # TorchScript model
    qconfig_dict, # qconfig dict
    calibrate, # calibration function
    [data_loader], # positional arguments to calibration function, typically some sample dataset
    inplace=False, # whether to modify the model inplace or not
    debug=True) # whether to prduce a debug friendly model or not
```

可以看到，相较于eager mode模式下的量化，我们节省了背景中所列的复杂的手工工作。

# 量化感知训练（QAT）
这部分的开发进度最慢，目前仍没有可以使用的API。你可以关注本文，当该功能上线后，Gemfield将会第一时间进行更新。
# 最后
借助deepvac项目，用户可以无感知的使用上述量化功能，Gemfield建议普通用户使用。
https://github.com/DeepVAC/deepvac

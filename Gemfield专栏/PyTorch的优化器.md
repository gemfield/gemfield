##  **背景**

假设要在计算机上实现一个函数f(x)，它的输入x是一张图片的像素值，需要让它的输出是这张图片的一个类别。那么如何设计这个函数，以及如何对这个函数的系数进行求解呢？这就是CV领域的一个最最基础的问题。如果我们抱着简化这个问题的目的把这个问题实例化，那么Gemfield会使用如下的方式重新描述下这个问题：“对于一个224x224分辨率的RGB图片，如何设计一个函数来根据输入的224
* 224 * 3 = 150528 个值，来输出这个图片对应的类别（是猫是狗还是人）？“。

在1946年以前，这个问题是不存在的，因为计算机是1946年发明的；

在1969年以前，这个问题“几乎”是不存在的，因为贝尔实验室在这一年才发明了CCD，在未来的20年时间内，数码图片才慢慢开始普及开来；

在1989~1998年以后，这个问题的答案以确凿的证据新增了一种，那就是名为CNN（卷积神经网络）的函数；

在2012年以后，伴随着AlexNet石破天惊式的成功，这个问题的答案变成了只有确定的一种——还是曾经那个名为CNN的函数；如果你觉得答案不是非得如此，并且还能够给出证据，那么你就还拥有另外一种称号：图灵奖获得者；

在2015年，这个问题的答案依然是CNN，而且是一个名为resnet的CNN，它的里程碑意义在于：在一个名为ImageNet的试卷上，求解这个问题的能力首次超过了人类。

##  **如何求解f(x)函数的各项系数**

在我们已经确定了f(x)就是经典的resnet50的情况下，Gemfield和你仍然面临一个问题。那就是——resnet50这个函数大约有2000万个系数需要计算出来——我们该如何计算出这么多系数的值呢？如果系数计算的好，那么在ImageNet试卷上可以超越人类；而如果计算的不好，那就是无尽的嘲讽。

可是计算出2000万个函数的系数又谈何容易呢？这些系数究竟该如何计算出来呢？

一个最直接的方式就是穷举一遍参数，看看哪组参数在测试集上表现的最好，也就是在模拟试卷上能得到最高分，那么该组参数就是我们要求解出来的系数值。真是个机智的少年！只不过要这么遍历下来，以每个系数由32个bit表示的话，我们需要大约迭代2^32^20M
次，这是个python表达式，翻译成人话就是——愚公没断奶的孙子移喜马拉雅山，这不是一个人定胜天的神话故事，而是一个绝望的悲剧。

没有智慧的蛮力是没有什么价值的！

事实上，在1989~1998年以后，使用反向传播求解这些系数的梯度，然后再使用随机梯度下降法（SGD优化器）来求解（或者叫逼近）这些系数的最终值就渐渐成为主流了。直到今天，求解这2000万系数的方法仍然是BP
+ 各种优化器。如果你觉得答案不是非得如此，并且还能够给出证据，那么你就还拥有另外一种称号：2个图灵奖的获得者。

那么这种BP +
优化器求解得到的系数值和穷举（如果愚公的孙子真的把喜马拉雅搬走的话）求解得到的值会一样吗？不一样！穷举可以得到全局最优解（这不废话嘛，我所有的值都穷举了一遍，是不是全局最优我不知道？当然需要模拟试卷上有足够多的题目啊，不然不同的系数值的组合会导致一样的分数...)；而BP+优化器求解得到的值是接近全局最优解的值（不是局部最优也不是鞍点，而是高维空间下不可描述的不利地形），这是BP+优化器的局限之一，同时也是市场会提供这么多炼丹师岗位的原因之一。

本文就是来描述PyTorch中是如何实现优化器的，以及SGD优化器的工作原理。要开始本文，Gemfield先给出一个具体的微型的CNN网络用以演示。

##  **用于演示的网络**

就以下面这个网络为例：

    
    
    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, 1)
            self.conv2 = nn.Conv2d(32, 64, 3, 1)
            self.dropout1 = nn.Dropout2d(0.25)
            self.dropout2 = nn.Dropout2d(0.5)
            self.fc1 = nn.Linear(9216, 128)
            self.fc2 = nn.Linear(128, 10)
    
        def forward(self, x):
            x = self.conv1(x)
            x = F.relu(x)
            x = self.conv2(x)
            x = F.relu(x)
            x = F.max_pool2d(x, 2)
            x = self.dropout1(x)
            x = torch.flatten(x, 1)
            x = self.fc1(x)
            x = F.relu(x)
            x = self.dropout2(x)
            x = self.fc2(x)
            output = F.log_softmax(x, dim=1)
            return output

如果你熟悉这篇文章的话： [ Gemfield：详解Pytorch中的网络构造
](https://zhuanlan.zhihu.com/p/53927068)
，你就轻松的知道这里虽然使用了relu、pool，但是在这里它们并没有可学习的参数；而且你亦很自豪的知道——这里可学习的参数及其大小都有：

  * conv1.weight，大小为 torch.Size([32, 1, 3, 3]) 
  * conv1.bias，大小为 torch.Size([32]) 
  * conv2.weight，大小为 torch.Size([64, 32, 3, 3]) 
  * conv2.bias，大小为 torch.Size([64]) 
  * fc1.weight，大小为 torch.Size([128, 9216]) 
  * fc1.bias，大小为 torch.Size([128]) 
  * fc2.weight，大小为 torch.Size([10, 128]) 
  * fc2.bias，大小为 torch.Size([10]) 

这些参数在一次前向中是如何参与运算的呢？我们看到上面的参数分为卷积和全连接两种操作。我们先说卷积：
**当输入是多个channel的话，一般来说卷积中的术语kernel和filter表达的意思就有区别了：**

  * **输出channel数量 = 输出的feature map数量 = filter的数量 ；**
  * **输入channel数量= 每个filter中的kernel数量；**
  * **每个输入的channel 和 每个filter中对应的kernel 进行 cross-correlation 运算，然后一个filter中的所有计算结果累加起来就是一个输出的feature map：**

    
    
    for i, filter in enumerate(filters):
      for j, kernel in enumerate(kernels_in_one_filter):
        #filters[j] is the kernel
        output_feature[i] += filters[j] cross-correlation input_channel[j]
      output_feature[i] += bias[i]

所以可以这么说，一个传统卷积层（不考虑group等）中一个filter的参数数量为input_channel * kernel_w *
kernel_h，一共有output_channel个filter，每个filter上还有一个bias。而conv1的输入channel是1，输出channel是32，kernel
size是3*3；conv2的输入channel是32，输出channel是64，kernel size是3*3。那么参数数量是多少呢？继续看吧。

我们再来说全连接：对于全连接fc操作来说，y = x*W^T + b ：

    
    
    y = x.matmul(m.weight.t()) + m.bias 

如此以来，上述用于演示的CNN中的参数由如下 **8个parameter实例** 组成：

  * conv1的weights参数数量为32*1*3*3 = 288； 
  * conv1的bias参数数量为32； 
  * conv2的weights参数数量为 64 * 32 * 3 * 3 = 18432； 
  * conv2的bias参数数量为64； 
  * fc1的weights参数数量为128 * 9216 = 1179648； 
  * fc1的bias参数数量为128； 
  * fc2的weights参数数量为10 * 128 = 1280； 
  * fc2的bias参数数量为10； 

该网络的总共参数数量为 288 + 32 + 18432 + 64 + 1179648 + 128 + 1280 + 10 = **1199882**
，可以看出来参数数量主要是由全连接层贡献的。

而针对类似的CNN使用优化器的典型步骤如下所示：

    
    
    optimizer = optim.SGD(model.parameters(), lr=args.lr)
    for epoch in epochs:
      for batch in epoch:
        optimizer.zero_grad()
        ...前向...loss...反向...
        optimizer.step()

这就引申出如下的问题：

  1. 构造一个优化器实际上是在构造什么呢？需要传入什么内容呢？ 
  2. 一个优化器的本质工作或者目的是什么呢？实现一个新的优化器主要是实现什么呢？ 
  3. 为什么每次迭代前需要调用优化器的zero_grad()方法呢？ 
  4. 为什么每次迭代后需要调用优化器的step()方法呢？ 
  5. PyTorch都有哪些内置的优化器？它们的本质区别是什么呢？ 

##  **PyTorch的优化器**

PyTorch的优化器就是Optimizer类以及它的子类孩子们：

    
    
    >>> print("\n".join([o for o in dir(torch.optim) if "_" not in o]))
    ASGD
    Adadelta
    Adagrad
    Adam
    AdamW
    Adamax
    LBFGS
    Optimizer
    RMSprop
    Rprop
    SGD
    SparseAdam

想必你已经看到了很多熟悉的名字了，比如SGD——使用BP计算梯度，使用SGD或者其它Optimizer更新权重，这是炼丹师们永恒不变的主题。像SGD这样的子类，它们继承Optimizer基类，并重写了父类中的__init__和step方法。

那么Optimizer类维护了什么资源呢？有且仅有3种资源——在定义Optimizer类的序列化行为的__getstate__方法中，代码明确且丝毫没有迟疑的给出了它们的名字：

    
    
    def __getstate__(self):
        return {
            'defaults': self.defaults,
            'state': self.state,
            'param_groups': self.param_groups,
        }

没错，就是defaults、state、param_groups。Gemfield来一一介绍下：

**1，defaults**

它是个字典，定义全局的优化器参数（一个parameter
group没有显式指定的话，就使用这个），比如，如果Gemfield使用的是SGD的话，Optimizer中的defaults就是：

    
    
    {'lr': 1.0, 'momentum': 0.9, 'dampening': 0, 'weight_decay': 0, 'nesterov': False}

  * lr：学习率 
  * momentum：动量系数 
  * dampening：用于动量SGD中调节当前梯度权重的参数； 
  * weight_decay：L2 penalty系数 
  * nesterov：是否启用nesterov动量 

可见都是和SGD相关的一些超参数。

**2，state**

state是一个defaultdict类型，它首先就是一个dict，既然是字典，那么它的key和value是什么呢？

  * key是Parameter（也就是带有梯度的Tensor）； 
  * Value是个字典dict，具体内容取决于优化器的种类，在SGD中，是{"momentum_buffer": [tensor,...]}； 

state这个字典有多少元素呢？SGD中，在初始化的时候，它就是个空的字典，而在第1次迭代后（为什么是第1次迭代后？因为有了历史梯度信息），state中包含了8个k-
v对，k和v分别是该网络的8个parameter及其对应的历史梯度。

**3，param_groups**

如果你没有显式的把model的parameters按组进行划分的话，那么默认所有的参数都会存放在Optimizer为你自动生成的1个param_group中，像下面这样：

    
    
    [{'params': [tensor...]}]

咦？为啥需要把一个model的所有parameters划分为多个parameter
groups？那目的自然是要适用不同的训练参数，当然你可以不划分，这时候就会使用defaults中的参数。Optimizer的构造接收2个参数：defaults（上面说过了）和params（模型的参数）。

而对于params来说，其最终是要维护在Optimizer中的self.param_groups中的。首先params的类型必须是list或者迭代器中的一种——换言之，不能是Tensor、dict、set或者其它类型。如果传入的是迭代器（比如model.parameters())，则会立刻将其转换为list。至此，入参已经全部被转换为了list，而list又有两种：

  * list中的每个元素是个dict；如果是这种情况，说明 **用户显式的传入了分组的parameters** ，形式看起来像这样：[{'params': [tensor...], 超参1: 超参的值,...}, {'params': [tensor...], 超参1: 超参的值,...}...] 
  * list中的每个元素是个tensor；则该list会被转换为[{'params': [tensor...]}]，没错，就相当于只有一个parameter group； 

如果有多个parameter group的话，还需要检查两两之间是否包含了重复的参数。Optimizer的多个parameter
group之间不允许有重复出现的parameter。

构造完毕后的Optimizer，在其self.param_groups成员中就已经维护好了1个或多个parameter
group。在上面的简单示例中，我们只有1个parameter group，其中存放的是8个parameter tensor。哪8个呢？如下所示：

  * conv1.weight，大小为 torch.Size([32, 1, 3, 3]) 
  * conv1.bias，大小为 torch.Size([32]) 
  * conv2.weight，大小为 torch.Size([64, 32, 3, 3]) 
  * conv2.bias，大小为 torch.Size([64]) 
  * fc1.weight，大小为 torch.Size([128, 9216]) 
  * fc1.bias，大小为 torch.Size([128]) 
  * fc2.weight，大小为 torch.Size([10, 128]) 
  * fc2.bias，大小为 torch.Size([10]) 

##  **优化器的train**

在对网络进行训练的过程中，我们要注意以下几点：

**1，需要将model设置为train模式**

使用model.train()来设置train模式，这个调用会递归的调用网络中定义的每一个module：

    
    
    self.training = mode
        for module in self.children():
            module.train(mode)

相当于是对以下module递归的调用了train：

  * conv1 
  * conv2 
  * dropout1 
  * dropout2 
  * fc1 
  * fc2 

这个调用只对某些特定的module起作用，比如Dropout、BN等，这些module在train和eval中的行为是不一样的。

**2，optimizer.zero_grad()**

在每次迭代的forward之前，优化器都需要调用zero_grad()函数来把所有的parameter（Tensor）从计算图上detach掉（无法参与BP了）并且把其上的梯度清零：

    
    
    def zero_grad(self):
      for group in self.param_groups:
        for p in group['params']:
          if p.grad is not None:
            p.grad.detach_()
            p.grad.zero_()

嗯？我听说带动量的SGD是需要历史梯度参与运算的，那历史的梯度信息在哪里呢？在Optimizer类的state成员中。

**3，step()**

在每次迭代的backward之后，优化器都需要调用step()来更新所有的parameters：

    
    
    for p in group['params']:
      for p in group['params']:
        d_p = p.grad
        p.add_(d_p, alpha=-group['lr'])

Pytorch
Tensor的add_方法就不必介绍了，其意义和方法名一样直截了当，需要说明的是，当alpha参数不为None的话——当前的代码就是这种情况，则

    
    
    p.add_(d_p, alpha=-group['lr'])

就相当于 p = p + (-group['lr'] * d_p )。

而d_p就是PyTorch在每一次backward中使用BP算法得到的每个parameter的梯度值。以上就是传统SGD及其如何更新parameter的奥秘。

但如今在实际使用中，都会结合动量来使用——也就是带momentum的SGD。而在PyTorch实现的带momentum的SGD优化器中，又根据参数nesterov的true或false来决定是否启用nesterov
momentum：

    
    
    #buf代表历史梯度
    buf = param_state['momentum_buffer']
    buf.mul_(momentum).add_(d_p, alpha=1 - dampening)
    if nesterov:
      d_p = d_p.add(buf, alpha=momentum)
    else:
      d_p = buf

如果没有启用nesterov动量的话，则新的梯度 = 当前梯度 + 历史梯度 * 动量系数，同时新的梯度在下一次迭代中成为历史梯度：

buf = d_p * (1 - dampening) + (buf * momentum)

如果启用nesterov动量的话，则新的梯度还要 **再次** 基于动量系数做一次更新，相当于超前做了一次动量更新：

d_p = d_p + buf * momentum

##  **4，L2正则**

为了防止过拟合而在loss上加的L2 penalty: ˜( **** ) = ( **** ) + * **^** 2 / 2，导致更新权重的公式变成了(
是权重parameter、 是学习率、 是正则系数)：

← − * (∂ /∂ )− * *

← − * ( (∂ /∂ ) + * )

这个逻辑正好和优化器相关， 正是PyTorch优化器中的weight_decay入参，而整个逻辑正是实现在了PyTorch优化器的step()方法中：

    
    
    if weight_decay != 0:
      d_p = d_p.add(p, alpha=weight_decay)

也就是说，如果在构造优化器的时候传入了weight_decay参数，那么梯度首先会应用L2 penalty：d_p = d_p + (p *
weight_decay)。这正是实现了 ← − * ( (∂ /∂ ) + * )公式中的括号内部分。

##  **总结**

我们来进行下技术总结。

**1，构造一个优化器实际上是在构造什么呢？需要传入什么内容呢？**

构造parameter group，需要传入网路训练相关的超参数。

**2，一个优化器的本质工作或者目的是什么呢？实现一个新的优化器主要是实现什么呢？**

根据BP算法得到的每个parameter的梯度，优化器研究如何更快、更好的去更新paramter本身的值；实现一个新的优化器，代码层面就是重写step()方法。

**3，为什么每次迭代前需要调用优化器的zero_grad()方法呢？**

舍弃上一次BP计算得到的梯度，为新的一次前向+反向做好准备。你可能会感觉有些困惑...好多优化器中，参数值的更新是要和历史梯度值进行计算的，这些历史梯度的值在哪里呢？维护在Optimizer类的state成员中。

**4，为什么每次迭代后需要调用优化器的step()方法呢？**

前向+反向计算得到梯度，调用step()使用该梯度来更新各parameter的值。

**5，PyTorch都有哪些内置的优化器？它们的本质区别是什么呢？**

    
    
    >>> print("\n".join([o for o in dir(torch.optim) if "_" not in o]))
    ASGD
    Adadelta
    Adagrad
    Adam
    AdamW
    Adamax
    LBFGS
    Optimizer
    RMSprop
    Rprop
    SGD
    SparseAdam

本质区别在于，重新实现了各自的step()方法——根据backward计算得到的grad，实现了不同的更新parameter值的方式。


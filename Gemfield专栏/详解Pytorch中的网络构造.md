##  **背景**

在PyTroch框架中，如果要自定义一个Net(网络，或者model，在本文中，model和Net拥有同样的意思)，通常需要继承自nn.Module然后实现自己的layer。比如，在下面的示例中，gemfield（tiande亦有贡献）使用Pytorch实现了一个Net（可以看到其父类为nn.Module)：

    
    
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    
    class CivilNet(nn.Module):
        def __init__(self):
            super(CivilNet, self).__init__()
            self.conv1 = nn.Conv2d(3, 6, 5)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1 = nn.Linear(16 * 5 * 5, 120)
            self.fc2 = nn.Linear(120, 84)
            self.fc3 = nn.Linear(84, 10)
            self.gemfield = "gemfield.org"
            self.syszux = torch.zeros([1,1])
    
        def forward(self, x):
            x = self.pool(F.relu(self.conv1(x)))
            x = self.pool(F.relu(self.conv2(x)))
            x = x.view(-1, 16 * 5 * 5)
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            return x

这就带来了一系列的问题：

1，为什么要继承自nn.Module？

2，网络的各个layer或者module为什么要直接定义在构造函数中，而不能（比方说）放在构造函数中的一个list里？

3，forward函数什么时候会被调用？为什么要使用net(input)而不是net.forward(input)来做前向呢？

4，保存模型时，保存的究竟是什么？

5，重新载入一个pth模型时，究竟发生了什么？

你肯定要问了，为什么没说到反向？因为反向是optimizer和tensor的grad共同完成的，本文只讨论Net部分，这一系列文章的后续部分会讨论反向。

##  **CivilNet的实例化**

一个Net，也就是继承自nn.Module的类，当实例化后，本质上就是维护了以下8个字典(OrderedDict)：

    
    
    _parameters
    _buffers
    _backward_hooks
    _forward_hooks
    _forward_pre_hooks
    _state_dict_hooks
    _load_state_dict_pre_hooks
    _modules

这8个字典用于网络的前向、反向、序列化、反序列化中。

因此，当实例化你定义的Net(nn.Module的子类)时，要确保父类的构造函数首先被调用，这样才能确保上述8个OrderedDict被create出来，否则，后续任何的初始化操作将抛出类似这样的异常：cannot
assign module before Module.__init__() call。

对于前述的CivilNet而言，当CivilNet被实例化后，CivilNet本身维护了这8个OrderedDict，更重要的是，CivilNet中的conv1和conv2(类型为nn.modules.conv.Conv2d）、pool（类型为nn.modules.pooling.MaxPool2d）、fc1、fc2、fc3（类型为torch.nn.modules.linear.Linear）均维护了8个OrderedDict，因为它们的父类都是nn.Module，而gemfield（类型为str）、syszux（类型为torch.Tensor)则没有这8个OrderedDict。

也因此，在你定义的网络投入运行前，必然要确保和上面一样——构造出那8个OrderedDict，这个构造，就在nn.Module的构造函数中。如此以来，
**你定义的Net就必须继承自nn.Module** ；如果你的Net定义了__init__()方法，
**则必须在你的__init__方法中调用nn.Module的构造函数** ，比如super(your_class).__init__()
，注意，如果你的子类没有定义__init__()方法，则在实例化的时候会默认用nn.Module的，这种情况也对。

nn.Module通过使用__setattr__机制，使得定义在类中（不一定要定义在构造函数里）的成员（比如各种layer），被有序归属到_parameters、_modules、_buffers或者普通的attribute里；那具体怎么归属呢？很简单，当类成员的type
派生于Parameter类时（比如conv的weight，在CivilNet类中，就是self.conv1中的weight属性），该属性就会被划归为_parameters；当类成员的type派生于Module时（比如CivilNet中的self.conv1，其实除了gemfield和syszux外都是），该成员就会划归为_modules。

如果知道了这个机制，就会自然而然的知道，如果上面的CivilNet里的成员封装到一个list里，像下面这样：

    
    
    class CivilNet(nn.Module):
        def __init__(self):
            super(CivilNet, self).__init__()
            conv1 = nn.Conv2d(3, 6, 5)
            pool = nn.MaxPool2d(2, 2)
            conv2 = nn.Conv2d(6, 16, 5)
            self.layer1 = [conv1, pool, conv2]
            ...

那么在运行的时候，可能optimizer就会提示parameters为empty。这就是因为成员layer1的type派生自list，而非Module；而像CivilNet这样的Net，在取所有的parameters的时候，都是通过_modules桥梁去取得的......

**1，_parameters**

前述说到了parameters就是Net的权重参数（比如conv的weight、conv的bias、fc的weight、fc的bias)，类型为tensor，用于前向和反向；比如，你针对Net使用cpu()、cuda()等调用的时候，实际上调用的就是parameter这个tensor的cpu()、cuda()等方法；再比如，你保存模型或者重新加载pth文件的时候，针对的都是parameter的操作或者赋值。

如果你针对的是CivilNet直接取_parameters属性的值的话，很遗憾是空的，因为CivilNet的成员并没有直接派生自Parameter类；但是当针对CivilNet取parameters()函数的返回值（是个iter）时，则会递归拿到所有的，比如conv的weight、bias等；

**2，_buffers**

该成员值的填充是通过register_buffer
API来完成的，通常用来将一些需要持久化的状态（但又不是网络的参数）放到_buffer里；一些极其个别的操作，比如BN，会将running_mean的值放入进来；

**3，_modules**

_modules成员起很重要的桥梁作用，在获取一个net的所有的parameters的时候，是通过递归遍历该net的所有_modules来实现的。

像前述提到的那个问题，如果将这些成员都放倒一个python list里：self.layer1 = [conv1, pool, conv2]
——会导致CivilNet不能将conv1, pool,
conv2等划归到_modules里，从而通过CivilNet的parameters()获取所有权重参数时，拿到的东西为空，就会报optimizer got
an empty parameter list这样的错误。针对这种情况，那怎么办呢？

ModuleList就是为了解决这个问题的，首先，ModuleList类的基类正是Module：

    
    
    class ModuleList(Module)

其次，ModuleList实现了python的list的功能；

最后，在使用ModuleList的时候，该类会使用基类（也就是Module）的add_module()方法，或者直接操作_modules成员来将list中的module成功注册。

Sequential模块也具备ModuleList这样的注册功能，另外其还实现了forward，这是和ModuleList不同的地方：

    
    
    def forward(self, input):
        for module in self._modules.values():
            input = module(input)
        return input

##  **CivilNet的前向**

网络的前向需要通过诸如CivilNet(input)这样的形式来调用，而非CivilNet.forward(input)，是因为前者实现了额外的功能：

    
    
    1，先执行完所有的_forward_pre_hooks里的hooks
    2, 再调用CivilNet的forward函数
    3, 再执行完所有的_forward_hooks中的hooks
    4, 再执行完所有的_backward_hooks中的hooks

可以看到:

1，_forward_pre_hooks是在网络的forward之前执行的。这些hooks通过网络的register_forward_pre_hook()
API来完成注册，通常只有一些Norm操作会定义_forward_pre_hooks。这种hook不能改变input的内容。

2，_forward_hooks是通过register_forward_hook来完成注册的。这些hooks是在forward完之后被调用的，并且不应该改变input和output。目前就是方便自己测试的时候可以用下。

3，_backward_hooks和_forward_hooks类似。

所以总结起来就是，如果你的网络中没有Norm操作，那么使用CivilNet(input)和CivilNet.forward(input)是等价的。

另外，你必须使用CivilNet.eval()操作来将dropout和BN这些op设置为eval模式，否则你将得到不一致的前向返回值。eval()调用会将Net的实例中的training成员设置为False。

##  **CivilNet模型的保存和重新加载**

如果我们要保存一个训练好哦PyTorch模型的话，会使用下面的API：

    
    
    cn = CivilNet()
    ......
    torch.save(cn.state_dict(), "your_model_path.pth")

可以看到使用了网络的state_dict() API调用以及torch模块的save调用。一言以蔽之，模型的保存就是先通过state_dict()
API的调用获得一个关于网络参数的字典，再通过pickle模块序列化成文件的形式。

而如果我们要load一个pth模型来进行前向的时候，会使用下面的API：

    
    
    cn = CivilNet()
    
    #参数反序列化为python dict
    state_dict = torch.load("your_model_path.pth")
    #加载训练好的参数
    cn.load_state_dict(state_dict)
    
    #变成测试模式，dropout和BN在训练和测试时不一样
    #eval()会把模型中的每个module的self.training设置为False 
    cn = cn.cuda().eval()

可以看到使用了torch模块的load调用和网络的load_state_dict()
API调用。一言以蔽之，模型的重新加载就是先通过torch.load反序列化pickle文件得到一个Dict，然后再使用该Dict去初始化当前网络的state_dict。torch的save和load
API在python2中使用的是cPickle，在python3中使用的是pickle。另外需要注意的是，序列化的pth文件会被写入header信息，包括magic
number、version信息等。

关于模型的保存，我们需要弄清楚以下概念：1, state_dict；2, 序列化一个pth模型用于以后的前向；3,
为之后的再训练保存一个中间的checkpoint；4,将多个模型保存为一个文件；5,用其它模型的参数来初始化当前的网络；6,跨设备的模型的保存和加载。

**1, state_dict**

在Pytorch中，可学习的参数(如Module中的weights和biases)是包含在网络的parameters()调用返回的字典中的，这就是一个普通的OrderedDict，这里面的key-
value是通过网络及递归网络里的Module成员获取到的：它的key是每一个layer的成员的名字(加上prefix），而对应的value是一个tensor。比如本文前述的CivilNet类，它的state_dict中的key如下所示：

    
    
    conv1.weight
    conv1.bias
    conv2.weight
    conv2.bias
    fc1.weight
    fc1.bias
    fc2.weight
    fc2.bias
    fc3.weight
    fc3.bias

那如果你使用了DataParallel来训练的话：

    
    
    cn = nn.DataParallel(cn)

那么state_dict中的key将如下所示：

    
    
    module.conv1.weight
    module.conv1.bias
    module.conv2.weight
    module.conv2.bias
    module.fc1.weight
    module.fc1.bias
    module.fc2.weight
    module.fc2.bias
    module.fc3.weight
    module.fc3.bias

如果你使用了ModuleList的话，比如前述CivilNet的定义你写作了：

    
    
    class CivilNet(nn.Module):
        def __init__(self):
            super(CivilNet, self).__init__()
            conv1 = nn.Conv2d(3, 6, 5)
            pool = nn.MaxPool2d(2, 2)
            conv2 = nn.Conv2d(6, 16, 5)
            fc1 = nn.Linear(16 * 5 * 5, 120)
            fc2 = nn.Linear(120, 84)
            fc3 = nn.Linear(84, 10)
            self.gemfield = nn.ModuleList([conv1, pool, conv2, fc1, fc2, fc3])

那state_dict中的key将如下所示：

    
    
    gemfield.1.weight
    gemfield.1.bias
    gemfield.2.weight
    gemfield.2.bias
    gemfield.3.weight
    gemfield.3.bias
    gemfield.4.weight
    gemfield.4.bias
    gemfield.5.weight
    gemfield.5.bias

还有很多的变种，不过大抵上你也知道规律了。

**2，load_state_dict**

load_state_dict()调用是nn.Module的一个API，用模型文件反序列化后得到的Dict来初始化当前的模型。需要提及的是这个函数上的
strict参数，默认值是True。因此在初始化时候，该函数会严格比较源Dict和目标Dict的key是否一样，不能多也不能少，必须严格一样。

如果将strict参数设置为False，则将不会进行这样严格的check。只有key一样的才会进行赋值。

**3,序列化模型以保存state_dict**

这种情况是PyTorch中最常用的保存模型的方法。

    
    
    #save
    torch.save(model.state_dict(), PATH)
    
    #load
    model = CivilNet(*args, **kwargs)
    model.load_state_dict(torch.load(PATH))
    model.eval()

不再赘述。

**4，序列化整个模型**

    
    
    #save
    torch.save(model, PATH)
    #load
    model = torch.load(PATH)
    model.eval()

这种方式不推荐，其是通过Pickle模块将整个class序列化了，序列化过程中依赖很多具体的东西，比如定义model
class的路径。这样反序列化的时候就丧失了灵活性。

**5，序列化中间过程中的checkpoint**

这种序列化的目的是为了之后以这个状态为基点重新开始训练。和前述序列化模型的本质不同就在于还需要序列化optimizer的Dict（比如学习率等参数）。传统上，checkpoint文件用.tar作为后缀：

    
    
    #save
    torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': loss,
                ...
                }, PATH)
    
    #load
    model = CivilNet(*args, **kwargs)
    optimizer = TheOptimizerClass(*args, **kwargs)
    
    checkpoint = torch.load(PATH)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']
    
    model.train()
    #model.eval()

**6，将多个模型序列化到一个文件里**

比如，decoder-encoder这种结构会有多个Net。传统上，checkpoint文件用.tar作为后缀。

    
    
    #save
    torch.save({
                'modelA_state_dict': modelA.state_dict(),
                'modelB_state_dict': modelB.state_dict(),
                'optimizerA_state_dict': optimizerA.state_dict(),
                'optimizerB_state_dict': optimizerB.state_dict(),
                ...
                }, PATH)
    
    #load
    modelA = TheModelAClass(*args, **kwargs)
    modelB = TheModelBClass(*args, **kwargs)
    optimizerA = TheOptimizerAClass(*args, **kwargs)
    optimizerB = TheOptimizerBClass(*args, **kwargs)
    
    checkpoint = torch.load(PATH)
    modelA.load_state_dict(checkpoint['modelA_state_dict'])
    modelB.load_state_dict(checkpoint['modelB_state_dict'])
    optimizerA.load_state_dict(checkpoint['optimizerA_state_dict'])
    optimizerB.load_state_dict(checkpoint['optimizerB_state_dict'])

**7，用一个模型的部分参数初始化另一个模型（迁移学习）**

这种情况的目的是为了复用一个模型的部分layer，以实现迁移学习。

    
    
    #save
    torch.save(modelA.state_dict(), PATH)
    
    #load
    modelB = TheModelBClass(*args, **kwargs)
    modelB.load_state_dict(torch.load(PATH), strict=False)

和前述保存模型相比，序列化部分一样，反序列化只需要将strict参数设置为False。在前述load_state_dict章节中已经解释过，此处不再赘述。

**8，跨device（cpu/gpu）来save/load模型**

比如模型是在GPU上训练的，现在要load到cpu上。或者反之，或者在CPU上训练，在GPU上load。这三种情况下，save的方法是一样的：

    
    
    torch.save(model.state_dict(), PATH)

而load的方法就不一样了：

    
    
    ###############Save on GPU, Load on CPU #########
    device = torch.device('cpu')
    model = CivilNet(*args, **kwargs)
    model.load_state_dict(torch.load(PATH, map_location=device))
    
    ###############Save on GPU, Load on GPU #########
    device = torch.device("cuda")
    model = CivilNet(*args, **kwargs)
    model.load_state_dict(torch.load(PATH))
    model.to(device)
    #确保在输入给网络的tensor上调用input = input.to(device)
    
    ###############Save on CPU, Load on GPU #########
    device = torch.device("cuda")
    model = CivilNet(*args, **kwargs)
    model.load_state_dict(torch.load(PATH, map_location="cuda:0"))  # Choose whatever GPU device number you want
    model.to(device)
    #确保在输入给网络的tensor上调用input = input.to(device)

**9，使用torch.nn.DataParallel训练的模型如何序列化**

torch.nn.DataParallel
是一个wrapper，用来帮助在多个GPU上并行进行运算。这种情况下要保存训练好的模型，最好使用model.module.state_dict()，
**请参考本章第1节：state_dict** 。这种情况下你在重新加载pth模型文件的时候，就会有极大的灵活性，而不是出现一大堆unexpected
keys和missed keys：

    
    
    torch.save(model.module.state_dict(), PATH)

##  **打印CivilNet**

这个是靠__repr__机制，不再赘述；

    
    
    cn = CivilNet()
    print(cn)

另外，你的类可以重写nn.Module的extra_repr()方法来实现定制化的打印。


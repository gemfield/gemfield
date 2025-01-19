# 背景
在Docker公司重新发明（或发扬光大）容器这项技术以来，这项技术革命般的席卷了软件领域。随着生态的枝繁叶茂，各种分支也是层出不穷，包括横向分支和纵向分支。这些分支也会有自己的名字，于是经常给用户带来困扰。在本文，Gemfield将介绍这些术语及它们之间的区别：

- Docker（一般指那个发明docker技术的公司）；
- docker（指docker技术）；
- CRI
- OCI
- CRI-O
- CRI Plugin
- containerd
- runc
普通用户使用容器基本上是通过两种方式：

- 编排工具：比如kubernetes，简称k8s，大多数用户事实上的默认选择；
- 命令行：比如docker命令：
```
gemfield@CivilNet:/mnt/c/Users/civil$ docker ps -a
CONTAINER ID   IMAGE                  COMMAND   CREATED        STATUS                      PORTS                                                                                                                                                                      NAMES
a6648258fe0a   gemfield/homepod:2.0   "/init"   46 hours ago   Exited (255) 13 hours ago   0.0.0.0:3389->3389/tcp, :::3389->3389/tcp, 0.0.0.0:5900->5900/tcp, :::5900->5900/tcp, 0.0.0.0:7030->7030/tcp, :::7030->7030/tcp, 0.0.0.0:20022->22/tcp, :::20022->22/tcp   fervent_jackson
```
# 从k8s的视角自上而下
## 1，CRI

kubernetes是容器的编排工具，那少不了和容器（运行时+镜像）打交道。k8s把和容器打交道的方式制定了一个标准：CRI（CRI是container runtime interface的缩写）。也就是说，k8s按照CRI标准定义的方式去调度容器。既然CRI是个标准，那总得有对应的实现吧？没错：

- CRI-O：由Red Hat、IBM、Intel等实现，基于runc；
- rkt；
- cri-containerd（后来被重命名为了CRI Plugin）；
......等等

## 2，OCI 

和容器打交道的方式有了，那容器技术自身也得有个什么标准吧（Docker公司最初发明了它，但也不能只有Docker公司，对吧）？没错，那就是OCI。OCI是Open Container Initiative的缩写，是Docker公司发起的。OCI标准定义了container的image格式、container如何被运行等。既然OCI是个标准，那总得有对应的实现吧？没错：

- runc
- crun
- 等等。
但runc是主流，也主要是由Docker公司贡献的。

所以总结下来就是：gemfield和k8s打交道、k8s和CRI(实现)打交道、CRI(实现)和OCI(实现)打交道、OCI(实现)和系统内核打交道、内核和硬件打交道。

# 从Docker的视角自古至今
2013年Docker发布的时候，Docker公司拥有自己完整的生态。2013年底的时候，K8s的原型已经在实验中，在初期不可避免的要和docker打交道。在后来的发展中，Docker独立完整的生态对K8s及三方生态越来越不友好。

## 1，OCI之runc

这个时候，OCI开始标准化容器镜像格式和容器运行时。OCI就是Docker公司在2015年发起的，现在属于Linux基金会。OCI还在2015年7月发布了OCI规范的第一个实现：runc。runc偏向底层，通过系统调用和操作系统内核打交道。基于runc的上层实现有CRI-O、containerd等。

## 2，CNCF之containerd

Docker公司接着把自己的独立完整生态进行拆分，首先就是把容器运行时拆分成一个独立项目：containerd，并捐献给CNCF基金会。containerd的内容包含了处理底层存储、管理镜像、负责容器整个生命周期的管理等（containerd控制runc来实现）。

这样以来，K8s也舒服多了，就不用和Docker打交道了，转而就可以使用containerd项目了。

## 3，Docker命令行

有了上述的拆分行动后，Docker v1.11后，Docker引擎也开始基于runc和containerd进行构建。1.11版本是Docker的第一个基于OCI规范的发布，其实也是一种技术展示。这个时候，Docker变成了如下的架构：


Gemfield：Docker架构
Gemfield在命令行执行docker命令，docker命令请求Docker daemon(dockerd)，dockerd一直在侦听客户端的请求，然后转而通过containerd来做具体的容器的生命周期的管理，而containerd又通过runc去做更底层的事情。

# K8s和Docker
从K8s的角度来看，CRI是我唯一对容器提出的要求。所以你可以用CRI-O（符合CRI标准的一个实现），但是能不能用Docker生态里的东西呢？说到Docker生态里的东西，Gemfield具体指的是：

- dockerd（1.11之前）；
- containerd（1.11开始）。
```
你我相逢在黑夜的海上
你有你的，我有我的，方向
你记得也好，最好你忘掉
那交会时互放的光亮
——不知怎么的，Gemfield脑海里就浮现了这首诗。
```
但是dockerd和containerd都不支持CRI，那怎么办呢？添加一个中间层（单词shim，垫片）！比如，containerd 不支持CRI，但是cri-containerd就是这样一个shim，填满了CRI和containerd之间的缝隙。对了，cri-containerd如今被重命名为了 CRI Plugin。

dockerd不支持CRI，于是相应的也有了dockershim。当然，随着其它替代品的版本更新和功能完善，在今年年底，dockershim将被K8s彻底废除。

# 总结
阅读完Gemfield本文，下面这些术语想必你已不再陌生：

- Docker（一般指那个发明docker技术的公司）；
- docker（指docker技术）；
- CRI
- OCI
- CRI-O
- CRI Plugin
- containerd
- runc
正式这些商业的竞争、开源社区的奉献以及Gemfield孜孜不倦的实践，如今容器技术已经成熟到，足以让大名鼎鼎的TorchPod运行在Windows10上，你敢相信？

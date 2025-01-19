# 背景
从某种角度h审视的话，一个做着表情的人脸可以拆分为两部分：identity和expression。identity是某个人脸本质的东西，是区分一个人脸和另一个人脸的本质，是一个人脸在7x24小时的尺度内不会发生变化的东西；对应的，expression就是表情分量了，一张人脸有各种各样的表情，无时无刻都在变化着。这样一来，一个时刻下的人脸就可以看做是本质的identity叠加上此时此刻的expression。这样拆分出来的一个巨大好处就是，可以将一个人脸的expression分量提取出来，叠加到另一张人脸的identity上，让另一个人脸拥有相同的表情。甚至可以将expression分量叠加到另一张动物脸/卡通脸上——这就是Animoji。

# Blendshapes
但是表情这个东西看起来是一个无限多可能的东西，怎么能够计算expression呢？这就带来了Blendshapes——一组组成整体表情的基准（数量可以有十几个、50个、100+、 200+，越多就越细腻)。我们可以使用这一组基准通过线性组合来计算出整体的expression，用公式来说就是 
 ，其中e是expression，B是一组表情基准，d是对应的系数（在这一组里面的权重），b是neutral。

每个人有不同的identity，同样的就有不同的表情基准。根据上面的公式中，在刚开始的鸿蒙时代，一个人脸的B是不知道的，d也是不知道的，b也是不知道的......那我们要干什么？假设，我们先从美好的设想开始，假若我们知道每个人脸自己的B和b，那么把一个人脸的d应用到另一个人脸的B和b上，那么是不是另一个人脸就会露出同样的表情呢？

总之，上面一段的问题都是可以通过各种算法计算得到的，非常复杂。Blendshapes (Maya里面称之为 blend shapes ，而3DS Max里称之为morph targets) 在3D动画中被广泛使用。

# IPhone X上使用的Animoji
iphone x上使用的animoji需要52 blendshapes（ARKit 2规范），从苹果ARKit Face模块追踪得到的animation data将会驱动你的模型上的52 blendshapes ，从而线性组合出不同的表情。这52个Blendshapes如下所示：
```bash
eyeBlinkLeft
eyeLookDownLeft
eyeLookInLeft
eyeLookOutLeft
eyeLookUpLeft
eyeSquintLeft
eyeWideLeft
eyeBlinkRight
eyeLookDownRight
eyeLookInRight
eyeLookOutRight
eyeLookUpRight
eyeSquintRight
eyeWideRight
jawForward
jawLeft
jawRight
jawOpen
mouthClose
mouthFunnel
mouthPucker
mouthRight
mouthLeft
mouthSmileLeft
mouthSmileRight
mouthFrownRight
mouthFrownLeft
mouthDimpleLeft
mouthDimpleRight
mouthStretchLeft
mouthStretchRight
mouthRollLower
mouthRollUpper
mouthShrugLower
mouthShrugUpper
mouthPressLeft
mouthPressRight
mouthLowerDownLeft
mouthLowerDownRight
mouthUpperUpLeft
mouthUpperUpRight
browDownLeft
browDownRight
browInnerUp
browOuterUpLeft
browOuterUpRight
cheekPuff
cheekSquintLeft
cheekSquintRight
noseSneerLeft
noseSneerRight
tongueOut
gemfield
```
三维动画建模师的责任就在于此，他根据你的长相为你的脸建了个模型（scanned head, a photorealistic 3D head模型，甚至是一个卡通人物），并且更重要的是，他帮你的人脸构建了这52个表情基准和一个neutral中性基准——如果参数设计的不好，那可能你的微笑看起来就像是牙疼：
![Image](https://github.com/user-attachments/assets/42ded6da-0cb8-4c5e-9b21-1029e2b67032)
这些设计好的参数就会封装在业界主流的文件格式中，一般有FBX格式的, Unity的， Maya的。其中FBX是通用的格式，gemfield会使用blender软件打开FBX格式的文件。

# 总结
有了这些后，现在产业界流行使用AI技术（CNN网络）来对一个输入的人脸推理出expression的系数，也就是一组表情基准（比如上面就是52个）中每个基准的每个权重系数。一般也会同时给出头的3D倾角数值，用于在驱动表情的同时还会模拟头部的转动。有时间了gemfield会在gemfield专栏中介绍一个这样的项目：

Gemfield
​zhuanlan.zhihu.com/gemfield

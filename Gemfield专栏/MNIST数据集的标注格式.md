# 背景
Mnist数据集的识别问题可以算得上是——机器学习在视觉领域的hello world了，至少Gemfield这样认为。它的训练集有6万项数据，而测试集有1万项数据（其中前5000个来自最初NIST项目的训练集.，后5000个来自最初NIST项目的测试集。前5000个比后5000个要规整，这是因为前5000个数据来自于美国人口普查局的员工，而后5000个来自于大学生。还是大学生轻浮啊......）。在官方网站上，这些数据以4个gz压缩包的方式提供下载：

- train-images-idx3-ubyte.gz:  training set images (9912422 bytes)
- train-labels-idx1-ubyte.gz:  training set labels (28881 bytes)
- t10k-images-idx3-ubyte.gz:   test set images (1648877 bytes)
- t10k-labels-idx1-ubyte.gz:   test set labels (4542 bytes)

这些数据的格式还是比较简单的，上面文件中的所有的数字都是按照MSB（大端）的方式存储的。Gemfield要提醒你的是，intel处理器是little-endian的。所以在intel处理器上或者其它的little-endian处理器上，用户必须要进行相应的翻转处理。不过Gemfield在本文中展示的代码使用了python的struct模块，其fmt格式符中的大于号很好的应付了这种情况。

# IDX数据格式
这四个文件采用了IDX的文件格式，一种平铺直叙的方式：
```
magic number 
size in dimension 0 
size in dimension 1 
size in dimension 2 
..... 
size in dimension N 
data
```
其中magic number为4字节，前2字节永远是0，第3字节代表数据的格式：
- 0x08: unsigned byte
- 0x09: signed byte
- 0x0B: short (2 bytes)
- 0x0C: int (4 bytes)
- 0x0D: float (4 bytes)
- 0x0E: double (8 bytes)

第4字节的含义表示维度的数量（dimensions）: 1 表示一维（比如vectors）, 2 表示二维（ 比如matrices），3表示三维（比如numpy表示的图像，高，宽，通道数）。

# 训练集和测试集的标签文件的格式(train-labels-idx1-ubyte和t10k-labels-idx1-ubyte)
格式还是很简单的：
- 1，前4个字节（第0～3个字节）是魔数2049（int型，0x00000801, 大端）;
- 2，再往后4个字节（第4～7个字节）是标签的个数：60000或10000；
- 3，再往后每1个字节是一个无符号型的数，值为0～9。

用python代码来表示就是(我们使用了struct模块，其中fmt中的大于号表示大端，big endian)：
```python
import struct
for file in ['gemfield_data/t10k-labels-idx1-ubyte','gemfield_data/train-labels-idx1-ubyte']:
    data = open(file, 'rb').read()
    #fmt of struct unpack, > means big endian, i means integer, well, ii mean 2 integers
    fmt = '>ii'
    offset = 0
    magic_number, label_number = struct.unpack_from(fmt, data, offset)
    print('magic number is {} and label number is {}'.format(magic_number, label_number))
    #slide over the 2 numbers above
    offset += struct.calcsize(fmt)
    #B means unsigned char
    fmt = '>B'
    labels = np.empty(label_number)
    for i in range(label_number):
        labels[i] = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)

    print(labels)
```
输出：
```
magic number is 2049 and label number is 10000
[ 7.  2.  1. ...,  4.  5.  6.]
magic number is 2049 and label number is 60000
[ 5.  0.  4. ...,  5.  6.  8.]
```

# 训练集和测试集的图像文件的格式(train-images-idx3-ubyte和t10k-images-idx3-ubyte)
格式比label复杂些，但也比较简单：
- 1，前4个字节（第0～3个字节）是魔数2051（int型，0x00000803, 大端）;
- 2，再往后4个字节（第4～7个字节）是图像的个数：60000或10000（第1个维度）；
- 3，再往后4个字节（第8～11个字节）是图像在高度上由多少个像素组成（第2个维度，高28个像素）；
- 4，再往后4个字节（第12～15个字节）是图像在宽度上由多少个像素组成（第3个维度，宽28个像素）；
- 3，再往后是一个三维数组，表示10000个或60000个分辨率28x28的灰度图像，一句话来说就是10000x28x28个像素，每个像素的值为0～255（0是背景，为白色；255是黑色）。

用python代码来表示就是(我们使用了struct模块，其中fmt中的>表示big endian，大端)：
```python
import struct
import numpy as np
for file in ['gemfield_data/t10k-images-idx3-ubyte','gemfield_data/train-images-idx3-ubyte']:
    data = open(file, 'rb').read()
    #fmt of struct unpack, > means big endian, i means integer, well, iiii mean 4 integers
    fmt = '>iiii'
    offset = 0
    magic_number, img_number, height, width = struct.unpack_from(fmt, data, offset)
    print('magic number is {}, image number is {}, height is {} and width is {}'.format(magic_number, img_number, height, width))
    #slide over the 2 numbers above
    offset += struct.calcsize(fmt)
    #28x28
    image_size = height * width
    #B means unsigned char
    fmt = '>{}B'.format(image_size)
    
    images = np.empty((img_number, height, width))
    for i in range(img_number):
        images[i] = np.array(struct.unpack_from(fmt, data, offset)).reshape((height, width))
        offset += struct.calcsize(fmt)

    print(images)
```
输出：
```
magic number is 2051, image number is 10000, height is 28 and width is 28
[[[ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  ..., 
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]]

 [[ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  ..., 
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]]

 [[ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  ..., 
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]
  [ 0.  0.  0. ...,  0.  0.  0.]]

 ..., 
```

使用matplotlib.pyplot来显示其中一个数字的图像：
```python
import matplotlib.pyplot as plt
plt.imshow(images[0])
plt.show()
```
# 我们做了什么？
Gemfield把idx格式的Mnist数据转换为了numpy的ndarray！

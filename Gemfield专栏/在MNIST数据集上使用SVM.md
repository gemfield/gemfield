# 1, 下载数据
到Mnist官方网站上（MNIST handwritten digit database, Yann LeCun, Corinna Cortes and Chris Burges）下载训练集和测试集，一共4个gz压缩包；解压如下所示：
```bash
gemfield@ThinkPad-X1C:~/learning/gemfield_data$ ls -l
总用量 53672
-rw-rw-r-- 1 gemfield gemfield  7840016 12月 30 14:17 t10k-images-idx3-ubyte
-rw-rw-r-- 1 gemfield gemfield    10008 12月 30 14:16 t10k-labels-idx1-ubyte
-rw-rw-r-- 1 gemfield gemfield 47040016 12月 30 14:43 train-images-idx3-ubyte
-rw-rw-r-- 1 gemfield gemfield    60008 12月 30 14:42 train-labels-idx1-ubyte
```

# 2, 将Mnist的idx格式转化为python numpy的ndarray格式
参考：MNIST数据集的Python解析

Gemfield将其封装为了一个函数，代码如下所示：
```python3
import numpy as np
import timeit
from sklearn import svm
import struct

TRAIN_ITEMS = 60000
TEST_ITEMS = 10000

def loadMnistData():
    mnist_data = []
    for img_file,label_file,items in zip(['gemfield_data/train-images-idx3-ubyte','gemfield_data/t10k-images-idx3-ubyte'],
                                   ['gemfield_data/train-labels-idx1-ubyte','gemfield_data/t10k-labels-idx1-ubyte'],
                                   [TRAIN_ITEMS, TEST_ITEMS]):
        data_img = open(img_file, 'rb').read()
        data_label = open(label_file, 'rb').read()
        #fmt of struct unpack, > means big endian, i means integer, well, iiii mean 4 integers
        fmt = '>iiii'
        offset = 0
        magic_number, img_number, height, width = struct.unpack_from(fmt, data_img, offset)
        print('magic number is {}, image number is {}, height is {} and width is {}'.format(magic_number, img_number, height, width))
        #slide over the 2 numbers above
        offset += struct.calcsize(fmt)
        #28x28
        image_size = height * width
        #B means unsigned char
        fmt = '>{}B'.format(image_size)
        #because gemfield has insufficient memory resource
        if items > img_number:
            items = img_number
        images = np.empty((items, image_size))
        for i in range(items):
            images[i] = np.array(struct.unpack_from(fmt, data_img, offset))
            #0~255 to 0~1
            images[i] = images[i]/256
            offset += struct.calcsize(fmt)

        #fmt of struct unpack, > means big endian, i means integer, well, ii mean 2 integers
        fmt = '>ii'
        offset = 0
        magic_number, label_number = struct.unpack_from(fmt, data_label, offset)
        print('magic number is {} and label number is {}'.format(magic_number, label_number))
        #slide over the 2 numbers above
        offset += struct.calcsize(fmt)
        #B means unsigned char
        fmt = '>B'
        #because gemfield has insufficient memory resource
        if items > label_number:
            items = label_number
        labels = np.empty(items)
        for i in range(items):
            labels[i] = struct.unpack_from(fmt, data_label, offset)[0]
            offset += struct.calcsize(fmt)
        
        mnist_data.append((images, labels.astype(int)))
    return mnist_data
```
# 3，使用sklearn模块中的svm
代码如下所示：
```python3
def forwardWithSVM():
    start_time = timeit.default_timer()
    training_data, test_data = loadMnistData()
    # train
    clf = svm.SVC()
    clf.fit(training_data[0], training_data[1])
    train_time = timeit.default_timer()
    print('gemfield train cost {}'.format(str(train_time - start_time) ) )
    # test
    print('Begin the test...')
    predictions = [int(a) for a in clf.predict(test_data[0])]
    num_correct = sum(int(a == y) for a, y in zip(predictions, test_data[1]))

    print("%s of %s values correct." % (num_correct, len(test_data[1])))
    test_time = timeit.default_timer()
    print('gemfield test cost {}'.format(str(test_time - train_time) ) )
```
# 4，运行及测试
整个代码文件参考：https://github.com/CivilNet/Gemfield/blob/master/src/python/svm/svm.py

将TRAIN_ITEMS的值设置为10的时候，测试效果如下所示(可以看到正确性和瞎猜差不多)：
```bash
gemfield@ThinkPad-X1C:~/learning$ python3 svm.py 
magic number is 2051, image number is 60000, height is 28 and width is 28
magic number is 2049 and label number is 60000
magic number is 2051, image number is 10000, height is 28 and width is 28
magic number is 2049 and label number is 10000
gemfield start the training...
gemfield train cost 0.5457151120062917
Begin the test...
1135 of 10000 values correct.
gemfield test cost 0.1183781250147149
```
将TRAIN_ITEMS的值设置为100的时候，测试效果如下所示（哇，正确性翻了一番啊）：
```bash
gemfield@ThinkPad-X1C:~/learning$ python3 svm.py 
magic number is 2051, image number is 60000, height is 28 and width is 28
magic number is 2049 and label number is 60000
magic number is 2051, image number is 10000, height is 28 and width is 28
magic number is 2049 and label number is 10000
gemfield start the training...
gemfield train cost 0.5702047150116414
Begin the test...
2563 of 10000 values correct.
gemfield test cost 1.0582328418968245
```
将TRAIN_ITEMS的值设置为1000的时候，测试效果如下所示（及格了唉）：
```bash
gemfield@ThinkPad-X1C:~/learning$ python3 svm.py 
magic number is 2051, image number is 60000, height is 28 and width is 28
magic number is 2049 and label number is 60000
magic number is 2051, image number is 10000, height is 28 and width is 28
magic number is 2049 and label number is 10000
gemfield start the training...
gemfield train cost 1.7026840379694477
Begin the test...
8267 of 10000 values correct.
gemfield test cost 9.486829451052472
```
将TRAIN_ITEMS的值设置为10000的时候，测试效果如下所示（设为60000的话，在gemfield的PC上需要运行太多的时间）：
```bash
gemfield@ThinkPad-X1C:~/learning$ python3 svm.py 
magic number is 2051, image number is 60000, height is 28 and width is 28
magic number is 2049 and label number is 60000
magic number is 2051, image number is 10000, height is 28 and width is 28
magic number is 2049 and label number is 10000
gemfield start the training...
gemfield train cost 46.46685998595785
Begin the test...
9214 of 10000 values correct.
gemfield test cost 57.5887356440071
```
# 5，SVM的核心思想是什么？和神经网络的本质区别是什么？
稍等啊。

最起码随着训练数据的增加，SVM做forward消耗的时间也明显增加。

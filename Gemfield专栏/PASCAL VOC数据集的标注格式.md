# 背景
PASCAL的全称是Pattern Analysis, Statistical Modelling and Computational Learning。

VOC的全称是Visual Object Classes。

第一届PASCAL VOC举办于2005年，然后每年一届，于2012年终止。

本文以PASCAL VOC 2012为基础。

# 数据标注方式
![v2-44e6a443ed802c48600ad641b17c4a2b_720w](https://github.com/user-attachments/assets/e3a69e5c-9508-4966-8ce2-9bb252f45a00)

# 数据集简介
PASCAL VOC竞赛目标主要是目标识别，其提供的数据集里包含了20类的物体。

- person
- bird, cat, cow, dog, horse, sheep
- aeroplane, bicycle, boat, bus, car, motorbike, train
- bottle, chair, dining table, potted plant, sofa, tv/monitor

PASCAL VOC的主要2个任务是(按照其官方网站所述，实际上是5个)：

- 分类： 对于每一个分类，判断该分类是否在测试照片上存在（共20类）；
- 检测：检测目标对象在待测试图片中的位置并给出矩形框坐标（bounding box）；
- Segmentation: 对于待测照片中的任何一个像素，判断哪一个分类包含该像素（如果20个分类没有一个包含该像素，那么该像素属于背景）；
    （在给定矩形框位置的情况下）人体动作识别；
- Large Scale Recognition（由ImageNet主办）。

另外，PASCAL VOC利用其训练集的一个子集对外提供2个尝鲜性质的任务：

- （无给定矩形框位置的情况下）人体动作识别；
- Person Layout: 对于待测照片中的每一个人，预测出这个人的bounding box，以及这个人的头、手、脚的bounding box。

在本文中，Gemfield只讨论目标检测。关于语义分割的访问，请访问gemfield专栏文章：语义分割的数据集

# XML标注格式
对于目标检测来说，每一张图片对应一个xml格式的标注文件。所以你会猜到，就像gemfield准备的训练集有8万张照片一样，在存放xml文件的目录里，这里也将会有8万个xml文件。下面是其中一个xml文件的示例：
```
<?xml version="1.0" encoding="utf-8"?>
<annotation>
    <folder>VOC2007</folder>
    <filename>test100.mp4_3380.jpeg</filename>
    <size>
        <width>1280</width>
        <height>720</height>
        <depth>3</depth>
    </size>
    <object>
        <name>gemfield</name>
        <bndbox>
            <xmin>549</xmin>
            <xmax>715</xmax>
            <ymin>257</ymin>
            <ymax>289</ymax>
        </bndbox>
        <truncated>0</truncated>
        <difficult>0</difficult>
    </object>
    <object>
        <name>civilnet</name>
        <bndbox>
            <xmin>842</xmin>
            <xmax>1009</xmax>
            <ymin>138</ymin>
            <ymax>171</ymax>
        </bndbox>
        <truncated>0</truncated>
        <difficult>0</difficult>
    </object>
    <segmented>0</segmented>
</annotation>
```
在这个测试图片上，我们标注了2个object，一个是gemfield，另一个是civilnet。

在这个xml例子中：

- bndbox是一个轴对齐的矩形，它框住的是目标在照片中的可见部分；
- truncated表明这个目标因为各种原因没有被框完整（被截断了），比如说一辆车有一部分在画面外；
- occluded是说一个目标的重要部分被遮挡了（不管是被背景的什么东西，还是被另一个待检测目标遮挡）；
- difficult表明这个待检测目标很难识别，有可能是虽然视觉上很清楚，但是没有上下文的话还是很难确认它属于哪个分类；标为difficult的目标在测试成绩的评估中一般会被忽略。

注意：在一个<object />中，<name /> 标签要放在前面，否则的话，目标检测的一个重要工程实现SSD会出现解析数据集错误（另一个重要工程实现py-faster-rcnn则不会）。

# 如何评判目标检测的成绩？
先来介绍几个概念

## 1，IoU
这是关于一个具体预测的Bounding box的准确性评估的数据。对于目标检测任务来说，一个具体的目标预测包括一个bounding box的坐标和它的置信度。通过测量预测的bndbox(bounding box)和ground truth的bndbox之间的重合度，我们来得出此次预测是true positive还是false positive。
![v2-44871b3c87b1fcff35272b7f3d2e3476_720w](https://github.com/user-attachments/assets/6f273865-da00-4753-8093-22b618eb4358)

一般来说，重合区域的面积（上面公式的分子）和2个bndbox的面积之和的比例（上面公式的分母）如果大于50%，那么认为这是一个成功的预测（true positive），否则认为这是一个失败的预测(false positive)。公式等号的左边就是IoU。50%这个数值的选取是考虑了一些因素的，比方说人有胳膊有腿，有蜷缩有伸展的状态，因此这个数也不能太严格。

如果对于一个目标算法检测出多个目标，比如一个目标上算法给出了5个检测框，那么就算4个检测错误。

## 2，mAP
对于一个给定的任务和分类：
- precision/recall曲线是根据算法的输出计算得到的。
- Recall（召回率）说的是所有正样本中被算法预测出来的样本所占的比率（Recall is defined as the proportion of all positive examples ranked above a given rank.） 
- Precision（准确率）说的是预测出来的样本中是正确的比例是多少（Precision is the proportion of all examples above that rank which are from the positive class. ）

AP的值就某种程度上反映了上述PR曲线(precision/recall)的形状，我们把recall的值从0到1 （0%到100%）划分为11份：0、0.1、0.2、0.3、0.4、0.5、0.6、0.7、0.8、0.9、1.0，在每个recall尺度上我们计算下准确率，然后再计算总和并平均，就是AP值。
![v2-d47b666c253ad25230810fa8141c37f7_720w](https://github.com/user-attachments/assets/8d4195dd-2b1f-40f1-942a-9232cbb1304e)


因此，一个表现良好的算法应该是在各个recall层面上都有足够好的Precision。

对于给定的任务的所有的分类：

计算每个分类的AP，求和再平均，得到的就是mAP。

# PASCAL VOC数据集实例
当在PASCAL VOC官方网站上下载了development kit和challenge image database并将它们解压到同一目录下，会产生下面这样的目录结构：
```
gemfield@ai:/data/VOCdevkit2007/VOC2007$ ls -l
total 584
drwxrwxr-x 2 gemfield gemfield 270336 2月   7 19:22 Annotations
drwxrwxr-x 5 gemfield gemfield   4096 11月  7  2007 ImageSets
drwxrwxr-x 2 gemfield gemfield 274432 11月  7  2007 JPEGImages
drwxrwxr-x 2 gemfield gemfield  20480 11月  7  2007 SegmentationClass
drwxrwxr-x 2 gemfield gemfield  20480 11月  7  2007 SegmentationObject
```
其中：
- Annotations目录下放的是标注文件，xml格式，这是用于目标检测任务的一个总的标注集合，里面存放有大而全的xml文件；具体是在ImageSets/Main目录中去划分训练机、验证集、测试集；
- JPEGImages目录下是所有的jpg图片；
- ImageSets目录下有3个子目录：Layout, Main, Segmentation。
```
gemfield@ai:/VOCdevkit/VOC2007$ ls -l ImageSets/
total 12
drwxrwxr-x 2 gemfield gemfield 4096 11月  7  2007 Layout
drwxrwxr-x 2 gemfield gemfield 4096 2月   7 19:57 Main
drwxrwxr-x 2 gemfield gemfield 4096 2月   7 19:51 Segmentation
```
注意啊，这里面全是train.txt、val.txt、trainval.txt、test.txt。这些文件里的每一行都是个文件名，其有2层含义，一方面其对应的图片来自JPEGImages里的同名文件，另一方面其对应的标注结果来自Annotations里的同名文件。 

- SegmentationClass目录下放的也是图片，segmentations by object；
- SegmentationObject目录下放的也是图片，segmentations by class。

# 建立自己的数据集
本节Gemfield仅以目标检测为例，建立一个名为VOC2018的数据集。如下所示：
```
gemfield@ai:/bigdata$ mkdir VOC2018
gemfield@ai:/bigdata$ cd VOC2018/
gemfield@ai:/bigdata/VOC2018$ ls
gemfield@ai:/bigdata/VOC2018$ mkdir Annotations
gemfield@ai:/bigdata/VOC2018$ mkdir JPEGImages
gemfield@ai:/bigdata/VOC2018$ mkdir -p ImageSets/Main
```
可以看到，必备的目录只有Annotations、JPEGImages以及ImageSets/Main。

1，把所有的照片放入到JPEGImages目录：
```
gemfield@ai:/bigdata/VOC2018/JPEGImages$ ls | head
self1.mp4_0.jpg
self1.mp4_10000.jpg
self1.mp4_1000.jpg
self1.mp4_10010.jpg
self1.mp4_10020.jpg
self1.mp4_10030.jpg
self1.mp4_10040.jpg
self1.mp4_10050.jpg
......
```
2，把所有的xml标注文件放入到Annotations目录：
```
gemfield@ai:/bigdata/VOC2018/Annotations$ ls |head
self1.mp4_0.xml
self1.mp4_10000.xml
self1.mp4_10010.xml
self1.mp4_10020.xml
self1.mp4_10030.xml
self1.mp4_10040.xml
self1.mp4_10050.xml
......
```
3，把划分好的训练集测试集放入到 ImageSets/Main目录下：
```
gemfield@ai:/bigdata/VOC2018/ImageSets/Main$ ls -l
total 4012
-rw-r--r-- 1 root root 1278209 2月  11 16:53 imageset.txt
-rw-r--r-- 1 root root  127874 2月  11 16:53 test.txt
-rw-r--r-- 1 root root 1278209 2月  11 16:53 train.txt
-rw-r--r-- 1 root root 1278209 2月  11 16:53 trainval.txt
-rw-r--r-- 1 root root  127868 2月  11 16:53 val.txt
```
以val.txt文件为例，格式如下（这几个文件格式一样）：
```
gemfield@ai:/bigdata/VOC2018/ImageSets/Main$ cat val.txt |head
wzry203.mp4_3990
wzry19.mp4_16340
wzry232.mp4_9860
wzry228.mp4_4610
wzry240.mp4_120
wzry49.mp4_1920
wzry222.mp4_8170
wzry219.mp4_10720
wzry250.mp4_4410
wzry249.mp4_7700
```


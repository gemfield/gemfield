# 背景
原本Gemfield是不赞成用固定的上下班时间进行考勤的，但是近来，不这样做会导致一些严重的困难。这好比生产力发展的终极目标是按需分配，但目前能做到的只能是按劳分配一样。既然这样，设计一个符合团队文化的考勤系统就至关重要了。初步设想是利用深度学习在cv领域的成果，主要有人脸识别、REID等，并且整个系统要做到实时检测。

设计如下：

1，正对公司门口架设一个摄像头；

2，使用人脸识别技术识别一个具体的人。与此同时通过reid方面的技术提取这个人的其它一些特征，这样reid方面的特征就会和一个具体的人关联上，方便在没有正脸的情况下继续识别；

3，数据使用mysql进行存储。对于一个人来说，每天首次识别到的时间作为上班时间，最后一次识别到的时间为下班时间；

4，使用一个轻量级的web系统，可以进行报表的生成；还可以对一些错误的识别情况进行人工干预修正；

5，系统使用微信接口。如果检测到迟到，则在工作微信群里推送消息，提示迟到的人发红包，迟到几分钟就发几块的红包：


# 硬件
硬件包含摄像头和GPU卡。

Gemfield选取的是xx牌摄像头（在此不披露具体的品牌，摄像头厂商如果想署名做广告的话，欢迎联系我），确保摄像头支持一些标准的公开的协议。否则无法有效的将每一帧图像输入给后面的cv程序。

GPU选用的是xx（不披露具体的型号，不能免费打广告，哼），但是要确保达到实时检测的性能。

操作系统使用Ubuntu 16.04/18.04（开源）。

摄像头画面截帧
Gemfield使用的是SYSZUXav python软件包来进行摄像头画面的截帧。使用python进行编程，可以很高效方便的接入后续的AI能力，毕竟在AI的世界里python可是一等公民啊。使用SYSZUXav可以将摄像头画面转化为numpy数组，方便后续的cv程序继续处理。

安装和使用SYSZUXav，请访问：

CivilNet/SYSZUXav
​github.com/CivilNet/SYSZUXav



# 人脸检测
要从摄像头画面中筛选出人脸来进行后续的人脸识别和其它特征提取，我们首先要检测并且crop出画面中出现的所有人脸。Gemfield使用的是pymtcnn软件包，这个软件包是mtcnn的python实现。

安装和使用pymtcnn，请访问：

CivilNet/pymtcnn
​github.com/CivilNet/pymtcnn

#人脸识别
这一步很关键，这是首次可以实现画面和一个具体的人名关联的地方。Gemfield使用的是face_recognition：

ageitgey/face_recognition
​github.com/ageitgey/face_recognition

# WEB系统
我们使用的Django。Django帮我们做了http的封装，以及ORM对数据库的操作。比较简单，不再赘述。另外还有一些前端的技术。

# 微信推送
微信消息发推送到群里并不是茫无目的的发送，而是我们设计了一套规则。比如每个人每天首次出现的时候才会推送文字和画面；每个小时第一次出现的时候会发送文字；非工作时间（比如半夜和假日）只要检测到人都会发送画面和文字（呃，进入安防领域了...）。

使用微信接口推送相关的信息到微信群里有3层意义：

1，方便及时看到今天人们的出席情况；

2，方便早期对这套考勤系统的测试，如果有无识别或者漏识别，可人工通过web干预修正；

3，迟到情况下的发红包提醒。

微信发送使用的是itchat python包(shaoyang亦有贡献）：

```python
import itchat
import time
itchat.auto_login(enableCmdQR=2,hotReload=True)
sendgroup = "CivilNet"
def send_onegroup(msg,gname,imgpath=None):
    rooms = itchat.get_chatrooms(update=True)
    for g in rooms:
        if g['NickName'] != gname or gname != sendgroup:
            continue
        username = g['UserName']
        itchat.send(msg,toUserName=username)
        if imgpath:
            itchat.send_image(imgpath,toUserName=username)
            print("msg has sent to the group "+gname)
            return
```

但是itchat以及类似的微信封装程序目前都遇到了一个问题，就是新注册的微信号是不能登陆的，也有一些注册已久的但是被腾讯设置为不可信的微信帐号也无法登陆。可以使用https://wx.qq.com/ 进行扫码登陆测试。可以确信一点，很明显微信团队对"web禁止登陆微信"这一功能在进行灰度测试。目前还不确定以后完全封掉后将如何使用这一功能......

# 总结
这个AI考勤系统使用了GPU（电脑/服务器)、摄像头这两个硬件，使用了Ubuntu、SYSZUXav、pymtcnn、face_recognition、django、itchat这些开源软件，其中itchat的能力在以后面临极大的不确定性。这套系统目前已经在实际运行中，下一步的目标就是不断提升这套系统的可靠性，最终完全去掉人工干预。

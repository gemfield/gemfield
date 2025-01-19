# 背景
最近Gemfield团队在使用其它部门的某三方库进行GB28181协议的适配，然后在Docker化的过程中遇到了问题：SIP信令在Docker网络上无法正常工作。具体来说，当服务部署在宿主机（192.168.2.102）上的时候，UAS给UAC发送invite指令是没有问题的；但是服务一旦部署在Docker容器里，网络使用Docker自身的bridge进行SIP协议的收发时，UAS发送给UAC的invite指令的目的地址就是错误的（通过wireshark抓包分析），本来应该是UAC（国标IPC，地址192.168.2.103）的IP，但不知道什么原因，这个IP变成了宿主机的IP（192.168.2.102）：
![Image](https://github.com/user-attachments/assets/a961008b-8deb-4e61-adec-8e9f27d8a3ae)

为了排除其它网络问题，Gemfield在同一个容器里使用python脚本进行同一invite指令的模拟，发现指令的目的IP变成国标IPC的了（192.168.2.103），信令也能正常工作：
![Image](https://github.com/user-attachments/assets/4e9c8468-6c25-43b5-ab39-cf3915e11943)

模拟该信令的脚本如下所示：
```python
import socket
def main():
    # filename = sys.argv[1]
    port = 5060
    ip = '192.168.2.103'
    # ts, pkt = dpkt.pcap.Reader(open(filename, 'r'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gemfield_payload = bytearray.fromhex('30333a3...<copy the payload from wireshark as hex>...0300d0a0d0a')
    sock.sendto(gemfield_payload, (ip, port))

    buf, addr = sock.recvfrom(2048, 0)
    print(addr)

if __name__ == '__main__':
    main()
```
于是排除了网络的原因。但因为种种原因，主要因为其它部门太忙了，无法进一步debug下去，问题迟迟得不到解决。这个时候，Gemfield设置了一个独立的task，在小组内部来并行推动这个事情的解决：使用开源的SIP协议栈库来进行这个问题的模拟和复现。这个开源的SIP协议栈，Gemfield选择了ReSIProcate。

# ReSIProcate库的简介
ReSIProcate来源于功能完善的开源SIP协议栈VOCAL,基于RFC3261和RFC2327标准,使用C++语言编写,性能稳定。

- 项目地址为：https://github.com/resiprocate/resiprocate；
- ReSIProcate feature列表（非常值得一看）：https://www.resiprocate.org/ReSIProcate_Current_Features；
- Ubuntu上的ReSIProcate package：https://launchpad.net/ubuntu/+source/resiprocat；
ReSIProcate库主要分为reSIProcate stack（核心协议栈）、DUM（The Dialog Usage Manager ）、recon（Conversation Manager ）、repro（SIP Proxy）这四部分。

## reSIProcate stack

项目的resip/stack目录为核心的SIP栈的实现，基于该项目进行开发的普通程序员不应该涉及这部分底层的东西，相反，应该使用DUM、repro、recon这些层。核心协议栈的UTcase和参考例子在ReSIProcate项目的rutil/test 和 resip/stack/test 目录下，特别注意testStack.cxx这个文件。

## The Dialog Usage Manager (DUM)

这部分代码在resip/dum目录下，UT case和参考例子在resip/dum/test目录下。DUM在核心的SIP栈之上，用来SIP Dialog的创建和处理。这可以用来设置Registrations、Calls/InviteSessions、Subscriptions、Publications等。对于Invite Sessions来说，DUM会将收到的SDP bodies交给上层的应用程序处理。 大多数SIP应用程序都基于DUM这一层进行开发，因为DUM提供了极高的灵活性和可扩展性。

## Conversation Manager (recon)

代码在resip/recon目录下，UT case和参考例子在resip/recon/test目录下，可以特别留神testUA.cxx文件。recon在核心SIP栈和DUM层之上，用来和media以及相关的sip信令打交道。recon使用sipXtapi media栈提供audio RTP的处理。

## SIP Proxy（repro）

repro是一个独立的SIP服务程序，该部分代码在项目的repro目录下，repro在核心SIP栈之上，使用DUM来进行SIP注册的处理，使用核心SIP栈来进行SIP信令的proxy。

ReSIProcate库的消息处理架构如下所示：
![Image](https://github.com/user-attachments/assets/39f2153a-7887-45af-96de-d8d74d9a4a07)

ReSIProcate库中的类层次如下图所示：
![Image](https://github.com/user-attachments/assets/63ed5cf7-1709-4e4d-8a96-b70645580ff9)

# 编译ReSIProcate库
使用如下步骤进行基本的编译：
```bash
root@uas:/home/gemfield/github/resiprocate-master# autoreconf -fi
root@uas:/home/gemfield/github/resiprocate-master# ./configure
root@uas:/home/gemfield/github/resiprocate-master# make -j4
root@uas:/home/gemfield/github/resiprocate-master# make check
root@uas:/home/gemfield/github/resiprocate-master# make install
```
上述configure的时候可以指定安装的目录，比如：./configure --prefix=/home/gemfield/github/tmp_install/ 将会导致最后的安装如下所示：
```bash
root@5a941ec09bd0:/home/gemfield/github/Gemfield/resiprocate# make install
Making install in rutil
......
Libraries have been installed in:
   /home/gemfield/github/tmp_install/lib
```
生成的install目录如下所示：
```bash
root@uas:/home/gemfield/github/tmp_install# ls -l
total 12
drwxr-xr-x 4 root root 4096 Nov 25 08:04 include
drwxr-xr-x 2 root root 4096 Nov 25 08:04 lib
drwxr-xr-x 3 root root 4096 Nov 25 08:04 share
```
有头文件、库文件和文档。其中库文件如下所示：
```bash
root@uas:/home/gemfield/github/tmp_install# ls -l lib/
total 140876
-rwxr-xr-x 1 root root 13431224 Nov 25 08:04 libdum-1.12.so
-rw-r--r-- 1 root root 36667544 Nov 25 08:04 libdum.a
-rwxr-xr-x 1 root root     1183 Nov 25 08:04 libdum.la
lrwxrwxrwx 1 root root       14 Nov 25 08:04 libdum.so -> libdum-1.12.so
-rwxr-xr-x 1 root root 20110880 Nov 25 08:04 libresip-1.12.so
-rw-r--r-- 1 root root 54648650 Nov 25 08:04 libresip.a
-rwxr-xr-x 1 root root     1147 Nov 25 08:04 libresip.la
lrwxrwxrwx 1 root root       16 Nov 25 08:04 libresip.so -> libresip-1.12.so
-rwxr-xr-x 1 root root   181088 Nov 25 08:04 libresipares-1.12.so
-rw-r--r-- 1 root root   353168 Nov 25 08:04 libresipares.a
-rwxr-xr-x 1 root root     1061 Nov 25 08:04 libresipares.la
lrwxrwxrwx 1 root root       20 Nov 25 08:04 libresipares.so -> libresipares-1.12.so
-rwxr-xr-x 1 root root  5323416 Nov 25 08:04 librutil-1.12.so
-rw-r--r-- 1 root root 13493638 Nov 25 08:04 librutil.a
-rwxr-xr-x 1 root root     1097 Nov 25 08:04 librutil.la
lrwxrwxrwx 1 root root       16 Nov 25 08:04 librutil.so -> librutil-1.12.so
```
这些库和文件都来自：
```bash
#动态库
./resip/stack/.libs/libresip.so
./resip/stack/.libs/libresip-1.12.so
./resip/dum/.libs/libdum-1.12.so
./resip/dum/.libs/libdum.so
./rutil/dns/ares/.libs/libresipares-1.12.so
./rutil/dns/ares/.libs/libresipares.so
./rutil/.libs/librutil.so
./rutil/.libs/librutil-1.12.so
#静态库
./contrib/popt/win32/lib/libpopt.dll.a
./contrib/popt/win32/lib/libpopt.a
./resip/stack/.libs/libresip.a
./resip/dum/.libs/libdum.a
./rutil/dns/ares/.libs/libresipares.a
./rutil/.libs/librutil.a
#可执行文件
./resip/certs/makeCA
./resip/certs/makeCert
......
```
如果要使用这些库，则需要在编译的时候设置LD_RUN_PATH，而在运行的时候设置LD_LIBRARY_PATH；如果需要一个更多功能的编译，则在configure的时候加上更多的参数：
```bash
root@uas:/home/gemfield/github/resiprocate-master# ./configure --enable-ipv6 --with-ssl --with-geoip --with-tfm --with-repro --with-mysql --with-popt CXXFLAGS="-I`pwd`/contrib/cajun/include"
```
或者，仿照github项目中的构建脚本，先安装如下依赖：
```bash
sudo add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu/ bionic main universe"
sudo apt-get update -qq
sudo apt-get install -qq gperf libasio-dev libboost-dev libc-ares-dev libdb++-dev \
    libpopt-dev libssl-dev perl libmysqlclient-dev libpq-dev libcppunit-dev autotools-dev \
    libpcre3-dev libxerces-c-dev curl libcajun-dev python-cxx-dev libsrtp-dev libgloox-dev libtelepathy-qt5-dev
sudo apt-get install -qq debian-archive-keyring
wget -q -O - https://ftp-master.debian.org/keys/release-10.asc | sudo apt-key add -
wget -q -O - https://ftp-master.debian.org/keys/archive-key-10.asc | sudo apt-key add -
sudo add-apt-repository -y "deb http://http.us.debian.org/debian/ buster main"
sudo add-apt-repository -y "deb http://http.us.debian.org/debian/ buster-backports main"
curl -O http://apt.debify.org/debify/pool/main/d/debify-archive-keyring/debify-archive-keyring_2019.01_all.deb
sudo dpkg -i debify-archive-keyring_2019.01_all.deb
sudo add-apt-repository -y "deb http://apt.debify.org/debify debify-buster-backports main"
sudo apt-get update -qq
sudo apt-get install -qq --force-yes -t buster libradcli-dev libsoci-dev libqpid-proton-cpp12-dev
sudo apt-get install -qq --force-yes -t debify-buster-backports libsipxtapi-dev
```
再进行configure：
```bash
#build/travis/bootstrap
autoreconf --install
rm resip/stack/gen/*
ls -l /usr/include/asio.hpp

#build/travis/configure
./configure \
  --enable-assert-syslog \
  --with-popt \
  --with-ssl \
  --with-mysql \
  --with-postgresql \
  --with-apps \
  --with-telepathy \
  --enable-dtls \
  --enable-ipv6 \
  --with-radcli \
  --with-qpid-proton \
  --with-repro \
  --enable-repro-plugins \
  DEPS_PYTHON_CFLAGS="`/usr/bin/python2.7-config --cflags`" \
  DEPS_PYTHON_LIBS="`/usr/bin/python2.7-config --ldflags`" \
  PYCXX_SRCDIR=/usr/share/python2.7/CXX/Python2 \
  --with-python \
  --with-rend \
  --with-recon \
  CPPFLAGS="-I/usr/include/postgresql -I/usr/include/sipxtapi -D__pingtel_on_posix__ -D_linux_ -D_REENTRANT -D_FILE_OFFS -DDEFAULT_BRIDGE_MAX_IN_OUTPUTS=20 -DRESIP_DIGEST_LOGGING -I/usr/include/soci -I/usr/include/mysql" \
  CXXFLAGS="-Wformat -Werror=format-security -fpermissive" \
  --with-c-ares
```

# 基于DUM库开始进行应用程序的开发
大多数应用都是基于DUM库进行业务的开发。主要有以下几个阶段：

# 程序的初始化

程序主程序的初始化阶段要进行如下的设置：
```list
Create a Security Object (if required)
Create SipStack
Create DialogUsageManager
Add transports
Create/Set MasterProfile
Supported Methods, Mime Types, etc.
Validation Settings, Advertised Capabilities
Set Outbound Decorators
Set Handlers (ie. InviteSessionHandler)
Set Managers (ie. ClientAuth, KeepAlive)
Set AppDialogSet Factory
Start Stack Processing / Thread
Start DUM Processing / Thread
```
## 程序的关闭

使用DUM的Shutdown Handler：

DUM Application Shutdown
​www.resiprocate.org/DUM_Application_Shutdown

## DUM的handler
```list
Invite Session Handler
Client/Server Registration Handlers
Client/Server Subscription Handlers
Default Server Refer Handler (?)
Client/Server Publication Handlers
Pager Message Handler
Redirect Handler
DialogSet Handler
Out Of Dialog Handler
Shutdown Handler
```
## DUM的注册和鉴权

如果是UAS，则继承并实现ServerAuthManager中的相关API；如果是UAC，则继承并实现ClientAuthManager中的相关API。

# GB28181 UAS的开发
## 设备注册

很简单，继承并实现resip::ServerAuthManager中的
```
requiresChallenge
requestCredential
onAuthSuccess
onAuthFailure
```
## 实时点播的invite信令

按照GB28181的标准，invite消息格式为：

INVITE sip:媒体流发送者设备编码@目的域名或IP地址端口 SIP/2.0
```
To:sip:媒体流发送者设备编码@目的域名
Content-Length:消息实体的字节长度
Contact:<sip:媒体流接收者设备编码@源IP地址端口>
CSeq:1 INVITE
Call-ID:xxxxxxxxxxxxxxxxxxxsss@ip
Via:SIP/2.0/UDP源域名或IP地址
From:<sip:媒体流接收者设备编码@源域名;tag=gemfield
Subject:媒体流发送者设备编码:发送端媒体流序列号,媒体流接收者设备编码:接收端媒体流序列号
Content-Type:application/sdp
Max-Forwards:70
#下面是SDP的定义，INVITE消息体中携带的SDP内容应符合RFC2327的相关要求，有如下字段：
------Session description, by Gemfield------
v=0
o=
s=Play
c=IN IP4 192.168.
--------Time description, by Gemfield--------
t=0 0
--------Media description,by Gemfield---------
m=video 6000 RTP/AVP 96 98 97
a=recvonly
a=rtpmap:96 PS/90000
a=rtpmap:98 H264/90000
a=rtpmap:97 MPEG4/90000
y=
```
其中，SDP部分的字段含义如下：
```
v= 为protocol version；
o= owner/creator and session identifier;
s= 为Session name，如Play代表点播,Playback代表历史回放；Download代表文件下载；Talk代表语音对讲；
u=* 为URI of description;
c=* 为connection information-not required if included in all media;
t= 为time the session is active;点播时00，回放或下载时，t的值为开始时间和结束时间，用空格分开；
m= 为media name and transport address;
c=* 为connection information-optional if included at session-level;
b=* bandwidth information;
a=* zero or more media attribute lines;这个字段的格式为rtpmap:(payload type)(encoding name)/(clock rate)[/(encoding parameters)]
y=* SSRC;十进制整数字符串，格式为Dddddddddd（第一位为历史或实时媒体流的标识位，1为历史，0为实时）；
f=* 媒体描述：f=v/编码格式/分辨率/帧率/码率类型/码率大小 a/编码格式/码率大小/采样率。
```

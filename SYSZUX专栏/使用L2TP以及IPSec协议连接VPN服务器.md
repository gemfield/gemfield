##  **背景**

因为最近的这场疫情，居家办公；于是以前不怎么用的VPN服务，现在居然成为和水电网一样的基础设施了。在我所在的团队里，远端的VPN服务使用的是L2TP/IPSec Server，因此，本地就相应的要使用L2TP/IPSec客户端。和服务端不同的是，本地有很多种操作系统啊：iOS、Android、Windows、macOS、Linux(Ubuntu发行版)，于是Gemfield就需要实践每个操作系统上的VPN连接，确保伙伴们都可以用上这个珍贵的基础实施。

##  **iOS用户**

Gemfield拿出自己的iPhone X和iPad，打开"设置" -> "通用" -> "VPN" -> "添加VPN配置"，依次填写：

  * 类型：选择L2TP；
  * 服务器：VPN服务的IP；
  * 账户：Gemfield；
  * 密码：不告诉你；
  * 秘钥：预共享秘钥，问Gemfield要；

连接成功！iOS用户开始笑语。


##  **Android用户**
Gemfield拿出自己的mate30 pro，打开"设置" -> "更多连接" -> "VPN" -> "添加VPN网络"，依次填写：

  * 类型：选择L2TP/IPSec PSK；
  * 服务器地址：VPN服务的IP；
  * IPSec预共享秘钥： 问Gemfield要；

然后在连接的时候，依次输入：

  * 用户名：Gemfield；
  * 密码：不告诉你；

连接成功！Android用户开始笑语。


##  Mac用户
Gemfied拿出自己的macbook air，打开"设置" -> "网络" -> "+"，依次填写：

  * 接口：VPN；
  * VPN类型：L2TP/IPSec；
  * 服务名称：来自Gemfield；

然后点击"创建"，在新创建的连接的右侧，依次填写：

  * 服务器地址：VPN服务的IP；
  * 账户名称：Gemfield；

在"认证设置"中，依次填写:

  * 密码：不告诉你；
  * 共享的秘钥：问Gemfield要；

然后点击工具图标("齿轮"样式)按钮，选择“设定服务顺序”，将新建的VPN连接拖拽至最顶层。

如果缺少这一步，会导致VPN连接可能是成功的，但是公司内网的服务就是无法访问。或者（也或者如果还是有问题），在Gemfield的这个上下文中，使用如下设置路由表的命令就可以搞定：
```bash
#查看路由表
netstat -rn

#删除路由表（可选）
sudo route -v delete -net default -ifp ppp0

#增加上外网的路由，192.168.31.1换成你自己路由器的网关IP
sudo route -n add -net 0.0.0.0 -netmask 255.255.255.0 192.168.31.1

#增加上内网的路由,192.168.0.0 换成你公司内网的网段，192.168.2.1换成你自己VPN的ppp0的IP段
sudo route -n add -net 192.168.0.0/24 192.168.2.1
```
连接成功！macOS用户开始笑语。

##  Windows用户
Gemfield拿出自己的ThinkPad X1c，打开"设置" -> "VPN" -> "添加VPN连接"，依次填写：

  * 服务器名称或地址：VPN服务的IP；
  * VPN类型：使用预共享秘钥的L2TP/IPsec；
  * 预共享秘钥：问Gemfield要；
  * 登录信息的类型：用户名和密码；
  * 用户名(可选)：Gemfield；
  * 密码(可选)：不告诉你；

连接成功！Windows用户开始笑语；

某些情况下，如果你用的TP-LINK路由器的VPN服务，并且放置在NAT设备之后（比如，联通的光猫之后），VPN连接不能够成功，这时候你可以参考TPLINK的官方说明，在你的Windows系统上修改几处注册表：http://tp-link.com/us/support/faq/1029/。

Windows用户还在笑语。

## Linux用户
Gemfield拿出自己的另一台ThinkPad X1c，打开KDE Ubuntu操作系统，打开"设置" -> "连接" -> "+" -> "第二层隧道协议(L2TP)"，点击创建......等等，虽然都是Linux用户，但如果你用的不是Ubuntu发行版，那可能要安装的包不一样、看日志的方法不一样、设置的地方也不一样......卒！

复活后，你已经在Ubuntu发行版的世界中了，但如果你用的不是和Gemfield一样的KDE桌面，而是GNOME或者其它什么桌面，那可能设置的地方的名称、布局、位置等不一样......卒！

复活后，你已经和Gemfield用的一样的Ubuntu19.10，桌面都是KDE最新版（以Ubuntu19.10为例，我们要知道，负责管理网络的是network-manager软件包，其上配置的连接信息都在/etc/NetworkManager/system-connections/目录下），那继续往下配置吧。

network-manager软件包就体现在了图形界面中系统设置的网络按钮上，我们从点击那儿开始。Gemfield要使用network-manager连接VPN啦——于是打开"设置" -> "连接" -> "+" -> "第二层隧道协议(L2TP)"，点击创建，结果提示“缺少VPN插件”，卒！

复活后，Linux用户准备开始了解Linux下的L2TP/IPSec使用。


**1，了解Linux下的L2TP/IPSec使用**

L2TP/IPSec是什么呢？为什么要两者结合呢？Linux用户为啥需要了解这些呢？不耐烦中。

L2TP是Layer Two Tunneling Protocol的缩写，中文名称“第二层隧道协议”，本身不提供加密功能，一般为了安全考虑，需要搭配安全协议一起使用，这里的安全协议，大部分都选择了IPSec。这就是L2TP/IPSec的来历（标准：IETF RFC 3193）。其中：

  * L2TP使用UDP，端口号为1701，是在IP层之上的会话层实现并模拟了数据链路层；
  * IPSec工作在三层，需要自身处理可靠性和分片问题，因此比较复杂，前面屡次提到的预共享秘钥就是IPSec所需要的。

一个L2TP/IPSec会话建立的过程基本如下：

  * IPSec的客户端和服务端的SA开始协商（一般通过IKE），使用端口500（Ubuntu上，如果使用的是strongSwan，该守护进程为charon；如果使用的是libreswan，则守护进程为Pluto）；
  * 建立ESP通信，这个时候安全通道已经建立，但是VPN隧道还没有；
  * 在前述的安全通道中，L2TP两端的SA开始协商并建立连接，使用UDP协议和1701端口（Ubuntu上，该守护进程一般为/usr/sbin/xl2tpd），VPN隧道打通。

可是，还是那个问题，Linux用户为什么要了解上面这些东西呢？因为，你可能已经隐隐约约感觉到了，Linux上需要有进程去分别实现IPSec协议和L2TP协议的连接！每个进程背后有对应的开源项目，就需要安装不同的包！咋这么复杂啊？？？卒！

复活后，你安慰自己：“没事，这些以后都会被WireGuard代替的”。

**2，安装必备的包**

network-manager软件包默认是没有VPN插件的，不支持建立VPN连接。因为这里我们要连接的是L2TP/IPSec，于是，Gemfield先安装L2TP/IPSec插件：
```bash
#Ubuntu使用的是apt包管理
gemfield@ThinkPad-X1C:~$ sudo apt update
gemfield@ThinkPad-X1C:~$ sudo apt install network-manager-l2tp network-manager-l2tp-gnome
```
在Ubuntu上，这个network-manager-l2tp插件来自这个开源项目：https://github.com/nm-l2tp/NetworkManager-l2tp
​

这个项目作为network-manager的插件，本身并没有实现L2TP和IPSec协议，而是实现了对这些协议的管理。其中：

  * IPSec协议的实现依靠的是Libreswan或者strongSwan开源项目；使用ipsec --version命令来确认；
  * L2TP协议的实现依靠的是xl2tpd开源项目（https://http://github.com/xelerance/xl2tpd）；

因此，安装完这个插件后，需要确认以下的包都安装好了（作为插件的依赖项）：
```bash
#IPSec实现
gemfield@ThinkPad-X1C:~$ ipsec --version
Linux strongSwan U5.7.2/K5.3.0-24-generic

#L2TP实现
gemfield@ThinkPad-X1C:~$ dpkg -S /usr/sbin/xl2tpd
xl2tpd: /usr/sbin/xl2tpd
```
如果这些包有一个没有安装好，那你就手工安装下，否则......卒！复活后，继续配置。

**3，配置连接信息**

打开"设置" -> "连接" -> "+" -> "第二层隧道协议(L2TP)"，点击创建，终于不提示“缺少VPN插件”了，继续依次填写：

  * 网关：VPN服务的IP；
  * 用户名：Gemfield；
  * 密码：不告诉你；

点击IPSec设置：

  * 预分享秘钥：问Gemfield要；
  * Phase1算法：啥玩意儿？
  * Phase2算法：啥玩意儿？
  * 强制UDP封装：check

苍天啊，谁能告诉我，这个Phase1算法和Phase2算法填写啥啊？？？？卒！复活后，先看服务端支持什么加密算法，下载ike-scan工具，使用ike-scan -s 7030 gemfield.org命令：
```bash
gemfield@ThinkPad-X1C:~$ sudo ike-scan -s 7030 gemfield.org
Starting ike-scan 1.9.4 with 1 hosts (http://www.nta-monitor.com/tools/ike-scan/)
222.118.6.140   Main Mode Handshake returned HDR=(CKY-R=5dbdd715929274c4) SA=(Enc=3DES Hash=MD5 Group=2:modp1024 Auth=PSK LifeType=Seconds LifeDuration=28800) VID=09002689dfd6b712 (XAUTH) VID=afcad71368a1f1c96b8696fc77570100 (Dead Peer Detection v1.0)
```
原来服务端的TP-LINK路由器使用的是“Dead Peer Detection v1.0”，支持的是3DES。然后再经过简单的文档查找，IPSec设置如下：

  * 预分享秘钥：问Gemfield要；
  * Phase1算法：3des-sha1-modp1024
  * Phase2算法：3des-sha1
  * 强制UDP封装：check

连接成功！确认侦听在500和1701端口上的服务也都起好了：
```bash
#strongSwan的话则守护进程为charon；libreswan的话则守护进程为Pluto
gemfield@ThinkPad-X1C:~$ sudo netstat -anp | grep -w 500
udp        0      0 0.0.0.0:500             0.0.0.0:*                           23450/charon        
udp6       0      0 :::500                  :::*                                23450/charon        

gemfield@ThinkPad-X1C:~$ sudo netstat -anp | grep -w 1701
udp        0      0 192.168.5.124:1701      222.128.5.170:1701      ESTABLISHED 23501/xl2tpd        
udp        0      0 0.0.0.0:1701            0.0.0.0:*                           23501/xl2tpd
```
好景不长，下次再连接就连接不上了......一样的配置信息啊，都没有动过啊，为什么啊？卒！复活后，开始debug问题。

**4，debug问题**

当连接不上的时候，使用journalctl命令来看NetworkManager服务的log（一个systemd服务）：
```bash
#使用-f参数看最新的log
gemfield@ThinkPad-X1C:~/github/Gemfield$ journalctl -f --unit=NetworkManager
......
NetworkManager[22518]: conn: "821342c3-0e52-4970-b763-73eab2ba3662" esp=3des-sha1
NetworkManager[22518]: conn: "821342c3-0e52-4970-b763-73eab2ba3662" ike=3des-sha1-modp1024
......
133 "821342c3-0e52-4970-b763-73eab2ba3662" #1: STATE_PARENT_I1: sent v2I1, expected v2R1
002 "821342c3-0e52-4970-b763-73eab2ba3662" #1: STATE_PARENT_I1: received unauthenticated v2N_NO_PROPOSAL_CHOSEN - ignored
......
```
这是因为，NetworkManager-l2tp插件会自己创建xl2tpd进程，如果Ubuntu上的xl2tpd服务作为一个Systemd的服务已经在运行（那肯定先占用了l2tp的1701端口），那么插件自己创建的xl2tpd进程就无法使用协议标准端口（转而使用一个随机端口），虽然RFC3193标准允许使用别的端口，但有些L2TP/IPsec 服务（或者一些防火墙）遇到这种情况就会出现问题，而Gemfield的VPN Server就是会出问题的这种！卒！

复活后，Gemfield赶紧停止并且禁用了Ubuntu自身使用Systemd来管理的xl2tpd服务：
```bash
gemfield@ThinkPad-X1C:~$ sudo systemctl stop xl2tpd
gemfield@ThinkPad-X1C:~$ sudo systemctl disable xl2tpd
```
然后再通过之前新建的VPN连接来connect办公区域的VPN服务，连接成功！但是，内网的服务还是没法访问啊......卒！复活后，决定看看路由信息。

**5，更改路由**

看自己的IP：
```bash
gemfield@ThinkPad-X1C:~/github/Gemfield$ ip a
......
3: wlp4s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    inet 192.168.5.124/24 brd 192.168.5.255 scope global dynamic noprefixroute wlp4s0
       valid_lft 5528sec preferred_lft 5528sec
......
236: ip_vti0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN group default qlen 1000
    link/ipip 0.0.0.0 brd 0.0.0.0
237: ppp0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1400 qdisc fq_codel state UNKNOWN group default qlen 3
    link/ppp 
    inet 192.168.2.75 peer 192.168.2.10/32 scope global ppp0
       valid_lft forever preferred_lft forever
```
看路由表:
```bash
gemfield@ThinkPad-X1C:~/github/Gemfield$ ip r
default via 192.168.5.1 dev wlp4s0 
default dev ppp0 proto static scope link metric 50 
192.168.2.10 dev ppp0 proto kernel scope link src 192.168.2.75 metric 50 
192.168.5.0/24 dev wlp4s0 proto kernel scope link src 192.168.5.124 metric 600 
192.168.5.1 dev wlp4s0 proto static scope link metric 600 
222.128.5.170 via 192.168.5.1 dev wlp4s0 proto static metric 600
```
发现似乎缺少个到内网192.168.0.*网段的路由，于是执行：
```bash
gemfield@ThinkPad-X1C:~$ sudo ip route add 192.168.0.0/24 dev ppp0
```
之后的路由表就多了这样一条记录：192.168.0.0/24 dev ppp0 scope link，如下所示：
```bash
gemfield@ThinkPad-X1C:~/github/Gemfield$ ip r
default via 192.168.5.1 dev wlp4s0 
default dev ppp0 proto static scope link metric 50 
default via 192.168.5.1 dev wlp4s0 proto dhcp metric 600 
192.168.0.0/24 dev ppp0 scope link 
......
```
发现内网终于可以访问了,大功告成。想当初第一次连上VPN的时候，Gemfield曾经有心做过笔记，现在一对照，一目了然。当初做的路由表笔记如下：
```bash
#没有连接VPN时：
gemfield@ThinkPad-X1C:~$ ip r
default via 192.168.5.1 dev wlp4s0 proto dhcp metric 600 
192.168.5.0/24 dev wlp4s0 proto kernel scope link src 192.168.5.124 metric 600 

gemfield@ThinkPad-X1C:~$ route -n
内核 IP 路由表
目标            网关            子网掩码        标志  跃点   引用  使用 接口
0.0.0.0         192.168.5.1     0.0.0.0         UG    600    0        0 wlp4s0
192.168.5.0     0.0.0.0         255.255.255.0   U     600    0        0 wlp4s0

################################################################################
#连接上L2TP VPN时：
gemfield@ThinkPad-X1C:~$ ip r
default dev ppp0 proto static scope link metric 50 
default via 192.168.5.1 dev wlp4s0 proto dhcp metric 600 
192.168.2.10 dev ppp0 proto kernel scope link src 192.168.2.65 metric 50 
192.168.5.0/24 dev wlp4s0 proto kernel scope link src 192.168.5.124 metric 600 
192.168.5.1 dev wlp4s0 proto static scope link metric 600 
222.128.5.170 via 192.168.5.1 dev wlp4s0 proto static metric 600

gemfield@ThinkPad-X1C:~$ route -n
内核 IP 路由表
目标            网关            子网掩码        标志  跃点   引用  使用 接口
0.0.0.0         0.0.0.0         0.0.0.0         U     50     0        0 ppp0
0.0.0.0         192.168.5.1     0.0.0.0         UG    600    0        0 wlp4s0
192.168.2.10    0.0.0.0         255.255.255.255 UH    50     0        0 ppp0
192.168.5.0     0.0.0.0         255.255.255.0   U     600    0        0 wlp4s0
192.168.5.1     0.0.0.0         255.255.255.255 UH    600    0        0 wlp4s0
222.128.5.170   192.168.5.1     255.255.255.255 UGH   600    0        0 wlp4s0
```
仔细比较后说明，至少在路由表上应该达成这样的效果：

  * 要么默认路由都走ppp0，这样肯定可以访问公司内网；但是外网就不一定能访问了；
  * 要么设置只有192.168.0.*（公司内网服务器的IP段）的traffic走ppp0，这样访问公司内网服务器的时候走ppp0，访问互联网的traffic还是走默认路由，完美。
  
疲惫不堪的Linux用户开始向帘儿底下，听人笑语。

## 总结
在家中舒服无比的座椅上，Gemfield已经愉快的使用VPN在公司内网coding了，而回望来时的路，仔细数了数，仅仅只是连接个VPN到公司内网，Linux用户就前前后后卒了9次，真所谓九死一生。Linux用户天生起点就比别人低，因而更要倍加努力，默默无闻的钻研，只争朝夕，不负韶华。
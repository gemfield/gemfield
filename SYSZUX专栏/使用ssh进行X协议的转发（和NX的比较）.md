# 背景
至少到目前为止（2018年2月24日），Linux上的图形系统都依赖于X。gemfield预计各个发行版到wayland的迁移还得到2020年才成熟，那时候我们就是全面小康社会了。X是个CS架构，有客户端和服务端。这就神奇了，因为这种架构的存在，X的客户端和服务端可以不在同一台机器上。有的时候这种能力非常有用。

一般来说，X的客户端部分一般都使用的是libxcb（更早些时候是xlib）这样的库，其实主要的图形程序也不是直接使用libxcb或者xlib的，而是使用更流行的封装，比如Qt或者gtk。而服务端则是Xorg进程：
```bash
gemfield@ThinkPad-X1C:~$ ps -ef |grep Xorg
root      1002   807  0 2月16 tty7    01:23:43 /usr/lib/xorg/Xorg -nolisten tcp -auth /var/run/sddm/{ab81e385-8f3c-4f6c-881d-a2c8d17bbbef} -background none -noreset -displayfd 17 vt7
```
X采用C/S模型实现了一个X server 和多个应用程序（client）通信。server接收client的请求绘制窗口，并将来自鼠标、键盘等设备的输入传递给client。

现在的发行版默认情况下，Xorg这个server进程只接收本机的client。但是通过ssh建立隧道进行X协议的转发就可以克服这个障碍。要转发X11，我们需要在ssh的客户端和服务端都开启支持x11的功能，注意了，是ssh的客户端和服务端，从X协议的视角出发，它们正好是相反的。

# 设置
在ssh客户端部分(也就是X的Server端)，如果是Linux系统的话，事情就简单了。直接使用ssh -X参数即可。如果想要省掉每次都敲-X这个麻烦，则可以在~/.ssh/config中配置ForwardX11使得-X变成默认行为。
```bash
gemfield@ThinkPad-X1C:~$ ssh -X ai.gemfield.org
Welcome to Ubuntu 17.10 (GNU/Linux 4.13.0-32-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

 * Meltdown, Spectre and Ubuntu: What are the attack vectors,
   how the fixes work, and everything else you need to know
   - https://ubu.one/u2Know

0 packages can be updated.
0 updates are security updates.

Last login: Sat Feb 24 09:52:30 2018 from 192.168.1.119
/usr/bin/xauth:  /home/gemfield/.Xauthority not writable, changes will be ignored
gemfield@ai:~$ which xauth
/usr/bin/xauth
```
如果是Windows系统，麻烦就来了。因为。。。windows没有X Server 啊，所以你得安装个X Server在Windows上的实现，比如Xming, 然后启动X server；另外，windows没有原生的ssh啊，所以你还得安装个ssh的客户端，比如putty。然后相关的设置你自己搜下吧，原理类似。

在ssh的服务端部分（也就是X的客户端），必须保证xauth是在PATH中的，一般情况下都是满足的。然后必须在/etc/ssh/sshd_config文件中将X11Forwarding打开（默认是不打开的）。
```bash
gemfield@ai:~$ grep X11 -n /etc/ssh/sshd_config
89:X11Forwarding yes
```
使用ssh -X登陆后，ssh会在当前的会话中自动设置环境变量：DISPLAY=localhost:10.0，不需要我们手动介入。
```bash
gemfield@ai:~$ echo $DISPLAY
localhost:10.0
```
现在就可以启动个图形程序试试了：
```bash
gemfield@ai:~$ kinfocenter
```
# 错误处理
当然有时候不会这么顺利，比如会出现下面这样的情况：
```bash
gemfield@ai:~$ kinfocenter 
X11 connection rejected because of wrong authentication.
QXcbConnection: Could not connect to display localhost:10.0
Aborted (core dumped)
```
那么为什么会报错：X11 connection rejected because of wrong authentication ？

我们可以使用-v参数来进行debug：
```bash
gemfield@ThinkPad-X1C:~$ ssh -X -v ai.gemfield.org
OpenSSH_7.5p1 Ubuntu-10ubuntu0.1, OpenSSL 1.0.2g  1 Mar 2016
debug1: Reading configuration data /etc/ssh/ssh_config
debug1: /etc/ssh/ssh_config line 19: Applying options for *
debug1: Connecting to ai.gemfield.org [192.168.1.188] port 22.
debug1: Connection established.
......
Last login: Sat Feb 24 16:03:05 2018 from 192.168.1.119

/usr/bin/xauth:  timeout in locking authority file /home/gemfield/.Xauthority
gemfield@ai:~$
```
可以看到问题就出现在：/usr/bin/xauth: timeout in locking authority file /home/gemfield/.Xauthority，这一定是权限问题了。立马查看这个文件的权限：
```bash
gemfield@ai:~$ ls -l /home/gemfield/.Xauthority
-rw------- 1 root root 96 1月   5 11:42 /home/gemfield/.Xauthority
```
我的天啊，这个文件怎么是root产生的呢？过去肯定发生了什么混乱不堪的事情，所以才有今天的错误！把/home/gemfield/.Xauthority删除掉出新使用gemfield用户进行touch，结果就好了。

有个诀窍，如果还是各种出错的花，可以使用strace命令探测哪个系统调用出错了：
```bash
gemfield@ai:~$ strace xauth list 2>&1 |grep -E "^stat|^access"
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
stat("/home/gemfield/.Xauthority-c", 0x7ffc764cd060) = -1 ENOENT (No such file or directory)
statfs("/home/gemfield/.Xauthority-c", {f_type=EXT2_SUPER_MAGIC, f_bsize=4096, f_blocks=59699623, f_bfree=13717887, f_bavail=10667878, f_files=15237120, f_ffree=13507556, f_fsid={val=[776034305, 2830689012]}, f_namelen=255, f_frsize=4096, f_flags=ST_VALID|ST_RELATIME}) = 0
stat("/home/gemfield/.Xauthority-c", {st_mode=S_IFREG|0600, st_size=0, ...}) = 0
access("/sys/fs/ext4/nvme0n1p2", F_OK)  = 0
access("/home/gemfield/.Xauthority", F_OK) = 0
access("/home/gemfield/.Xauthority", W_OK) = 0
gemfield@ai:~$
```
但是你要能够区分出哪个是真正的致命的错误。

# 速度问题
当然了，在欢呼图形程序能够显示在另外的机器上的时候，悲伤也一并来了：它太慢了！！！这个时候，我们有几种方案：

## 1，还是X over ssh，但是我们启用压缩：
```bash
gemfield@ThinkPad-X1C:~$ ssh -X -C  ai.gemfield.org
```
再进一步的话（当然这是可选的），在登录到服务器后，我们启动图形程序的时候，将标准错误扔掉：
```bash
gemfield@ai:~$ dolphin 2>/dev/null
```
或者在ssh客户端机器上直接这样：
```bash
gemfield@ThinkPad-X1C:~$ ssh -X -C -n ai.gemfield.org dolphin 2>/dev/null
```
## 2，使用vnc：

gemfield一般使用tigervncserver，但是不知道为什么，在安装有NVIDIA专属驱动的机器上，vncserver不能启动X会话，至今还没找到原因。

另外，chrome浏览器商店里可以下载安装realvnc的客户端！

另外，KDE自带KRDC也支持VNC！

## 3，使用NoMachine的NX：

下载NoMachine 客户端：
```bash
gemfield@ThinkPad-X1C:~$ wget http://download.nomachine.com/download/6.0/Linux/nomachine-enterprise-client_6.0.78_1_amd64.deb
```
安装客户端：
```bash
gemfield@ThinkPad-X1C:~/下载$ sudo dpkg -i nomachine-enterprise-client_6.0.78_1_amd64.deb
[sudo] gemfield 的密码： 
正在选中未选择的软件包 nomachine-enterprise-client。
(正在读取数据库 ... 系统当前共安装有 462343 个文件和目录。)
正准备解包 nomachine-enterprise-client_6.0.78_1_amd64.deb  ...
正在解包 nomachine-enterprise-client (6.0.78-1) ...
正在设置 nomachine-enterprise-client (6.0.78-1) ...
NX> 700 Starting install at: 六 2月 24 17:36:19 2018.
NX> 700 Installing: nxclient version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 Compiling the USB module.
NX> 700 Installing: nxplayer version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 To connect the remote printer to the local desktop,
NX> 700 the user account must be a member of the CUPS System Group: lpadmin.
NX> 700 Install completed at: 六 2月 24 17:36:23 2018.
```
下载NoMachine 服务端：
```bash
gemfield@edge:~$ wget http://download.nomachine.com/download/6.0/Linux/nomachine_6.0.78_1_amd64.deb
```
安装服务端：
```bash
gemfield@edge:~$ sudo dpkg -i nomachine_6.0.78_1_amd64.deb
[sudo] password for gemfield: 
正在选中未选择的软件包 nomachine。
(正在读取数据库 ... 系统当前共安装有 284060 个文件和目录。)
正准备解包 nomachine_6.0.78_1_amd64.deb  ...
正在解包 nomachine (6.0.78-1) ...
正在设置 nomachine (6.0.78-1) ...
NX> 700 Starting install at: 六 2月 24 17:23:08 2018.
NX> 700 Installing: nxclient version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 Compiling the USB module.
NX> 700 Installing: nxplayer version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 To connect the remote printer to the local desktop,
NX> 700 the user account must be a member of the CUPS System Group: lpadmin.
NX> 700 Installing: nxnode version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 Creating configuration in: /usr/NX/etc/node.cfg.
NX> 700 Installing: nxserver version: 6.0.78.
NX> 700 Using installation profile: Ubuntu.
NX> 700 Install log is: /usr/NX/var/log/nxinstall.log.
NX> 700 Creating configuration in: /usr/NX/etc/server.cfg.
NX> 700 Install completed at: 六 2月 24 17:23:56 2018.
NX> 700 NoMachine was configured to run the following services:
NX> 700 NX service on port: 4000
```
NX服务监听在4000端口上：
```bash
gemfield@edge:~$ sudo netstat -antp |grep 4000
tcp        0      0 0.0.0.0:4000            0.0.0.0:*               LISTEN      10441/nxd       
tcp6       0      0 :::4000                 :::*                    LISTEN      10441/nxd
```
然后启动客户端程序，在系统的开始菜单里有（/usr/NX/bin/nxplayer.bin）。

## 4，使用x2go（基于ssh）。

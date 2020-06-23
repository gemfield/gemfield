##  **背景**

最近Gemfield利用团队废弃的硬件搭建了一个CEPH集群，这些硬件的关键信息如下：

  1. 主流的Intel x86 cpu； 
  2. 64GB RAM per node； 
  3. 1GbE+ NIC； 
  4. 1GbE+ 交换机； 
  5. 5400RPM的普通机械硬盘； 

当然，这些寒碜的硬件也带来了预期般的结果，这个CEPH集群的性能非常感人。性能指标如下所示：

    
    
    [root@rook-ceph-tools-7gemfield-syszux /]# ceph osd pool create gemfield 100 100
    pool 'gemfield' created
    
    #写测试
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# rados bench -p gemfield 10 write --no-cleanup       
    hints = 1
    Maintaining 16 concurrent writes of 4194304 bytes to objects of size 4194304 for up to 10 seconds or 0 objects
    Object prefix: benchmark_data_rook-ceph-tools-7bb5797c8-ns4_268170
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0      16        16         0         0         0           -           0
        1      16        19         3   11.9373        12      1.0033     0.88516
        2      16        35        19   37.8984        64    0.959745     1.16765
        3      16        50        34   45.2513        60     1.75533     1.14427
        4      16        66        50   49.9308        64      1.7261     1.08274
        5      16        79        63   50.3425        52     1.82505     1.04525
        6      16        92        76   50.6176        52    0.301995     1.04329
        7      16       103        87   49.6723        44    0.268341     1.09093
        8      16       111        95   47.4643        32     1.75813     1.15787
        9      16       117       101   44.8582        24    0.357698     1.14634
       10      16       127       111   44.3721        40    0.558962     1.17723
       11      16       128       112   40.7035         4    0.888134     1.17465
    Total time run:         11.8353
    Total writes made:      128
    Write size:             4194304
    Object size:            4194304
    Bandwidth (MB/sec):     43.2606
    Stddev Bandwidth:       20.616
    Max bandwidth (MB/sec): 64
    Min bandwidth (MB/sec): 4
    Average IOPS:           10
    Stddev IOPS:            5.15399
    Max IOPS:               16
    Min IOPS:               1
    Average Latency(s):     1.46968
    Stddev Latency(s):      1.15616
    Max latency(s):         6.57493
    Min latency(s):         0.268341
    
    #顺序读测试
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# rados bench -p gemfield 10 seq       
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        42        26   103.982       104    0.303402    0.280297
        2      16        77        61   121.986       140    0.324191    0.363301
        3      16       102        86   114.655       100    0.129616    0.335518
        4      16       109        93   92.9908        28    0.046699    0.401311
        5      16       124       108   86.3917        60    0.019722    0.394067
        6      16       128       112   74.6592        16   0.0841534     0.45322
        7      16       128       112   63.9929         0           -     0.45322
        8      16       128       112   55.9936         0           -     0.45322
        9      16       128       112    49.772         0           -     0.45322
       10      16       128       112   44.7944         0           -     0.45322
    Total time run:       10.5818
    Total reads made:     128
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   48.3848
    Average IOPS:         12
    Stddev IOPS:          13.1724
    Max IOPS:             35
    Min IOPS:             0
    Average Latency(s):   1.31546
    Max latency(s):       9.35307
    Min latency(s):       0.0112003
    
    #随机读测试
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# rados bench -p gemfield 10 rand       
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        44        28   111.984       112    0.345287    0.325227
        2      16        77        61   121.985       132    0.502314    0.354814
        3      16       105        89   118.654       112    0.144197    0.373102
        4      16       134       118   117.988       116    0.111743    0.445691
        5      16       168       152   121.588       136    0.235599    0.445785
        6      16       199       183   121.989       124    0.176444    0.450244
        7      16       229       213   121.703       120    0.111384    0.458033
        8      16       261       245   122.488       128    0.189708    0.474083
        9      16       292       276   122.655       124    0.206655    0.460007
       10      16       327       311   124.389       140    0.888494     0.46772
       11       7       327       320   116.353        36    0.628508    0.499252
    Total time run:       11.8967
    Total reads made:     327
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   109.946
    Average IOPS:         27
    Stddev IOPS:          7.04918
    Max IOPS:             35
    Min IOPS:             9
    Average Latency(s):   0.54098
    Max latency(s):       4.07673
    Min latency(s):       0.0020629

在这样的指标下，团队的炼丹人员普遍反映读取数据集的速度慢了2倍到10倍不等（相比于直接从固态硬盘load数据）。为了解决在K8s
Pod中基于CEPHFS创建的PVC上读取大量小文件的性能低下问题，Gemfield苦苦思索。首先，这是废弃的硬件，逻辑上不可能为了凑合这堆硬件再添置新的硬件；其次，我也没钱；那怎么办呢？

最后，Gemfield发现废弃硬件的主板是支持USB3.0、USB3.1的，这就让Gemfield有了两种截然不同的想法：

1，挂载USB设备，然后将ROOK
cluster.yaml中的metadataDevice设置为该USB设备；这个想法暂时被Gemfield压抑住了，主要是两个原因：1，metadataDevice的设置不支持热更新，需要将node
purge后重新安装，对于目前的集群来说这个工作量有点大；2，USB是相对不稳定的设备，把OSD的meta放在USB上，感觉是将大厦的根基放在沙地上。

2，使用USB设备来创建个local persistent volume！缺点就是无法分布式共享！但相比于使用的场景，Gemfield倾向于使用这个方案！

哎，MLab2.0还是太老了，期待新的MLab3.0的早日到来！不过在此之前，先用下面的 **三波实验** 来确认下上述的第二个想法。

##  第一波实验：普通三星USB3.0的U盘

**1，U盘性能**

Gemfield手头正好有一个闲置的三星U盘，先来对其的顺序读和随机读进行下IO性能测试：

    
    
    #####################使用1个线程读
    (base) gemfield@ThinkPad-X1C:~$ sudo fio -filename=/dev/sda1 -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=1 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    fio-3.16
    Starting 1 thread
    Jobs: 1 (f=1): [R(1)][100.0%][r=97.9MiB/s][r=6267 IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=1): err= 0: pid=198876: Thu May 21 15:33:54 2020
      read: IOPS=6550, BW=102MiB/s (107MB/s)(6141MiB/60001msec)
    ......
       bw (  KiB/s): min=88384, max=113312, per=100.00%, avg=104850.99, stdev=7011.68, samples=119
       iops        : min= 5524, max= 7082, avg=6553.18, stdev=438.23, samples=119
    ......
    
    Run status group 0 (all jobs):
       READ: bw=102MiB/s (107MB/s), 102MiB/s-102MiB/s (107MB/s-107MB/s), io=6141MiB (6440MB), run=60001-60001msec
    
    Disk stats (read/write):
      sda: ios=392373/1, merge=0/0, ticks=56234/0, in_queue=84, util=99.75%
    
    
    ######################使用3个线程读
    (base) gemfield@ThinkPad-X1C:~$ sudo fio -filename=/dev/sda1 -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=3 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    ...
    fio-3.16
    Starting 3 threads
    Jobs: 3 (f=3): [R(3)][100.0%][r=15.0MiB/s][r=1022 IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=3): err= 0: pid=199170: Thu May 21 15:36:36 2020
      read: IOPS=1121, BW=17.5MiB/s (18.4MB/s)(1052MiB/60003msec)
    ......
       bw (  KiB/s): min=14336, max=22624, per=100.00%, avg=17946.16, stdev=555.87, samples=360
       iops        : min=  896, max= 1414, avg=1121.62, stdev=34.74, samples=360
    ......
    
    Run status group 0 (all jobs):
       READ: bw=17.5MiB/s (18.4MB/s), 17.5MiB/s-17.5MiB/s (18.4MB/s-18.4MB/s), io=1052MiB (1103MB), run=60003-60003msec
    
    Disk stats (read/write):
      sda: ios=65448/3, merge=1745/0, ticks=116019/2, in_queue=480, util=99.80%
    
    ##################随机读，参数-rw=randread
    (base) gemfield@ThinkPad-X1C:~$ sudo fio -filename=/dev/sda1 -direct=1 -iodepth 1 -thread -rw=randread -ioengine=psync -bs=16k -size=20G -numjobs=3 -runtime=60 -group_reporting -name=gemfieldtest

**2，准备U盘空间**

在使用U盘空间之前，先在U盘上创建ext4文件系统：

    
    
    gemfield@ThinkPad-X1C:~$ sudo mkfs.ext4 /dev/sda

然后mount到worker node的/gemfield/u64目录下：

    
    
    mount /dev/sda /gemfield/u64

这个废弃的U盘是一个三星的USB3.0的64G的U盘，磁盘空间足够装下数据集了，但是还需要检查下inode的数量，不然即使空间足够，也会报“No space
left on device”的错误：

    
    
    (base) gemfield@ThinkPad-X1C:~$ df -i
    文件系统         Inode 已用(I) 可用(I) 已用(I)% 挂载点
    ......
    /dev/sda      3842048      11 3842037       1% /media/gemfield/e34efb11-76f2-48e3-9f0e-4617bf276159

inode的数量是3842048，呃，大概不够，你知道的，数据集每个文件都很小，而数量又很多。于是重新制作文件系统，使用-N参数将inode数量扩大一倍：

    
    
    gemfield@ai01:~$ sudo mkfs.ext4 -N 7847936 /dev/sda

当然这样做也是有代价的，增加的这300万inode，大约会损失掉8G的U盘空间。这之后，你就可以使用Hostpath或者local persistent
volume了，Gemfield选择的是HostPath。

**3，创建Hostpath Persistent Volumes**

创建PV的YAML如下：

    
    
    apiVersion: v1
    kind: PersistentVolume
    metadata:
      name: gemfieldu64-hostpath-pv
      namespace: mlab2
      labels:
        type: local
    spec:
      storageClassName: manual
      capacity:
        storage: 54Gi
      accessModes:
        - ReadWriteMany
      hostPath:
        path: "/gemfield/u64"

Apply后，结果显示如下：

    
    
    gemfield@ThinkPad-X1C:~$ kubectl -n mlab2 get pv
    NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM                            STORAGECLASS      REASON   AGE
    gemfieldu64-hostpath-pv                    54Gi       RWX            Retain           Bound      mlab2/gemfieldu64-hostpath-pvc   manual                     6s

创建PVC的YAML如下所示：

    
    
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: gemfieldu64-hostpath-pvc
      namespace: mlab2
    spec:
      storageClassName: manual
      accessModes:
        - ReadWriteMany
      resources:
        requests:
          storage: 54Gi

Apply后如下所示：

    
    
    gemfield@ThinkPad-X1C:~$ kubectl -n mlab2 get pvc
    NAME                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
    gemfieldu64-hostpath-pvc   Bound    gemfieldu64-hostpath-pv                    54Gi       RWX            manual            2m

之后创建Pod，将PVC挂载到Volumes，不解释了。

**4，总结**

在USB3.0的U盘的加持下，炼丹师们反映读取数据的速度并没怎么加快。哼，一定是USB3.0的锅。等我择日在使用USB3.1的U盘试试吧。

##  **第二波实验：USB3.1（GEN 2）转NVME**

**Gemfield选择的是绿联CM238 NVME固态硬盘盒，SSD选择的是西数的SN550（容量500GB）。**

  1. 选择绿联CM238硬盘盒是看重了以下功能（其它牌子也可能支持）； 
  2. 支持USB3.1 GEN2标准，传输速度10Gbps，也就是传说中的SS10； 
  3. 主控支持UASP加速传输协议（用于透过USB接口连接SSD设备，提高传输速度，并降低CPU的利用率、数据延迟和等待时间，该协议提供了高性能主机及设备之间的数据传输）； 
  4. 支持TRIM指令（微软联合各大SSD厂商所开发的一项技术，提高SSD的写入速度）。 

将该USB硬盘组装完毕后，使用硬盘盒自带的type-c数据线接到电脑的USB3.1 type-c口上。我们使用lsusb命令来查看下：

    
    
    gemfield@ai01:~$ lsusb
    ......
    Bus 006 Device 007: ID 174c:2362 ASMedia Technology Inc. Ugreen Storage Device
    ......

可见该USB硬盘是挂载到了Bus 6上，成为了device
7。这是Ugreen绿联的设备，使用的是ASMedia的主控方案（祥硕科技）。我们再使用lsusb -t命令来查看下：

    
    
    gemfield@ai01:~$ lsusb -t
    /:  Bus 06.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/2p, 10000M
        |__ Port 1: Dev 7, If 0, Class=Mass Storage, Driver=uas, 10000M
        |__ Port 2: Dev 6, If 0, Class=Mass Storage, Driver=usb-storage, 5000M

可以看到在Bus 06的Dev 7设备（就是绿联硬盘盒）使用的driver是uas，这说明系统将会用到上述提到的UASP加速传输协议；而Dev
6设备（就是第一波实验中的三星U盘）的驱动是usb-
storage，说明不支持UASP；此外，Dev7和Dev6分别是10000M和5000M，分别代表两个设备分别使用USB3.1 GEN2和最早的USB
3.0协议。

再看下该组装移动固态硬盘的可用空间，可见有465.78 GiB的空间可供使用：

    
    
    gemfield@ai01:~$ sudo fdisk -l /dev/sdd
    [sudo] password for gemfield: 
    Disk /dev/sdd: 465.78 GiB, 500107862016 bytes, 976773168 sectors
    Disk model: 00G2B0C-00PXH0  
    Units: sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 33553920 bytes

这之后，我们在该SSD硬盘盒上创建ext4文件系统并挂载：

    
    
    gemfield@ai01:~$ sudo mkfs.ext4 /dev/sdd
    gemfield@ai01:~$ sudo mount /dev/sdd /gemfield/hostpv/
    
    gemfield@ai01:~$ df -h | grep gemfield
    /dev/sdd        458G   73M  435G   1% /gemfield/hostpv

**1，USB固态硬盘性能**

先确认

    
    
    #单线程读
    gemfield@ai01:~$ sudo fio -filename=/dev/sdd -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=1 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    fio-3.16
    Starting 1 thread
    Jobs: 1 (f=1): [R(1)][100.0%][r=177MiB/s][r=11.3k IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=1): err= 0: pid=2207076: Thu Jun 11 11:12:09 2020
      read: IOPS=11.5k, BW=180MiB/s (188MB/s)(10.5GiB/60001msec)
        clat (usec): min=60, max=12994, avg=85.68, stdev=52.21
         lat (usec): min=60, max=12994, avg=85.81, stdev=52.23
    ......
       bw (  KiB/s): min=148576, max=190432, per=99.97%, avg=183818.45, stdev=6638.34, samples=119
       iops        : min= 9286, max=11902, avg=11488.65, stdev=414.89, samples=119
    ......
    
    Run status group 0 (all jobs):
       READ: bw=180MiB/s (188MB/s), 180MiB/s-180MiB/s (188MB/s-188MB/s), io=10.5GiB (11.3GB), run=60001-60001msec
    
    Disk stats (read/write):
      sdd: ios=688288/2, merge=0/0, ticks=53392/0, in_queue=68, util=99.74%
    
    #3个线程读
    gemfield@ai01:~$ sudo fio -filename=/dev/sdd -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=3 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    ...
    fio-3.16
    Starting 3 threads
    Jobs: 3 (f=3): [R(3)][100.0%][r=388MiB/s][r=24.9k IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=3): err= 0: pid=2217813: Thu Jun 11 11:17:25 2020
      read: IOPS=24.6k, BW=385MiB/s (403MB/s)(22.5GiB/60001msec)
        clat (usec): min=67, max=14744, avg=120.41, stdev=69.41
         lat (usec): min=67, max=14744, avg=120.58, stdev=69.42
    ......
       bw (  KiB/s): min=219200, max=413216, per=99.99%, avg=393774.71, stdev=10054.19, samples=357
       iops        : min=13700, max=25826, avg=24610.92, stdev=628.39, samples=357
      lat (usec)   : 100=15.98%, 250=83.34%, 500=0.61%, 750=0.04%, 1000=0.01%
      lat (msec)   : 2=0.01%, 4=0.01%, 10=0.01%, 20=0.01%
    ......
    
    Run status group 0 (all jobs):
       READ: bw=385MiB/s (403MB/s), 385MiB/s-385MiB/s (403MB/s-403MB/s), io=22.5GiB (24.2GB), run=60001-60001msec
    
    Disk stats (read/write):
      sdd: ios=1472203/3, merge=1674/0, ticks=163786/0, in_queue=172, util=99.82%

可见在单个线程read上，对三星U盘的提升就是USB3.1对USB3.0的提升，不管是IOPS还是吞吐量都接近2倍；而在多线程read上，那是碾压态势，完全没有可比性了。

再测试个对普通人比较关心的文件写入吧（swap.img是一个8G大文件）：

    
    
    gemfield@ai01:/gemfield/hostpv$ sudo time cp /swap.img .
    0.05user 
    9.71system 
    0:09.80elapsed 
    
    gemfield@ai01:~$ sudo time cp /gemfield/hostpv/swap.img .
    0.06user 
    8.59system 
    0:08.82elapsed 

不到10秒写入8GB的大文件，不到9秒读取8GB的大文件，嗯，基本就这样了。

**2，准备U盘空间**

类似，不再赘述。

**3，创建Hostpath Persistent Volumes**

类似，不再赘述。

**4，总结**

这个训练速度获得了明显提升。

##  **第三波实验：使用文件来虚拟块设备**

前文也提到过了，MLab2.0贫瘠的硬件限制了很多发挥。比方说只有一个NVME设备接口，且没有多余的PCI可供使用，因此也没法扩展。但是，唯一的这一个NVME
SSD有512G的大小，给Linux操作系统和基础软件留上200多个GB的空间是足够了，那么Gemfield可以额外划分出200G大小的磁盘空间来虚拟出一个块设备。

使用dd命令先创建出一个200G大小的文件：

    
    
    gemfield@ai02:~# dd if=/dev/zero of=/root/hostpv.img bs=1G count=200

创建loop块设备，使用-f参数是说帮我们找到第一个可用的loop设备：

    
    
    gemfield@ai02:~# losetup -fP /root/hostpv.img

查看创建的loop块设备，就可以发现losetup命令帮我们找到的是loop1设备：

    
    
    gemfield@ai02:~# losetup -a
    /dev/loop1: [2082]:17170440 (/root/hostpv.img)
    /dev/loop6: [2082]:20582286 (/var/lib/snapd/snaps/lxd_15457.snap)
    /dev/loop4: [2082]:20588815 (/var/lib/snapd/snaps/lxd_15359.snap)
    /dev/loop2: [2082]:20584910 (/var/lib/snapd/snaps/core18_1754.snap)
    /dev/loop0: [2082]:20581035 (/var/lib/snapd/snaps/core18_1705.snap)
    /dev/loop5: [2082]:20578743 (/var/lib/snapd/snaps/snapd_7777.snap)
    /dev/loop3: [2082]:20581037 (/var/lib/snapd/snaps/snapd_7264.snap)

创建ext4文件系统：

    
    
    gemfield@ai02:~# mkfs.ext4 /root/hostpv.img

挂载loop1设备：

    
    
    gemfield@ai02:~# mkdir -p /gemfield/hostpv
    gemfield@ai02:~# mount -o loop /dev/loop1 /gemfield/hostpv/

最后，在/etc/rc.local文件中添加下面这行内容来持久化：

    
    
    losetup /dev/loop1 /root/hostpv.img

**1，loop设备的性能**

**上fio命令！Gemfield分别测试了SATA协议的SSD和NVME协议的SSD：**

    
    
    #SATA协议的SSD
    
    gemfield@ai02:~# fio -filename=/dev/loop1 -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=1 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    fio-3.16
    Starting 1 thread
    Jobs: 1 (f=1): [R(1)][100.0%][r=532MiB/s][r=34.0k IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=1): err= 0: pid=3577222: Thu Jun 11 16:11:42 2020
      read: IOPS=36.5k, BW=570MiB/s (597MB/s)(20.0GiB/35947msec)
        clat (usec): min=15, max=7162, avg=26.80, stdev=22.59
         lat (usec): min=15, max=7162, avg=26.86, stdev=22.59
    ......
       bw (  KiB/s): min=520320, max=676352, per=100.00%, avg=583979.85, stdev=46053.87, samples=71
       iops        : min=32520, max=42272, avg=36498.73, stdev=2878.36, samples=71
    ......
    Run status group 0 (all jobs):
       READ: bw=570MiB/s (597MB/s), 570MiB/s-570MiB/s (597MB/s-597MB/s), io=20.0GiB (21.5GB), run=35947-35947msec
    
    Disk stats (read/write):
      loop1: ios=1309220/0, merge=0/0, ticks=26849/0, in_queue=16, util=99.76%
    
    #NVME协议的SSD
    
    root@ai03:~# fio -filename=/dev/loop5 -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=20G -numjobs=1 -runtime=60 -group_reporting -name=gemfieldtest
    gemfieldtest: (g=0): rw=read, bs=(R) 16.0KiB-16.0KiB, (W) 16.0KiB-16.0KiB, (T) 16.0KiB-16.0KiB, ioengine=psync, iodepth=1
    fio-3.16
    Starting 1 thread
    Jobs: 1 (f=1): [R(1)][100.0%][r=1100MiB/s][r=70.4k IOPS][eta 00m:00s]
    gemfieldtest: (groupid=0, jobs=1): err= 0: pid=2969320: Thu Jun 11 16:20:08 2020
      read: IOPS=66.6k, BW=1041MiB/s (1092MB/s)(20.0GiB/19668msec)
        clat (usec): min=7, max=12144, avg=14.75, stdev=31.35
         lat (usec): min=7, max=12144, avg=14.79, stdev=31.36
    ......
       bw (  MiB/s): min=  837, max= 1218, per=100.00%, avg=1042.72, stdev=89.33, samples=39
       iops        : min=53592, max=77982, avg=66734.46, stdev=5717.25, samples=39
    ......
    Run status group 0 (all jobs):
       READ: bw=1041MiB/s (1092MB/s), 1041MiB/s-1041MiB/s (1092MB/s-1092MB/s), io=20.0GiB (21.5GB), run=19668-19668msec
    
    Disk stats (read/write):
      loop5: ios=1308941/0, merge=0/0, ticks=15695/0, in_queue=88, util=99.27%

可见SATA的SSD比USB3.1 Gen2 的SSD要上了一个台阶，而NVME的SSD是王者！！！

**2，准备U盘空间**

类似，不再赘述。

**3，创建Hostpath Persistent Volumes**

类似，不再赘述。

**4，总结**

这个训练速度获得了明显提升。

##  **总结**

**NVME SSD > SATA SSD > USB 3.1 Gens SSD > USB 3.0 flash drive。 **


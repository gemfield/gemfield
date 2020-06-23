##  **背景**

最近在做个对象存储，基于ROOK项目，简而言之，就是使用Rook提供的K8s operator，基于K8s cluster部署Ceph服务。

##  **部署**

将Rook项目克隆到本地，使用里面的k8s/ceph目录。

**1，部署CRD**

    
    
    kubectl apply -f common.yaml

**2，部署operator**

    
    
    kubectl apply -f operator.yaml

**3，部署Ceph cluster**

cluster.yaml文件里的内容需要修改，一定要适配自己的硬件情况。修改完成后：

    
    
    kubectl apply -f cluster.yaml

**4，创建对象存储**

    
    
    kubectl apply -f object.yaml
    
    #以及用户
    kubectl apply -f object-user.yaml

**5，创建Ceph pool（块存储池）**

使用的kind是CephBlockPool

    
    
    kubectl apply -f pool.yaml

**6，创建文件存储**

这块宿主机的内核版本一定要>= 5.3（详情参考文末）：

    
    
    kubectl apply -f filesystem.yaml
    kubectl apply -f storageclass.yaml

**7，创建PVC**

之后你就可以创建各种PVC了。

##  入门条款

**1，判断ceph安装是否成功**

首先看pod的情况，有operator、mgr、agent、discover、mon、osd、tools，且osd-
prepare是completed的状态，其它是running的状态：

    
    
    gemfield@master:~/rook-ceph/rook/cluster/examples/kubernetes/ceph$ kubectl -n rook-ceph get pods
    NAME                                           READY   STATUS      RESTARTS   AGE
    csi-cephfsplugin-4f2wl                         3/3     Running     0          3h47m
    csi-cephfsplugin-5k6z8                         3/3     Running     0          3h47m
    csi-cephfsplugin-d5rhh                         3/3     Running     0          3h47m
    csi-cephfsplugin-provisioner-c6b8b6dff-ds56t   4/4     Running     0          3h47m
    csi-cephfsplugin-provisioner-c6b8b6dff-zjx6x   4/4     Running     0          3h47m
    csi-cephfsplugin-sw98v                         3/3     Running     0          3h47m
    csi-cephfsplugin-vsgwq                         3/3     Running     0          3h47m
    csi-rbdplugin-f8cdm                            3/3     Running     0          3h47m
    csi-rbdplugin-g7xcf                            3/3     Running     0          3h47m
    csi-rbdplugin-kvr4m                            3/3     Running     0          3h47m
    csi-rbdplugin-lc2lp                            3/3     Running     0          3h47m
    csi-rbdplugin-provisioner-68f5664455-4pjm2     5/5     Running     0          3h47m
    csi-rbdplugin-provisioner-68f5664455-p9n9r     5/5     Running     0          3h47m
    csi-rbdplugin-zsdk9                            3/3     Running     0          3h47m
    rook-ceph-agent-6dczj                          1/1     Running     0          3h47m
    rook-ceph-agent-rvvtr                          1/1     Running     0          3h47m
    rook-ceph-agent-t79hz                          1/1     Running     0          3h47m
    rook-ceph-agent-w65x2                          1/1     Running     0          3h47m
    rook-ceph-agent-wbxv4                          1/1     Running     0          3h47m
    rook-ceph-mgr-a-77b8674677-zph5s               1/1     Running     0          3h44m
    rook-ceph-mon-a-578bcdc486-4nfxn               1/1     Running     0          3h45m
    rook-ceph-mon-b-7c5fdd6794-29frc               1/1     Running     0          3h45m
    rook-ceph-mon-c-7d79cf845c-tbdbf               1/1     Running     0          3h45m
    rook-ceph-operator-6dbdbc6b94-dsd6z            1/1     Running     0          3h48m
    rook-ceph-osd-0-7dd859cc77-42gj9               1/1     Running     0          3h43m
    rook-ceph-osd-1-7b48479788-8vq4m               1/1     Running     0          3h43m
    rook-ceph-osd-2-d95cb9479-fpbhd                1/1     Running     0          3h42m
    rook-ceph-osd-3-779699c4fd-82zrl               1/1     Running     0          3h43m
    rook-ceph-osd-4-5c87768ddf-wcsw4               1/1     Running     0          3h43m
    rook-ceph-osd-5-689d78db84-t28qk               1/1     Running     0          3h42m
    rook-ceph-osd-prepare-ai02-r4lg9               0/1     Completed   0          3h44m
    rook-ceph-osd-prepare-ai03-vx6nj               0/1     Completed   0          3h44m
    rook-ceph-osd-prepare-ai04-h69zf               0/1     Completed   0          3h44m
    rook-ceph-tools-7cf4cc7568-6lcgv               1/1     Running     0          6m23s
    rook-discover-flxm2                            1/1     Running     0          3h48m
    rook-discover-h7j2f                            1/1     Running     0          3h48m
    rook-discover-nwsm5                            1/1     Running     0          3h48m
    rook-discover-t6fl7                            1/1     Running     0          3h48m
    rook-discover-t6xgz                            1/1     Running     0          3h48m

其次看ceph status的状态需要是HEALTH：

    
    
    gemfield@master:~/rook-ceph/rook/cluster/examples/kubernetes/ceph$ kubectl -n rook-ceph exec -it rook-ceph-tools-7cf4cc7568-6lcgv bash
    [root@AI03 /]# ceph status
      cluster:
        id:     0cf36812-094c-4920-84aa-0c0099b01fe0
        health: HEALTH_WARN
                mon b is low on available space
     
      services:
        mon: 3 daemons, quorum a,b,c (age 3h)
        mgr: a(active, since 3h)
        osd: 6 osds: 6 up (since 3h), 6 in (since 3h)
     
      data:
        pools:   0 pools, 0 pgs
        objects: 0 objects, 0 B
        usage:   6.0 GiB used, 21 TiB / 21 TiB avail
        pgs:

然后创建 **[ Block
](https://link.zhihu.com/?target=https%3A//rook.io/docs/rook/master/ceph-
block.html) 、 [ Object
](https://link.zhihu.com/?target=https%3A//rook.io/docs/rook/master/ceph-
object.html) 、 [ Shared File System
](https://link.zhihu.com/?target=https%3A//rook.io/docs/rook/master/ceph-
filesystem.html) ； ** 最后创建Dashboard。

**2，如何重启Dashboard？**

Dashboard上enable一些功能后，通常需要重启Dashboard服务才能使用。使用下面的命令来重启Dashboard：

    
    
    #在toolbox容器里执行
    [root@AI03 /]# ceph mgr module disable dashboard
    [root@AI03 /]# ceph mgr module enable dashboard

##  **基础条款**

**1，需要osd、mon、mds、rbd、rgw、CephFS服务**

其中后三者分别提供block、object/gw、fs/shared fs服务。

**2，K8s化部署使用Rook**

其它情况可以使用官方的ceph-deploy或者docker方式。

**3，一个磁盘一个osd**

**4，Ceph的Dashboard用着还不错**

但dashboard上看性能数据需要安装prometheus和Grafana，并启用；

**5，部署完成后应该立刻做性能测试**

基础健康状态确认好，再应用上层业务。我用的机械硬盘，30个OSD测试的写入速度大概是70MB/s。

**6，注意检查有些Ceph host或者osd是不是down了**

有时候是因为宿主机上的磁盘设备号变了。

**7，Ceph的Pool（多租户）**

以pool为颗粒度，如果不创建/指定，则数据会存放在默认的pool里。创建pool需要设置pg的数量，一般来说每个OSD为100个PG，也可以按照如下规则配置：

    
    
    若少于5个OSD， 设置pg_num为128。
    5~10个OSD，设置pg_num为512。
    10~50个OSD，设置pg_num为4096。
    超过50个OSD，可以参考pgcalc计算。

Pool上还需要设置 **CRUSH Rules** 策略，这是data如何分布式存储的策略。

此外，针对pool，还可以调整POOL副本数量、删除POOL、设置POOL配额、重命名POOL、查看POOL状态信息。

**8，Ceph的backup & Restore **

Pool上有创建快照的功能。

**9，怎么提高ceph的写入速度？**

接入的服务越来越多，每秒钟需要写入的数据将从几十MB慢慢到1GB、10GB...集群如何扩展？

**10，Ceph的Pool有2种方式**

replicated和erasure两种，默认是replicated。replicated就是多重备份（官方建议是3），好处是数据更安全，功能更全面，坏处是消耗磁盘空间大，成本高；而erasure相当于RAID5，好处是节省空间，坏处是支持的操作有限。

**11，replicated的数量**

官方建议是3，但我觉得2也可以。并且replica=2节省空间、速度更快。

如果有25 OSDs ，每个对应一个4TB的磁盘。那么可用的pool的存储量为：

Raw size: 25*4 = 100TB  
replica=2 : 100/2 = 50TB  
replica=3 : 100/3 = 33.33TB

**12，Ceph可以提供NFS支持**

依赖NFS-Ganesha，并且要在Ceph中启用。

##  **高阶问题**

**1，使用CephFS的时候，速度奇慢无比。**

首先为什么会使用CephFS呢？因为CephFS可以被多个Pod挂载共享。当使用CephFS作为SC，然后通过k8s
PVC将存储挂载到Pod的目录上，在挂载的目录上使用dd命令进行写入测试：

    
    
    root@media-76d54565f5-dhc2w:/app/gemfield# dd if=/dev/zero of=gemfieldtest bs=500M count=1             
    1+0 records in
    1+0 records out
    524288000 bytes (524 MB, 500 MiB) copied, 14.1455 s, 37.1 MB/s

速度只有37.1MB/s，下面是当前Ceph集群上所用的

    
    
    gemfield@deepvac:~$ kubectl get pvc
    NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
    media            Bound    pvc-4828fa4e-de02-40a7-a972-64fef09f411c   18627Gi    RWX            csi-cephfs        24d
    
    gemfield@deepvac:~$ kubectl get sc
    NAME              PROVISIONER                     AGE
    csi-cephfs        rook-ceph.cephfs.csi.ceph.com   30d
    
    gemfield@deepvac:~$ kubectl describe sc csi-cephfs
    Name:            csi-cephfs
    IsDefaultClass:  No
    Annotations:     kubectl.kubernetes.io/last-applied-configuration={"apiVersion":"storage.k8s.io/v1","kind":"StorageClass","metadata":{"annotations":{},"name":"csi-cephfs"},"mountOptions":null,"parameters":{"clusterID":"rook-ceph","csi.storage.k8s.io/node-stage-secret-name":"rook-ceph-csi","csi.storage.k8s.io/node-stage-secret-namespace":"rook-ceph","csi.storage.k8s.io/provisioner-secret-name":"rook-ceph-csi","csi.storage.k8s.io/provisioner-secret-namespace":"rook-ceph","fsName":"myfs","pool":"myfs-data0"},"provisioner":"rook-ceph.cephfs.csi.ceph.com","reclaimPolicy":"Retain"}
    
    Provisioner:           rook-ceph.cephfs.csi.ceph.com
    Parameters:            clusterID=rook-ceph,csi.storage.k8s.io/node-stage-secret-name=rook-ceph-csi,csi.storage.k8s.io/node-stage-secret-namespace=rook-ceph,csi.storage.k8s.io/provisioner-secret-name=rook-ceph-csi,csi.storage.k8s.io/provisioner-secret-namespace=rook-ceph,fsName=myfs,pool=myfs-data0
    AllowVolumeExpansion:  <unset>
    MountOptions:          <none>
    ReclaimPolicy:         Retain
    VolumeBindingMode:     Immediate
    Events:                <none>
    
    gemfield@deepvac:~$ mount | grep kubelet | grep pvc | awk '{print $1}'
    ceph-fuse
    ceph-fuse
    ceph-fuse
    ceph-fuse
    ceph-fuse
    ceph-fuse

速度慢的原因在 [ https://  github.com/rook/rook/is  sues/3315
](https://link.zhihu.com/?target=https%3A//github.com/rook/rook/issues/3315) 和
[ https://  github.com/rook/rook/is  sues/3619
](https://link.zhihu.com/?target=https%3A//github.com/rook/rook/issues/3619)
已经有所描述，总而言之，就是：

1，如果Linux内核版本<4.17的话，只能使用ceph-fuse client，要想维持可观的磁盘IO，只能使用flexVolume：

    
    
        volumes:
        - name: image-store
        flexVolume:
            driver: ceph.rook.io/rook
            fsType: ceph
            options:
            fsName: myfs # name of the filesystem specified in the filesystem CRD.
            clusterNamespace: rook-ceph # namespace where the Rook cluster is deployed
            # by default the path is /, but you can override and mount a specific path of the filesystem by using the path attribute
            # the path must exist on the filesystem, otherwise mounting the filesystem at that path will fail
            # path: /some/path/inside/cephfs

2，如果Linux内核版本>= 4.17的话，可以使用kernel client，磁盘IO性能会大为改观（在Ubuntu 18.04
LTS上，如果要升级内核版本，可以使用下面的命令）：

    
    
    sudo apt install linux-generic-hwe-18.04

在升级完内核版本后，更改 [ https://  github.com/rook/rook/bl
ob/master/cluster/examples/kubernetes/ceph/csi/cephfs/storageclass.yaml#L31
](https://link.zhihu.com/?target=https%3A//github.com/rook/rook/blob/master/cluster/examples/kubernetes/ceph/csi/cephfs/storageclass.yaml%23L31)
：

    
    
    mounter: kernel

**重新创建SC、PVC，然后mount到Pod上** ，再进行dd命令的测试：

    
    
    root@media-759f9dd87-bbhhw:/app/gemfield# dd if=/dev/zero of=deleteme bs=10G count=1
    0+1 records in
    0+1 records out
    2147479552 bytes (2.1 GB, 2.0 GiB) copied, 2.24164 s, 958 MB/s
    
    
    root@media-759f9dd87-bbhhw:/app/gemfield# time cp deleteme deleteme2
    real    0m22.985s
    user    0m0.005s
    sys     0m2.725s

可见速度得到了无与伦比的增长。

**2，Ceph安装成功后，一段时间后会crash**

如果在一个子网里，有的宿主机可以访问公网，有的不能访问公网，这就会出现时间同步问题。可以安装ntp服务来解决这个问题：

1，在可以访问公网的机器上安装ntp服务

    
    
    sudo apt install ntp

2，修改ntp服务配置文件

    
    
    # /etc/ntp.conf, configuration for ntpd; see ntp.conf(5) for help
    
    driftfile /var/lib/ntp/ntp.drift
    
    # Leap seconds definition provided by tzdata
    leapfile /usr/share/zoneinfo/leap-seconds.list
    
    # Enable this if you want statistics to be logged.
    #statsdir /var/log/ntpstats/
    
    statistics loopstats peerstats clockstats
    filegen loopstats file loopstats type day enable
    filegen peerstats file peerstats type day enable
    filegen clockstats file clockstats type day enable
    
    # Specify one or more NTP servers.
    server 0.cn.pool.ntp.org
    server 1.cn.pool.ntp.org
    server 2.cn.pool.ntp.org
    server 3.cn.pool.ntp.org
    
    # Use servers from the NTP Pool Project. Approved by Ubuntu Technical Board
    # on 2011-02-08 (LP: #104525). See http://www.pool.ntp.org/join.html for
    # more information.
    pool 0.cn.pool.ntp.org iburst
    pool 1.cn.pool.ntp.org iburst
    pool 2.cn.pool.ntp.org iburst
    pool 3.cn.pool.ntp.org iburst
    
    # Use Ubuntu's ntp server as a fallback.
    pool ntp.ubuntu.com
    
    # Access control configuration; see /usr/share/doc/ntp-doc/html/accopt.html for
    # details.  The web page <http://support.ntp.org/bin/view/Support/AccessRestrictions>
    # might also be helpful.
    #
    # Note that "restrict" applies to both servers and clients, so a configuration
    # that might be intended to block requests from certain clients could also end
    # up blocking replies from your own upstream servers.
    
    # By default, exchange time with everybody, but don't allow configuration.
    restrict -4 default kod notrap nomodify nopeer noquery limited
    restrict -6 default kod notrap nomodify nopeer noquery limited
    
    # Local users may interrogate the ntp server more closely.
    restrict 127.0.0.1
    restrict ::1
    
    # Needed for adding pool entries
    restrict source notrap nomodify noquery
    
    # Clients from this (example!) subnet have unlimited access, but only if
    # cryptographically authenticated.
    #restrict 192.168.1.0 mask 255.255.255.0 trust
    
    
    # If you want to provide time to your local subnet, change the next line.
    # (Again, the address is an example only.)
    broadcast 192.168.1.255
    
    # If you want to listen to time broadcasts on your local subnet, de-comment the
    # next lines.  Please do this only if you trust everybody on the network!
    #disable auth
    #broadcastclient
    
    #Changes recquired to use pps synchonisation as explained in documentation:
    #http://www.ntp.org/ntpfaq/NTP-s-config-adv.htm#AEN3918
    
    #server 127.127.8.1 mode 135 prefer    # Meinberg GPS167 with PPS
    #fudge 127.127.8.1 time1 0.0042        # relative to PPS for my hardware
    
    #server 127.127.22.1                   # ATOM(PPS)
    #fudge 127.127.22.1 flag3 1            # enable PPS API

3，在其它宿主机上配置时间同步

修改的文件是timesyncd.conf，属于systemd。

    
    
    sudo vi /etc/systemd/timesyncd.conf
    
    #修改为以下内容，IP是前述配置了ntp server的
    [Time]
    NTP=192.168.1.93

4，使“时间同步”配置生效

    
    
    sudo systemctl restart systemd-timesyncd.service 
    sudo systemctl status systemd-timesyncd.service


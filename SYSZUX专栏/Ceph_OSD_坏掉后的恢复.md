##  **背景**

Ceph集群的一个宿主机因为意外断电，等到再次启动后，其上的一个OSD一直启动不了。日志显示：

    
    
    ......
    -2393> 2020-05-13 10:24:55.180 7f5d5677aa80 -1 Falling back to public interface
    -1754> 2020-05-13 10:25:07.419 7f5d5677aa80 -1 osd.2 875 log_to_monitors {default=true}
    -1425> 2020-05-13 10:25:07.803 7f5d48d7c700 -1 osd.2 875 set_numa_affinity unable to identify public interface 'eth0' numa node: (2) No such file or directory
    -2> 2020-05-13 10:25:23.731 7f5d4436d700 -1 rocksdb: submit_common error: Corruption: block checksum mismatch: expected 717694145, got 2263389519  in db/001499.sst offset 43727772 size 3899 code = 2 Rocksdb transaction: 
    Put( Prefix = P key = 0x000000000000044b'.0000000880.00000000000000017197' Value size = 183)
    Put( Prefix = P key = 0x000000000000044b'._info' Value size = 948)
    Delete( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00000000'x')
    Delete( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00080000'x')
    Delete( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00100000'x')
    Delete( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00180000'x')
    Delete( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00190000'x')
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00000000'x' Value size = 540)
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00080000'x' Value size = 537)
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00100000'x' Value size = 531)
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00180000'x' Value size = 80)
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff6f00190000'x' Value size = 7)
    Put( Prefix = O key = 0x7f800000000000000124b6c6ef217262'd_data.1a8008b735603.0000000000008028!='0xfffffffffffffffeffffffffffffffff'o' Value size = 1143)
    Put( Prefix = L key = 0x0000000000000011 Value size = 4135)
    Merge( Prefix = T key = 0x0000000000000001 Value size = 40)
        -1> 2020-05-13 10:25:23.735 7f5d4436d700 -1 /home/jenkins-build/build/workspace/ceph-build/ARCH/x86_64/AVAILABLE_ARCH/x86_64/AVAILABLE_DIST/centos7/DIST/centos7/MACHINE_SIZE/gigantic/release/14.2.9/rpm/el7/BUILD/ceph-14.2.9/src/os/bluestore/BlueStore.cc: In function 'void BlueStore::_kv_sync_thread()' thread 7f5d4436d700 time 2020-05-13 10:25:23.733456
    /home/jenkins-build/build/workspace/ceph-build/ARCH/x86_64/AVAILABLE_ARCH/x86_64/AVAILABLE_DIST/centos7/DIST/centos7/MACHINE_SIZE/gigantic/release/14.2.9/rpm/el7/BUILD/ceph-14.2.9/src/os/bluestore/BlueStore.cc: 11016: FAILED ceph_assert(r == 0)
    
     ceph version 14.2.9 (581f22da52345dba46ee232b73b990f06029a2a0) nautilus (stable)
     1: (ceph::__ceph_assert_fail(char const*, char const*, int, char const*)+0x14a) [0x56297aa20f7d]
     2: (()+0x4cb145) [0x56297aa21145]
     3: (BlueStore::_kv_sync_thread()+0x11c3) [0x56297af95233]
     4: (BlueStore::KVSyncThread::entry()+0xd) [0x56297afba3fd]
     5: (()+0x7e65) [0x7f5d537bfe65]
     6: (clone()+0x6d) [0x7f5d5268388d]
    
         0> 2020-05-13 10:25:23.735 7f5d4436d700 -1 *** Caught signal (Aborted) **
     in thread 7f5d4436d700 thread_name:bstore_kv_sync
    
     ceph version 14.2.9 (581f22da52345dba46ee232b73b990f06029a2a0) nautilus (stable)
     1: (()+0xf5f0) [0x7f5d537c75f0]
     2: (gsignal()+0x37) [0x7f5d525bb337]
     3: (abort()+0x148) [0x7f5d525bca28]
     4: (ceph::__ceph_assert_fail(char const*, char const*, int, char const*)+0x199) [0x56297aa20fcc]
     5: (()+0x4cb145) [0x56297aa21145]
     6: (BlueStore::_kv_sync_thread()+0x11c3) [0x56297af95233]
     7: (BlueStore::KVSyncThread::entry()+0xd) [0x56297afba3fd]
     8: (()+0x7e65) [0x7f5d537bfe65]
     9: (clone()+0x6d) [0x7f5d5268388d]
     NOTE: a copy of the executable, or `objdump -rdS <executable>` is needed to interpret this.

看起来这个原因是一个“rocksdb: submit_common error: Corruption: block checksum mismatch:
expected 717694145, got 2263389519 in db/001499.sst offset 43727772 size 3899
code = 2 Rocksdb transaction”，assert出错，OSD程序就一直启动不了。那么如何解决这个block mismatch问题呢？

##  **问题分析**

上面这个问题里的一个关键字是rocksdb，这是什么呢？Ceph的文件存储引擎以前是filestore，为了改善性能，如今改为了bluestore，而bluestore引擎的metadata就存放在rocksdb中。这说明：Ceph的文件存储引擎bluestore的元数据损坏了！

##  **解决步骤**

直接恢复是恢复不回来了，gemfield也不准备再深入debug了。于是准备删掉这个对应的OSD，然后再重新加回来。

**1，查看当前OSD的状态**

    
    
    [root@rook-ceph-tools-7bbsyszux-584k5 /]# ceph osd status
    +----+------+-------+-------+--------+---------+--------+---------+----------------+
    | id | host |  used | avail | wr ops | wr data | rd ops | rd data |     state      |
    +----+------+-------+-------+--------+---------+--------+---------+----------------+
    | 0  | ai05 |  299G | 3426G |    0   |     0   |    5   |   382k  |   exists,up    |
    | 1  | ai05 |  178G | 3547G |    0   |    18   |    2   |  1110k  |   exists,up    |
    | 2  |      |    0  |    0  |    0   |     0   |    0   |     0   | autoout,exists |
    | 3  | ai01 |  438G | 3287G |    0   |   763   |    7   |   708k  |   exists,up    |
    | 4  | ai03 |  217G | 3508G |    0   |   339   |    7   |  63.6k  |   exists,up    |
    | 5  | ai02 |  217G | 2576G |    1   |  10.9k  |    6   |   403k  |   exists,up    |
    | 6  | ai04 |  300G | 3425G |   15   |   100k  |    7   |   161k  |   exists,up    |
    | 7  | ai03 |  109G | 3616G |    0   |     0   |    0   |     0   |   exists,up    |
    | 8  | ai02 |  246G | 3479G |    1   |  23.6k  |    2   |   813k  |   exists,up    |
    | 9  | ai03 |  108G | 3617G |    0   |   944   |    5   |  84.0k  |   exists,up    |
    | 10 | ai03 |  136G | 3589G |    0   |   741   |    4   |   679k  |   exists,up    |
    | 11 | ai03 |  162G | 3563G |    0   |  22.2k  |    4   |   824k  |   exists,up    |
    | 12 | ai03 | 55.7G | 3670G |    0   |     0   |    2   |   952k  |   exists,up    |
    | 13 | ai01 |  194G | 3531G |    0   |   130k  |    3   |  37.9k  |   exists,up    |
    +----+------+-------+-------+--------+---------+--------+---------+----------------+
    

**2，把出问题的OSD标记为out**

    
    
    [root@rook-ceph-tools-7gemfield-584k5 /]# ceph osd out osd.2
    osd.2 is already out. 

其实已经out了。

**3，等待backfilling完成**

这是为了确保数据安全备份到其它OSD上。但是这里我们的OSD本来就回不来了，所以不等了。

**4，更新cluster.yaml**

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph device ls-by-host ai04
    DEVICE                    DEV DAEMONS EXPECTED FAILURE 
    ST4000DM004-2CV1_ZFN2AW5F sda osd.2     //挂掉了               
    ST4000DM004-2CV1_ZFN2AX5L sdc osd.6
    
    或者
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph device ls-by-daemon osd.2                          
    DEVICE                    HOST:DEV EXPECTED FAILURE 
    ST4000DM004-2CV1_ZFN2AW5F ai04:sda
    
    可以看到挂掉的OSD是sda，可以用下面的命令来佐证：
    
    gemfield@ai04:~$ sudo hdparm -I /dev/sda | grep ZFN2AW5F
            Serial Number:      ZFN2AW5F

**5，可以佐证下这个磁盘**

要细致，别删错硬盘。

    
    
    gemfield@ai04:~$ sudo hdparm -I /dev/sda | grep ZFN2AW5F
            Serial Number:      ZFN2AW5F

**6，purge掉osd.2**

得加上--force

    
    
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# ceph osd purge osd.2 --force

**7，查看当前状态**

    
    
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# ceph osd status
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | id | host |  used | avail | wr ops | wr data | rd ops | rd data |   state   |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | 0  | ai05 |  298G | 3427G |    0   |   339   |    0   |     0   | exists,up |
    | 1  | ai05 |  175G | 3550G |    0   |     0   |    1   |    72   | exists,up |
    | 3  | ai01 |  435G | 3290G |    1   |  13.7k  |    1   |  19.5k  | exists,up |
    | 4  | ai03 |  217G | 3508G |    0   |     0   |    0   |     0   | exists,up |
    | 5  | ai02 |  217G | 2576G |    0   |     0   |    0   |     0   | exists,up |
    | 6  | ai04 |  300G | 3425G |    0   |     0   |    0   |     0   | exists,up |
    | 7  | ai03 |  109G | 3616G |    0   |   370   |    0   |    20   | exists,up |
    | 8  | ai02 |  246G | 3479G |    0   |  22.7k  |    0   |     0   | exists,up |
    | 9  | ai03 |  109G | 3616G |    0   |     0   |    0   |     0   | exists,up |
    | 10 | ai03 |  135G | 3590G |    0   |     0   |    0   |     0   | exists,up |
    | 11 | ai03 |  162G | 3563G |    0   |     0   |    0   |     0   | exists,up |
    | 12 | ai03 | 55.4G | 3670G |    0   |     0   |    0   |     0   | exists,up |
    | 13 | ai01 |  197G | 3528G |    0   |  4557   |    0   |     0   | exists,up |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+

**8，清除OSD的Pod**

因为我设置的removeOSDsIfOutAndSafeToRemove: false，所以坏掉的OSD不会被自动删除，所以我手动清除掉rook-ceph-
osd-2：

    
    
    (base) gemfield@ThinkPad-X1C:~/github/ai1_gemfield_org/mlab$ kubectl -n rook-ceph delete deployment rook-ceph-osd-2
    deployment.apps "rook-ceph-osd-2" deleted

**9，彻底清理掉sda**

    
    
    gemfield@ai04:~$ DISK="/dev/sda"
    gemfield@ai04:~$ sudo sgdisk --zap-all $DISK
    gemfield@ai04:~$ sudo dd if=/dev/zero of="$DISK" bs=1M count=100 oflag=direct,dsync
    
    gemfield@ai04:~$ ls /dev/mapper/ceph-*
    /dev/mapper/ceph--971efece--8880--4e81--90c6--621493c66294-osd--data--7775b10e--7a0d--4ddd--aaf7--74c4498552ff
    /dev/mapper/ceph--a7d7b063--7092--4698--a832--1cdd1285acbd-osd--data--ec2df8ee--0a7a--407f--afe3--41d045e889a9
    
    #清理掉lvm的残余
    gemfield@ai04:~$ sudo dmsetup remove /dev/mapper/ceph--a7d7b063--7092--4698--a832--1cdd1285acbd-osd--data--ec2df8ee--0a7a--407f--afe3--41d045e889a9
    
    #查看还剩余一个
    gemfield@ai04:~$ ls /dev/mapper/ceph-*
    /dev/mapper/ceph--971efece--8880--4e81--90c6--621493c66294-osd--data--7775b10e--7a0d--4ddd--aaf7--74c4498552ff
    
    #确保/dev下还剩一个
    gemfield@ai04:~$ ls -l /dev/ceph-*
    total 0
    lrwxrwxrwx 1 root root 7 May 15 20:14 osd-data-7775b10e-7a0d-4ddd-aaf7-74c4498552ff -> ../dm-0

**10，重新把ai04的sda加回去**

更新cluster.yaml：

    
    
        - name: "ai04"
          devices: # specific devices to use for storage can be specified for each node
          - name: "sda"
          - name: "sdc"

**11，查看最终状态**

osd-prepare完成后，就可以看到团员的OSD家族的状态了：

    
    
    [root@rook-ceph-tools-7bb5797c8-ns4bw /]# ceph osd status
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | id | host |  used | avail | wr ops | wr data | rd ops | rd data |   state   |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | 0  | ai05 |  298G | 3427G |    0   |     0   |    0   |     0   | exists,up |
    | 1  | ai05 |  176G | 3549G |    0   |     0   |    1   |    72   | exists,up |
    | 2  | ai04 | 1600M | 3724G |    0   |     0   |    0   |     0   | exists,up |
    | 3  | ai01 |  435G | 3290G |    1   |  44.3k  |    0   |     0   | exists,up |
    | 4  | ai03 |  217G | 3508G |    1   |  9830   |    0   |     0   | exists,up |
    | 5  | ai02 |  217G | 2576G |    6   |  31.6k  |    2   |  29.1k  | exists,up |
    | 6  | ai04 |  300G | 3425G |    0   |  14.1k  |    0   |     0   | exists,up |
    | 7  | ai03 |  109G | 3616G |    0   |    38   |    0   |    20   | exists,up |
    | 8  | ai02 |  246G | 3479G |    0   |     0   |    0   |     0   | exists,up |
    | 9  | ai03 |  109G | 3616G |    0   |     0   |    0   |     0   | exists,up |
    | 10 | ai03 |  135G | 3590G |    0   |     0   |    0   |     0   | exists,up |
    | 11 | ai03 |  163G | 3562G |    0   |   124k  |    0   |     0   | exists,up |
    | 12 | ai03 | 55.4G | 3670G |    0   |     0   |    0   |     0   | exists,up |
    | 13 | ai01 |  197G | 3528G |    0   |     0   |    0   |     0   | exists,up |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    

##  **总结**

我现在看着这个恢复了的OSD，就像我看着你，满怀喜悦。


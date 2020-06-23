##  **背景**

最新在以PVC挂载的方式在使用CephFS，流程上就是CephFS -> SC -> PVC -> Volume ->
directory。其中：myfs、SC、PVC的定义使用：

[ Gemfield：使用Rook 1.3.3 部署Ceph 14.2.9
](https://zhuanlan.zhihu.com/p/138991974)

出现的问题就是，读写小文件的性能严重低于预期。我们就以拷贝文件为例：

    
    
    #################大文件
    root@gemfieldhome-5ff6d79c75-2vq4g:/home/gemfield/Pictures# ls -lh /opt/gemfield/bigfile.zip
    -rwxr-xr-x 1 root root 1.1G May 11 10:13 /opt/gemfield/bigfile.zip
    
    root@gemfieldhome-5ff6d79c75-2vq4g:/home/gemfield/Pictures# time cp /opt/gemfield/bigfile.zip tmp/
    
    real    0m11.581s
    user    0m0.000s
    sys     0m1.427s
    
    ##################小文件
    root@gemfieldhome-5ff6d79c75-2vq4g:/home/gemfield/Pictures# du -sh small_files
    696M    small_files
    
    root@gemfieldhome-5ff6d79c75-2vq4g:/home/gemfield/Pictures# find small_files/ -type f | wc -l
    9999
    
    root@gemfieldhome-5ff6d79c75-2vq4g:/home/gemfield/Pictures# time cp -r small_files/ tmp/
    
    real    4m39.327s
    user    0m0.256s
    sys     0m3.614s

可以看到，如果是大文件，则一秒钟至少可以进行100MB的读+写；如果是小文件，则每秒钟只能进行2MB的读+写。

在开始进行性能debug之前，我们需要先掌握一些Ceph环境中经常使用的命令。

##  **环境检查的常用命令**

**1，ceph集群状态**

    
    
    [root@rook-ceph-tools-7bb5797c8-8tqv4 /]# ceph -s
      cluster:
        id:     f4c18790-b9be-4bcb-819a-92f3fb3f9ab9
        health: HEALTH_WARN
                1 MDSs report oversized cache
                Degraded data redundancy: 481323/32360784 objects degraded (1.487%), 2 pgs degraded, 2 pgs undersized
                5 daemons have recently crashed
     
      services:
        mon: 3 daemons, quorum a,b,c (age 47m)
        mgr: a(active, since 46m)
        mds: myfs:1 {0=myfs-a=up:active} 1 up:standby-replay
        osd: 14 osds: 14 up (since 47m), 14 in (since 42h); 12 remapped pgs
        rgw: 1 daemon active (my.store.a)
     
      data:
        pools:   10 pools, 176 pgs
        objects: 10.79M objects, 170 GiB
        usage:   2.3 TiB used, 48 TiB / 50 TiB avail
        pgs:     481323/32360784 objects degraded (1.487%)
                 2395149/32360784 objects misplaced (7.401%)
                 164 active+clean
                 10  active+remapped+backfill_wait
                 2   active+undersized+degraded+remapped+backfilling
     
      io:
        client:   13 MiB/s rd, 625 KiB/s wr, 628 op/s rd, 6 op/s wr
        recovery: 66 KiB/s, 8 objects/s

唉？问题十联：

  1. 为啥集群状态会是HEALTH_WARN？ 
  2. 为啥会有1 MDSs report oversized cache？ 
  3. 为啥会有Degraded data redundancy？ 
  4. 为啥会有5 daemons have recently crashed？ 
  5. 为啥会有objects degraded？ 
  6. 为啥会有objects misplaced？ 
  7. 为啥会有10个PG是active+remapped+backfill_wait？ 
  8. 为啥会有2个PG是active+undersized+degraded+remapped+backfilling？ 
  9. client的io速度是13 MiB/s rd, 625 KiB/s wr, 628 op/s rd, 6 op/s wr，正常吗？ 
  10. 什么是recovery？速度是66 KiB/s, 8 objects/s正常吗？ 

pg的状态我来解释下，首先pg有个replica的配置，默认是size = 3, min_size =
2。也就是说正常是3份，最小不能小于2。也就是正常情况下，每个PG的内容会在3个OSD中各有一份。下面就来说下各自的含义：

  1. active_clean是正常的状态； 
  2. remapped是该pg； 
  3. Degraded是说，一个OSD挂掉了，就把这个OSD上所有的PG都标记为degraded； 
  4. unsersized是说，一个PG的内容没有保存在3个osd中了，只保存在2个中，一般和degraded相关； 
  5. peered是说，一个PG的内容只保存在1个OSD中了，差的更多；这种状态下，该PG就停止提供服务了，除非状态恢复（或者手工更改min_size）； 
  6. active+clean+scrubbing+deep是说正在对PG做一致性检查； 

**2，ceph集群健康详情**

    
    
    [root@rook-ceph-tools-7bb5797c8-8tqv4 /]# ceph health detail
    HEALTH_WARN 1 MDSs report oversized cache; Degraded data redundancy: 477653/32360814 objects degraded (1.476%), 2 pgs degraded, 2 pgs undersized; 5 daemons have recently crashed; 1/3 mons down, quorum a,c
    MDS_CACHE_OVERSIZED 1 MDSs report oversized cache
        mdsmyfs-b(mds.0): MDS cache is too large (2GB/1GB); 0 inodes in use by clients, 0 stray files
    PG_DEGRADED Degraded data redundancy: 477653/32360814 objects degraded (1.476%), 2 pgs degraded, 2 pgs undersized
        pg 10.6 is stuck undersized for 3198.385925, current state active+undersized+degraded+remapped+backfilling, last acting [10,8]
        pg 10.10 is stuck undersized for 5718.817092, current state active+undersized+degraded+remapped+backfilling, last acting [5,0]
    RECENT_CRASH 5 daemons have recently crashed
        mgr.a crashed on host rook-ceph-mgr-a-647c856d65-9qrg6 at 2020-05-12 09:20:34.086438Z
        osd.2 crashed on host rook-ceph-osd-2-fbcd964c7-cdm75 at 2020-05-11 20:59:55.168534Z
        osd.2 crashed on host rook-ceph-osd-2-fbcd964c7-cdm75 at 2020-05-12 17:21:57.126603Z
        osd.2 crashed on host rook-ceph-osd-2-fbcd964c7-cdm75 at 2020-05-12 01:46:20.945849Z
        osd.6 crashed on host rook-ceph-osd-6-75db64bd55-vbpfm at 2020-05-12 04:33:05.333852Z
    MON_DOWN 1/3 mons down, quorum a,c
        mon.b (rank 1) addr [v2:10.106.45.244:3300/0,v1:10.106.45.244:6789/0] is down (out of quorum)

这里的问题总结下来，和ceph -s不一样的信息就是：

  1. 为什么会有MDS cache is too large (2GB/1GB)？ 
  2. 日志“0 inodes in use by clients, 0 stray files”表示什么意思，正常吗？ 
  3. ceph -s中说的5个daemons最近crash，这里指出了具体的时间，但是为什么会crash呢？ 
  4. mon.b会什么会down，out of quorum又是指的什么？ 

偶尔还出出现这样的日志：

    
    
    OSD_SLOW_PING_TIME_FRONT Long heartbeat ping times on front interface seen, longest is 1086.243 msec
        Slow heartbeat ping on front interface from osd.9 to osd.12 1086.243 msec

偶尔还会出现这样的日志：

    
    
    1 pools have many more objects per pg than average
    或者
    1 MDSs report oversized cache
    或者
    1 MDSs report slow metadata IOs
    或者
    1 MDSs report slow requests
    或者
    4 slow ops, oldest one blocked for 295 sec, daemons [osd.0,osd.11,osd.3,osd.6] have slow ops.
    

集群断电再启动后：

    
    
      data:
        pools:   10 pools, 654 pgs
        objects: 5.76M objects, 122 GiB
        usage:   789 GiB used, 20 TiB / 21 TiB avail
        pgs:     49.541% pgs unknown
                 50.459% pgs not active
                 324 unknown
                 222 peering
                 108 remapped+peering

**3，OSD状态**

    
    
    [root@rook-ceph-tools-7bb5797c8-8tqv4 /]# ceph osd status
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | id | host |  used | avail | wr ops | wr data | rd ops | rd data |   state   |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+
    | 0  | ai05 |  241G | 3484G |    0   |     0   |   30   |  1633k  | exists,up |
    | 1  | ai05 |  168G | 3557G |    0   |   837   |   29   |  1603k  | exists,up |
    | 2  | ai04 |  149G | 3576G |    1   |   276k  |   13   |  3776k  | exists,up |
    | 3  | ai01 |  403G | 3322G |    0   |    60   |   36   |  2464k  | exists,up |
    | 4  | ai03 |  168G | 3557G |    0   |   232   |   48   |  3584k  | exists,up |
    | 5  | ai02 |  192G | 2602G |    0   |     0   |   44   |  2277k  | exists,up |
    | 6  | ai04 |  236G | 3489G |    0   |   819   |   35   |  1520k  | exists,up |
    | 7  | ai03 | 96.3G | 3629G |    1   |   409k  |   33   |  3108k  | exists,up |
    | 8  | ai02 |  239G | 3486G |    1   |     0   |   29   |  2016k  | exists,up |
    | 9  | ai03 |  125G | 3600G |    0   |     0   |   26   |  1279k  | exists,up |
    | 10 | ai03 |  120G | 3605G |    0   |     0   |   43   |  5284k  | exists,up |
    | 11 | ai03 |  144G | 3581G |    0   |  1184   |   37   |  1733k  | exists,up |
    | 12 | ai03 | 50.7G | 3675G |    0   |     0   |   32   |  4856k  | exists,up |
    | 13 | ai01 | 83.8G | 3642G |    0   |  7372   |    9   |   858k  | exists,up |
    +----+------+-------+-------+--------+---------+--------+---------+-----------+

这里的问题就是：

  1. wr ops是0和1代表什么意思呢？ 
  2. wr data代表什么？ 
  3. rd ops代表什么？ 
  4. rd data 代表什么？ 

**4，查看存储使用量**

整体的：

    
    
    [root@rook-ceph-tools-7bb5797c8-8tqv4 /]# ceph df
    RAW STORAGE:
        CLASS     SIZE       AVAIL      USED        RAW USED     %RAW USED 
        hdd       50 TiB     48 TiB     2.3 TiB      2.4 TiB          4.73 
        TOTAL     50 TiB     48 TiB     2.3 TiB      2.4 TiB          4.73 
     
    POOLS:
        POOL                            ID     STORED      OBJECTS     USED        %USED     MAX AVAIL 
        replicapool                      1     930 MiB       1.23k     2.9 GiB         0        14 TiB 
        my-store.rgw.control             2         0 B           8         0 B         0        14 TiB 
        my-store.rgw.meta                3     1.2 KiB           7     1.1 MiB         0        14 TiB 
        my-store.rgw.log                 4        96 B         211     384 KiB         0        14 TiB 
        my-store.rgw.buckets.index       5         0 B           1         0 B         0        14 TiB 
        my-store.rgw.buckets.non-ec      6         0 B           0         0 B         0        14 TiB 
        .rgw.root                        7     3.7 KiB          16     2.8 MiB         0        14 TiB 
        my-store.rgw.buckets.data        8     190 KiB           2     768 KiB         0        14 TiB 
        myfs-metadata                    9     258 MiB     175.61k     543 MiB         0        14 TiB 
        myfs-data0                      10     182 GiB      10.61M     2.3 TiB      5.18        14 TiB

分OSD的：

    
    
    [root@rook-ceph-tools-7bb5797c8-8tqv4 /]# ceph osd df tree
    ID  CLASS WEIGHT   REWEIGHT SIZE    RAW USE DATA    OMAP    META    AVAIL   %USE  VAR  PGS STATUS TYPE NAME      
     -1       50.03192        -  50 TiB 2.4 TiB 2.3 TiB  16 GiB  43 GiB  48 TiB  4.73 1.00   -        root default   
     -5        7.27737        - 7.3 TiB 488 GiB 478 GiB 2.2 GiB 7.6 GiB 6.8 TiB  6.55 1.39   -            host ai01  
      3   hdd  3.63869  1.00000 3.6 TiB 404 GiB 397 GiB 858 MiB 6.0 GiB 3.2 TiB 10.84 2.29  49     up         osd.3  
     13   hdd  3.63869  1.00000 3.6 TiB  84 GiB  81 GiB 1.3 GiB 1.6 GiB 3.6 TiB  2.25 0.48  43     up         osd.13 
     -9        6.36768        - 6.4 TiB 431 GiB 421 GiB 3.3 GiB 6.8 GiB 5.9 TiB  6.61 1.40   -            host ai02  
      5   hdd  2.72899  1.00000 2.7 TiB 192 GiB 188 GiB 1.3 GiB 3.0 GiB 2.5 TiB  6.87 1.45  30     up         osd.5  
      8   hdd  3.63869  1.00000 3.6 TiB 239 GiB 233 GiB 2.0 GiB 3.8 GiB 3.4 TiB  6.42 1.36  63     up         osd.8  
    -11       21.83212        -  22 TiB 706 GiB 687 GiB 4.9 GiB  13 GiB  21 TiB  3.16 0.67   -            host ai03  
      4   hdd  3.63869  1.00000 3.6 TiB 168 GiB 165 GiB 843 MiB 2.7 GiB 3.5 TiB  4.51 0.96  26     up         osd.4  
      7   hdd  3.63869  1.00000 3.6 TiB  96 GiB  94 GiB 659 MiB 1.7 GiB 3.5 TiB  2.59 0.55  27     up         osd.7  
      9   hdd  3.63869  1.00000 3.6 TiB 126 GiB 123 GiB 512 MiB 2.1 GiB 3.5 TiB  3.38 0.72  24     up         osd.9  
     10   hdd  3.63869  1.00000 3.6 TiB 120 GiB 118 GiB 1.0 GiB 1.7 GiB 3.5 TiB  3.23 0.68  26     up         osd.10 
     11   hdd  3.63869  1.00000 3.6 TiB 144 GiB 141 GiB 690 MiB 2.3 GiB 3.5 TiB  3.87 0.82  29     up         osd.11 
     12   hdd  3.63869  1.00000 3.6 TiB  51 GiB  47 GiB 1.3 GiB 2.7 GiB 3.6 TiB  1.36 0.29  22     up         osd.12 
     -7        7.27737        - 7.3 TiB 386 GiB 376 GiB 3.3 GiB 7.5 GiB 6.9 TiB  5.18 1.10   -            host ai04  
      2   hdd  3.63869  1.00000 3.6 TiB 150 GiB 144 GiB 1.4 GiB 3.9 GiB 3.5 TiB  4.01 0.85  45     up         osd.2  
      6   hdd  3.63869  1.00000 3.6 TiB 237 GiB 231 GiB 1.9 GiB 3.6 GiB 3.4 TiB  6.36 1.35  47     up         osd.6  
     -3        7.27737        - 7.3 TiB 410 GiB 400 GiB 2.1 GiB 7.9 GiB 6.9 TiB  5.50 1.16   -            host ai05  
      0   hdd  3.63869  1.00000 3.6 TiB 241 GiB 235 GiB 1.1 GiB 5.2 GiB 3.4 TiB  6.48 1.37  56     up         osd.0  
      1   hdd  3.63869  1.00000 3.6 TiB 168 GiB 165 GiB 1.0 GiB 2.7 GiB 3.5 TiB  4.52 0.96  39     up         osd.1  
                          TOTAL  50 TiB 2.4 TiB 2.3 TiB  16 GiB  43 GiB  48 TiB  4.73                                
    MIN/MAX VAR: 0.29/2.29  STDDEV: 2.36

查看OSD的性能：

    
    
    [root@rook-ceph-tools-7bb5797c8-df9tk /]# ceph osd perf
    osd commit_latency(ms) apply_latency(ms) 
     13                 55                55 
     12                326               326 
     11                 32                32 
     10                 91                91 
      3                 32                32 
      2                101               101 
      1                 44                44 
      0                 76                76 
      4                 16                16 
      5                 21                21 
      6                 31                31 
      7                 40                40 
      8                 43                43 
      9                 28                28

设置OSD的backfill线程（用于调整速度），一个是--osd-max-backfills，一个是--osd-recovery-max-active：

    
    
    # 10 as default
    [root@rook-ceph-tools-7bb5797c8-584k5 ~]# ceph tell 'osd.*' injectargs '--osd-max-backfills 16'
    osd.0: osd_max_backfills = '16' 
    osd.1: osd_max_backfills = '16' 
    Error ENXIO: problem getting command descriptions from osd.2
    osd.2: problem getting command descriptions from osd.2
    osd.3: osd_max_backfills = '16' 
    osd.4: osd_max_backfills = '16' 
    osd.5: osd_max_backfills = '16' 
    osd.6: osd_max_backfills = '16' 
    osd.7: osd_max_backfills = '16' 
    osd.8: osd_max_backfills = '16' 
    osd.9: osd_max_backfills = '16' 
    osd.10: osd_max_backfills = '16' 
    osd.11: osd_max_backfills = '16' 
    osd.12: osd_max_backfills = '16' 
    osd.13: osd_max_backfills = '16'
    
    #15 as default
    [root@rook-ceph-tools-7bb5797c8-584k5 ~]# ceph tell osd.* injectargs '--osd-recovery-max-active 30'
    osd.0: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.1: osd_recovery_max_active = '30' (not observed, change may require restart) 
    Error ENXIO: problem getting command descriptions from osd.2
    osd.2: problem getting command descriptions from osd.2
    osd.3: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.4: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.5: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.6: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.7: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.8: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.9: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.10: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.11: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.12: osd_recovery_max_active = '30' (not observed, change may require restart) 
    osd.13: osd_recovery_max_active = '30' (not observed, change may require restart)

设置mds cache limit：

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph config get mds.1 mds_cache_memory_limit
    2147483648
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph config set mds.0 mds_cache_memory_limit 8589934592

**5，rados命令**

rados使用量

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# rados df
    POOL_NAME                      USED  OBJECTS CLONES   COPIES MISSING_ON_PRIMARY UNFOUND DEGRADED   RD_OPS      RD   WR_OPS      WR USED COMPR UNDER COMPR 
    .rgw.root                   2.8 MiB       16      0       48                  0       0        0      245 245 KiB       32  23 KiB        0 B         0 B 
    my-store.rgw.buckets.data   2.1 MiB        6      0       18                  0       0        0       31 393 KiB      120 398 KiB        0 B         0 B 
    my-store.rgw.buckets.index      0 B        1      0        3                  0       0        0   176767 176 MiB       39  25 KiB        0 B         0 B 
    my-store.rgw.buckets.non-ec     0 B        0      0        0                  0       0        0        0     0 B        0     0 B        0 B         0 B 
    my-store.rgw.control            0 B        8      0       24                  0       0        0        0     0 B        0     0 B        0 B         0 B 
    my-store.rgw.log            384 KiB      211      0      633                  0       0       13   324349 316 MiB   222756 9.9 MiB        0 B         0 B 
    my-store.rgw.meta           1.1 MiB        7      0       21                  0       0        0     9192 8.5 MiB       72  28 KiB        0 B         0 B 
    myfs-data0                  2.3 TiB 10642439      0 31927317                  0       0   384586 12231654 430 GiB 34392611 269 GiB        0 B         0 B 
    myfs-metadata               714 MiB   175610      0   526830                  0       0        0 26197439 1.6 TiB  2472174  83 GiB        0 B         0 B 
    replicapool                 3.1 GiB     1252      0     3756                  3       0        4    39378 299 MiB   174349 2.3 GiB        0 B         0 B 
    
    total_objects    10819550
    total_used       2.4 TiB
    total_avail      48 TiB
    total_space      50 TiB

这里的RD_OPS、RD、WR、WR_OPS是什么呢？

**6，查看和设置pool的pg number**

    
    
    #查看所有的 pool
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool ls
    gemfield
    my-store.rgw.control
    my-store.rgw.meta
    my-store.rgw.log
    my-store.rgw.buckets.index
    my-store.rgw.buckets.non-ec
    .rgw.root
    my-store.rgw.buckets.data
    myfs-metadata
    myfs-data0
    
    
    #查看，pool的name是myfs-data0
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool get myfs-data0 pg_num
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool get myfs-data0 pgp_num
    
    #设置
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool set myfs-data0 pg_num 512
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool set myfs-data0 pgp_num 512

注意，myfs-metadata pool是myfs-data0 配套的metadata
pool，因为是存放metadata的，因此pg_num不用设置很大。

骚操作之如何删掉一个pool？

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool delete replicapool 
    Error EPERM: WARNING: this will *PERMANENTLY DESTROY* all data stored in pool replicapool.  If you are *ABSOLUTELY CERTAIN* that is what you want, pass the pool name *twice*, followed by --yes-i-really-really-mean-it
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool delete replicapool replicapool --yes-i-really-really-mean-it
    

**7，查看pg的状态**

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph pg dump
    dumped all
    version 23011
    stamp 2020-05-14 08:33:34.980295
    last_osdmap_epoch 0
    last_pg_scan 0
    PG_STAT OBJECTS MISSING_ON_PRIMARY DEGRADED MISPLACED UNFOUND BYTES     OMAP_BYTES* OMAP_KEYS* LOG  DISK_LOG STATE                                             STATE_STAMP                VERSION     REPORTED     UP        UP_PRIMARY ACTING    ACTING_PRIMARY LAST_SCRUB  SCRUB_STAMP                LAST_DEEP_SCRUB DEEP_SCRUB_STAMP           SNAPTRIMQ_LEN 
    10.1f7    21233                  0        0         0       0 364965473           0          0 3939     3939                                      active+clean 2020-05-14 02:01:56.728098 2147'735639 2154:1321620   [5,7,3]          5   [5,7,3]              5   196'19065 2020-05-10 23:59:26.930129             0'0 2020-05-08 11:32:53.053002             0 
    10.1f6    21229                  0        0     21221       0 381608041           0          0 3927     3927                     active+remapped+backfill_wait 2020-05-14 02:05:55.228361 2147'731327 2154:1130882 [11,13,8]         11  [11,8,3]             11   196'19403 2020-05-10 22:31:01.046904             0'0 2020-05-08 11:32:53.053002             0
    ......
    10 10877253 0 789466 2011421 0 190277360663         0      0 2026821 2026821 
    9    175940 0      0       0 0    150881406 430127204 931016   97424   97424 
    8         6 0      1       0 0       405913         0      0       0       0 
    7        16 0      0       0 0         3826         0      0     535     535 
    6         0 0      0       0 0            0         0      0       0       0 
    5         1 0      0       0 0            0         0      0      46      46 
    1      1213 0     94       0 0   2569568465       189     17 1625497 1625497 
    2         8 0      0       0 0            0         0      0    1922    1922 
    3         7 0      0       0 0         1236         0      0      28      28 
    4       211 0      0       0 0           96         0      0   24510   24510 
                                                                                  
    sum 11054633 0 789561 2011421 0 192937899552 430127389 931033 3745585 3745585 
    OSD_STAT USED    AVAIL   USED_RAW TOTAL   HB_PEERS                      PG_SUM PRIMARY_PG_SUM 
    11       145 GiB 3.5 TiB  149 GiB 3.6 TiB      [0,1,3,4,5,6,8,10,12,13]    151             90 
    4        182 GiB 3.5 TiB  186 GiB 3.6 TiB       [0,1,3,5,6,7,8,9,10,13]    197             74 
    12        48 GiB 3.6 TiB   52 GiB 3.6 TiB       [0,1,3,5,6,7,8,9,11,13]    111             59 
    3        436 GiB 3.2 TiB  444 GiB 3.6 TiB [0,1,4,5,6,7,8,9,10,11,12,13]    409            103 
    1        162 GiB 3.5 TiB  165 GiB 3.6 TiB [0,3,4,5,6,7,8,9,10,11,12,13]    260             87 
    5        193 GiB 2.5 TiB  197 GiB 2.7 TiB   [0,1,3,4,6,7,9,10,11,12,13]    258            100 
    0        252 GiB 3.4 TiB  257 GiB 3.6 TiB [1,3,4,5,6,7,8,9,10,11,12,13]    362             89 
    6        235 GiB 3.4 TiB  241 GiB 3.6 TiB [0,1,3,4,5,7,8,9,10,11,12,13]    374             88 
    8        217 GiB 3.4 TiB  223 GiB 3.6 TiB   [0,1,3,4,6,7,9,10,11,12,13]    394             90 
    13       102 GiB 3.5 TiB  106 GiB 3.6 TiB  [0,1,3,4,5,6,7,8,9,10,11,12]    270            104 
    7         97 GiB 3.5 TiB   99 GiB 3.6 TiB      [0,1,3,5,6,8,9,10,12,13]    147             77 
    9         97 GiB 3.5 TiB   99 GiB 3.6 TiB      [0,1,3,5,6,7,8,10,12,13]    160             99 
    10       121 GiB 3.5 TiB  124 GiB 3.6 TiB       [0,1,3,5,6,7,8,9,11,13]    207             71 
    sum      2.2 TiB  44 TiB  2.3 TiB  46 TiB                                                     
    
    * NOTE: Omap statistics are gathered during deep scrub and may be inaccurate soon afterwards depending on utilisation. See http://docs.ceph.com/docs/master/dev/placement-group/#omap-statistics for further details.

这里的HB_PEERS、PG_SUM、PRIMARY_PG_SUM是什么呢？

要修复pg，可以使用命令：

    
    
    #假设pg是1.0
    gemfield@ThinkPad-X1C:~$ ceph pg repair 1.0

##  **性能测试**

**1，dd**

使用dd命令进行读和写的测试：

    
    
    #
    dd if=/dev/zero of=gemfield bs=1G count=1 oflag=direct
    dd if=/dev/zero of=gemfield bs=1M count=1000 oflag=direct
    
    #
    dd if=gemfield of=/dev/null iflag=direct bs=1M count=1000

**2，网络**

使用iperf3工具来测试网络的状态：

    
    
    #iperf3 -s on ai2.gemfield.org
    gemfield@ai01:~$ iperf3 -c ai2.gemfield.org
    Connecting to host ai2.gemfield.org, port 5201
    [  5] local 192.168.0.114 port 54898 connected to 192.168.0.180 port 5201
    [ ID] Interval           Transfer     Bitrate         Retr  Cwnd
    [  5]   0.00-1.00   sec   112 MBytes   938 Mbits/sec    0    506 KBytes       
    [  5]   1.00-2.00   sec   112 MBytes   937 Mbits/sec    0    506 KBytes       
    [  5]   2.00-3.00   sec   111 MBytes   927 Mbits/sec    0    530 KBytes       
    [  5]   3.00-4.00   sec   111 MBytes   933 Mbits/sec    0    530 KBytes       
    [  5]   4.00-5.00   sec   112 MBytes   939 Mbits/sec    0    530 KBytes       
    [  5]   5.00-6.00   sec   111 MBytes   929 Mbits/sec    0    530 KBytes       
    [  5]   6.00-7.00   sec   110 MBytes   926 Mbits/sec    0    588 KBytes       
    [  5]   7.00-8.00   sec   111 MBytes   932 Mbits/sec    0    588 KBytes       
    [  5]   8.00-9.00   sec   111 MBytes   935 Mbits/sec    0    588 KBytes       
    [  5]   9.00-10.00  sec   111 MBytes   931 Mbits/sec    0    615 KBytes       
    - - - - - - - - - - - - - - - - - - - - - - - - -
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec  1.09 GBytes   933 Mbits/sec    0             sender
    [  5]   0.00-10.00  sec  1.08 GBytes   930 Mbits/sec                  receiver
    
    iperf Done.

##  使用rados进行性能测试

**1，写入的性能测试**

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# ceph osd pool create gemfield 32 32
    pool 'gemfield' created
    
    #specify --no-cleanup, because we need test read later
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# rados bench -p gemfield 10 write --no-cleanup    
    hints = 1
    Maintaining 16 concurrent writes of 4194304 bytes to objects of size 4194304 for up to 10 seconds or 0 objects
    Object prefix: benchmark_data_rook-ceph-tools-7bb5797c8-584_1605810
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        16         0         0         0           -           0
        2      16        22         6    11.999        12    0.222219      1.0085
        3      16        22         6   7.99923         0           -      1.0085
        4      16        22         6    5.9994         0           -      1.0085
        5      16        24         8   6.39934   2.66667     4.71792     1.87322
        6      16        24         8   5.33276         0           -     1.87322
        7      16        24         8   4.57094         0           -     1.87322
        8      16        26        10   4.99946   2.66667     7.28216       2.955
        9      16        26        10   4.44396         0           -       2.955
       10      16        28        12   4.79948         4     5.11534     3.66568
       11      16        29        13   4.72675         4    0.782554      3.4439
       12      16        29        13   4.33285         0           -      3.4439
       13      16        29        13   3.99956         0           -      3.4439
       14      14        29        15   4.28524   2.66667     11.4966     4.62831
    Total time run:         14.6111
    Total writes made:      29
    Write size:             4194304
    Object size:            4194304
    Bandwidth (MB/sec):     7.93917
    Stddev Bandwidth:       3.29724
    Max bandwidth (MB/sec): 12
    Min bandwidth (MB/sec): 0
    Average IOPS:           1
    Stddev IOPS:            0.841897
    Max IOPS:               3
    Min IOPS:               0
    Average Latency(s):     7.95842
    Stddev Latency(s):      5.32131
    Max latency(s):         14.6109
    Min latency(s):         0.222219
    Cleaning up (deleting benchmark objects)
    Removed 29 objects
    Clean up completed and total clean up time :0.692274

结合之前gemfield在SS CEPH集群（3个node，12个OSD per node）上测试的性能数据：

    
    
    #以前的CEPH集群
    Total time run:         10.4436
    Total writes made:      231
    Write size:             4194304
    Object size:            4194304
    Bandwidth (MB/sec):     88.4757
    Stddev Bandwidth:       18.3981
    Max bandwidth (MB/sec): 104
    Min bandwidth (MB/sec): 40
    Average IOPS:           22
    Stddev IOPS:            4.59952
    Max IOPS:               26
    Min IOPS:               10
    Average Latency(s):     0.722744
    Stddev Latency(s):      0.231247
    Max latency(s):         1.46561
    Min latency(s):         0.296237

可以看到当前的集群比之前的集群在吞吐速度上慢10倍，在IOPS上慢几十倍，在延迟上慢十倍。再上个数据，之前Gemfield在CDS
CEPH集群（5个node，12个OSD per node，10G交换）上测试的性能数据：

    
    
    [root@gemfield03 /]# rados bench -p gemfield 10 write --no-cleanup
    hints = 1
    Maintaining 16 concurrent writes of 4194304 bytes to objects of size 4194304 for up to 10 seconds or 0 objects
    Object prefix: benchmark_data_gmefield03_36434
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        91        75   299.987       300    0.117985    0.196412
        2      16       178       162   323.971       348    0.105185    0.187288
        3      16       271       255   339.963       372    0.146098    0.179063
        4      16       360       344    343.96       356    0.284012    0.180643
        5      16       460       444   355.157       400    0.105455    0.177374
        6      16       566       550   366.617       424    0.185362    0.172304
        7      16       648       632   361.089       328    0.128824    0.174546
        8      16       745       729   364.447       388    0.194238    0.173477
        9      16       832       816   362.615       348    0.122373    0.174306
       10      16       928       912   364.747       384    0.240703     0.17363
    Total time run:         10.1402
    Total writes made:      928
    Write size:             4194304
    Object size:            4194304
    Bandwidth (MB/sec):     366.068
    Stddev Bandwidth:       36.3587
    Max bandwidth (MB/sec): 424
    Min bandwidth (MB/sec): 300
    Average IOPS:           91
    Stddev IOPS:            9.08968
    Max IOPS:               106
    Min IOPS:               75
    Average Latency(s):     0.174214
    Stddev Latency(s):      0.0928665
    Max latency(s):         0.742311
    Min latency(s):         0.0755959

**2，顺序读的性能测试**

    
    
    [root@rook-ceph-tools-7bb5797c8-584k5 /]# rados bench -p gemfield 10 seq
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        40        24   95.9797        96    0.231409    0.322722
        2      14        50        36   71.9879        48     0.65605    0.420961
        3      14        50        36   47.9927         0           -    0.420961
        4      14        50        36   35.9947         0           -    0.420961
    Total time run:       4.24236
    Total reads made:     50
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   47.1435
    Average IOPS:         11
    Stddev IOPS:          11.4891
    Max IOPS:             24
    Min IOPS:             0
    Average Latency(s):   1.24729
    Max latency(s):       4.08062
    Min latency(s):       0.11719

以前在SS ceph集群（3个node，12个OSD per node）的seq性能测试结果：

    
    
    #以前的ceph集群
    Total time run:       8.43526
    Total reads made:     231
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   109.54
    Average IOPS:         27
    Stddev IOPS:          4.65219
    Max IOPS:             35
    Min IOPS:             21
    Average Latency(s):   0.578438
    Max latency(s):       1.7001
    Min latency(s):       0.168042

看来在读上面平均慢2倍。

之前在CDS CEPH上（5个node，12个OSD per node，10G交换）测试的性能数据：

    
    
    [root@gemfield03 /]# rados bench -p gemfield 10 seq
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      15       138       123   491.605       492    0.300807    0.121921
        2      15       342       327   653.238       816   0.0494801    0.093751
        3      15       570       555   739.058       912   0.0601687   0.0833514
        4      16       784       768   767.239       852   0.0527719   0.0806853
    Total time run:       4.7224
    Total reads made:     928
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   786.041
    Average IOPS:         196
    Stddev IOPS:          47.0532
    Max IOPS:             228
    Min IOPS:             123
    Average Latency(s):   0.0791107
    Max latency(s):       0.32468
    Min latency(s):       0.0231932

**3，随机读性能测试**

    
    
    [root@rook-ceph-tools-7gemfield-584k5 /]# rados bench -p gemfield 10 rand
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      16        46        30   119.974       120    0.547172    0.297584
        2      16        75        59   117.979       116    0.214033    0.381791
        3      16       103        87   115.982       112    0.236008    0.413016
        4      16       134       118   117.982       124    0.377865    0.429721
        5      16       161       145   115.984       108    0.117358    0.464719
        6      16       191       175   116.651       120   0.0791308    0.486277
        7      16       222       206   117.699       124   0.0742925    0.480169
        8      16       254       238   118.985       128      2.4242    0.475601
        9      16       283       267   118.652       116     2.30648    0.481071
       10      16       315       299   119.585       128    0.356745    0.476258
    Total time run:       10.5661
    Total reads made:     316
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   119.628
    Average IOPS:         29
    Stddev IOPS:          1.66333
    Max IOPS:             32
    Min IOPS:             27
    Average Latency(s):   0.531533
    Max latency(s):       3.66058
    Min latency(s):       0.00457582

在以前的SS cpeh集群上（3个node，12个OSD per node）的性能测试结果：

    
    
    #以前的ceph集群
    Total time run:       10.4674
    Total reads made:     288
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   110.056
    Average IOPS:         27
    Stddev IOPS:          1.85293
    Max IOPS:             29
    Min IOPS:             23
    Average Latency(s):   0.574028
    Max latency(s):       2.62393
    Min latency(s):       0.111288

唉？这个好像差不多，估计是有缓存了吧。

之前在CDS CEPH集群（5个node，12个OSD per node，10G交换）的随机读性能测试结果：

    
    
    [root@gemfield03 /]# rados bench -p gemfield 10 rand
    hints = 1
      sec Cur ops   started  finished  avg MB/s  cur MB/s last lat(s)  avg lat(s)
        0       0         0         0         0         0           -           0
        1      15       281       266   1063.74      1064   0.0654033   0.0558857
        2      16       559       543   1085.78      1108    0.168871   0.0560086
        3      16       831       815   1086.45      1088   0.0266952   0.0565254
        4      16      1100      1084    1083.8      1076    0.130492   0.0565693
        5      15      1383      1368    1094.2      1136   0.0133922   0.0562535
        6      15      1652      1637   1091.14      1076   0.0595208   0.0563363
        7      15      1931      1916   1094.67      1116   0.0614772   0.0561414
        8      15      2210      2195   1097.32      1116       0.018    0.056143
        9      16      2478      2462   1094.04      1068    0.151174   0.0562376
       10      16      2750      2734   1093.42      1088   0.0277268   0.0563393
    Total time run:       10.0731
    Total reads made:     2750
    Read size:            4194304
    Object size:          4194304
    Bandwidth (MB/sec):   1092.02
    Average IOPS:         273
    Stddev IOPS:          6.02218
    Max IOPS:             284
    Min IOPS:             266
    Average Latency(s):   0.0566209
    Max latency(s):       0.284946
    Min latency(s):       0.00474428

##  **性能方面的建议**

  * 至少要把 journal、metadata等放在单独的SSD (NVMe更好)，有条件的话OSD也放在SSD上。 
  * 至少使用10GbE网卡 ； 
  * replica是3对数据的安全有好处，但是代价就是慢； 
  * 默认情况下scrubbing一直在运行，最好把它改成晚上再进行；在低带宽的环境中，pg的scrubbing对性能有严重的影响。使用下面的命令来禁止： 

    
    
    ceph osd set noscrub
    ceph osd set nodeep-scrub

  * OSD的文件存储引擎改成BlueStore，在Gemfield的最新版中，这就是默认的； 
  * mon、mds、osd进程的健康对性能有直接的影响，有的时候，某些进程的重启会导致性能提升； 
  * 不要启用实验的那个multus network，使用host network： 

    
    
      network:
        hostNetwork: true

注意这个配置不支持在线更改！

  * 不要启用crashCollector； 
  * metadataDevice配置一个独立的SSD； 
  * 增加metadataServer的activeCount，1个count数对应2个mds instance（active-standby嘛），需要两个独立的k8s worker node； 
  * pool的pg number，不过如今都是autoscale的了，不用太操心这块，可以针对一个pool开启和关闭autoscale，也可以查看当前autoscale的状态（其中 **NEW PG_NUM这一列如果不为空，则是系统推荐你应该设置的pg数** ）： 

    
    
    [root@rook-ceph-tools-gemfield-t9cbl /]# ceph osd pool autoscale-status
    POOL                          SIZE TARGET SIZE RATE RAW CAPACITY  RATIO TARGET RATIO BIAS PG_NUM NEW PG_NUM AUTOSCALE 
    my-store.rgw.buckets.index  49099               3.0       40054G 0.0000               1.0      8            on        
    my-store.rgw.log            84606               3.0       40054G 0.0000               1.0      8            on        
    myfs-data0                  430.7G              2.0       40054G 0.0215               1.0     32            on        
    my-store.rgw.buckets.non-ec     0               3.0       40054G 0.0000               1.0      8            on        
    replicapool                     0               3.0       40054G 0.0000               1.0     32            on        
    my-store.rgw.buckets.data   236.0M              3.0       40054G 0.0000               1.0     32            on        
    .rgw.root                    3826               3.0       40054G 0.0000               1.0      8            on        
    myfs-metadata                5861M              2.0       40054G 0.0003               4.0     32            on        
    my-store.rgw.meta            1415               3.0       40054G 0.0000               1.0      8            on        
    my-store.rgw.control            0               3.0       40054G 0.0000               1.0      8            on

经过调整后，Gemfield在老旧的硬件上取得了一些进展，就不再赘述了。消除掉之前CEPH累积下来的warning：

    
    
    #查看所有的warning
    [root@rook-ceph-tools-7gemfield-584k5 /]# ceph crash ls
    
    #查看每条的信息
    [root@rook-ceph-tools-7gemfield-584k5 /]# ceph crash info <id>
    
    #清除
    [root@rook-ceph-tools-7gemfield-584k5 /]# ceph crash archive <id>
    
    #清除所有
    [root@rook-ceph-tools-7gemfield-584k5 /]# ceph crash archive-all

##  **总结**

上面的问题有哪个不清楚，请评论留言。Gemfield会持续关注BandWidth、IOPS、latency这几个指标，不提高不舒服。


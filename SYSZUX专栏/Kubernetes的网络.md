##  **背景**

Gemfield的K8s cluster
中的一台node（hostname为ai）遭遇跳闸断电给挂掉了，办公室供电跳闸的原因到目前还未知，此为第一个忧伤；当ai重新供电并开机后，ai虽然成功接入了k8s，不过由于之前所有k8s的service的externalIP设置成了ai的host
IP，现在这些对应的服务全部不能通过ai的host IP来访问了！这又是一个深深的忧伤。

以其中的gerrit
service为例，该服务通过8080和29418两个端口对外提供服务，之前使用的就是上文所说的externalIP方式，也就是通过<ai的host
ip>:29418 和 <ai的host ip>:8080对外提供访问。而现在，访问这些端口就被阻塞住了。

gemfield本文就来探索这背后的原因以及如何恢复这些service的访问。

    
    
    gemfield@master:~$ kubectl get node -o wide
    NAME         STATUS    ROLES     AGE       VERSION   INTERNAL-IP     EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
    ai           Ready     <none>    76d       v1.11.1   192.168.1.188   <none>        Ubuntu 18.04.1 LTS   4.15.0-36-generic   docker://18.6.0
    hp           Ready     <none>    71d       v1.11.1   192.168.1.172   <none>        Ubuntu 18.04.1 LTS   4.15.0-30-generic   docker://18.6.0
    master       Ready     master    76d       v1.11.1   192.168.1.196   <none>        Ubuntu 18.04.1 LTS   4.15.0-29-generic   docker://18.6.0
    ml           Ready     <none>    76d       v1.11.1   192.168.1.121   <none>        Ubuntu 18.04.1 LTS   4.15.0-29-generic   docker://18.6.0

ai上的PodCIDR

    
    
    gemfield@master:~$ kubectl describe node ai | grep PodCIDR
    PodCIDR:                     172.16.2.0/24

##  **K8s的网络**

在准备debug上述问题之前，我们需要对K8s的网络有一个简单的了解。

下文提到的端口号29418、8080、30080、30587等，在本文的语义中都是等价的。

访问<ai的host
ip>:29418的traffic是如何到达<gerrit容器的ip>:29418的，以及再如何返回的呢？我们不得不去窥探k8s的网络了，具体来说，就是要能够回答以下几个问题：

1，K8s的master和worker等node之间是如何通信的呢？

2，容器和自身所在的node（宿主机）之间是如何通信的呢？

3，容器和同一个node上的容器之间是如何通信的呢？

4，容器和其它宿主机上的容器是如何通信的呢？

5，K8s的CNI是如何发挥作用的呢？

CNI是容器网络接口（Container Network Interface），它的项目地址如下：

[ https://  github.com/containernet  working/cni
](https://link.zhihu.com/?target=https%3A//github.com/containernetworking/cni)

这里就不过多描述了，值得注意的是，CNI是专注的，它只关心容器创建（add）和销毁（del）时候的网络资源的创建与销毁。calico项目、K8s项目等都在使用CNI。其中k8s使用的是
**projectcalico/cni-plugin**

[ https://  github.com/projectcalic  o/cni-plugin
](https://link.zhihu.com/?target=https%3A//github.com/projectcalico/cni-
plugin)

你要了解K8s的CNI
的二进制文件在哪个路径(/opt/...)，配置文件在哪个路径(/etc/cni/...)，定义了ADD/DEL...等方法，输入输出是什么，在什么时候被执行，执行的时候产生了什么效果（比如产生了iptable
rule，产生了route table rule等），这些规则被注入tecd或者kubernetes
datastore，然后由calico在confd的动态更新中重新实施这些规则。

##  **开始Debug**

gemfield开始了问题的解决之路，我们来一步一步循序渐进抽丝剥茧般的分析。

**1，gerrit服务的pod是正常的吗？**

    
    
    gemfield@master:~$ kubectl get pods -o wide
    NAME                     READY     STATUS    RESTARTS   AGE       IP             NODE
    gerrit-7477c8576-rvnvx   1/1       Running   0          1d        172.16.1.133   ml
    ldap-65d497b7c4-72mfn    1/1       Running   0          1d        172.16.1.131   ml

是正常的；

**2， gerrit服务的k8s service是正常的吗?**

是正常的：

    
    
    gemfield@master:~$ kubectl get svc -o wide

**3，ai host上有没有29418/8080的端口在侦听呢？**

有的：

    
    
    gemfield@ai:~$ sudo netstat -antp | grep 8080
    tcp6       0      0 :::8080                :::*                    LISTEN      523/kube-proxy

**4，把gerrit的externalIP换成NodePort类型交叉验证下**

这一步的意义是什么呢？就是NodePort类型会将端口映射到每个宿主机的30000+端口上，之前不是说ai不能访问了吗，我访问另外一台node的同一个服务的端口就可以对比了：

    
    
    gemfield@master:~$ kubectl get svc -o wide
    NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                          AGE       SELECTOR
    gerrit       NodePort    10.96.166.167   <none>        29418:30587/TCP,8080:30080/TCP   1d        app=gerrit
    kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP                          76d       <none>
    ldap         ClusterIP   None            <none>        389/TCP                          1d        app=ldap

这里就很明显了，<ai的host ip>:30080仍然不可以访问，但是访问<ml的host ip>:30080就是正常的，ml是k8s
cluster中的另外一台node。而之前断电的正是ai这台node！

而继续往下debug就不得不熟悉K8s的网络了。

**5，iptables**

在ai上查看和30080端口相关的iptables规则：

    
    
    gemfield@ai:~$ sudo iptables-save | grep 30080
    -A KUBE-NODEPORTS -p tcp -m comment --comment "default/gerrit:gerrit1" -m tcp --dport 30080 -j KUBE-MARK-MASQ
    -A KUBE-NODEPORTS -p tcp -m comment --comment "default/gerrit:gerrit1" -m tcp --dport 30080 -j KUBE-SVC-S2MNSV4IPTVV5KRU

这些规则是K8s在创建service的时候create出来的，而这里ai node上的输出和ml node是一样的。所以service的创建是没有问题的。

**6, node上的route**

首先看ai上的：

    
    
    gemfield@ai:~$ ip r | grep bird
    blackhole 172.16.2.0/24 proto bird

再看ml上的：

    
    
    gemfield@ML:~$ ip r | grep bird
    172.16.0.0/24 via 192.168.1.196 dev tunl0 proto bird onlink 
    blackhole 172.16.1.0/24 proto bird 
    172.16.3.0/24 via 192.168.1.172 dev tunl0 proto bird onlink 

呃，route信息不对，ml上没有到ai上的ipip，但是有到其它node的ipip；而ai上是啥也没有！据此可以判断是各个node上的calico
CNI之间的通信出现了问题，具体是ai和其它node都不通，而其它node是互通的，进一步把线索指向了ai的跳闸掉电。

**7，使用calicoctl命令**

没有这个命令的话可以直接从官网下载，是一个static linked的binary可执行文件。

先看看所有node上的calico容器：

    
    
    gemfield@master:~$ kubectl get pods --all-namespaces -o wide | grep calico
    kube-system     calico-node-26655                          2/2       Running   0          1d        192.168.1.188   ai
    kube-system     calico-node-4zsxl                          2/2       Running   0          1d        192.168.1.172   hp-probook
    kube-system     calico-node-69gdw                          2/2       Running   0          1d        192.168.1.196   master
    kube-system     calico-node-xrpjw                          2/2       Running   0          1d        192.168.1.121   ml

进行ml node上的calico状态检查：

    
    
    gemfield@master:~$ kubectl -n kube-system exec -it calico-node-xrpjw -- /home/calicoctl node status
    Defaulting container name to calico-node.
    Use 'kubectl describe pod/calico-node-xrpjw -n kube-system' to see all of the containers in this pod.
    Calico process is running.
    
    IPv4 BGP status
    +---------------+-------------------+-------+------------+-------------+
    | PEER ADDRESS  |     PEER TYPE     | STATE |   SINCE    |    INFO     |
    +---------------+-------------------+-------+------------+-------------+
    | 172.19.0.1    | node-to-node mesh | start | 2018-10-19 | Connect     |
    | 192.168.1.172 | node-to-node mesh | up    | 2018-10-19 | Established |
    | 192.168.1.196 | node-to-node mesh | up    | 2018-10-19 | Established |
    +---------------+-------------------+-------+------------+-------------+
    IPv6 BGP status
    No IPv6 peers found.

##  进行hp node上的calico状态检查：

    
    
    gemfield@master:~$ kubectl -n kube-system exec -it calico-node-4zsxl -- /home/calicoctl node status     
    Defaulting container name to calico-node.
    Use 'kubectl describe pod/calico-node-4zsxl -n kube-system' to see all of the containers in this pod.
    Calico process is running.
    
    IPv4 BGP status
    +---------------+-------------------+-------+------------+-------------+
    | PEER ADDRESS  |     PEER TYPE     | STATE |   SINCE    |    INFO     |
    +---------------+-------------------+-------+------------+-------------+
    | 172.19.0.1    | node-to-node mesh | start | 2018-10-19 | Connect     |
    | 192.168.1.196 | node-to-node mesh | up    | 2018-10-19 | Established |
    | 192.168.1.121 | node-to-node mesh | up    | 2018-10-19 | Established |
    +---------------+-------------------+-------+------------+-------------+
    
    IPv6 BGP status
    No IPv6 peers found.

进行ai node上的calico状态检查：

    
    
    gemfield@master:~$ kubectl -n kube-system exec -it calico-node-26655 -- /home/calicoctl node status                                
    Defaulting container name to calico-node.
    Use 'kubectl describe pod/calico-node-26655 -n kube-system' to see all of the containers in this pod.
    Calico process is running.
    
    IPv4 BGP status
    +---------------+-------------------+-------+------------+--------------------------------+
    | PEER ADDRESS  |     PEER TYPE     | STATE |   SINCE    |              INFO              |
    +---------------+-------------------+-------+------------+--------------------------------+
    | 192.168.1.172 | node-to-node mesh | start | 2018-10-19 | Connect Socket: Connection     |
    |               |                   |       |            | closed                         |
    | 192.168.1.196 | node-to-node mesh | start | 2018-10-19 | Active Socket: Connection      |
    |               |                   |       |            | reset by peer                  |
    | 192.168.1.121 | node-to-node mesh | start | 2018-10-19 | Active Socket: Connection      |
    |               |                   |       |            | closed                         |
    +---------------+-------------------+-------+------------+--------------------------------+
    
    IPv6 BGP status
    No IPv6 peers found.

果然，根据上面的输出，进一步确认了是ai上的calico无法和其它node上的calico通信。并且令人诧异的是，ai node上的BGP
address为什么是172.19.0.1 而不是192.168.1.* ?

再看看calico的BGP的服务端口是否在侦听（Calico BGP , listen on 179 port）：

    
    
    #gemfield on calico container
    /var # netstat -antp | grep 179
    tcp        0      0 0.0.0.0:179             0.0.0.0:*               LISTEN      116/bird

**8, bird**

calico的BGP是由bird实现的，我们找到了bird的配置文件（在/etc/calico/confd/config/目录下）bird.cfg：

    
    
    #在gemfield的ai node上的calico容器里
    /etc/calico/confd/config # cat bird.cfg
    # Generated by confd
    include "bird_aggr.cfg";
    include "bird_ipam.cfg";
    
    
    router id 172.19.0.1;
    ......

我们发现bird的配置文件里有router id
172.19.0.1，那这个值是哪里来的呢？在calico容器里，bird的配置文件是由confd维护的，confd会定期更新这个bird.cfg，在K8s
cluster（哪怕是更一般的情况下），confd是从etcd中读取值来更新配置文件的。

**9，confd**

confd的配置文件/etc/calico/confd/conf.d/bird.toml 如下所示：

    
    
    #在calico容器里，by gemfield
    /etc/calico/confd/conf.d # cat /etc/calico/confd/conf.d/bird.toml 
    [template]
    src = "bird.cfg.template"
    dest = "/etc/calico/confd/config/bird.cfg"
    prefix = "/calico/bgp/v1"
    keys = [
        "/host",
        "/global",
    ]
    check_cmd = "bird -p -c {{.src}}"
    reload_cmd = "pkill -HUP bird || true"

再看模板文件：

    
    
    #gemfield的calico容器里
    /etc/calico/confd/conf.d # cat /etc/calico/confd/templates/bird.cfg.template 
    # Generated by confd
    include "bird_aggr.cfg";
    include "bird_ipam.cfg";
    {{$node_ip_key := printf "/host/%s/ip_addr_v4" (getenv "NODENAME")}}{{$node_ip := getv $node_ip_key}}
    
    router id {{$node_ip}};

当node-to-node mesh 被设置后（默认），主要的BIRD配置就是由这些模板定义的。在上面，我们可以看到router id
{{$node_ip}};的语句，也即意味着node_ip的值为getv $node_ip_key进一步展开就是getv
"/host/ai/ip_addr_v4"，这个值不知为何从etcd中读成了172.19.0.1。

**10, etcd**

使用etcd的客户端命令（注意k8s现在使用的是etcd v3, 必须提供ca、key、cert，否则会出现Error: context deadline
exceeded）：

    
    
    #在gemfield的etcd容器里
    / # ETCDCTL_API=3 etcdctl --cacert /etc/kubernetes/pki/etcd/ca.crt  --cert /etc/kubernetes/pki/etcd/peer.crt --key /etc/kubernetes/pki/etcd/peer.key get --prefix /calico/bgp/v1

但是，从K8s 1.11开始，calico就废弃了使用etcd作为backend，改为了kubernetes
datastore。因此上面的命令是不能得到相关信息的。

[ projectcalico/calico
](https://link.zhihu.com/?target=https%3A//github.com/projectcalico/calico/tree/master/v2.6/getting-
started/kubernetes/installation/hosted/kubernetes-datastore)

etcd-calico(bgp)实现docker跨主机通信，Calico实现了基于BGP协议的路由方案。

**11, 谁将这个key的值更新成了172.19.0.1**

看看log怎么说：

    
    
    #ai上的calico pod
    gemfield@master:~$ kubectl -n kube-system logs -f calico-node-26655 calico-node | grep 172.19 
    2018-10-19 06:41:19.968 [INFO][10] startup.go 564: Using autodetected IPv4 address on interface br-cddff8a3b81c: 172.19.0.1/16
    2018-10-19 06:41:22.362 [INFO][119] int_dataplane.go 485: Linux interface addrs changed. addrs=set.mapSet{"172.19.0.1":set.empty{}, "fe80::42:e4ff:fe19:ef2b":set.empty{}} ifaceName="br-cddff8a3b81c"
    2018-10-19 06:41:22.363 [INFO][119] int_dataplane.go 641: Received interface addresses update msg=&intdataplane.ifaceAddrsUpdate{Name:"br-cddff8a3b81c", Addrs:set.mapSet{"172.19.0.1":set.empty{}, "fe80::42:e4ff:fe19:ef2b":set.empty{}}}
    2018-10-19 06:41:22.363 [INFO][119] hostip_mgr.go 84: Interface addrs changed. update=&intdataplane.ifaceAddrsUpdate{Name:"br-cddff8a3b81c", Addrs:set.mapSet{"172.19.0.1":set.empty{}, "fe80::42:e4ff:fe19:ef2b":set.empty{}}}
    2018-10-19 06:41:22.377 [INFO][119] int_dataplane.go 611: Received *proto.HostMetadataUpdate update from calculation graph msg=hostname:"ai" ipv4_addr:"172.19.0.1"

其中有一句话很显眼：Using autodetected IPv4 address on interface br-cddff8a3b81c:
172.19.0.1/16。那我们就来看看为什么在ai上自动选择了这个IP：

    
    
    gemfield@ai:/bigdata/gemfield/github/Gemfield$ ip a | grep -C 3 172.19
           valid_lft forever preferred_lft forever
    46: br-cddff8a3b81c: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
        link/ether 02:42:e4:19:ef:2b brd ff:ff:ff:ff:ff:ff
        inet 172.19.0.1/16 brd 172.19.255.255 scope global br-cddff8a3b81c
           valid_lft forever preferred_lft forever
        inet6 fe80::42:e4ff:fe19:ef2b/64 scope link 
           valid_lft forever preferred_lft forever

是br-cddff8a3b81c，经检查发现这是以前某个docker-
compose服务设置的bridge。将这个birdge删掉，然后将ai上的calico pod delete掉：

    
    
    gemfield@master:~$ kubectl -n kube-system delete pod calico-node-26655

这样会导致ai上的calico容器重启，再看看重启时候的log：

    
    
    2018-10-21 07:33:54.298 [INFO][10] startup.go 251: Early log level set to info
    2018-10-21 07:33:54.299 [INFO][10] startup.go 267: Using NODENAME environment for node name
    2018-10-21 07:33:54.299 [INFO][10] startup.go 279: Determined node name: ai
    2018-10-21 07:33:54.300 [INFO][10] startup.go 302: Checking datastore connection
    2018-10-21 07:33:54.336 [INFO][10] startup.go 326: Datastore connection verified
    2018-10-21 07:33:54.336 [INFO][10] startup.go 99: Datastore is ready
    2018-10-21 07:33:54.350 [INFO][10] startup.go 564: Using autodetected IPv4 address on interface eno1: 192.168.1.188/24
    2018-10-21 07:33:54.350 [INFO][10] startup.go 432: Node IPv4 changed, will check for conflicts
    2018-10-21 07:33:54.354 [WARNING][10] startup.go 849: IPv4 address has changed. This could happen if there are multiple nodes with the same name. node="ai" original="172.19.0.1" updated="192.168.1.188"
    2018-10-21 07:33:54.354 [INFO][10] startup.go 627: No AS number configured on node resource, using global value
    2018-10-21 07:33:54.504 [INFO][10] startup.go 510: FELIX_IPV6SUPPORT is false through environment variable
    2018-10-21 07:33:54.504 [INFO][10] k8s.go 264: EnsuringInitialized - noop
    2018-10-21 07:33:54.530 [INFO][10] startup.go 176: Using node name: ai
    2018-10-21 07:33:54.617 [INFO][30] allocate_ipip_addr.go 41: Kubernetes datastore driver handles IPIP allocation - no op
    Calico node started successfully

可以看到ip切换到了gem-field所想要的，接着看看calico node status：

    
    
    /home # wget http://x99.gemfield.org:8080/static/calicoctl 
    Connecting to x99.gemfield.org:8080 (61.149.179.174:8080)
    calicoctl            100% |********************************************************************************************************************************************| 29883k  0:00:00 ETA
    /home # chmod +x calicoctl 
    /home # ./calicoctl node status
    Calico process is running.
    
    IPv4 BGP status
    +---------------+-------------------+-------+----------+-------------+
    | PEER ADDRESS  |     PEER TYPE     | STATE |  SINCE   |    INFO     |
    +---------------+-------------------+-------+----------+-------------+
    | 192.168.1.172 | node-to-node mesh | up    | 07:33:58 | Established |
    | 192.168.1.196 | node-to-node mesh | up    | 07:33:59 | Established |
    | 192.168.1.121 | node-to-node mesh | up    | 07:33:58 | Established |
    +---------------+-------------------+-------+----------+-------------+
    
    IPv6 BGP status
    No IPv6 peers found.
    

之后访问gerrit服务在ai上的端口，也正常了。

##  **庆祝**

哈哈哈哈哈。


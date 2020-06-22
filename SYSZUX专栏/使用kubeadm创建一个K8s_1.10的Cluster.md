我们有很多种方式在很多种环境下安装配置Kubernetes的cluster（包含master和worker nodes），如 [ Picking the
Right Solution
](https://link.zhihu.com/?target=https%3A//kubernetes.io/docs/setup/pick-
right-solution/) 所展示的这样。 本文中，Gemfield将演示如何使用kubeadm在Bare
metal的Ubuntu操作系统中创建一个K8s的Cluster，版本为1.10。

注意：1.11已经发布，关于1.11的部署可以参考专栏文章：

[ Gemfield：使用kubeadm安装Kubernetes 1.11 ](https://zhuanlan.zhihu.com/p/40931670)

注意：本文的安装方式是基于直接访问谷歌服务的，中间过程涉及到跨越城墙，如果对这个没有兴趣的话，可以使用境内厂商提供的镜像。如果决定使用境内厂商提供的镜像的话，请移步上述1.11的安装。

##  **一，为每个node安装kubeadm**

**1，禁掉swap分区**

    
    
    gemfield@sl:~$ sudo swapoff -a
    
    #要永久禁掉swap分区，打开如下文件注释掉swap那一行
    gemfield@sl:~$ sudo vi /etc/fstab

这一步是为了让kubelet正常工作，否则会报错：

    
    
    11月 25 16:52:38 sl kubelet[2856]: error: failed to run Kubelet: Running with swap on is not supported, please disable swap! or set --fail-swap-on
    11月 25 16:52:38 sl systemd[1]: kubelet.service: Main process exited, code=exited, status=1/FAILURE
    11月 25 16:52:38 sl systemd[1]: kubelet.service: Unit entered failed state.
    11月 25 16:52:38 sl systemd[1]: kubelet.service: Failed with result 'exit-code'.

  

**2，可以得到机器的MAC和product_uuid**

    
    
    gemfield@sl:~$ ip link
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    2: enp8s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
        link/ether 60:eb:69:af:b2:76 brd ff:ff:ff:ff:ff:ff
    3: wlp5s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DORMANT group default qlen 1000
        link/ether 5c:ac:4c:bf:6d:12 brd ff:ff:ff:ff:ff:ff
    4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN mode DEFAULT group default 
        link/ether 02:42:d2:2f:a7:0b brd ff:ff:ff:ff:ff:ff
    
    gemfield@sl:~$ sudo cat /sys/class/dmi/id/product_uuid
    20FD5881-4A7E-11CB-A0FC-C6E1CB03C2A6

确保Kubunetes能正确使用机器的网卡设备，在多网卡的环境下，有必要的时候你要设置路由。

另外，需要以下TCP端口：

    
    
    #Master Node上
    6443*，Kubernetes API server
    2379-2380， etcd server client API
    10250， Kubelet API
    10251，kube-scheduler
    10252，kube-controller-manager
    10255，Read-only Kubelet API
    
    #worker node上需要以下TCP端口：
    10250，Kubelet API
    10255，Read-only Kubelet API
    30000-32767，NodePort Services**

  

**3，安装Docker**

在每台机器上安装docker，在今天（2018年4月27日）这个时刻，这些docker版本是验证过的：v1.12、
v1.11、v1.13和17.03。使用下面的命令来安装docker。

    
    
    gemfield@sl:~$ sudo apt-get update
    gemfield@sl:~$ sudo apt-get install -y docker.io

更多docker详情，请参考Gemfield专栏的前述文章

  

**4，安装kubeadm、kubelet、kubectl**

**这3个包要在所有的机器上安装。**

  * ` kubeadm ` :从零开始配置K8s cluster的tool。目前kubeadm整体还是beta状态，官方宣称的是在2018年结束之前变为General Availability (GA)状态。 
  * ` kubelet ` : 集群的每个机器上都需要运行的组件，用来启动pods和containers。 
  * ` kubectl ` : 用来和集群交互的命令行工具。 

**配置如下apt源**

    
    
    gemfield@sl:~$ cat /etc/apt/sources.list.d/kubernetes.list
    deb http://apt.kubernetes.io/ kubernetes-xenial main 

**配置apt的proxy来翻墙**

因为下载的package都在 [ http://  packages.cloud.google.com  /apt
](https://link.zhihu.com/?target=http%3A//packages.cloud.google.com/apt)
下，你懂的。

    
    
    gemfield@sl:~$ cat /etc/apt/apt.conf
    Acquire::http::Proxy "http://gemfield.org:7030";
    Acquire::https::Proxy "http://gemfield.org:7030";
    gemfield@sl:~$

**安装这个源的公钥**

    
    
    #配置代理，mmp你懂的
    gemfield@edge:~$ export http_proxy=gemfield.org:7030
    gemfield@edge:~$ export https_proxy=gemfield.org:7030
    
    #安装
    gemfield@sl:~$ curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

否则无法验证签名，会出现如下错误：

    
    
    获取:3 https://packages.cloud.google.com/apt kubernetes-xenial InRelease [8,942 B]
    错误:3 https://packages.cloud.google.com/apt kubernetes-xenial InRelease
      由于没有公钥，无法验证下列签名： NO_PUBKEY 3746C208A7317B0F
    正在读取软件包列表... 完成   
    W: GPG 错误：https://packages.cloud.google.com/apt kubernetes-xenial InRelease: 由于没有公钥，无法验证下列签名： NO_PUBKEY 3746C208A7317B0F
    E: 仓库 “http://apt.kubernetes.io kubernetes-xenial InRelease” 没有数字签名。
    N: 无法安全地用该源进行更新，所以默认禁用该源。
    N: 参见 apt-secure(8) 手册以了解仓库创建和用户配置方面的细节。

值得再次强调的是，这个代理不止在这里起作用，而且在下面运行kubeadm init的时候也需要。继续看吧。

**运行apt update更新源**

    
    
    gemfield@gemfield:~$ sudo apt update

**9，安装kubeadm, kubelet 和 kubectl**

    
    
    gemfield@gemfield:~$ sudo apt install -y kubelet kubeadm kubectl   
    正在读取软件包列表... 完成
    正在分析软件包的依赖关系树       
    正在读取状态信息... 完成       
    将会同时安装下列软件：
      ebtables kubernetes-cni
    下列【新】软件包将被安装：
      ebtables kubeadm kubectl kubelet kubernetes-cni
    升级了 0 个软件包，新安装了 5 个软件包，要卸载 0 个软件包，有 0 个软件包未被升级。
    需要下载 51.5 MB/51.6 MB 的归档。
    解压缩后会消耗 369 MB 的额外空间。
    ......

master node 就是运行了control plane组件的机器， 包括etcd (the cluster database)和 API server
(也就是kube-apiserver，让kubectl命令交互的)。也就是说， ` kubectl ` 和 ` kube-apiserver `
交互来进行集群的管理。 发出的命令将实际工作在master node上，这是因为kube-apiserver运行在master node上。而在worker
nodes上，将只运行 ` kubelet ` 和 ` kube-proxy ` 。

##  **二，初始化master node**

**1，使用kubeadm init 去初始化master node**

kubeadm init的时候要先想好使用什么网络插件，gemfield选择的是Calico插件，所以init时候的命令就是（注意：确保--pod-
network-cidr的值不要和宿主机的局域网网段冲突）：

    
    
    #In order for Network Policy to work correctly, you need to pass --pod-network-cidr=172.16.0.0/16 to kubeadm init
    kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118

这一步首先要配置好代理(export http_proxy= [ http://  gemfield.org:17030
](https://link.zhihu.com/?target=http%3A//gemfield.org%3A17030)
)，否则会报getsockopt: connection timed out错误：

    
    
    root@gemfield:~# kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118
    unable to get URL "https://dl.k8s.io/release/stable-1.10.txt": Get https://storage.googleapis.com/kubernetes-release/release/stable-1.10.txt: dial tcp 172.217.160.112:443: getsockopt: connection timed out

但是后面你又得去掉这个代理(unset http_proxy https_proxy，否则。。。继续看吧)。

**2，设置好代理继续kubeadm init**

    
    
    #要用root账户去弄
    root@gemfield:~# kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118             
    [init] Using Kubernetes version: v1.10.2
    [init] Using Authorization modes: [Node RBAC]
    [preflight] Running pre-flight checks.
    ......
    Unfortunately, an error has occurred:
            timed out waiting for the condition
    
    This error is likely caused by:
            - The kubelet is not running
            - The kubelet is unhealthy due to a misconfiguration of the node in some way (required cgroups disabled)
            - Either there is no internet connection, or imagePullPolicy is set to "Never",
              so the kubelet cannot pull or find the following control plane images:
                    - k8s.gcr.io/kube-apiserver-amd64:v1.10.2
                    - k8s.gcr.io/kube-controller-manager-amd64:v1.10.2
                    - k8s.gcr.io/kube-scheduler-amd64:v1.10.2
                    - k8s.gcr.io/etcd-amd64:3.1.12 (only if no external etcd endpoints are configured)
    
    If you are on a systemd-powered system, you can try to troubleshoot the error with the following commands:
            - 'systemctl status kubelet'
            - 'journalctl -xeu kubelet'
    couldn't initialize a Kubernetes cluster

上面的错误一定是墙的问题了，哼！不信你手工执行：

    
    
    root@gemfield:~# docker pull k8s.gcr.io/kube-apiserver-amd64:v1.10.2
    Error response from daemon: Get https://k8s.gcr.io/v1/_ping: dial tcp 64.233.189.82:443: i/o timeout

所以，为了docker pull能够正常工作，gemfield需要设置docker server的proxy。

**3，设置docker server代理**

注意啊，有2种代理，一种是docker client的，一种是docker server的，不要搞混了。这里设置的是docker server的：

    
    
    #为docker service创建一个systemd drop-in 目录
    mkdir -p /etc/systemd/system/docker.service.d
    
    #使用下面内容创建文件/etc/systemd/system/docker.service.d/http-proxy.conf
    [Service]
    Environment="HTTP_PROXY=http://gemfield.org:17030/"
    
    #使用下面内容创建文件/etc/systemd/system/docker.service.d/https-proxy.conf
    [Service]
    Environment="HTTPS_PROXY=http://gemfield.org:17030/"
    
    #写入改动
    sudo systemctl daemon-reload
    
    #重启docker服务
    sudo systemctl restart docker
    
    #验证配置已经生效
    root@gemfield:~# systemctl show --property=Environment docker
    Environment=HTTP_PROXY=http://gemfield.org:17030/ HTTPS_PROXY=http://gemfield.org:17030/

重新pull：

    
    
    root@gemfield:~# docker pull k8s.gcr.io/kube-apiserver-amd64:v1.10.2
    v1.10.2: Pulling from kube-apiserver-amd64
    f70adabe43c0: Pull complete 
    aaa6c3636312: Pull complete 
    Digest: sha256:1ba863c8e9b9edc6d1329ebf966e4aa308ca31b42a937b4430caf65aa11bdd12
    Status: Downloaded newer image for k8s.gcr.io/kube-apiserver-amd64:v1.10.2

好了吧。好了我们就继续kubeadm init。

**4，设置好docker server proxy后再次kubeadm init**

    
    
    root@gemfield:~# kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118
    [init] Using Kubernetes version: v1.10.2
    [init] Using Authorization modes: [Node RBAC]
    [preflight] Running pre-flight checks.
    ......
    [init] This might take a minute or longer if the control plane images have to be pulled.
    ......
    完蛋了！死在这里了

使用journalctl -xeu kubelet 命令查看下log：

    
    
    gemfield@gemfield:~$ journalctl -xeu kubelet
    ......
    4月 28 17:13:29 sl kubelet[28886]: W0428 17:13:29.441478   28886 cni.go:171] Unable to update cni config: No networks found in /etc/cni/net.d
    4月 28 17:13:29 sl kubelet[28886]: E0428 17:13:29.442451   28886 kubelet.go:2125] Container runtime network not ready: NetworkReady=false reason:NetworkPlugin
    4月 28 17:13:34 sl kubelet[28886]: W0428 17:13:34.444718   28886 cni.go:171] Unable to update cni config: No networks found in /etc/cni/net.d
    4月 28 17:13:34 sl kubelet[28886]: E0428 17:13:34.445849   28886 kubelet.go:2125] Container runtime network not ready: NetworkReady=false reason:NetworkPlugin
    ......

程序一直在循环报这个错误：Unable to update cni config: No networks found in
/etc/cni/net.d。这是为什么呢？这是因为前面设置了代理，导致kubelet访问API Server不通，所以需要关闭http proxy。

    
    
    gemfield@sl:~$ unset http_proxy https_proxy
    #或者下面这个更优雅的方法
    gemfield@sl:~$ export no_proxy=192.168.1.118

**5，关闭http proxy后再次kubeadm init**

    
    
    root@sl:~# kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118
    [init] Using Kubernetes version: v1.10.2
    [init] Using Authorization modes: [Node RBAC]
    [preflight] Running pre-flight checks.
            [WARNING FileExisting-crictl]: crictl not found in system path
    Suggestion: go get github.com/kubernetes-incubator/cri-tools/cmd/crictl
    [preflight] Some fatal errors occurred:
            [ERROR Port-6443]: Port 6443 is in use
            [ERROR Port-10250]: Port 10250 is in use
            [ERROR Port-10251]: Port 10251 is in use
            [ERROR Port-10252]: Port 10252 is in use
            [ERROR FileAvailable--etc-kubernetes-manifests-kube-apiserver.yaml]: /etc/kubernetes/manifests/kube-apiserver.yaml already exists
            [ERROR FileAvailable--etc-kubernetes-manifests-kube-controller-manager.yaml]: /etc/kubernetes/manifests/kube-controller-manager.yaml already exists
            [ERROR FileAvailable--etc-kubernetes-manifests-kube-scheduler.yaml]: /etc/kubernetes/manifests/kube-scheduler.yaml already exists
            [ERROR FileAvailable--etc-kubernetes-manifests-etcd.yaml]: /etc/kubernetes/manifests/etcd.yaml already exists
            [ERROR Port-2379]: Port 2379 is in use
            [ERROR DirAvailable--var-lib-etcd]: /var/lib/etcd is not empty

这是因为前面已经执行过一次kubeadm init了（其实是好几次...）。这个时候需要加个参数来忽略到这些：--ignore-preflight-
errors=all

**6，忽略所有前置检查错误后kubeadm init**

    
    
    root@gemfield:~# kubeadm init --pod-network-cidr=172.16.0.0/16 --apiserver-advertise-address=192.168.1.118 --ignore-preflight-errors=all
    [init] Using Kubernetes version: v1.10.2
    [init] Using Authorization modes: [Node RBAC]
    [preflight] Running pre-flight checks.
    ......
    [addons] Applied essential addon: kube-dns
    [addons] Applied essential addon: kube-proxy
    
    Your Kubernetes master has initialized successfully!
    
    To start using your cluster, you need to run the following as a regular user:
    
      mkdir -p $HOME/.kube
      sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
      sudo chown $(id -u):$(id -g) $HOME/.kube/config
    
    You should now deploy a pod network to the cluster.
    Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
      https://kubernetes.io/docs/concepts/cluster-administration/addons/
    
    You can now join any number of machines by running the following on each node
    as root:
    
      kubeadm join 192.168.1.118:6443 --token 9frx62.qp99ri6ds8mo6p41 --discovery-token-ca-cert-hash sha256:a7cff4b98899bcc0a4d5d9eae41648a8f42d4e7334ae52a3ec17910b7e4869af

终于成功了。注意最后的这3段输入，分别是：为正常非root用户所做的配置；部署pod
network；添加其它node到这个集群（注意token是保密的，不要泄露给别人）。下面会继续提到。

**7，去掉kubenetes配置文件中的http_proxy：**

这些ENV变量都是从当前的会话中继承过去的（前面的步骤为了翻墙）, 把这些值删掉：

    
    
    root@master:~# find /etc/kubernetes/ -type f -exec grep -n 17030 {} \+
    /etc/kubernetes/manifests/kube-controller-manager.yaml:30:      value: http://localhost:17030
    /etc/kubernetes/manifests/kube-controller-manager.yaml:32:      value: http://localhost:17030
    /etc/kubernetes/manifests/kube-apiserver.yaml:45:      value: http://localhost:17030
    /etc/kubernetes/manifests/kube-apiserver.yaml:47:      value: http://localhost:17030
    /etc/kubernetes/manifests/kube-scheduler.yaml:21:      value: http://localhost:17030
    /etc/kubernetes/manifests/kube-scheduler.yaml:23:      value: http://localhost:17030

然后重启kubelet service：

    
    
    gemfield@master:~$ sudo systemctl restart kubelet.service

**8，使用非root的正常用户执行以下配置**

    
    
    gemfield@sl:~$ mkdir -p $HOME/.kube
    gemfield@sl:~$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    [sudo] gemfield 的密码： 
    gemfield@sl:~$ sudo chown $(id -u):$(id -g) $HOME/.kube/config

##  **三，部署pod network**

**1，安装Calico pod network**

注意修改官方的calico.yaml
中的CALICO_IPV4POOL_CIDR的值来避免和宿主机所在的局域网段冲突（gemfield就是把原始的192.168.0.0/16
修改成了172.16.0.0/16）：

    
    
    gemfield@sl:~$ kubectl apply -f https://docs.projectcalico.org/v3.1/getting-started/kubernetes/installation/hosted/kubeadm/1.7/calico.yaml
    Unable to connect to the server: Access violation

这是因为当前的terminal的会话里设置了http_proxy和https_proxy，使得kubectl不能访问kube-
apiserve。使用下面的命令来修复这个问题：

    
    
    #kube-apiserve的IP为192.168.1.118
    gemfield@sl:~$ export no_proxy=192.168.1.118

**2，再次安装Calico pod network**

    
    
    gemfield@sl:~$ kubectl apply -f https://docs.projectcalico.org/v3.1/getting-started/kubernetes/installation/hosted/kubeadm/1.7/calico.yaml
    configmap "calico-config" created
    daemonset.extensions "calico-etcd" created
    service "calico-etcd" created
    daemonset.extensions "calico-node" created
    deployment.extensions "calico-kube-controllers" created
    clusterrolebinding.rbac.authorization.k8s.io "calico-cni-plugin" created
    clusterrole.rbac.authorization.k8s.io "calico-cni-plugin" created
    serviceaccount "calico-cni-plugin" created
    clusterrolebinding.rbac.authorization.k8s.io "calico-kube-controllers" created
    clusterrole.rbac.authorization.k8s.io "calico-kube-controllers" created
    serviceaccount "calico-kube-controllers" created

**3, 确保所有的pod此刻都是running**

使用kubectl get pods --all-namespaces来查看。

    
    
    gemfield@sl:~$ watch kubectl get pods --all-namespaces
    #输出
    NAMESPACE     NAME                                       READY     STATUS              RESTARTS   AGE
    kube-system   calico-etcd-z4vwl                          1/1       Running             0          9m
    kube-system   calico-kube-controllers-685755779f-tkssx   0/1       Pending             0          9m
    kube-system   calico-node-2fw5b                          0/2       ContainerCreating   0          9m
    kube-system   etcd-sl                                    1/1       Running             0          47m
    kube-system   kube-apiserver-sl                          1/1       Running             0          47m
    kube-system   kube-controller-manager-sl                 1/1       Running             0          47m
    kube-system   kube-dns-86f4d74b45-psbkm                  0/3       Pending             0          46m
    kube-system   kube-proxy-qsf27                           1/1       Running             0          46m
    kube-system   kube-scheduler-sl                          1/1       Running             0          47m

就在这里看着，直到所有的状态都变成Running。Gemfield大约等了20分钟，可能是在pull image吧。

    
    
    gemfield@sl:~$ watch kubectl get pods --all-namespaces
    #输出
    NAMESPACE     NAME                                       READY     STATUS    RESTARTS   AGE
    kube-system   calico-etcd-z4vwl                          1/1       Running   0          21m
    kube-system   calico-kube-controllers-685755779f-tkssx   1/1       Running   0          21m
    kube-system   calico-node-2fw5b                          2/2       Running   0          21m
    kube-system   etcd-sl                                    1/1       Running   0          59m
    kube-system   kube-apiserver-sl                          1/1       Running   0          59m
    kube-system   kube-controller-manager-sl                 1/1       Running   0          59m
    kube-system   kube-dns-86f4d74b45-psbkm                  3/3       Running   1          59m
    kube-system   kube-proxy-qsf27                           1/1       Running   0          59m
    kube-system   kube-scheduler-sl                          1/1       Running   0          59m

**4，确定你的集群里现在有node了**

    
    
    gemfield@sl:~$ kubectl get nodes -o wide
    NAME      STATUS    ROLES     AGE       VERSION   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
    sl        Ready     master    1h        v1.10.1   <none>        Ubuntu 16.04.3 LTS   4.13.0-38-generic   docker://1.13.1

##  **四，添加其它node**

登陆到需要添加的node上，切换到root账户（注意：如果你在墙内，这个node也需要配置docker server的代理）。

    
    
    #切换到root账户下
    root@ai:~# kubeadm join 192.168.1.118:6443 --token 9frx62.qp99ri6ds8mo6p41 --discovery-token-ca-cert-hash sha256:a7cff4b98899bcc0a4d5d9eae41648a8f42d4e7334ae52a3ec17910b7e4869af
    [preflight] Running pre-flight checks.
            [WARNING SystemVerification]: docker version is greater than the most recently validated version. Docker version: 17.12.0-ce. Max validated version: 17.03
            [WARNING FileExisting-crictl]: crictl not found in system path
    Suggestion: go get github.com/kubernetes-incubator/cri-tools/cmd/crictl
    [discovery] Trying to connect to API Server "192.168.1.118:6443"
    [discovery] Created cluster-info discovery client, requesting info from "https://192.168.1.118:6443"
    [discovery] Requesting info from "https://192.168.1.118:6443" again to validate TLS against the pinned public key
    [discovery] Cluster info signature and contents are valid and TLS certificate validates against pinned roots, will use API Server "192.168.1.118:6443"
    [discovery] Successfully established connection with API Server "192.168.1.118:6443"
    
    This node has joined the cluster:
    * Certificate signing request was sent to master and a response
      was received.
    * The Kubelet was informed of the new secure connection details.
    
    Run 'kubectl get nodes' on the master to see this node join the cluster.


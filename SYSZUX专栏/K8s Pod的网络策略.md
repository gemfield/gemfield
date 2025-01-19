# 背景
你有听说过大名鼎鼎的TorchPod吗？没有的话也完全没关系，它就是一个经典的K8s Pod，只不过使用的image包含了如下用于开发的组件：

- KDE桌面系统
- 常用开发工具
- conda
- Intel MKL
- Nvidia CUDA
- PyTorch

于是使得原本用作微服务的Pod，摇身一变成为了云上炼丹师们的开发环境。哦，其实你不需要关心这些东西，你只需要知道，TorchPod是一个经典的K8s Pod。

那么问题是什么呢？那就是，TorchPod作为一个团队的开发环境，必然要保证其系统安全。而在这些安全之中，最主要的一项就是网络策略——也就是管理员要设计和决定流向/流出K8s Pod的网络流量。没错，MLab HomePod的网络安全就使用了K8s的Pod的NetworkPolicy。要使用NetworkPolicy，你需要确保你的k8s集群配置的network plugin支持NetworkPolicy。

# NetworkPolicy简介
默认情况下，k8s的pod的网络是不受限的——它接收来自任何来源的流量。一旦有某个NetworkPolicy选中了该pod，则该pod的网络就变成受限的了。需要注意的是，NetworkPolicy中定义的多个策略是叠加的（不是互斥的），因此策略定义的顺序并不影响最终的结果。

一个典型的NetworkPolicy配置如下：
```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gemfield-policy
  namespace: mlab2
spec:
  podSelector:
    matchLabels:
      app: homepod
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 172.17.0.0/16
        except:
        - 172.17.1.0/24
    - namespaceSelector:
        matchLabels:
          project: deepvac
    - podSelector:
        matchLabels:
          app: civilnet
    ports:
    - protocol: TCP
      port: 27030
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/24
    ports:
    - protocol: TCP
      port: 7030
```
我们知道在4层上，用来控制网络流量的四元组是：源IP、源port、目的ip、目的port（协议）。下面要讨论的术语就包含了对这个四元组的实践（其实只用到了三个），Gemfield来一一解释下：

- apiVersion、kind为k8s yaml中的基础关键字，不再赘述；
- metadata，定义了名称和命名空间，其中NetworkPolicy的名称必须符合dns name规范；
- spec部分就是该策略的详细定义了，包含有podSelector、policyTypes、ingress、egress。

1，podSelector: 指明NetworkPolicy要适用到哪一组（或一个）pod上，上述例子中使用lable "app=homepod"选中了一组pod。podSelector如果值为空的话，则表明选中了当前namespace下的所有pod：
```
spec:
  podSelector: {}
```
2，policyTypes: 每个NetworkPolicy 都包含了一个policyTypes列表，值可以为Ingress、Egress或者两者。Ingress和Egress的含义在下面有解释。如果一个NetworkPolicy上没有指定policyTypes，那么Ingress默认会被设置上，而Egress只有配置上至少一条规则后才会生效。

3，ingress: 每个NetworkPolicy都可以包含一组（列表）ingress规则。ingress规则由from和ports关键字定义，用来决定从from来的连接能否到达该pod上的ports。比如上面的例子就在说，该pod仅允许从172.17.0.0/16、deepvac命名空间下的pod、当前命名空间下的app标记为civilnet的Pod来访问，且只能访问被选中pod的27030端口。

4，egress: 每个NetworkPolicy都可以包含一组（列表）egress规则。egress规则由to和ports关键字定义，用来决定当前pod能否访问pod to 的ports。比如上面的例子就在说，当前pod（被选中的pod）可以访问10.0.0.0/24地址空间下的任何一个ip上的7030端口。

# TorchPod的NetworkPolicy
对于TorchPod来说，Gemfield的网络策略设计如下：

TorchPod位于mlab2命名空间下（以后会更新到mlab3命名空间）；
只能允许192.168.0.0/16和172.17.0.0/16 这些局域网地址来访问HomePod；
只能访问HomePod的5900、7030端口（HomePod中的服务所侦听的端口）；
从TorchPod只能访问192.168.0.xx、http://192.168.0.xxx的22端口（这是两个数据备份服务器的IP）。
那么TorchPod的k8s NetworkPolicy设计如下：
```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: homepod-policy
  namespace: mlab2
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 192.168.0.0/16
    - ipBlock:
        cidr: 172.17.0.0/16
    ports:
    - protocol: TCP
      port: 5900
    - protocol: TCP
      port: 7030
  egress:
  - to:
    - ipBlock:
        cidr: 192.168.0.xx/32
    - ipBlock:
        cidr: 192.168.0.xxx/32
    ports:
    - protocol: TCP
      port: 22
```
# 总结
借助K8s的NetworkPolicy，Gemfield实现了MLab HomePod的网络访问控制。但是仍有一些不完美的地方...最大的问题就是，云上炼丹师们需要经常做以下依赖网络的操作：
```
apt install
pip install
git clone
```
而前述的yaml文件并不能覆盖这些操作，问题在于：

- 如何通过NetworkPolicy指定apt服务器、pip服务器、github服务器的域名地址？
- 上面这一步解决后，必然要开放对这三类服务器的80或者443端口的访问（web服务）；我们原意只是想允许下载，而禁止上传——但是下载和上传都属于egress范畴，显然NetworkPolicy解决不了。

针对这些问题，Gemfield已经设计了另外一套方案，这里就不展开了。那么，你有什么好的建议呢？

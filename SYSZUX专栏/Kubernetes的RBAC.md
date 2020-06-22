##  **背景**

RBAC是Role-based access control的缩写，是一种访问控制的模型。K8s的RBAC API定义了四种K8s对象：

  * Role 
  * ClusterRole 
  * RoleBinding 
  * ClusterRoleBinding 

这些rule给予的权限都是纯添加的，没有那种禁止某种权限的rule——言外之意就是一开始什么都没有、不添加就没有。因为rule是给user用的，我们还需要创建user。Kubernetes集群有两种user:
Kubernetes管理的service accounts、常规的users，下面分别予以描述。

RBAC rule就是给一些user的一些资源定义一些操作/动作。

**资源（resource）** 一般有：

  * Pods 
  * PersistentVolumes 
  * ConfigMaps 
  * Deployments 
  * Nodes 
  * Secrets 
  * Namespaces 

**操作/动作（verb）** 一般有：

  * create 
  * get 
  * delete 
  * list 
  * update 
  * edit 
  * watch 
  * exec 

##  **环境准备**

**1，创建namespace**

在开始本文之前，先创建一个namespace：

    
    
    gemfield@master:~$ kubectl create namespace mlab2
    
    #我再创建一个，反正不花钱
    gemfield@master:~$ kubectl create namespace devel

**2，创建serviceaccount（和User二选一）**

Gemfield使用了serviceaccount，因为这个使用起来很简单：

    
    
    gemfield@master:~$ kubectl -n mlab2 create serviceaccount gemfield

这里Gemfield创建了gemfield账户......至此，serviceaccount gemfield创建完毕了。

**3，创建User（和serviceaccount二选一）**

**如果不想使用serviceaccount，可以选择这种方式。**

创建用户私钥：

    
    
    syszux@master:~/gemfield$ openssl genrsa -out gemfield.key 2048

创建证书签名申请crt：

    
    
    syszux@master:~/gemfield$ openssl req -new -key gemfield.key -out gemfield.csr -subj "/CN=gemfield/O=civilnet"

Kubernetes集群的证书机构certificate authority
(CA)的授权文件在/etc/kubernetes/pki/目录下（ca.crt和ca.key），用来负责批准上述的证书签名申请，并生成必要的证书用来授权对K8s集群API的访问。要批准并创建证书，使用下面的命令，有效期365天：

    
    
    syszux@master:~/gemfield$ openssl x509 -req -in gemfield.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out gemfield.crt -days 365

创建$HOME/.cert目录，然后把申请后的证书以及Key放进来，因为后面创建$HOME/.kube/config的时候，config内容里会引用这个地址。下面开始创建$HOME/.kube/config文件：

    
    
    syszux@master:~/gemfield$ mv gemfield.key ~/.cert/
    syszux@master:~/gemfield$ mv gemfield.crt ~/.cert/
    
    #配置用户证书
    syszux@master:~/gemfield$ kubectl config set-credentials gemfield --client-certificate=/home/syszux/.cert/gemfield.crt --client-key=/home/syszux/.cert/gemfield.key
    
    配置cluster
    syszux@master:~/gemfield$ kubectl config set-cluster gemfield --server=https://192.168.0.95:6443 --insecure-skip-tls-verify
    #配置context
    syszux@master:~/gemfield$ kubectl config set-context gemfield-context --cluster=gemfield --namespace=devel --user=gemfield
    syszux@master:~/gemfield$ kubectl config use-context gemfield-context

至此，User gemfield就创建完毕了。

##  **判断当前账户的权限**

K8s提供了一个can-i子命令，用来判断在指定的命名空间下是否有某种权限：

    
    
    gemfield@ThinkPad-X1C:~$ kubectl auth can-i create deployments --namespace dev

admin用户可以模拟某个用户，以测试这个用户是否有某些权限：

    
    
    gemfield@ThinkPad-X1C:~$ kubectl auth can-i list secrets --namespace dev --as gemfield

##  **Role和ClusterRole**

**可以创建Role和ClusterRole。**

1，如果需要创建一个Role

举个例子，创建一个在mlab-2命名空间下可以登录pod的role：

    
    
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      namespace: mlab2
      name: mlab-user
    rules:
    - apiGroups: [""]
      resources: ["pods", "pods/log"]
      verbs: ["get", "watch", "list"]
    - apiGroups: [""]
      resources: ["pods/exec"]
      verbs: ["create"]

再举个例子，创建一个用于开发的role：

    
    
    kind: Role
    apiVersion: rbac.authorization.k8s.io/v1beta1
    metadata:
      namespace: devel
      name: mlab-devel
    rules:
    - apiGroups: ["", "extensions", "apps"]
      resources: ["deployments", "replicasets", "pods", "pods/log"]
      verbs: ["get", "list", "watch", "update", "patch", "delete"]
    - apiGroups: [""]
      resources: ["pods/exec"]
      verbs: ["create"]

2，如果需要创建一个ClusterRole

设置权限为可以读secrets，因为是ClusterRole，所以可以读任何namespace

    
    
    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRole
    metadata:
      # "namespace" omitted since ClusterRoles are not namespaced
      name: secret-reader
    rules:
    - apiGroups: [""]
      resources: ["secrets"]
      verbs: ["get", "watch", "list"]

##  **RoleBinding 和 ClusterRoleBinding**

RoleBinding就是将Role绑定到User上的，相当于给一个User授予指定权限。可以使用YAML文件创建RoleBinding:

    
    
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: use-mlab-devel
      namespace: devel
    subjects:
    - kind: User
      name: gemfield
      apiGroup: rbac.authorization.k8s.io
    roleRef:
      kind: Role
      name: mlab-devel
      apiGroup: rbac.authorization.k8s.io

也可以使用命令行，绑定一个serviceaccount。还记得吗，本文前面为了图省事，创建的是serviceaccount。使用如下的命令来进行绑定：

    
    
    gemfield@master:~$ kubectl -n mlab2 create rolebinding use-mlab2-pods --serviceaccount=mlab2:gemfield --role=mlab-user

##  **创建用于kubectl命令的鉴权文件**

我们需要在$HOME/.kube/目录下生成一个config文件，这样方能愉快的让刚才创建的gemfield用户来使用kubectl命令。使用如下的命令来生成这个config鉴权配置文件：

    
    
    gemfield@master:~$ TOKEN=$(kubectl -n mlab2 describe secrets "$(kubectl -n mlab2 describe serviceaccount gemfield | grep -i Tokens | awk '{print $2}')" | grep token: | awk '{print $2}')
    gemfield@master:~$ kubectl config set-credentials gemfield --token=$TOKEN
    gemfield@master:~$ kubectl config set-cluster gemfield --server=https://192.168.0.95:6443 --insecure-skip-tls-verify
    gemfield@master:~$ kubectl config set-context mlab2user --cluster=gemfield --user=gemfield
    gemfield@master:~$ kubectl config use-context mlab2user

这些命令分别对应的设置了config文件中的不同字段，执行完成后，$HOME/.kube/config文件的内容如下所示：

    
    
    apiVersion: v1
    clusters:
    - cluster:
        insecure-skip-tls-verify: true
        server: https://192.168.0.95:6443
      name: gemfield
    contexts:
    - context:
        cluster: gemfield
        user: gemfield
      name: mlab2user
    current-context: mlab2user
    kind: Config
    preferences: {}
    users:
    - name: gemfield
      user:
        token: eyJhbGciOiJSUzI1NiIsImtpZCI6InJESzlfaF9Hc2lHMThVdU5mM0M3UWhRRlRsUzFmUHZaZXBYOHNkajJGN1EifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJtbGFiMiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJnZW1maWVsZC10b2tlbi1ucG10OCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJnZW1maWVsZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjVhYjQ0NDFhLWNhNDktNGRmOS1hMjZiLTM4MzYzMmMyMzBmMSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDptbGFiMjpnZW1maWVsZCJ9.E-pM3XJgcdphz2gYUktb9WLChqOx8ZTWWd_6ML0aqE-ht8V1MNeHpX45USFHsSQ_rtF8lWB6gfITLLXgYo52NYYQmUWxjSMNAIi_fl-oUdTwqUstt9JLNYkCc3WqORJ3EAz2ecoKo1TOKUvkPkvYOht8AwF2h2ejmW1OzNOjGIlGHiWTo40OsLceAYe_neQ8kk4T4Owa9oala_otwZXMIjy0X77QDPVAkmYP4wzl3E3ehZxS4Zp82EjhVw93uxOuyjI5RR0Ucq68zvGBGzAWENgELsrDKG_JYK6Tr_X-RjrbUKGnLcDAeJ6A87P0GJIUgwSXS3U4b6BnFA9e2TVnFQ

##  **最终使用效果**

现在，gemfield用户可以使用kubectl命令了。比如，可以list当前的pod：

    
    
    civilnet@master:~$ kubectl get po -n mlab2
    NAME                              READY   STATUS    RESTARTS   AGE
    gemfieldhome-5ff6d79c75-2vq4g     1/1     Running   0          32h
    gemfieldsshd-779bcd8d64-9fq4w     1/1     Running   0          28h

如果访问default命名空间，对不起，没有被授予权限：

    
    
    civilnet@master:~$ kubectl get po
    Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:mlab2:gemfield" cannot list resource "pods" in API group "" in the namespace "default"

如果想在mlab2命名空间下删除一个pod，对不起，没有被授予权限：

    
    
    civilnet@master:~$ kubectl -n mlab2 delete pod gemfieldhome-5ff6d79c75-2vq4g
    Error from server (Forbidden): pods "gemfieldhome-5ff6d79c75-2vq4g" is forbidden: User "system:serviceaccount:mlab2:gemfield" cannot delete resource "pods" in API group "" in the namespace "mlab2"


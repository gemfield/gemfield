# 背景
最近有一个小项目涉及到了opengl的开发，不同于以往，这次Gemfield使用的是Docker化的OpenGL开发模式，部署也是使用了同样的模式。实践此文，你需要具备以下环境：

- 安装有Ubuntu或者其它Linux发行版的宿主机；
- 宿主机上安装有Nvidia驱动:
```
gemfield@ThinkPad-X1C:~$  lsmod | grep nvidia
nvidia_uvm            966656  0
nvidia_drm             45056  8
nvidia_modeset       1114112  21 nvidia_drm
nvidia              20430848  1119 nvidia_uvm,nvidia_modeset
drm_kms_helper        184320  2 nvidia_drm,i915
drm                   491520  13 drm_kms_helper,nvidia_drm,i915
ipmi_msghandler       106496  2 ipmi_devintf,nvidia
```
- Docker；
```
gemfield@ThinkPad-X1C:~$ docker version
Client: Docker Engine - Community
 Version:           19.03.8
 API version:       1.40
 Go version:        go1.12.17
 Git commit:        afacb8b7f0
 Built:             Wed Mar 11 01:25:55 2020
 OS/Arch:           linux/amd64
 Experimental:      false

Server: Docker Engine - Community
 Engine:
  Version:          19.03.8
  API version:      1.40 (minimum version 1.12)
  Go version:       go1.12.17
  Git commit:       afacb8b7f0
  Built:            Wed Mar 11 01:24:26 2020
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.2.13
  GitCommit:        7ad184331fa3e55e52b890ea95e65ba581ae3429
 runc:
  Version:          1.0.0-rc10
  GitCommit:        dc9208a3303feef5b3839f4323d9beb36df0a9dd
 docker-init:
  Version:          0.18.0
  GitCommit:        fec3683
```
- Nvidia-docker2或者nvidia-container-toolkit，请参考：
Gemfield：使用nvidia-docker2
​zhuanlan.zhihu.com/p/37519492

Gemfield使用的是nvidia-docker2，年纪大了，不想换更新的nvidia-container-toolkit来尝鲜了。

# 安装OpenGL环境
1，准备docker image

Gemfield使用的是Nvidia官方的nvidia/opengl：

Docker Hub
​hub.docker.com/r/nvidia/opengl
开发环境是nvidia/opengl:1.0-glvnd-devel，运行时使用的时nvidia/opengl:1.0-glvnd-runtime。你也可以从头编译这个image，相关的Dockerfile如下：
```
FROM ubuntu:18.04
LABEL maintainer "Gemfield CivilNet <gemfield@civilnet.cn>"

RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y --no-install-recommends \
        libxau6 libxau6:i386 \
        libxdmcp6 libxdmcp6:i386 \
        libxcb1 libxcb1:i386 \
        libxext6 libxext6:i386 \
        libx11-6 libx11-6:i386 && \
    rm -rf /var/lib/apt/lists/*

# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics,compat32,utility

RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

# Required for non-glvnd setups.
ENV LD_LIBRARY_PATH /usr/lib/x86_64-linux-gnu:/usr/lib/i386-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config \
    	libglvnd-dev libglvnd-dev:i386 \
	libgl1-mesa-dev libgl1-mesa-dev:i386 \
	libegl1-mesa-dev libegl1-mesa-dev:i386 \
	libgles2-mesa-dev libgles2-mesa-dev:i386 && \
    rm -rf /var/lib/apt/lists/*
```
可以看到，我们的OpenGL编程基于的是mesa库。简单介绍下这几个库：

- libgl是opengl的实现；
- libgles是opengles的实现；
- libegl是opengl、opengles和当前操作系统的窗口系统之间的桥梁，也就是传说中的libegl创建的context，libegl早先是现在移动端连接起系统(Android、黑莓、Tizen)和opengles，这些年也开始进军桌面了（wayland等，看下一条）；
- 如果说libegl是向开发者屏蔽了操作系统的区别，那么没有libegl的时候，要创建OpenGL context，Windows提供的是WGL，MacOS提供的是CGL，Vulkan提供的是 WSI ，而X11提供的是GLX（libGLX.so）。

2，安装编译相关的软件包

nvidia/opengl中并没有安装编译相关的工具，gemfield需要的是CMake、g++等工具，以及libfreeimage-dev库，因此要么在Dockerfile中追加这些安装，要么容器启动后再自行安装。Gemfield是提前安装好的：
```
RUN apt-get update && apt-get install -y --no-install-recommends \
        cmake g++ libfreeimage-dev && \
    rm -rf /var/lib/apt/lists/*
```
3，启动docker

启动docker之前，需要先设置允许docker中的root进程能够访问当前的Xorg会话：
```
gemfield@ThinkPad-X1C:~$ xhost local:root
```
不然运行GUI程序会报错：No protocol specified。

然后使用下面的命令来启动Docker容器：
```
gemfield@ThinkPad-X1C:~$ docker run --runtime=nvidia --rm -it \
        -v /home/gemfield:/home/gemfield \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -e DISPLAY -e XAUTHORITY -e NVIDIA_DRIVER_CAPABILITIES=all \
        nvidia/opengl:1.0-glvnd-devel bash
```
经过这样的启动参数设置后，docker里就可以启动GUI程序了。

# 代码和编译
1，Hello Triangle

使用来自CivilNet/Gemfield仓库的代码，也就几十行：

https://github.com/CivilNet/Gemfield/blob/master/src/cpp/opengl/gemfield_hello_triangle.cpp
​github.com/CivilNet/Gemfield/blob/master/src/cpp/opengl/gemfield_hello_triangle.cpp
代码使用了EGL和Xlib，Xlib的XOpenDisplay 函数建立起和X Server的连接，参数的意义等价于DISPLAY环境变量，NULL的话就使用的是default。XOpenDisplay返回一个Display指针，使用DefaultScreenOfDisplay(Display* display)获得screen。

2，编译

使用如下的命令来进行编译：
```
g++ gemfield_hello_triangle.cpp -o gemfield -lEGL -lGLESv2 -lX11
```
可见编译这个程序需要链接这3个库：libEGL.so、libGLESv2.so、libX11.so。在Nvidia的容器中，这些库正是由NVIDIA实现的，在NVIDIA的libglvnd官方仓库中：

https://github.com/NVIDIA/libglvnd/tree/master/src
​github.com/NVIDIA/libglvnd/tree/master/src
GLX目录用来编译生成libGLX.so，EGL目录用来编译生成libEGL.so，GLdispatch目录用来编译生成libGLdispatch.so（这个库用来将opengl的函数调用派发到相应的各厂商实现的opengl库中），OpenGL、 GLESv1、 GLESv2目录分别用来编译生成libOpenGL.so、 libGLESv1_CM.so、libGLESv2.so，这些库都只是libGLdispatch的wrapper，最终的实现都是在各厂商名作为后缀的库里（比如libGLX_mesa.so、libGLX_nvidia.so、libEGL_mesa.so、libEGL_nvidia.so）。更多信息，可以参考：

https://www.x.org/wiki/Events/XDC2016/Program/xdc-2016-glvnd-status.pdf
​www.x.org/wiki/Events/XDC2016/Program/xdc-2016-glvnd-status.pdf
2016年以来，在glvnd规范的指引下，Linux平台上的opengl ABI迎来了新的纪元。

3，运行
```
./gemfield
```
一个红色的三角形就会显示在你的Linux窗口系统上。

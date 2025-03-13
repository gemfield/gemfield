# 背景
我们大家平常使用的python实现都是cpython，所以使用C语言或者C++来写一些扩展的时候，就相当于在写cpython的插件。cpython的扩展关键在于要实现一个PyObject* PyInit_modulename(void)的函数，也叫initialization function，这个函数返回一个PyModuleDef 的instance。

本文中，gemfield将介绍如何使用pybind11 来实现cpython的扩展。

# 从源码安装pybind11环境
## 1，基于Ubuntu 16.04
## 2，安装必要的依赖
```bash
gemfield@ThinkPad-X1C:~$ apt update
gemfield@ThinkPad-X1C:~$ apt install vim git cmake python3-dev python3-pip
gemfield@ThinkPad-X1C:~$ pip3 install pytest
```
## 3，克隆pybind11仓库
```bash
gemfield@ThinkPad-X1C:~$ git clone https://github.com/pybind/pybind11

#在pybind11项目目录下
gemfield@ThinkPad-X1C:~/pybind11$ mkdir build && cd build && cmake ..
-- Building tests WITHOUT Eigen
-- Could NOT find Boost
-- Catch not detected. Interpreter tests will be skipped. Install Catch headers manually or use `cmake -DDOWNLOAD_CATCH=1` to fetch them automatically.
-- pybind11 v2.3.dev0
-- Configuring done
-- Generating done
-- Build files have been written to: /root/pybind11/build
```
## 4，编译
```bash
#编译
gemfield@ThinkPad-X1C:~/pybind11/build$ make check -j 4
......
===== 229 passed, 89 skipped in 5.67 seconds =====

#安装
gemfield@ThinkPad-X1C:~/pybind11/build$ make install
```

## 5，设置PYTHONPATH
```bash
#设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/home/gemfield/pybind11
```
否则会报类似下面的错误：
```bash
/usr/bin/python3: No module named pybind11.__main__; 'pybind11' is a package and cannot be directly executed；
```
或者
```bash
/usr/bin/python3: No module named pybind11
```

# 绑定函数
## 1，源代码示例
```c++
//gemfield.cpp
#include <pybind11/pybind11.h>

int add(int i, int j) {
    return i + j;
}

PYBIND11_MODULE(gemfield, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring
    m.def("add", &add, "A function which adds two numbers");
}
```
## 2，编译
```bash
#该编译命令会生成 gemfield.cpython-35m-x86_64-linux-gnu.so
g++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 --includes` gemfield.cpp -o gemfield`python3-config --extension-suffix`
```
## 3，运行
```bash
......
Python 3.5.2 (default, Nov 12 2018, 13:43:14) 
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import gemfield
>>> gemfield.add(1,7)
8
```
## 4，发生了什么
上述PYBIND11_MODULE(gemfield, m)的宏展开了后，如下所示：
```c++
static void pybind11_init_gemfield(pybind11::module &); 
extern "C" __attribute__ ((visibility("default"))) PyObject *PyInit_gemfield() { 
    { 
        const char *compiled_ver ="3.5"; 
        const char *runtime_ver = Py_GetVersion(); 
        size_t len = std::strlen(compiled_ver); 
        if (std::strncmp(runtime_ver, compiled_ver, len) != 0 || (runtime_ver[len] >= '0' && runtime_ver[len] <= '9')) { 
            PyErr_Format(PyExc_ImportError, "Python version mismatch: module was compiled for Python %s, " "but the interpreter version is incompatible: %s.", compiled_ver, runtime_ver); 
            return nullptr; 
        } 
    } 
    auto m = pybind11::module("gemfield"); 
    try { 
        pybind11_init_gemfield(m); 
        return m.ptr(); 
    } catch (pybind11::error_already_set &e) { 
        PyErr_SetString(PyExc_ImportError, e.what()); 
        return nullptr; 
    } catch (const std::exception &e) { 
        PyErr_SetString(PyExc_ImportError, e.what()); 
        return nullptr; 
    } 
}

void pybind11_init_gemfield(pybind11::module &m){
    m.doc() = "pybind11 example plugin";
    m.def("add", &add, "A function which adds two numbers");
}
```
可以看到实现了PyObject *PyInit_gemfield()函数。

# 绑定类
既然是C++，就不能不提到class。

## 1，源代码示例
#文件syszuxav.cpp
```c++
#include <pybind11/pybind11.h>
#include <iostream>

extern "C" bool initav(const char* url);
class SYSZUXav {
    public:
        SYSZUXav(const std::string &url) : url(url){initav(url.c_str());}
        const std::string &getFrame() const;

    private:
        std::string url;
};

const std::string& SYSZUXav::getFrame() const
{
    std::cout<< url << std::endl;
    return url;
}

PYBIND11_MODULE(syszuxav, m) {
    pybind11::class_<SYSZUXav>(m, "SYSZUXav")
        .def(pybind11::init<const std::string &>())
        .def("getFrame", &SYSZUXav::getFrame);
}
```
## 2，编译
```bash
g++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 --includes` syszuxav.cpp -o syszuxav`python3-config --extension-suffix`
```
## 3，运行
那就在Python中import吧。
## 4，发生了什么
上述PYBIND11_MODULE(syszuxav, m)宏展开了后，代码如下所示：
```c++
extern "C" bool initav(const char* url);
class SYSZUXav {
    public:
        SYSZUXav(const std::string &url) : url(url){initav(url.c_str());}
        const std::string &getFrame() const;

    private:
        std::string url;
};

const std::string& SYSZUXav::getFrame() const
{
    std::cout<< url << std::endl;
    return url;
}

static void pybind11_init_syszuxav(pybind11::module &); 
extern "C" __attribute__ ((visibility("default"))) PyObject *PyInit_syszuxav() 
{ 
    { 
        const char *compiled_ver = "3.5"; 
        const char *runtime_ver = Py_GetVersion(); 
        size_t len = std::strlen(compiled_ver); 
        if (std::strncmp(runtime_ver, compiled_ver, len) != 0 || (runtime_ver[len] >= '0' && runtime_ver[len] <= '9')) { 
            PyErr_Format(PyExc_ImportError, "Python version mismatch: module was compiled for Python %s, \
                    but the interpreter version is incompatible: %s.", compiled_ver, runtime_ver); 
            return nullptr;
        } 
    } 
    auto m = pybind11::module("syszuxav"); 
    try { 
        pybind11_init_syszuxav(m); 
        return m.ptr(); 
    } catch (pybind11::error_already_set &e) { 
        PyErr_SetString(PyExc_ImportError, e.what()); 
        return nullptr; 
    } catch (const std::exception &e) { 
        PyErr_SetString(PyExc_ImportError, e.what()); 
        return nullptr; 
    } 
} 
void pybind11_init_syszuxav(pybind11::module &m)
{
    pybind11::class_<SYSZUXav>(m, "SYSZUXav").def(pybind11::init<const std::string &>()).def("getFrame", &SYSZUXav::getFrame);
}
```
可以看到实现了PyObject *PyInit_syszuxav()函数。
# 福利
最后，包含initav函数在内的整个实现开源在了：[CivilNet/SYSZUXav](https://github.com/CivilNet/SYSZUXav)

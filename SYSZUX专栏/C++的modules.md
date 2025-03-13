# 背景
先看一段使用了module的小程序：
```c++
//gemfield.cpp
export module gemfield;
import <iostream>;
export void whoami(){
    std::cout<<"I am Gemfield."<<std::endl;
}

//main.cpp
import gemfield;
int main(){
    whoami();
}
```
使用g++编译（注意module是C++20加的，所以编译要加上-std=c++20；又因为import只有在开启-fmodules-ts下才能使用，所以还要加上-fmodules-ts）：
```bash
g++ -fmodules-ts -std=c++20 gemfield.cpp main.cpp -o gemfield
```
但是编译报错：
```bash
/usr/include/c++/11/iostream: error: failed to read compiled module: No such file or directory
/usr/include/c++/11/iostream: note: compiled module file is ‘gcm.cache/./usr/include/c++/11/iostream.gcm’
/usr/include/c++/11/iostream: note: imports must be built before being imported
/usr/include/c++/11/iostream: fatal error: returning to the gate for a mechanical issue
```
这是因为标准库还没有被转换成module，使用如下命令进行转换：
```bash
g++ -c -fmodules-ts -x c++-system-header  -std=c++20 iostream string vector
```
然后再编译，程序编译成功。上面就是使用C++ modules的一个最简化的例子。

# Modules的好处
从上面的程序示例中就可以看出，module替代的是之前的头文件。因此modules带来的好处自然就是头文件机制带来的坏处，主要有这么几点：

- 避免了include头文件重复预处理的过程，加快了编译速度；
- 避免了头文件中同名宏定义；
- 结构化及方便工具分析，得益于import和module关键字，工具能更快更有效的理解项目代码的依赖图；
- 源代码不再需要提供接口（头文件）+实现的形式。注意1：module当然也可以提供接口+实现的方式；注意2：这不是说头文件就完全不需要了，有些header-only的库还是有存在价值的，毕竟同一份源码就一个版本；而以二进制形式提供的库，同一份源码需要有多份不同的编译版本。

# 入门Modules语法
仅仅通过背景章节中的小例子，我们也能够看出module的一些基本语法：

- export module gemfield就是module的声明，声明了当前的翻译单元是个module unit（这是啥意思？后面讲）。放在whoami函数的前面，于是whoami就可以被export并使用；
- import gemfield 导入gemfield模块，并且使得whoami函数在main.cpp中可见。

下面的例子中：
```c++
export module gemfield; // 为命名module gemfield声明了 primary module interface unit
 
// 其它翻译单元如果使用import gemfield, 则whoami() 将可见
export char const* whoami() { return "I am Gemfield"; } 
 
// whoAreYou()则不可见
char const* whoAreYou() { return "CivilNet"; }
 
// one() 和 zero() 都可见
export{
    int one()  { return 1; }
    int zero() { return 0; }
}
 
// Exporting namespaces: gem::english() and gem::chinese() 都可见
export namespace gem{
    char const* english() { return "Hi!"; }
    char const* chinese()  { return "有朋自远方来"; }
}
```
- 在module中，import关键字必须出现在export之后，其它所有声明之前；
- 假如module A 中 import了 module B，那么import A也就间接的包含了import B；
```c++
/////// A.cpp (primary module interface unit of 'A')
export module A;
export char const* hello() { return "hello"; }
/////// B.cpp (primary module interface unit of 'B')
export module B;
export import A;
export char const* world() { return "world"; }
 
/////// main.cpp (not a module unit)
#include <iostream>
import B;
int main(){
    std::cout << hello() << ' ' << world() << '\n';
}
```
# Module Unit
module unit就是声明了module的翻译单元（translation unit）。分为如下几种：

- module interface unit：在module unit中声明module的时候使用了export关键字；
- module implementation unit：所有不是module interface unit 的module init，也就是没有使用export关键字；
- module partition：声明module时包含了module-partition（参考下面的module partitions章节）；
- module interface partition：首先是一个module interface unit，其次是一个module partition（也就是既有export关键字，又有module-partition）；
- module implementation partition：包含module-partition，但没有export关键字；
- primary module interface unit：没有partition的module interface unit。一个module只有一个primary module interface unit。

为了预防大型源文件变得难以处理， C++ module可以将单个module分为不同的翻译单元（多份源文件），这些翻译单元合并在一起形成整个module。这种分割方式称之为module partitions。

# Module partitions
假设我们不想在同一个模块中包含两个庞大、繁琐且笨拙的函数：
```c++
export module gemfield;
//假设下面的函数是庞大的
export const char* getWeibo(){
    return "@在通州"；
}
export const char* getZhihu(){
    return "libGemfield";
}
```
现在我们将上面的代码重构成使用module partitions：
```c++
//gemfield.cpp
export module gemfield;

export import :weibo;
export import :zhihu;

//gemfield_weibo.cpp
export module gemfield:weibo;
export const char* getWeibo(){
    return "@在通州"；
}

//gemfield_zhihu.cpp
export module gemfield:zhihu;
export const char* getZhihu(){
    return "libGemfield";
}

//main.cpp
import gemfield;
import <iostream>;

int main(){
    std::cout<<getWeibo()<<std::endl;
    std::cout<<getZhihu()<<std::endl;
}
```
上面的例子中，我们定义了：

- 一个叫gemfield的module;
- gemfield module有2个partitions：weibo和zhihu；
- export module <module-name>:<part-name> （比如：export module gemfield:weibo） 声明了一个属于module-name的module interface partition ;
- import :<part-name>（比如： import :zhihu)，import 由part-name指定的partition。注意：被import的partition必须属于当前的module；
- export import :<part-name> ，import到当前module的partition，再被export出去，这样该partition作为module interface的一部分对外可见了。注意：export import语法只适用于import interface partition。

其中，getWeibo、getZhihu函数都属于gemfield module。且：

- gemfield.cpp是primary module interface unit。注意：primary interface unit必须直接或间接的export出当前module的所有的interface partitions，否则程序错误；
- gemfield_weibo.cpp、gemfield_zhihu.cpp是module interface partitions；
- main.cpp是常规的翻译单元。

# module implementation unit
module关键字前没有export关键字的module unit，就是module implementation unit。在implementation unit中声明的实体，只在该module中可见。举个例子：
```c++
//gemfield.cpp
export module gemfield;
import :weibo
import :zhihu

export const char* getWeibo();
export const char* getZhihu();

// gemfield_weibo.cpp
module gemfield:weibo;
const char* getWeibo(){
    return "@在通州"；
}

// gemfield_zhihu.cpp
module gemfield:zhihu;
const char* getZhihu(){
    return "libGemfield";
}
```
相比于再往前一个的例子，这个例子做了如下改动：

- 在primary interface unit（也就是gemfield.cpp）中，没有使用export关键字来import partition；
- 在partition中（gemfield_weibo.cpp、gemfield_zhihu.cpp），也没有使用export关键字，这就使得这俩翻译单元从之前的module interface partitions变成了implementation partitions；
- implementation partitions中的函数也没有export关键字了，注意：在implementation unit中是否使用export关键字没关系；
- 在primary interface unit中，这俩函数的声明使用了export关键字，这就使得这俩函数也是接口的一部分（即使它们还没有被定义）。

实际上，在implementation units中不允许export关键字的存在。那么module implementation unit有什么好处呢？那就是，implementation units中的改动不会导致使用该module的其它源文件重新编译，从而大大加快整个工程的编译速度。

# Header Units 
在背景章节的小例子中，我们import 了<iostream>，iostream已经是module了吗？非也，它是Header Units。Header Units说的是，可以把include header直接改成import header：
```c++
#include <vector>      => import <vector>;
#include "gemfield.h"  => import "gemfield.h"; 
```
import查找头文件的方式遵循了include，但是，import又不像是include（只是文本替换），而是会生成一些中间物，并试图将其看成是真正的module——这种方式将导致编译速度超过precompiled headers。由于precompiled headers不是C++标准，各个编译器实现也不一样，因此header units就更吃香了。

但是美中不足的是，不是所有的header都可以import（C++标准保证了标准库头文件都可以import）。

# Global module fragment
在module中include头文件会带来一个问题，举个例子：
```c++
export module gemfield;
#include <standard_header.h>
```
这样做会将standard_header.h中的每个符号绑定到module gemfield上，很显然，这并不符合预期。那怎么办呢？一种解决方案就是使用上面说的header units：
```c++
export module gemfield;
import <standard_header.h>
```
但这也有两个问题：

- header unit 不会考虑当前翻译单元的preprocessor的状态，也就是当前翻译单元中的#define 宏对header units不起作用——这就产生了宏的单向隔离；
- 不是所有的header都可以import。

是时候有请global module fragment了，语法为：
```c++
module;
//#include <...>
//...
module gemfield;
```
第一行的module; 告诉编译器，虽然这是一个module，但是后面的内容先按照非module来处理，直到遇到module gemfield。于是，在module; 和module gemfield之间的代码（也就是global module fragment），将像从前那样进行预处理，且将被绑定到global module上（一个默认的隐式module，也是main函数所在的module）。

但请注意，只有preprocessor directive可以出现在global module fragment中，比如：
```c++
module;
extern void gem(); //错误，这不是preprocessor directive。

export module gemfield;
```
你可以改为：
```c++
//gem.h
extern void gem();

//gemfield.cpp
module;
#include "gem.h"   //正确，#include是 preprocessor directive。

export module gemfield;
```
# Private module fragment
通过上文，我们已经知道module也可以将interface和implementation分开。但有时候，我们既想把它分开，但又只想使用一个源码文件，可以吗？这就是private module fragment的作用。语法为：module : private;

举个例子： 
```c++
export module gemfield;
export int civilnet();

module : private; 

int civilnet() {          // civilnet函数的定义对别的翻译单元不可见
    return 7030;
}
```
Primary module interface unit后面可以跟个private，表明接口部分的内容到此结束。后面的内容将不再影响别的翻译单元。

# Module ownership
通常情况下，如果一个名称声明出现在module的声明之后，那么这个名称就会绑定到这个module上。并且，如果名称的声明被绑定到这个module上，那么它的定义也只能绑定到这个module上。

如果绑定到named module上的声明没有被export，那么该名称具有module linkage，这一点在Gemfield：C++的符号链接一文中已经说过：
```c++
export module gemfield;
int f() { return 0; } // f 具有module linkage
```
但是，前面说的是“通常情况下”名称会绑定到前面的module上，那什么情况下不会绑定呢？有两个例外：

- 当名称是namespace时；
- 名称声明时使用了language linkage specification。
```c++
export module gemfield;
namespace ns // ns没有绑定到gemfield上
{
    export extern "C++" int f(); // 函数f没有绑定到gemfield上
           extern "C++" int g(); // 函数g没有绑定到gemfield上
    export              int h(); // 函数h绑定到gemfield上
}
```
因此ns::h必须定义在module gemfield中，而ns::f、ns::g则可以定义到module之外。不过，namespace可以显式的进行export：
```c++
export namespace CivilNet {
   int gemfield = 7030; // 正确，export了CivilNet::gemfield
   static int gemfield2 = 7030; // 错误，internal linkage的符号不能export（参考下面）
}
```
# 还有什么符号不能被export？

- 具有internal linkage的符号，比如static变量/函数，比如匿名命名空间中的符号:
```c++
namespace {
   export void libGemfield() {}  //错误，匿名namespace
   export int gemfield = 7030; //错误，匿名namespace
   export class Gemfield {}; //错误，匿名namespace 
}

export static void gemfield() {} //错误，static函数
export static int gemfield = 7030; //错误，static变量
```
- 要export的符号必须在首次声明时就export：
```c++
export class Gemfield;  // 正确
export class Gemfield;  // 正确，只不过重复了
class Gemfield;  // 隐式带有export关键字

class Gemfield { // 隐式带有export关键字
    int g;
    int e;
};

class CivilNet; // 正确，没有export
export class CivilNet; // 错误! 要export的符号必须在首次声明时就export!
```
- 要export的符号必须在namespace层级，换言之，不能是在class内、函数内等。

# 背景
传统的C代码中，当我们处理异常情况的时候，我们使用的是函数返回值，或者是非局部的errno变量来指示一个错误或者异常的发生。而在C++中，我们引入了try、throw、catch关键字组成的异常处理机制，而且已经习以为常。但是，在异常处理这类问题中，为什么函数返回值不够好用，以至于我们需要新引入try catch呢？原因大概这几方面：

- 传统的代码中，处理异常的代码和正常的逻辑代码交织在一起，代码容易膨胀（各种if）、不好维护，容易出错；
- 构造函数这样没有返回值的函数，你就不得不使用try catch异常了；以及，异常后资源的自动释放也由stack unwinding来完成；
- 现代C++中，try catch 机制也不像有些人想象的那样会变慢程序的速度。在不发生异常的情况下，try catch 速度要好于或者等于 if(error)；而在发生异常的情况下，跳转到异常处理逻辑的速度会慢个3%左右？

既然我们知道了try catch异常处理机制的意义，我们不妨回答如下的问题，看看我们是否能够合规的运用try catch机制：

- throw和catch的是什么类型的对象？这种对象的类的继承体系是什么样的？如果遇到异常，我在程序中应该throw什么呢？
- catch接收throw的对象，是值拷贝、引用拷贝还是个指针呢？我应该使用哪种方式去catch呢？
- 一个try block后面经常跟着多个catch语句（携带不同的参数），那么throw的对象由哪个catch语句匹配？它的依据的是什么？
- 什么是rethrow？什么是catch-all handler？
- 构造函数中发生异常该怎么办？构造函数初始化列表发生异常怎么办？
- 析构函数中发生异常该怎么办？
- noexcept关键字有什么意义？合成的拷贝构造函数上有吗？析构函数是noexcept的吗？

# Exception object（异常对象）
我们在程序中throw的东西，就是Exception object（throw的对象）。它必须具备完整的类型，并且当其类型是class的时候，这个class必须具备可访问的析构函数、拷贝构造函数或者移动构造函数。如果throw的表达式（对象）是个数组或者函数类型，那么这个表达式会被转换为对应的指针类型。

Exception object会存放在由编译器管理的某个空间下，以此确保任何一个被匹配到的catch语句都可以访问的到。当异常被处理后，Exception object会被释放。当Exception object是个指针的时候，必须确保该指针指向的不是一个局部的内存，不然在try代码块结束的时候，该内存已经被释放，那么在catch中访问到的指针，指向的就是一个无效的地址了。

值得说明的是，throw表达式中的对象的类型为静态编译期决定的类型，比如，当throw一个基类修饰的指针的dereference，该指针指向子类的对象，那么当处在throw表达式中的时候，该dereference只会解出来基类部分然后throw。

而在catch语句的接收部分，当catch语句的参数类型是non reference类型的时候，那么这个参数就会被值拷贝，所有针对这个参数所做的修改都是局部有效的，而不是针对throw的Exception object的；当catch参数类型是引用的时候，不说了，其效果就和正常的函数传参是一样的。
标准库提供了如下的异常类（exception class）：

- std::exception
- std::runtime_error
- std::range_error
- std::overflow_error
- std::underflow_error
- std::logic_error
- std::domain_error
- std::invalid_argument
- std::length_error
- std::out_of_range
- std::bad_alloc
- std::bad_cast

这些类的继承关系如下所示：
![v2-25bdf96456e600bc3eb99498c3b85d3b_720w](https://github.com/user-attachments/assets/2611acc6-ed36-4552-8a92-f14c8b996fd0)

- std::exception是基类，定义了拷贝构造函数、赋值运算符、虚析构函数、返回值类型为const char*的虚成员函数what()；
- std::exception、std::bad_alloc、std::bad_cast还定义了默认构造函数， 因此不使用参数就可以默认初始化；
- 其它的exception class没有默认构造函数，你需要显式的使用字符串去初始化它们。另外，这些Exception class都定义了一个what()操作，内容为对Exception信息的文本描述。

# catch匹配和rethrow
throw一个对象后，程序逻辑并不是一定会到紧挨着try block的catch语句，也不是一定会到参数最匹配的catch语句，而是到达第一个参数能够匹配上的catch语句。这就是catch的匹配规则。所以在写代码的时候你要注意catch语句的排列顺序，尤其是对象的类型有一个继承体系的时候。

catch匹配规则和函数重载中的参数类型匹配规则还是有些不一样的，或者说，catch的参数类型匹配要更严格——除了以下几种情况，所有的类型转换都是禁止的：

- 从noncost到const是允许的；
- 从子类到基类的转换是允许的；
- 从数组到指针的转换是允许的；
- 从函数到函数类型的指针的转换是允许的。

正是因为上面这四种转换的存在，你才要更加注意catch语句的排列顺序。比如，由于从子类到基类的转换是允许的，所以catch语句的顺序中，越是子类越要往前放（如果基类在最前面，那么永远匹配的是第一个基类）。
有时候啊，我们还想在catch语句中继续throw这个异常，让别的catch去继续处理，这称之为rethrow。它的语法极其简单：
```c
throw;
```
没错，就是一个空的throw表达式。它默认Exception object会继续沿着catch链条往后传递。当然了，如果该Exception object是引用，那么在一个catch中针对Exception object所做的改变会在rethrow中继续往后传递。注意：rethrow表达式必须出现在catch语句中或者是catch语句调用的函数中，否则，程序将会terminate然后退出。

再有时候啊，我们想要catch任何的异常，不管Exception object的类型是什么，这种就是catch-all语句，语法为：
```c
catch(...)
```
catch-all语句一般有两种用法：

- 单独使用；这种情况下，catch-all一般做点清理工作，然后rethrow；
- 和其它catch语句一起使用；这种情况下，catch-all在顺序上要放到最后（不然就屏蔽了它后面的catch语句）。

# noexcept关键字
noexcept关键字的作用就在于，它同时告诉了编译器和用户一个事实：当前的函数不会发生异常。编译器得知这个事实后，可以更加的优化代码；用户得知这个事实后，可以不用想太多和异常相关的事情：
```c
void gemfield(int i); //这个函数可能会throw；
void gemfield(int i) noexcept; //承诺这个函数不会throw；
```
注意noexcept只是一份承诺，编译器并不会去检查该函数内部是否真的会不会throw。这就意味着，在noexcept的函数里代码如果有throw表达式，编译器并不会报错。取而代之的是，在运行时，程序会terminate。

注意，在noexcept之前还有另外的语法来描述同样的语义，所以你需要知道，以下两种语法是等价的：
```c
void gemfield(int i) noexcept;
void gemfield(int i) throw();
```
这两个gemfield函数都是承诺自身不会抛出异常 。noexcept接收参数，默认为true：
```c
void gemfield(int i) noexcept(true);
void gemfield(int i) noexcept(false);
```
如果基类的虚函数成员加上了noexcept关键字，那么子类也要承诺noexcept；如果基类的虚函数成员可以throw except，那么子类也可以承诺noexcept。也就是说子类可以更加严格，而不能更加宽松。

是否承诺不抛异常在某些情况下是很关键的，比如Gemfield曾提到过如下的用法：“移动构造函数不参与新的资源的申请，因此一般不会throw异常，于是最好是被noexcept修饰；此外，noexcept修饰的移动构造函数还具备其它的意义，标准库能否看到这个noexcept承诺会有不一样的行为。比如vector在push_back一个对象时，如果该对象的move constructor不能承诺noexcept，那么vector会转而使用这个对象的copy constructor，以确保vector在reallocation错误的时候，不会犯下回不去的错误。”

# 构造函数中的异常
如果在类的构造函数中发生了异常呢？可能和很多人的直觉相反，在构造函数中因为错误而主动throw异常是标准行为。因为构造函数没有返回值，人们是无从得知其构造是否成功，如果有错误，就抛出异常。那么已经new的资源会不会被释放呢？这个取决于是什么情况。
 
对于class实例化的对象而言，不管是在堆上还是栈上，这个资源一定是会释放的（注意：不代表这个对象的成员自己申请的资源啊）：
```c++
void gemfield()
{
  X x;             // If X::X() throws, the memory for x itself will not leak
  Y* p = new Y();  // If Y::Y() throws, the memory for *p itself will not leak
}
```
但是对于这个对象的成员来说，就不一定了。当成员没有申请动态内存，由于stack unwinding，这个资源是一定释放的；但是如果成员是个指针，并且指向了在构造函数中new的动态内存，那么之后发生的Exception将会导致内存泄漏：
```c++
class A{
    public:
        A(int i){i_ = i;}
        ~A(){}
    private:
        int i_;
};

class Gemfield{
    public:
        Gemfield(){a2 = new A(2); throw std::exception();}
        ~Gemfield(){}
    private:
        A a1{1};
        A* a2;
};
```
上面的代码片段中，类Gemfield的构造函数中抛出了异常，请回答以下问题：

- Gemfield的析构函数会被调用吗？
- a1的析构函数会被调用吗？也就是a1会被释放吗？
- a2的析构函数会被调用吗？a2 new的资源会被释放吗？

答案如下：

- Gemfield的析构函数不会被调用；但是由于stack unwinding，gemfield对象自身依然被销毁；
- a1的析构函数会被调用，a1的资源被释放；
- a2的析构函数不会被调用，a2指向的new申请的内存不会被释放，但是a2指针自身的8个字节会被销毁；

要想解决上述问题，答案就在于智能指针：https://zhuanlan.zhihu.com/p/271732707。

此外，为了处理构造函数初始化列表中发生的异常，我们必须将构造函数写为 function try block：
```c++
Gemfield::Gemfield(A a) try : a_(a) {
//constructor body
} catch(...){
  //handle the exception.
}
```
try关键字要放在“指示构造函数初始化列表开始的”分号前面。在这个例子中，catch语句连同构造函数体里的异常也一并会catch住。

# 析构函数中的异常
析构函数中可以throw异常吗？以C++11为例，默认情况下不可以。为啥说是默认情况呢？因为析构函数默认情况下是noexcept的：
```bash
gemfield.cpp: In destructor ‘A::~A()’:
gemfield.cpp:62:35: warning: throw will always call terminate() [-Wterminate]
   62 |         ~A(){throw std::exception();}
      |                                   ^
gemfield.cpp:62:35: note: in C++11 destructors default to noexcept
```
也就是说析构函数中的throw行为一定会导致程序的terminate，就像编译日志警告的那样：“note: in C++11 destructors default to noexcept”。那么如果我们显式的将析构函数的noexcept改为noexcept(false)呢？就像下面的代码展示的这样：
```c++
class A{
    public:
        A(int i){i_ = i;}
        ~A() noexcept(false){throw std::exception();}
    private:
        int i_;
};
```
答案是什么呢？

- 如果A的析构是由一次Exception导致的stack unwinding过程中触发的，那么答案是不可以。这种事情一旦发生，会使得我们的程序遇到这样尴尬的问题：在一个异常导致的stack unwinding的过程中，程序自动析构一些成员变量，在析构过程中再遇到异常，程序就不知道再继续处理哪个异常，因此还是terminate来快刀斩乱麻；
- 如果在上述情况下，如果A的析构可以在自身析构函数中被catch住，那么程序逻辑是正常的，如下所示：
```c++
class A{
    public:
        A(int i){i_ = i;std::cout<<"A construct "<<i<<std::endl;}
        ~A() noexcept(false){
            try{
                throw std::exception();
            }catch(...){}; 
        }
    private:
        int i_;
};
```
也就是说，你必须保证这个异常直接就在当前类的析构函数中被catch住。一旦异常离开了当前的析构函数，非常坏的事情将会发生——程序终止运行。

- 如果A的析构不是stack unwinding过程触发的，那么析构函数中的异常也可以被外面的catch语句捕获。

而从现实中的实践来看，由于析构函数是用来释放资源的，通常不会发生异常；即使发生异常，我们也没什么有效的应对措施。再综合上面的复杂情况，我们在实践中一般禁止在析构函数中抛出异常，改为记录日志等其它操作。

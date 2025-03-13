# 背景
本文主要讨论了C++对象的内存分配、对齐要求、生命周期等。

# 内存模型
说说byte和memory location这两个概念。
## 1，最小寻址单位：byte
C++内存模型中最基础的存储单元是byte，也是可编址的最小单位。下列类型正好需要一个byte来进行存储：

- char
- unsigned char
- signed char

一个byte中的bit数量可以从std::numeric_limits<unsignedchar>::digits 中获得（头文件：#include <limits>）。
## 2，memory location
memory location是一种标量类型（arithmetic type, pointer type, enumeration type, or std::nullptr_t）的对象，或者largest contiguous sequence of bit fields of non-zero length。后面这个有点难理解（比如啥是non-zero length的bit fields），举个例子：
```c++
struct S {
    char a;     // 第1个memory location
    int b : 5;  // 第2个memory location
    int c : 11, // 还是第2个memory location #2 (继续)
          : 0,  // zero-length bit-field分开了memory location
        d : 8;  // 第3个memory location
    struct {
        int ee : 8; // 第4个memory location  ，嵌套的struct分开了memory location
    } e;
} gemfield; // gemfield对象由4个分开的memory location组成
```
不同的memory location有个重要的寓意：只有分开的memory location才能被多线程同时更新。那么在上述gemfield结构体的例子中，a、d、e.ee可以同时被多线程修改，b和c却不能。当然了，a、b是可以同时被修改的。

# 对象模型
C++，面向对象的语言——C++程序创建、销毁、引用、访问、操纵对象。C++程序中的一个对象具备：

- size；
- 对齐要求（alignment requirement，可以通过alignof 获得该值）；
- storage duration（automatic, static, dynamic, thread-local）；
- 生命周期（bounded by storage duration 或者 temporary）；
- type；
- value；
- name（可选）。

按照上述要求，这些东西就不算对象了：value、reference、function、enumerator、type、class member、bit-field、template、template specialization、namespace、parameter pack、this。

那么对象是什么时候创建出来的呢？有如下几种情况：

- 定义（definition）；
- new表达式；
- throw表达式；
- 当改变一个union的active number；
- 当需要创建临时对象（temporary object）的时候。

## 1，Subobjects
一个对象可以拥有子对象，比如：

- 成员对象；
- 基类子对象（base class subobjects）；
- 数组元素（array elements）。

不是子对象的对象被称为完整对象（complete object）。完整对象、成员对象、数组元素又属于most derived objects，以此和base class subobjects区分开。除了这些概念，还有一个对象嵌套的概念，一个对象可以包含其它对象，被包含的对象就被称为嵌套对象。比如，如果满足下述情况，我们称对象g嵌套在对象e中：

- g是e的子对象；
- e为g提供了存储（比如： E e; G g = new(e）G;)；
- g嵌套在m中，而m又嵌套在e中。

有了这些概念，就可以引出两个原则了。

**原则1：任何两个有生命周期交集的对象（不是bit fields），它们的地址必不相同，除非：**

- 是嵌套关系；
- 是一个complete object的两个subobjects，且这两者type不同，且其中一个size为0。

比如g1和g2拥有相同的值，但地址不同：
```c++
static const char g1 = 'e';
static const char g2 = 'e';
assert(&g1 != &g2); // 相同的值, 不同的地址
std::cout<<"g1 address:"<<std::to_address((void*)&g1)<<"\ng2 address:"<<std::to_address((void*)&g2)<<std::endl;
```
**原则2：empty base optimization。** 
大家知道，所有的对象至少都需要占用1个字节（即使该对象为空），以确保不同的对象拥有不同的地址。但当基类为空时，在子类中其作为base class subobject，其大小会被优化为0。下面的示例非常关键：
```c++
struct B {}; // empty class
 
struct D1 : B {
  int i;
};

struct D2 {
  B b_;
};
 
struct D3 : B {
  B b_;
  int i;
};
 
struct D4 : B {
  D1 d1_;
  int i;
};

struct D5 : B {
  int i;
  D1 d1_; 
};

int main()
{
  std::cout<<"B size:"<< sizeof(B)<<std::endl;   //1
  std::cout<<"D1 size:"<< sizeof(D1)<<std::endl; //4
  std::cout<<"D2 size:"<< sizeof(D2)<<std::endl; //1
  std::cout<<"D3 size:"<< sizeof(D3)<<std::endl; //8
  std::cout<<"D4 size:"<< sizeof(D4)<<std::endl; //12
  std::cout<<"D5 size:"<< sizeof(D5)<<std::endl; //8
}
```
上述D4和D5的对比非常微妙，D4为什么会比D5多出4个字节呢？这是因为，如果D类型的成员作为子类的第一个非静态成员，empty base optimization将被禁止——这又是为什么呢？因为对于most derived type，其内部同类型的两个base subobjects需要有不同的地址。

## 2，多态对象
class类型的对象，如果有至少一个虚函数，或者其基类至少有一个虚函数，那么就称之为多态对象。多态对象有什么特别的地方呢？那就是，在其内部存储有额外的信息——一个指针——用来实现虚函数调用和RTTI功能（dynamic_cast和typeid）。这就意味着，多态对象的size比非多态对象要多出一个指针的size：
```c++
struct B1{
  virtual ~B1() {}
};
 
struct D1 : B1{};
 
struct B2{};
 
struct D2 : B2{};
 
int main()
{
    D1 d1;
    D2 d2; 
 
    B1& b1 = d1; 
    B2& b2 = d2; 
 
    std::cout << "Expression type of b1: " << typeid(decltype(b1)).name() << '\n' //B1
              << "Expression type of b2: " << typeid(decltype(b2)).name() << '\n' //B2
              << "Object type of b1: " << typeid(b1).name() << '\n'  //D1
              << "Object type of b2: " << typeid(b2).name() << '\n'  //D2
              << "Size of b1: " << sizeof b1 << '\n'  // 8
              << "Size of b2: " << sizeof b2 << '\n'; //1
}
```
## 3，对齐要求
每个object类型都有个属性叫alignment requirement，其值可以通过alignof或者std::alignment_of获得。这个值代表对一个对象所分配的地址的要求。不同类型的对齐要求是不一样的，如下所示：
```c++
class GEMFIELD1 {
  char g; // size: 1, alignment: 1
  char c; // size: 1, alignment: 1
  int n;  // size: 4, alignment: 4
  // two bytes padding
};

class GEMFIELD2 {
  char c; // size: 1, alignment: 1
  int n;  // size: 4, alignment: 4
  char g; // size: 1, alignment: 1
  // three bytes padding
}; 
 
int main()
{
    std::cout << "sizeof(GEMFIELD1) = " << sizeof(GEMFIELD1)<< " alignof(GEMFIELD1) = " << alignof(GEMFIELD1) << '\n';
    std::cout << "sizeof(GEMFIELD2) = " << sizeof(GEMFIELD2)<< " alignof(GEMFIELD2) = " << alignof(GEMFIELD2) << '\n';
}
```
GEMFIELD1的大小是8，而GEMFIELD2的大小是12，就是这种对齐要求所体现出来的微妙差异。

# 对象的生命周期
## 1，非临时对象
每个对象和引用（reference）都有自己的生命周期，讲的就是其生命什么时候开始，什么时候结束。对象的生命周期开始于：

- 获得符合size要求和对齐要求的storage，并且
- 初始化已经结束（包括通过no constructor或者trivial default constructor进行的default initialization ）。

但是这个“初始化结束”是有些非常规情况的：

- 如果对象是个union member，那么只有当该union member是union的initialized member时，或者被激活后，其生命周期才开始；
- 如果对象是个数组，那么当其内存被std::allocator::allocate分配后，其生命周期就可能已经开始了;
- 一些操作会在给定的存储区域中隐式创建implicit-lifetime类型的对象并开始它们的生命周期。

对象的生命周期结束于：

- 对于非class类型，该对象被销毁的时候；
- 对于class类型时，析构函数调用开始时；
- 该对象对应的内存被释放，或者被其它对象占用时。

类的非静态数据成员和base subobjects的生命周期按照类初始化顺序开始和结束。

## 2，临时对象
如下情况会创建临时对象：

- 当一个prvalue转换为xvalue的时候（何为prvalue、xvalue，可参考：Gemfield：C++的左值(lvalue)和右值(rvalue)）；
- 当传参或者函数返回一个trivially-copyable类型的对象时；
- 当抛异常的时候。

临时对象的materialization通常是一种lazy模式，也就是临时对象要尽可能晚的创建，以避免创建不必要的临时对象。临时对象在如下情况下会被materialized：

- 绑定引用到prvalue ;
- 对class类型的prvalue进行成员访问；
- 当对一个array prvalue进行array-to-pointer转换或者下标运算时；
- 使用braced-init-list来初始化std::initializer_list<T>类型的对象；
- 函数返回一个prvalue；
- 由conversion创建一个prvalue时；
- lambda表达式；
- 需要转换initializer的copy-initialization； 
- 到一个不同类型（但又可转换）或者到bitfield的reference-initialization；
- sizeof和typeid中的未计算的操作数；
- 当在discarded-value表达式中出现prvalue时； 
- 如果实现支持的话，在函数调用表达式中传参或者函数返回一个trivially-copyable类型的对象时（此种模型会在 CPU 寄存器中传递结构体） 。

在表达式的最后一步执行完后，其创建的临时对象将被销毁。如果多个临时对象被创建了，那么销毁的顺序将是创建顺序的反方向。请注意，当临时对象被绑定到一个const lvalue reference或者一个rvalue reference上，其生命周期会被延长——但这条规则也有个以外：假如临时对象绑定的是函数返回值，那么临时对象的生命周期并不会被延长，其将在return 表达式后销毁。

# storage duration
storage duration是C++对象的一个属性，其定义了存放该对象的内存空间的最小潜在生命周期。storage duration是以下几种之一：

- static storage duration;
- thread storage duration;
- automatic storage duration;
- dynamic storage duration.

## 1，Static storage duration
使用static关键字来声明一个局部变量的时候，或者一个类成员的时候，获得static storage duration。这种静态存储周期伴随着整个程序。
## 2，Thread storage duration
使用thread_local关键字声明的变量，该变量获得thread storage duration。其周期伴随着整个线程。
## 3，Automatic storage duration
block-scope中的变量，如果没有被显式的使用static、thread_local、extern来声明，则具有automatic storage duration。其周期一直持续到该block（创建该变量的块作用域）结束。
## 4，Dynamic storage duration
对象使用new表达式创建。在C++中，dynamic storage的创建和维护是通过global的allocation函数来进行的：

- operator new;
- operator new[];

销毁则是通过global deallocation函数：

- operator delete;
- operator delete[];

上述列的只是函数名，但是由于参数不同，函数原型还是不少的：
```c++
//返回值类型是void*，代表申请内存的首地址
//第一个参数类型是std::size_t，申请内存的大小
//第二个参数类型是std::align_val_t，代表对齐要求
[[nodiscard]] void* operator new(std::size_t);
[[nodiscard]] void* operator new(std::size_t, std::align_val_t);
void operator delete(void*) noexcept;
void operator delete(void*, std::size_t) noexcept;
void operator delete(void*, std::align_val_t) noexcept;
void operator delete(void*, std::size_t, std::align_val_t) noexcept;

[[nodiscard]] void* operator new[](std::size_t);
[[nodiscard]] void* operator new[](std::size_t, std::align_val_t);
void operator delete[](void*) noexcept;
void operator delete[](void*, std::size_t) noexcept;
void operator delete[](void*, std::align_val_t) noexcept;
void operator delete[](void*, std::size_t, std::align_val_t) noexcept;
```
上述的函数会在如下场景中被调用：

- new或delete表达式；
- 直接调用；
- 为coroutine state分配内存时的间接调用；
- 调用标准库的时候触发的间接调用。

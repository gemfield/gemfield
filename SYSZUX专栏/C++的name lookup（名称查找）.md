# 背景
名称查找（name lookup）指的是当在程序中遇到一个变量名/类型名/...的名字时，如何去寻找该变量的声明。比如当遇到下面的代码时：
```c++
std::cout << std::endl;
```
编译器将进行：

- 使用unqualified name lookup规则来查找std的声明，最终会在<iostream>头文件中找到std的声明；
- 使用qualified name lookup来查找cout的声明，最终会在std namespace中找到cout的声明；
- 使用qualified name lookup 来查找endl的声明，最终会在std namespace中找到一个名为endl的function template；
- 使用ADL(argument dependent lookup)来查找操作符<<，最终会在std namespace中找到多个名为<<的函数模板。

对于函数或者函数模板来说，名称可以匹配多个声明，因此有重载机制嘛。对于其它名称（变量名、namespace、类等），只能匹配一个声明。名称查找有三种：

- Qualified name lookup：如果名称紧跟在作用域符号(::)的右边，则使用这种方式；
- Unqualified name lookup：如果名称不是紧跟在作用域符号(::)的右边，则使用这种方式；
- Argument-dependent lookup：如果名称为函数名。

一旦找到名称的声明，名称查找就会结束。如果没有找到声明，则程序错误。

# 1，Unqualified name lookup

- 在global scope内使用的名称，也就是在任何函数、类或用户声明的命名空间之外使用的名称，其应该在global scope内使用之前声明。
- 由using指定的命名空间中的声明，将会在using所在的scope中变得可见。
- namespace中，搜索顺序为函数内、上层命名空间、上上层命名空间......global作用域，举例：
```c++
namespace A {
    namespace N {
        void f();
    }
}
void A::N::f() {
    gemfield = 7030;
    // 将在以下范围内寻找gemfield变量的声明::
    // 1) outermost block scope of A::N::f, before the use of gemfield
    // 2) scope of namespace N
    // 3) scope of namespace A
    // 4) global scope, before the definition of A::N::f
}
```
- 类和嵌套类中：
```c++
namespace M {
    class B { };
}
namespace N {
    class Y : public M::B {
        class X {
            int gemfield[i];
        };
    };
}
// 将在以下范围内寻找i变量的声明:
// 1) scope of class N::Y::X, before the use of i
// 2) scope of class N::Y, before the definition of N::Y::X
// 3) scope of N::Y’s base class M::B
// 4) scope of namespace N, before the definition of N::Y
// 5) global scope, before the definition of N
```
- 变量如果出现在class成员中，且class成员在class之外定义：
```c++
class B { };
namespace M {
    namespace N {
        class X : public B {
            void f();
        };
    }
}
void M::N::X::f() {
    gemfield = 16;
}
// 将在以下范围内寻找gemfield变量的声明:
// 1) outermost block scope of M::N::X::f, before the use of gemfield
// 2) scope of class M::N::X
// 3) scope of M::N::X’s base class B
// 4) scope of namespace M::N
// 5) scope of namespace M
// 6) global scope, before the definition of M::N::X::f
```
- 类成员函数定义：
```c++
struct X { void f(); };
struct B1: virtual X { void f(); };
struct B2: virtual X {};
struct D : B1, B2{
    void foo(){
        X::f(); // 调用 X::f (qualified lookup)
        f(); // 调用B1::f (unqualified lookup)
    }
};
////////////GEMFIELD/////////////
struct V { int v; };
struct A{
    int a;
    static int s;
    enum { e };
};
struct B : A, virtual V {};
struct C : A, virtual V {};
struct D : B, C {};

void f(D& pd){
    ++pd.v;       // OK: 只有1个v，因为是virtual继承
    ++pd.s;       // OK: 只有1个A::s, 因为是static
    int i = pd.e; // OK: 只有1个enumerator A::e, 因为是enumerator
    ++pd.a;       // error：因为不知道是B中的A::a还是C中的A::a 
}
```
- 友元函数声明：
```c++
template<class T>
struct S;

struct A {
    typedef int AT;
    void f1(AT);
    void f2(float);
    template <class T> void f3();
    void f4(S<AT>);
};
struct B {
    typedef char AT;
    typedef float BT;
    friend void A::f1(AT); // 参数类型是 A::AT
    friend void A::f2(BT); // 参数类型是 B::BT
    friend void A::f3<AT>(); // 参数类型是 B::AT
};
template<class AT>
struct C{
    friend void A::f4(S<AT>); // lookup for AT finds A::AT
};
```
- 函数参数名字的优先级高，可以覆盖包含该函数的作用域中其它地方定义的变量名：
```c++
class X
{
    int a, b, i, j;
public:
    const int& r;
    X(int i): r(a),      // initializes X::r to refer to X::a
              b(i),      // initializes X::b to the value of the parameter i
              i(i),      // initializes X::i to the value of the parameter i
              j(this->i) // initializes X::j to the value of X::i
    {}
};
 
int a;
int f(int a, int b = a); // error: b=a, 而不是::a，但该参数(括号中的第一个a)不允许被用为默认参数的值
```
- 类静态数据成员定义：
```c++
struct X
{
    static int x;
    static const int n = 1; // 第1优先级
};
 
int n = 2;                  // 第2优先级
int X::x = n;               // finds X::n, sets X::x to 1, not 2
```
- 枚举相关的：
```c++
const int RED = 7;
enum class color
{
    RED,
    GREEN = RED + 2, // 使用color::RED, 而非::RED, 因此GREEN = 2
    BLUE = ::RED + 4 // 变身qualified lookup，于是找的是::RED, 因此BLUE = 11
};
```
- 在namespace之外引用的变量：
```c++
namespace N {
    int i = 70;
    extern int j;
}

int i = 30;
int N::j = i; // N::j == 70
```
- try...catch块的：
```c++
int n = 3;          // 第3优先级
int f(int n = 2){    // 参数是第2优先级
  try{
    int n = -1;     // 不会被catch块找上门
  }catch(...){
    // int n = 1;   // 第1优先级
    assert(n == 2); // 这种情况下将查找到f的参数
  }
}
```
- 重载运算符：
```c++
struct A {};
void operator+(A, A);  // user-defined non-member operator+
struct B
{
    void operator+(B); // user-defined member operator+
    void f();
};
 
A a;
void B::f(){
    operator+(a, a); // error: 在B中找到操作符+并停止去global作用域中寻找，参数不匹配，报错；
    a + a; // OK: member-lookup找到B::operator+, non-member-lookup找到::operator+(A,A), 重载选择了::operator+(A,A)
}
```
- 模板定义：
```c++
void f(char); // f的第1次声明
template<class T> 
void g(T t){
    f(1);    // non-dependent name(不依赖T): 找到的是::f(char)；
    f(T(1)); // dependent name: lookup postponed
    f(t);    // dependent name: lookup postponed
}
 
enum E { e };
void f(E);   // f的第2次声明
void f(int); // f的第3次声明
double dd;
 
void h()
    g(e);  // instantiates g<E>, 找到了find ::f(char) (by lookup) and ::f(E) (by ADL)，然后重载选择了::f(E).
           // This calls f(char), then f(E) twice
 
    g(32); // instantiates g<int>, at which point the second and the third uses of the name 'f'
           // are looked up and find ::f(char) only then overload resolution chooses ::f(char)
           // This calls f(char) three times
}
 
typedef double A;
 
template<class T>
class B
{
    typedef int A;
};
 
template<class T>
struct X : B<T>
{
    A a; // 找的是::A (double), 而非B<T>::A
};
```

# 2，Argument-dependent name lookup
先看一个例子：
```c++
namespace N{
    struct S{};
    void f(S){
        std::cout<<"f: "<<std::endl;
    }
}
struct S{};

int main(int argc, char** argv){
    N::S s;
    //S s;  //error, will not find the f declaration
    f(s);
}
```
在main函数中，定义变量s的时候如果使用的是global中声明的S，那么编译将报错，因为找不到f函数的声明；但是如果定义s的时候切换为N::S，则编译正常。这就是ADL：Argument-dependent lookup。也就是说，查找函数名称的时候，除了在Unqualified name lookup中寻找函数的名字外，还要在参数的命名空间里寻找。
但是参数也不是那么简单的事情，对于函数的每个参数T，其上都关联了0个、1个、多个namespaces/entities。规则如下：

- 如果T是基础类型，那么不关联namespaces/entities；
- 如果T是个class，或者union，那么关联的entities有：类自身、包含该类的类、父类，以及和模板相关的一系列规则；
- 如果T是个enumeration，那么关联的namespace是该enumeration声明所在的最内层namespace；
- 如果T是个指向U的指针，或者是个U数组，那么关联的namespaces或者entities是U关联的；
- 如果T是个函数类型，那么关联的namespaces或者entities是该函数参数关联的，以及该函数返回值所关联的；
- 如果T是个指向class X成员函数的指针，那么关联的namespaces或者entities除了上一条所说的，还要再加上X；
- 如果T是个指向class X数据成员的指针，那么关联的namespaces或者entities除了数据成员自身所关联的之外，还要再加上X。

这里还有个问题，假设Unqualified name lookup搜寻的结果为X，ADL搜寻的结果为Y，那么X和Y是什么关系呢？如果X包含：

- 一个class成员的声明，或者
- 没有使用using指示符的block-scope function；
- 非函数（模板）的名称。

那么Y就置空，否则Y就是Y。最后名称查找的结果就是X和Y的联合。最后再说一个由ADL导致的特别的C++惯用法：
```c++
using std::swap;
swap(obj1, obj2);
```
因为直接调用 std::swap(obj1, obj2) 不会考虑用户定义的 swap() 函数——这些函数可能会定义在与 obj1 或 obj2 的类型相同的命名空间中。而当只调用unqualified的swap(obj1, obj2)的时候（也即没有使用using std::swap），那么如果没有提供用户定义的重载，则不会调用任何内容。std::iter_swap 和所有其他标准库算法在处理Swappable类型时都会使用这种方法。

# 3，Qualified name lookup
Qualified name指的就是出现在::右侧的名称。Qualified name可以指：

- 类成员；
- namespace中的成员；
- enumerator。

如果::左侧没有出现任何东西，那么名称查找就只找global空间（包含使用using指示符向global空间注入的名字）。特别需要注意的是::后面如果跟的是~符号，比如::Gemfield::~Gemfield()，那么::~后的Gemfield和::前的Gemfield是同一个空间：
```c++
struct Gemfield {
    ~Gemfield(){
        std::cout<<"gemfield destructor"<<std::endl;
    }
};

int main() {
   Gemfield x;
   x.Gemfield::~Gemfield(); // ::~后的Gemfield和::前的Gemfield是同一个空间
}
```
## 3.1，类成员
如果::的左边出现的是class或者struct或者union的名字，那么::右边的名字将会在该class/struct/union中寻找，除了以下情况（例外）：

- destructor（参考上面的小节）；
- user-defined conversion function，先在class type的scope中寻找，如果找不到，再在当前的scope中寻找；
- template arguments的名称将在当前的scope中寻找（而非template name的scope）；
- using指示符会把其间的class/enum引入到当前scope。

还需要说明一点，如果::左右出现的名字一样，意味着构造函数来了：
```c++
struct A { A(); };
struct B : A { B(); };
A::A() { } // A::A names a constructor, used in a declaration
B::B() { } // B::B names a constructor, used in a declaration
B::A ba;   // B::A names the type A (looked up in the scope of B)
A::A a;    // Error, A::A does not name a type
```
Qualified name lookup可以用来寻找由于嵌套而被隐藏的名称，举例：
```c++
struct B { virtual void foo(); };
struct D : B { void foo() override; };
int main()
{
    D x;
    B& b = x;
    b.foo(); // calls D::foo (virtual dispatch)
    b.B::foo(); // calls B::foo (static dispatch)
}
```
最后还有个非常重要的概念：Injected-class-name。这是什么意思呢？就是在一个class的scope中出现了class自身的名字（或者父类的名字），举个例子：
```c++
int X;
struct X{
    void f(){
        X* p;   // 正确！X就是injected-class-name
        ::X* q; // 错误！在global作用域中寻找，结果找到一个int型变量的名字，它隐藏了struct名字
    }
};
```
再举个更有意思的例子：
```c++
struct A {};
struct B : private A {};
struct C : public B{
    A* p;   // 错误！injected-class-name A是不可访问的（private继承）
    ::A* q; // 正确！没有使用injected-class-name，而是从global作用域中寻找到A
};
```

## 3.2，命名空间成员
当::左侧出现的是namespace的名字，或者没有出现名字，那么::右侧的名称就是namespace中的成员。

- 用于template arguments的名称，将只在当前scope中被寻找：
```c++
namespace N {
   template<typename T> struct foo {};
   struct X {};
}
N::foo<X> x; // error: X is looked up as ::X, not as N::X
```
- 在命名空间N中进行Qualified lookup，将首先查找N中的所有声明，如果没有找到，在寻找N中using指示符引入的符号，递归的查找，直到最终找到：
```c++
int x;
namespace Y {
  void f(float);
  void h(int);
}
namespace Z {
  void h(double);
}
namespace A {
  using namespace Y;
  void f(int);
  void g(int);
  int i;
}
namespace B {
  using namespace Z;
  void f(char);
  int i;
}
namespace AB {
  using namespace A;
  using namespace B;
  void g();
}
void h()
{
  AB::g();  // AB is searched, AB::g found by lookup and is chosen AB::g(void)
  AB::f(1); // First, AB is searched, there is no f
            // Then, A, B are searched，A::f, B::f found by lookup，overload resolution picks A::f(int)
  AB::x++;    // 这是错误的。First, AB is searched, there is no x。Then A, B are searched. There is no x
              // Then Y and Z are searched. There is still no x。
  AB::i++;  // 这是错误的。AB is searched, there is no i
            // Then A, B are searched. A::i and B::i found by lookup: this is an error
  AB::h(16.8);  // First, AB is searched: there is no h
                // Then A, B are searched. There is no h
                // Then Y and Z are searched.lookup finds Y::h and Z::h. 函数重载挑选了Z::h(double)
}
```
同一个声明可以被找到多次，如下所示：
```c++
namespace A { int a; }
namespace B { using namespace A; }
namespace D { using A::a; }
namespace BD {
  using namespace B;
  using namespace D;
}
void g()
{
  BD::a++; // OK: finds the same A::a through B and through D
}
```
# 4，Elaborated type specifiers
当一个class/struct/union的名字被一个non-type声明遮盖时，使用Elaborated type specifiers可以重新找到这个class/struct/union的名字，举个例子：
```c++
class T {
  public:
    class U;
  private:
    int U;
};
 
int main()
{
    int T;
    T t; // 错误: T是前面定义的局部变量（class T被该int变量T所遮挡）
    class T t; // 正确: 借助Elaborated type specifiers找到了 ::T, 局部int变量T被忽略
    T::U* u; // 错误: 名称查找找到的是class T的private data member
    class T::U* u; // 正确: 借助Elaborated type specifiers，class T的data member被忽略
}
```
当然了，如果Elaborated type specifiers没有找到前面声明的class类型，那么就会新声明一个（也有一些注意事项）：
```c++
template <typename T>
struct Node {
    struct Node* Next; // 正确: 这是injected-class-name
    struct Data* Data; // 正确: 既在global scope中声明了类型Data，又在这里声明了data member Data
    friend class ::List; // 错误: ::List是个qualified name
    enum Kind* kind; // 错误: class/struct关键字可以，enum不行
};
Data* p; // 正确: struct Data刚才已经被声明了
```
再介绍一些注意事项：
```c++
template <typename T>
class Node {
    friend class T; // 错误: type parameter不能出现在elaborated type specifier中
};
 
class A {};
enum b { f, t };
 
int main()
{
    class A a; // 正确: 等价于'A a;'
    enum b flag; // 正确: 等价于'b flag;'
}
////////////////////
enum class E { a, b };
enum E x = E::a; // 正确
enum class E y = E::b; // 错误: 'enum class' 不能引出elaborated type specifier
 
struct A {};
class A a; // 正确：struct和class在这里等价
```


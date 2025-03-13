# 背景
C++有两种大的类型：基础类型（fundamental type）和复合类型（compound type）。类型描述和定义了object、reference、function。在开始说这两大类型之前，我们先说说TriviallyCopyable这个概念。

C++的类型上有个TriviallyCopyable的概念，就是说一个type是否是个trivially copyable type。下列几个类型是trivially copyable type：

- 标量类型（scalar types）；
- trivially copyable class types（下面继续讲）；
- 上述类型组成的数组（arrays of such types）；
- 上述类型的cv-qualified版本。

标量类型有：Arithmetic types、enumeration types、pointer types、pointer-to-member types、std::nullptr_t、以及这些类型的cv-qualified版本。 这些都好理解，就第二项——什么是trivially copyable class types呢？

# 1，trivially copyable class type
符合下列所有要求的class就是trivially copyable class types：

- 没有non-trivial 拷贝构造函数；
- 没有non-trivial 移动构造函数；
- 没有non-trivial 拷贝赋值操作符；
- 没有non-trivial 移动赋值操作符；
- 具备trivial destructor。 

这里提到的trivial关键字，意思是“非常直截了当的方式”。但对于不同的构造/赋值函数，其意思也略有不同：

- 当说一个默认构造函数是trivial的时候，意思是它“什么也不做”（如果用户自己定义构造函数，那就是non-trivial的，即使用户定义的构造函数是空函数体，什么也不做。）；
- 当说一个拷贝构造/赋值函数是trivial的时候，意思是“等价于原始内存拷贝，就像memcpy那样”。

### 1，当满足如下所有条件时，我们就说类的拷贝/移动构造函数是trivial的：

- 不是用户定义的（也即是隐式定义的——也即编译器默认合成的构造函数，或者是默认的构造函数——如果是默认的，它的函数签名要和隐式定义的一样）；
- 且没有虚函数；
- 且没有虚基类；
- 没有volatile-qualified类型的非静态数据成员（后面会讲volatile-qualified）；
- 为所有直接基类所选择的拷贝构造函数是trivial的；
- 为所有非静态的class类型的成员选择的拷贝构造函数是trivial的；

### 2，对于类的拷贝/移动赋值函数来说，条件和上述类似，不再赘述。
### 3，当析构函数满足下列条件时，它就是trivial的：

- 不是用户提供的；
- 不是虚析构函数；
- 直接基类的析构函数是trivial的；
- 所有非静态的class类型的成员，其析构函数也是trivial的。

## 2，trivially copyable type的特点
如果一个类型T是trivially copyable type，那么T满足如下约束：

- T的一个对象被拷贝进char/unsigned char/std::byte 数组，并且当再次被拷贝回这个对象后，该对象拥有原始的值：
```c++
constexpr std::size_t N = sizeof(T);
char buf[N];
T gemfield; // 对象gemfield已经初始化为原始的值
std::memcpy(buf, &gemfield, N); 
std::memcpy(&gemfield, buf, N); // gemfield又回来了
```
- T的一个对象gem1，拷贝至T的另一个对象gem2，则gem2拥有和gem1一样的值：
```c++
T* gem1;
T* gem2;
std::memcpy(gem1, gem2, sizeof(T));//这个时候，gem1中的每个subobject都拥有和gem2中每个对应subobject一样的值
```
## 3，std::is_trivially_copyable
最后，我们可以使用std::is_trivially_copyable来判断一个类型是否为trivially copyable：
```c++
#include <iostream>
#include <type_traits>
 
struct A{
    int m;
};
 
struct B{
    B(B const&) {}
};
 
struct C{
    virtual void foo();
};
 
struct D{
    int m;
    D(D const&) = default; // -> trivially copyable
    D(int x): m(x+1) {}
};
 
int main()
{
    std::cout << std::boolalpha;
    std::cout << std::is_trivially_copyable<A>::value << '\n'; //true
    std::cout << std::is_trivially_copyable<B>::value << '\n'; //false
    std::cout << std::is_trivially_copyable<C>::value << '\n'; //false
    std::cout << std::is_trivially_copyable<D>::value << '\n'; //true
}
```
# 基础类型（Fundamental types）
基础类型有如下六大类。
## 1，void type
void类型是一种incomplete type，因此不会有void数组，也不会有void引用。但是，指针可以是void类型，以及函数可以返回void。
## 2，std::nullptr_t
这是null pointer literal(也就是nullptr)的类型，其大小为：sizeof(std::nullptr_t) == sizeof(void *)。下面举个例子：
```c++
#include <cstddef>
#include <iostream>
 
void f(int*){
   std::cout << "Pointer to integer overload\n";
}
 
void f(double*){
   std::cout << "Pointer to double overload\n";
}
 
void f(std::nullptr_t){
   std::cout << "null pointer overload\n";
}
 
int main()
{
    int* pi {}; double* pd {};
    f(pi);
    f(pd);
    f(nullptr); // 如果没有定义void f(nullptr_t)，则会出现ambiguous编译错误。
}

//输出:
//Pointer to integer overload
//Pointer to double overload
//null pointer overload
```
## 3，signed and unsigned integer types
有5种标准的有符号整数类型：signed char、short int、int、long int、long long int；对于每种有符号整数类型，都有一个对应的无符号整数类型：unsigned char、unsigned short int、unsigned int、unsigned long int、unsigned long long int。
这5种整数类型所占用的字节数如下：
![signed and unsigned integer types的位宽](https://github.com/user-attachments/assets/734b2260-028a-4acc-ad7e-f506b445500a)


## 4，boolean type
值为true或者false，sizeof(bool)的值一般是1（不一定是1，由实现决定。）
## 5，character type
字符类型有三种：

- signed char
- unsigned char：它比较特殊的一点是，可以表示raw memory；
- char：其中在x86-64上，char一般是signed；在ARM上一般是unsigned；
- wchar_t：表示宽字符，在Linux上是32位并且可以存放UTF-32字符；在Windows上是16位。因此这个类型在Windows就是个错误；
- char16_t：表示UTF-16字符的；
- char32_t：表示UTF-32字符的；
- char8_t：表示UTF-8字符的。和unsigned char具有同样的size、signedness、alignment。

C++标准保证：1== sizeof(char)<= sizeof(short)<= sizeof(int)<= sizeof(long)<= sizeof(longlong)。

## 6，floating-point types
有以下三种类型：

- float：单精度浮点型；
- double：双精度浮点型；
- long double：扩展精度浮点型。

浮点型有几个比较特殊的值：

- infinity
- negative zero, -0.0
- not-a-number (NaN)：和任何值都不相等（包括它自己）

# 复合类型（Compound types）
复合类型有如下种类：

- 数组；
- 函数；
- 指针；
- 引用（包含左值引用和右值引用）；
- 类；
- unions；
- enumerations；

std::is_compound用来判断类型T是否为复合类型：
```c++
#include <iostream>
#include <type_traits>
 
int main() {
    class Gemfield {};
    std::cout << std::boolalpha;
    std::cout << std::is_compound<Gemfield>::value <<std::endl;  //true
    std::cout << std::is_compound<int>::value <<std::endl;  //false
}
```
# CV-qualifiers
## 1，三种cv qualifiers
cv qualifiers可出现在任何type specifier中，用来指定被命名对象的constness或者volatility。对于函数和引用类型之外的任何类型T，都还有另外三种不同的类型：

- const-qualified T：const修饰的对象，或const对象的non-mutable子对象，这些被修饰的对象不能被修改。注意这是编译期概念，如果代码中试图修改这种类型的对象，程序编译将报错；
- volatile-qualified T：类型为volatile修饰的对象，或volatile对象的子对象，或const-volatile对象的mutable子对象。通过 volatile 限定类型的 glvalue 表达式进行的每次访问（读取或写入操作、成员函数调用等），都可以看作是用来抵抗编译器优化的（也即，在单个执行线程中，volatile表达式不能被优化或重新排序）;任何通过non-volatile 的左值引用去绑定volatile 对象的尝试都会导致未定义的行为;
- const-volatile-qualified T：类型为const-volatile 修饰的对象、const volatile 对象的non-mutable子对象、volatile 对象的 const 子对象、const 对象的non-mutable volatile 子对象。const-volatile-qualified修饰的对象既可以看作是const对象，也可以看作是volatile对象。

另外需要注意两点：

- 数组的cv属性和其成员的cv属性一样。
- cv-qualifier只能出现一次，比如const const 和 volatile const volatile都是无效的。

最后举个例子：
```c++
int main()
{
    int n1 = 0;          // non-const object
    const int n2 = 0;    // const object
    int const n3 = 0;    // const object (same as n2)
    volatile int n4 = 0; // volatile object
 
    const struct
    {
        int n1;
        mutable int n2;
    } x = {0, 0};        // const object with mutable member
 
    n1 = 1;   // ok, modifiable object
//  n2 = 2;   // error: non-modifiable object
    n4 = 3;   // ok, treated as a side-effect
//  x.n1 = 4; // error: member of a const object is const
    x.n2 = 4; // ok, mutable member of a const object isn't const
 
    const int& r1 = n1; // reference to const bound to non-const object
//  r1 = 2; // error: attempt to modify through reference to const
    const_cast<int&>(r1) = 2; // ok, modifies non-const object n1
    const int& r2 = n2; // reference to const bound to const object
//  r2 = 2; // error: attempt to modify through reference to const
//  const_cast<int&>(r2) = 2; // undefined behavior: attempt to modify const object n2
}
```
## 2，mutable
cv qualifier介绍中屡次出现的mutable一词，也是一种type specifier，只能用来修饰类的成员（且是non-static、non-const、non-reference的），意思是：哪怕class是const的，该成员也可以被修改。
```c++
class Gemfield
{
    mutable const int* p; // 正确
    mutable int* const q; // 错误：const‘q’ cannot be declared ‘mutable’
    mutable int&       r; // 错误：reference‘r’cannot be declared ‘mutable’
};
```
## 3，cv void
文档中经常出现cv void 一词，注意：cv void不是个类型，实质意思是“可能是cv qualified的void”，也就是有四种情况：

- void
- const void
- volatile void
- const volatile void

## 4，类型转换
cv修饰的严格性是有顺序的，如下所示：

- unqualified < const 
- unqualified < volatile 
- unqualified < const volatile 
- const < const volatile 
- volatile < const volatile 

cv修饰的类型之间的隐式转换要符合一个约束：只能由不严格的向严格的方向转换。也即：

- reference/pointer to unqualified type 可以隐式转换为 reference/pointer to  const 
- reference/pointer to unqualified type 可以隐式转换为 reference/pointer to volatile 
- reference/pointer to unqualified type 可以隐式转换为 reference/pointer to const volatile 
- reference/pointer to const type 可以隐式转换为 reference/pointer to const volatile 
- reference/pointer to volatile type 可以隐式转换为 reference/pointer to const volatile 

要是把方向反过来可以呢？那就不能是隐式转换，而只能使用const_cast进行显式转换。

## 5，std::remove_cv
去除最顶层的const、或者最顶层的volatile、或者两者（如果存在的话）。举例：
```c++
#include <iostream>
#include <type_traits>

int main() {
    std::cout << std::boolalpha;
 
    using type1 = std::remove_cv<const int>::type;
    using type2 = std::remove_cv<volatile int>::type;
    using type3 = std::remove_cv<const volatile int>::type;
    using type4 = std::remove_cv<const volatile int*>::type;
    using type5 = std::remove_cv<int* const volatile>::type;
 
    std::cout << std::is_same<type1, int>::value << "\n"; //true
    std::cout << std::is_same<type2, int>::value << "\n"; //true
    std::cout << std::is_same<type3, int>::value << "\n"; //true
    std::cout << std::is_same<type4, int*>::value << "\n"; //false
    std::cout << std::is_same<type4, const volatile int*>::value << "\n"; //true
    std::cout << std::is_same<type5, int*>::value << "\n"; //true
}
```


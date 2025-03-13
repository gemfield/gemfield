## 背景
类型转换有显式转换和隐式转换两种方式。

## 1，显式转换
显式转换的语法为：
### 1，(new-type ) expression 
C风格的类型转换：
```c
double f = 3.14;
unsigned int n1 = (unsigned int)f; // C-style cast
```
编译器会按照如下的方式及顺序对待C风格类型转换：

- const_cast<new-type>(expression);
- static_cast<new-type>(expression);
- static_cast后面跟着const_cast;
- reinterpret_cast<new_type>(expression);
- reinterpret_cast后跟着const_cast。

### 2，new-type( expression-list) 
函数风格类型转换：
```c
double f = 3.14;
unsigned int n2 = unsigned(f);     // function-style cast
```
注意以下几点：

- new-type只能是一个单词（可以用typedef简化复杂类型），因此，如果new-type为unsigned int或者int*都是不对的；
- 如果括号里只有一个表达式，那么相当于C风格类型转换；
- 如果括号里有多个表达式，那么new-type必须声明了合适的构造函数；
- 如果括号里为空，参考Gemfield：C++对象的8种初始化方式。

### 3，new-type { expression-list}
参考：Gemfield：C++对象的8种初始化方式

## 2，转换构造函数和用户自定义转换函数
对于class来说，用户定义的转换构造函数和自定义转换函数对类型转换起着至关重要的作用。

### 1，converting constructor
converting constructor是转换构造函数，转换构造函数是不带explicit关键字的构造函数，其中包括隐式声明的或者用户声明的non-explicit copy constructor和move constructor。比如：
```c ++
struct A
{
    A() { }         // converting constructor (C++11及之后)  
    A(int) { }      // converting constructor，也就是转换构造函数
    A(int, int) { } // converting constructor (C++11及之后)
    A(const A& rhs) {} //拷贝构造函数
};
 
struct B
{
    explicit B() { }         //不是converting constructor
    explicit B(int) { }      //不是converting constructor
    explicit B(int, int) { } //不是converting constructor
    B(const B& rhs) {}       //拷贝构造函数
};
```
转换构造函数是如何被使用的呢？Gemfield举个例子：
```c++
A a1 = 1;      // OK: copy-initialization selects A::A(int)
A a2(2);       // OK: direct-initialization selects A::A(int)
A a3{4, 5};    // OK: direct-list-initialization selects A::A(int, int)
A a4 = {4, 5}; // OK: copy-list-initialization selects A::A(int, int)
A a5 = (A)1;   // OK: explicit cast performs static_cast, direct-initialization
 
B b1 = 1;      // error: copy-initialization does not consider B::B(int)
B b2(2);       // OK: direct-initialization selects B::B(int)
B b3{4, 5};    // OK: direct-list-initialization selects B::B(int, int)
B b4 = {4, 5}; // error: copy-list-initialization selected an explicit constructor B::B(int, int)
B b5 = (B)1;   // OK: explicit cast performs static_cast, direct-initialization
B b6;          // OK, default-initialization
B b7{};        // OK, direct-list-initialization
B b8 = {};     // error: copy-list-initialization selected an explicit constructor B::B()
```

### 2，用户自定义转换函数
用户自定义转换函数使得一个class可以转换为别的类型（通过隐式转换或者显式转换）。它以类的非静态成员函数的方式声明，且不显式指明返回值类型。有三种语法：

- operatorconversion-type-id：参与所有的隐式或显式类型转换：
```c++
struct Gemfield{
    operator int() const { return 7030; } // implicit conversion
}
```
- explicit operatorconversion-type-id：只参与direct-initialization 和 显式转换：
```c++
struct Gemfield{
    explicit operator int*() const { return nullptr; } // explicit conversion
}
```
- explicit ( expression ) operator conversion-type-id 。

注意：用户自定义函数是在隐式类型转换的第二阶段被触发（因为第一阶段是standard conversion sequence），第二阶段包含0/1个转换构造函数，或者0/1个用户自定义类型转换函数。如果class既有转换构造函数，又有自定义类型转换函数，那么：

- 在copy-initialization和reference-initialization上下文中，两者都参与函数重载；
- 在direct-initialization上下文中，只会考虑转换构造函数。
```c++
struct To
{
    To() = default;
    To(const struct From&) {} // converting constructor
};
 
struct From
{
    operator To() const {return To();} // conversion function
};
 
int main()
{
    From f;
    To t1(f);  // direct-initialization: 只会考虑转换构造函数
               // Note: if converting constructor is not available, implicit copy constructor
               // will be selected, and conversion function will be called to prepare its argument
 
    To t2 = f; // copy-initialization: ambiguous
               // Note: if conversion function is from a non-const type, e.g.
               // From::operator To();, it will be selected instead of the ctor in this case
 
    To t3 = static_cast<To>(f); // direct-initialization: 只会考虑转换构造函数
    const To& r = f;            // reference-initialization: ambiguous
}
```
## 3，隐式转换
隐式的将一种类型转换为另一种类型。当表达式的上下文中出现了T1类型、而实际期待的是T2类型时，隐式类型转换就可能会发生。T2类型会出现在如下的情况中：

- 函数形参类型为T2；
- 操作符期待的类型是T2；
- 使用T2类型的object初始化T1类型的object；
- 当T1类型用在switch语句中（T2是integral类型）；
- 当T1类型用在if语句中（T2是bool类型）。

如果被调用的函数或运算符有多个重载，则在构建从 T1 到每个可用 T2 的隐式转换序列之后，重载决策规则决定编译哪个重载项。

### 3.1，隐式类型转换的优先级顺序
隐式转换包含以下内容，优先级顺序亦如此：

- 0个或1个standard conversion sequence（下面讲）；
- 0个或1个用户自定义转换函数（前面说过了）；
- 0个或1个standard conversion sequence（仅当用户定义转换函数被使用了后 ）。

在类型转换发生在构造函数或用户定义转换函数的参数上时，或者当从一种非class类型转换为另一种非class类型时，只允许standard conversion sequence。

### 3.2，Standard conversion
Standard conversion是具有内置含义的隐式转换。standard conversion sequence是按以下顺序排列的一系列标准转换（Standard conversion）：

- 0个或1个右侧的转换：lvalue-to-rvalue 转换、 array-to-pointer转换、function-to-pointer转换；
- 0个或1个右侧的转换：integral promotions、floating-point promotion、integral conversions, floating-point conversions、floating-integral conversions、pointer conversions、pointer-to-member conversions、boolean conversions；
- 0个或1个function pointer conversion；
- 0个或1个qualification conversion。

当且仅当 T2 可以使用e复制初始化（也即T2 t = e可以编译成功），我们才能说表达式 e 可以隐式转换为 T2。请注意，这与直接初始化 T2 t(e) 不同，后者将额外考虑显式构造函数和转换函数。

## 3.3，Contextual conversions
### 3.3.1，contextually converted to bool
下面的情况中，bool类型是上下文期待的类型，且bool t(e)如果是合法的话，那么表达式e就称之为“contextually converted to bool”：

- 条件控制表达式：if, while, for 
- 内置的逻辑运算符： !, && ， || 
- 条件运算符的第一个操作数：?:
- static_assert声明；
- noexcept 说明符中的表达式；
- explicit specifier中的表达式；

### 3.3.2，contextually implicitly converted to the specified type T 
在下列上下文中，当需要一个特定于上下文的类型 T时，class类型 E 的表达式 e 仅在以下情况下才允许被使用：

- E具备一个non-explicit的用户定义的转换函数（可以转换到allowable type）；
- 在allowable types中只有一种类型 T ，使得 E 具有返回类型是（可能是cv限定的）T 或reference to（可能是cv限定的）T的non-explicit转换函数，并且e可以隐式转换为T。

像e这样的表达式就称之为contextually implicitly converted to the specified type T 。注意：这个过程不会考虑explicit conversion函数（作为对比，contextually converted to bool是会考虑的）。

- delete表达式的参数（T是任何object pointer类型）；
- 使用了literal class的integral constant expression（T是任何integral或者unscoped枚举类型，选择的用户定义转换函数必须是constexpr）；
- switch语句中（T是任何integral或者枚举类型）。
```c++
#include <cassert>
 
template<typename T>
class zero_init
{
    T val;
public:
    zero_init() : val(static_cast<T>(0)) {}
    zero_init(T val) : val(val) {}
    operator T&() { return val; }
    operator T() const { return val; }
};
 
int main()
{
    zero_init<int> i;
    assert(i == 0);
    i = 7;
    assert(i == 7);
    switch (i) {}     // error until C++14 (more than one conversion function)
                      // OK since C++14 (both functions convert to the same type int)
    switch (i + 0) {} // always okay (implicit conversion)
}
```
## 4，*_cast 类型转换
有4中显式的*_cast类型转换。
### 4.1，const_cast 转换
语法为：const_cast< new-type > (expression) 

只有const_cast才能被用于移除constness或者volatility属性。
```c++
#include <iostream>
 
struct type{
    int i;
    type(): i(3) {}
    void f(int v) const{
        // this->i = v;                 // 错误: 这是一个pointer to const
        const_cast<type*>(this)->i = v; // OK as long as the type object isn't const
    }
};
 
int main() 
{
    int i = 3;        
    const int& rci = i; 
    const_cast<int&>(rci) = 4; // OK: modifies i
 
    type t; // if this was const type t, then t.f(4) would be undefined behavior
    t.f(4);
 
    const int j = 3; // j is declared const
    [[maybe_unused]]
    int* pj = const_cast<int*>(&j);
    *pj = 4;      // undefined behavior
 
    [[maybe_unused]]
    void (type::* pmf)(int) const = &type::f; // pointer to member function
    const_cast<void(type::*)(int)>(pmf);   // 错误: const_cast不能用于函数指针
}
```
### 4.2，static_cast 转换
语法为：static_cast< new-type >( expression )

基于隐式类型转换和用户自定义转换函数的组合。
```c++
#include <vector>
#include <iostream>
 
struct B
{
    int m = 42;
    const char* hello() const{
        return "Hello Gemfield, this is B!\n";
    }
};
 
struct D : B
{
    const char* hello() const{
        return "Hello Gemfield, this is D!\n";
    }
};
 
enum class E { ONE = 1, TWO, THREE };
enum EU { ONE = 1, TWO, THREE };
 
int main()
{
    // 1. static downcast
    D d;
    B& br = d; // upcast via implicit conversion
    std::cout << br.hello(); //输出：Hello Gemfield, this is B!
    D& another_d = static_cast<D&>(br); // downcast
    std::cout << another_d.hello(); //输出：Hello Gemfield, this is D!
 
    // 2. lvalue to xvalue
    std::vector<int> v0{1,2,3};
    std::vector<int> v2 = static_cast<std::vector<int>&&>(v0); //new-type是rvalue reference,相当于std::move
    std::cout << v0.size(); //输出：0，上面的步骤将glvalue转换为xvalue，告诉编译器，v0将要销毁，那就把我v0的资源拿走吧
 
    // 3. initializing conversion
    int n = static_cast<int>(3.14);
    std::cout << n; //输出：3
    std::vector<int> v = static_cast<std::vector<int>>(10);
    std::cout << v.size(); //输出：10
 
    // 4. discarded-value expression
    static_cast<void>(v2.size()); //new type 是void，static_cast discards the value of expression after evaluating it
 
    // 5. inverse of implicit conversion
    void* nv = &n;
    int* ni = static_cast<int*>(nv);
    std::cout << *ni; //输出：3
 
    // 6. array-to-pointer followed by upcast
    D a[10];
    [[maybe_unused]]
    B* dp = static_cast<B*>(a);
 
    // 7. scoped enum to int
    E e = E::TWO;
    int two = static_cast<int>(e);
    std::cout << two; //输出：2
 
    // 8. int to enum, enum to another enum
    E e2 = static_cast<E>(two);
    [[maybe_unused]]
    EU eu = static_cast<EU>(e2);
 
    // 9. pointer to member upcast
    int D::*pm = &D::m;
    std::cout << br.*static_cast<int B::*>(pm); // 输出：42
 
    // 10. void* to any type
    void* voidp = &e;
    [[maybe_unused]]
    std::vector<int>* p = static_cast<std::vector<int>*>(voidp);
}
```
### 4.2，dynamic_cast 转换
语法为：dynamic_cast< new-type >( expression )

- new-type 是指向完整class类型的指针或引用，或者指向void的指针；
- 如果new-type是引用，则expression是完整class类型的glvaue；如果new-type是指针，expression是指向完整class类型的指针的prvalue。

如果转换成功，dynamic_cast返回一个new-type的value；如果转换失败：

- 如果new-type是指针类型，则返回null pointer；
- 如果new-type是引用，则抛出匹配std::bad_cast的异常。
```c++
#include <iostream>
 
struct V{
    virtual void f() {} // must be polymorphic to use runtime-checked dynamic_cast
};
struct A : virtual V {};
struct B : virtual V{
    B(V* v, A* a){
        // casts during construction (see the call in the constructor of D below)
        dynamic_cast<B*>(v); // well-defined: v of type V*, V base of B, results in B*
        dynamic_cast<B*>(a); // undefined behavior: a has type A*, A not a base of B
    }
};
 
struct D : A, B{
    D() : B(static_cast<A*>(this), this) {}
};
struct Base{
    virtual ~Base() {}
};
struct Derived: Base{
    virtual void name() {}
};
int main()
{
    D d; // the most derived object
    A& a = d; // upcast, dynamic_cast may be used, but unnecessary
 
    [[maybe_unused]]
    D& new_d = dynamic_cast<D&>(a); // downcast
    [[maybe_unused]]
    B& new_b = dynamic_cast<B&>(a); // sidecast
 
    Base* b1 = new Base;
    if (Derived* d = dynamic_cast<Derived*>(b1); d != nullptr) { //Gemfield备注：条件不满足
        std::cout << "downcast from b1 to d successful\n";
        d->name(); // safe to call
    }
 
    Base* b2 = new Derived;
    if (Derived* d = dynamic_cast<Derived*>(b2); d != nullptr){ //Gemfield备注：条件满足
        std::cout << "downcast from b2 to d successful\n";
        d->name(); // safe to call
    }
    delete b1;
    delete b2;
}
```
### 4.2，reinterpret_cast 转换
语法为：reinterpret_cast <new-type> (expression)

除了在integers、pointers之间的转换外，reinterpret_cast并不产生任何CPU指令，它只是简单的告诉编译器：把expression当作是new-type类型对待。
```c++
#include <cstdint>
#include <cassert>
#include <iostream>
 
int f() { return 42; }
 
int main(){
    int i = 7030;
    // pointer to integer and back
    std::uintptr_t v1 = reinterpret_cast<std::uintptr_t>(&i); // 如果是static_cast，则报错
    std::cout << "The value of &i is " << std::showbase << std::hex << v1 << '\n';
    int* p1 = reinterpret_cast<int*>(v1);
    assert(p1 == &i);
 
    // pointer to function to another and back
    void(*fp1)() = reinterpret_cast<void(*)()>(f);
    // fp1(); undefined behavior
    int(*fp2)() = reinterpret_cast<int(*)()>(fp1);
    std::cout << std::dec << fp2() << '\n'; // safe
 
    // type aliasing through pointer
    char* p2 = reinterpret_cast<char*>(&i);
    std::cout << (p2[0] == '\x7' ? "This system is little-endian\n" : "This system is big-endian\n");
 
    // type aliasing through reference
    reinterpret_cast<unsigned int&>(i) = 42;
    std::cout << i << '\n';
 
    [[maybe_unused]] const int &const_iref = i;
    int &iref = reinterpret_cast<int&>(const_iref); // 错误：不能去掉const属性
    //只能用const_cast: int &iref = const_cast<int&>(const_iref);
}
```


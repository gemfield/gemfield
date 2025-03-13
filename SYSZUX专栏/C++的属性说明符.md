# 背景
从C++11之后，C++引入了Attribute specifier sequence（属性说明符序列），相当于一种标准语法扩展。语法为：

- [[attribute-list]]
- [[usingattribute-namespace:attribute-list]] 

其中的attribute-list是逗号分割的0个或多个attributes，这些attribute有如下四种形式：

- identifier，这是最简单的attribute，比如[[noreturn]]
- attribute-namespace::identifier，这是带namespace的attribute，比如[[gnu::unused]]
- identifier( argument-list ) ，这是带参数的attribute，比如 [[deprecated("gemfield")]]
- attribute-namespace::identifier(argument-list)，这是带命名空间和参数的attribute。

还有就是C++17中引入的using关键字，出现在attribute list的最前面，相当于指定所有attributes的namespace，比如：[[using CC: opt(1), debug]] 相当于 [[CC::opt(1), CC::debug]]。
C++标准只定义了如下的attributes（C++20及之前）：

- [[noreturn]]
- [[carries_dependency]]
- [[deprecated]]
- [[deprecated("reason")]]
- [[fallthrough]]
- [[nodiscard]]
- [[nodiscard("reason"]]
- [[maybe_unused]]
- [[likely]]
- [[unlikely]]
- [[no_unique_address]]

除了标准attributes，GNU、IBM、MSVC都定义了自己的扩展，本文就不涉及了。
# 1，[[noreturn]]
用于指明函数不会返回。这个返回指的不是返回值（比如void什么的，不然void不就足够了吗？），而指的是该函数不会返回到调用它的地方。也就是说，程序执行到该函数里的时候，要么一直在该函数里循环下去，要么退出程序，总之控制流不会回到调用它的地方。

这样做的好处有两个，一是可以告诉编译器做出更好的优化，二是给出合适的编译告警（或者避免误报警告），比如：
```c
[[noreturn]]
void myAbort(){
    std::exit(0);
}
int f(bool b){
    if (b) {
        return 7030;
    } else {
        myAbort();
    }
 }
```
如果myAbort()不带有[[noreturn]] 的话，程序编译就会告警：warning: control reaches end of non-void function [-Wreturn-type]。

实际上，标准库如下函数都带有[[noreturn]]这个attribute：
```
    _Exit
    abort
    exit
    quick_exit
    terminate
    rethrow_exception
    rethrow_nested
    throw_with_nested
    longjmp
```
# 2，[[carries_dependency]]
表明release-consume  std::memory_order 中的dependency chain在函数内外传播，这允许编译器跳过不必要的memory fence指令。
# 3，[[deprecated]]
表明不推荐使用此属性声明的名称或实体，即虽然允许使用，但由于某种原因不鼓励使用。有两种语法：

- [[deprecated]]
- [[deprecated("reason")]]：参数就是加个解释，说明不鼓励的原因

这个attribute可以用在下列地方：

- class/struct/union: struct [[deprecated]] S
- typedef-name: [[deprecated]] typedef S* PS、using PS [[deprecated]] = S*
- variable: [[deprecated]] int x
- non-static data member: union U { [[deprecated]] int n; }
- function: [[deprecated]] void f()
- namespace: namespace [[deprecated]] NS { int x; }
- enumeration: enum [[deprecated]] E {}
- enumerator: enum { A [[deprecated]], B [[deprecated]] = 42 }
- template specialization: template<> struct [[deprecated]] X<int> {}

举个例子：
```c++
#include <iostream>
 
[[deprecated]]
void gemfield1() {
    std::clog << "gemfield1.\n";
}
 
[[deprecated("Use gem2() instead.")]]
void gemfield2() {
    std::clog << "gemfield2.\n";
}
 
[[deprecated("Use gemfield4(int).")]]    
int gemfield3(int x) {
    return x * 2;
}
 
int main()
{
    gemfield1();
    gemfield2();
}
```
编译输出：
```bash
gemfield.cpp: In function ‘int main()’:
gemfield.cpp:115:14: warning: ‘void gemfield1()’ is deprecated [-Wdeprecated-declarations]
  115 |     gemfield1();
      |     ~~~~~~~~~^~
gemfield.cpp:99:6: note: declared here
   99 | void gemfield1() {
      |      ^~~~~~~~~
gemfield.cpp:116:14: warning: ‘void gemfield2()’ is deprecated: Use gem2() instead. [-Wdeprecated-declarations]
  116 |     gemfield2();
      |     ~~~~~~~~~^~
gemfield.cpp:104:6: note: declared here
  104 | void gemfield2() {
      |      ^~~~~~~~~
```
# 4，[[fallthrough]]
只能用于switch语句中，表明从前一个case标签中没有中断是故意的，不应由编译器给出告警的诊断。举例：
```c++
void g(){}
void h(){}
void i(){}
void f(int n)
{
    switch (n){
        case 1:
        case 2:
            g();
            [[fallthrough]];
        case 3: // no warning on fallthrough
            h();
        case 4: // compiler may warn on fallthrough
            if (n < 3){
                i();
                [[fallthrough]]; // OK
            }else {
                return;
            }
        case 5:
            while (false){
                [[fallthrough]]; // 可能是ill-formed: next statement is not part of the same iteration
            }
        case 6:
            [[fallthrough]]; // ill-formed, attribute ‘fallthrough’ not preceding a case label or default label
    }
}
```
编译输出：
```bash
gemfield.cpp: In function ‘void f(int)’:
gemfield.cpp:25:28: warning: attribute ‘fallthrough’ not preceding a case label or default label
   25 |             [[fallthrough]]; // ill-formed, no subsequent case or default label
```
# 5，[[nodiscard]]
可以出现在函数声明、枚举声明、class声明中。在下列的使用场景中，如果代码中没有接收返回值，则编译器将告警：

- 带nodiscard声明的函数被调用时；
- 当函数的返回值为带nodiscard声明的enumeration或class，该函数被调用时；
- 带nodiscard的构造函数被显式类型转换触发调用时。

举个例子：
```c++
struct Vector{
    bool empty() const{return true;} // 当为空时返回true
};

int main()
{
    Vector vec;
    vec.empty();
}
```
在上面的程序中，empty()方法是用来判断是否为空的，但使用的地方却误认为是清空的动作。而编译器不知道你的意图，因此编译是没问题的。但是，如果class的作者加上[[nodiscard]]：
```c++
struct Vector{
    [[nodiscard]] bool empty() const{return true;} // 当为空时返回true
};
```
那么程序将会告警：
```bash
gemfield.cpp:8:14: warning: ignoring return value of ‘bool Vector::empty() const’, declared with attribute ‘nodiscard’ [-Wunused-result]
    8 |     vec.empty();
      |     ~~~~~~~~~^~
```
你甚至还可以使用新语法：[[nodiscard("reason"]] ，代码如下所示：
```c++
struct Vector{
    [[nodiscard ("may be what you want is clear()?")]] bool empty() const{return true;} // 当为空时返回true
};
```
这样在编译的时候可以给出更友好的提示。

# 6，[[maybe_unused]]
对于未使用的entities，避免编译器给出告警。为什么会有这种需求呢？举个例子：
```c++
#include <cassert>
 
[[maybe_unused]] void f([[maybe_unused]] bool thing1, [[maybe_unused]] bool thing2)
{
    [[maybe_unused]] bool gemfield = thing1 && thing2;
    assert(gemfield); // in release mode, assert is compiled out, and gemfield is unused
} // parameters thing1 and thing2 are not used, no warning
 
int main() {}
```
在release模式中，assert会被优化掉，于是布尔变量gemfield就没有被使用。但由于声明了 [[maybe_unused]]，编译器不会给出警告。
这个属性的使用场景还有：

- class/struct/union: struct [[maybe_unused]] S;
- typedef: [[maybe_unused]] typedef S* PS; 、 using PS [[maybe_unused]] = S*;
- variable: [[maybe_unused]] int x;
- non-static data member: union U { [[maybe_unused]] int n; };
- function: [[maybe_unused]] void f();
- enumeration: enum [[maybe_unused]] E {};
- enumerator: enum { A [[maybe_unused]], B [[maybe_unused]] = 42 };
- structured binding: [[maybe_unused]] auto [a, b] = std::make_pair(42, 0.23);

# 7，[[likely]]和[[unlikely]]
用来告诉编译器，代码的哪条分支路径更有可能执行。这样就可以优化程序执行速度。举例：
```c++
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <random>
 
namespace with_attributes {
constexpr double pow(double x, long long n) noexcept {
    if (n > 0) [[likely]]
        return x * pow(x, n - 1);
    else [[unlikely]]
        return 1;
}
constexpr long long fact(long long n) noexcept {
    if (n > 1) [[likely]]
        return n * fact(n - 1);
    else [[unlikely]]
        return 1;
}
constexpr double cos(double x) noexcept {
    constexpr long long precision{16LL};
    double y{};
    for (auto n{0LL}; n < precision; n += 2LL) [[likely]]
        y += pow(x, n) / (n & 2LL ? -fact(n) : fact(n));
    return y;
}
}  // namespace with_attributes
 
namespace no_attributes {
constexpr double pow(double x, long long n) noexcept {
    if (n > 0)
        return x * pow(x, n - 1);
    else
        return 1;
}
constexpr long long fact(long long n) noexcept {
    if (n > 1)
        return n * fact(n - 1);
    else
        return 1;
}
constexpr double cos(double x) noexcept {
    constexpr long long precision{16LL};
    double y{};
    for (auto n{0LL}; n < precision; n += 2LL)
        y += pow(x, n) / (n & 2LL ? -fact(n) : fact(n));
    return y;
}
}  // namespace no_attributes
 
double gen_random() noexcept {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_real_distribution<double> dis(-1.0, 1.0);
    return dis(gen);
}
 
volatile double sink{}; // ensures a side effect
 
int main() {
    auto benchmark = [](auto fun, auto rem) {
        const auto start = std::chrono::high_resolution_clock::now();
        for (auto size{1}; size != 10000000; ++size) {
            sink = fun(gen_random());
        }
        const std::chrono::duration<double> diff = std::chrono::high_resolution_clock::now() - start;
        std::cout << "Time: " << std::fixed << std::setprecision(6) << diff.count() << " sec " << rem << std::endl; 
    };
 
    benchmark(with_attributes::cos, "(with attributes)");
    benchmark(no_attributes::cos, "(without attributes)");
    benchmark([](double t) { return std::cos(t); }, "(std::cos)");
}
```
输出的结果一定会显示，with attributes的这一组benchmark用时更短（当然，标准库的用时最短，不知道标准库的实现是不是用了汇编语法）。

# 8，[[no_unique_address]]
可以优化掉class中非静态数据成员所占用的空间。但这需要有个前提条件，就是该成员本身为空。比如：
```c++
#include <iostream>
struct Empty {}; // empty class
struct X {
    int i;
    Empty e;
};
struct Y {
    int i;
    [[no_unique_address]] Empty e;
};
struct Z {
    char c;
    [[no_unique_address]] Empty e1, e2;
};
struct W {
    char c[2];
    [[no_unique_address]] Empty e1, e2;
};

int main()
{
    // C++规则：空的object至少要占用1个字节
    static_assert(sizeof(Empty) >= 1);
 
    // X的成员e虽为空，但也要占用1个字节
    static_assert(sizeof(X) >= sizeof(int) + 1);
 
    // Y的成员e由于标记了[[no_unique_address]]，空间被优化掉
    std::cout << "sizeof(Y) == sizeof(int) is " << std::boolalpha << (sizeof(Y) == sizeof(int)) << '\n';
 
    // C++规则：e1 和 e2 因为类型相同，所以地址不得相同，即使标记了[[no_unique_address]]
    // 但是, 可以和成员c共享一个地址。
    static_assert(sizeof(Z) >= 2);
}
```
一定要注意C++中的unique identity rule：对于两个objects来说，下列三种情况至少满足一种。

- 它们的类型不相同；
- 它们的地址不相同；
- 它们是同一个object。

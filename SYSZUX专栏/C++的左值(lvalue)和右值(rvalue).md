# 背景
lvalue（左值）、rvalue（右值）这些术语来自C语言（当然，C语言的术语习惯也可能来自更早的语言，Gemfield就不追溯了）。在C语言中，lvalue和rvalue中的l和r是left和right，分别代表着赋值表达式（等号）的左边和右边。并且：

- 出现在等号左边的必须是lvalue；
- rvalue只能出现在等号的右边。
```c++
g1 = g2
```
其中等号左边的g1必须是lvalue，g2可以是lvalue或者rvalue。但其实把lvalue中的l看成是location就容易理解，就是lvalue是有直接的memory location的，而rvalue没有。比如：
```c++
int gem;
gem = 7030;
```
gem是lvalue，我们可以通过&gem来获得gem的memory location；而7030则是rvalue，我们无法获得它的内存地址。

# C++的到来
C++语言的一些特性就改变了前述规则。

## 1，class类型
上述的规则在C++中就变得不准确了，首先就是class类型。在前述小节中我们得知，rvalue是没有memory的（备注：对于一些大的复杂的rvalue，其实也是隐式占用memory的，但对于外部用户来说，假定它没有占用），但当到了C++的class时代后，class类型的rvalue是会占用memory的：
```c++
struct Gemfield{
  int x;
  int y;
};
Gemfield f(){
  return {7,19};
}
```
函数f返回的依然是rvalue，但此时的rvalue已经是个默认的class类型的对象，它是占用内存的（不然为啥会有移动语义，好了这里先不展开）。

## 2，const
有了const后，不是所有的左值都可以出现在赋值表达式的左边了。比如：
```c++
const int gem = 7030;
gem = 1002; //error: assignment of read-only variable ‘gem'
```
gem是lvalue，但不能出现在等号左边了。

## 3，新的引用规则
C++新增了一条规则：reference可以绑定到lvalue，但只有reference to const 可以绑定到rvalue。具体来说：

- reference to T的引用只能绑定到T类型的lvalue上，比如下面的代码就是错误的（7030是rvalue）：
```c++
int& gem = 7030; //错误
```
- reference to const T却不一定非得绑定到T类型的lvalue上，只要表达式产生的值可以转换成T类型即可。比如下面两句代码都正确，因为7030这个表达式产生的值（也即7030）可以转换为int或者double，于是c++编译器就创建了一个临时对象（第一句是临时int，第二句是临时double对象），然后将gem引用绑定到该临时对象上：
```c++
const int& gem = 7030;
const double& gem = 7030;
```
这样的行为正是函数形参经常为reference to const T的重要原因。reference to non-const 形参只接收non-const的实参；而reference to const的形参可以接收const或者non-const的实参，不论接收哪种，reference to const都会产生一个non-modifiable lvalue。

# Morden C++的到来
Morden C++，也就是C++11，更具体来说就是ISO/IEC 14882:2011，带来了新的value分类——其中最重要的一点便是带来了右值引用（rvalue reference）。这就意味着:

- 传统C++时代的引用，在morden c++（C++11及以后）中成为了左值引用（lvalue reference）;
- Morden C++新引入的右值引用(rvalue reference)开创了一个全新的领域：移动语义。

左值引用使用&操作符，而右值引用使用&&操作符，比如：
```c++
int&& gem = 7030;
```
并且右值引用既可以作为函数形参，也可以作为函数返回值：
```c++
Gemfield&& f(int && g);
```
且morden c++又为reference增加了一条规则：rvalue reference只能绑定到rvalue上，甚至rvalue reference to const也只能绑定到rvalue上：
```c++
int gem = 7030;
int&& r = gem; //error: cannot bind rvalue reference of type ‘int&&’ to lvalue of type ‘int’
const int&& rr = gem; //error: cannot bind rvalue reference of type ‘const int&&’ to lvalue of type ‘int’
```
继续说回移动语义（move semantics）。C++11在移动语义的基础上，将value类别重构为如下几类：

- 有名字，就是glvalue（generalized lvalue，包含lvalue和xvalue）；
- 有名字，且不能被move，就是lvalue；
- 有名字，且可以被move，就是xvalue（eXpiring value，走到生命周期尽头的value，因此可以被move）;
- 没有名字，且可以被移动，则是prvalue（pure rvalue）。

![图片](https://github.com/user-attachments/assets/a1ecf689-fa1a-4b0d-801c-4857ade714dc)

其中lvalue、prvalue、xvalue是最基础的分类，而glvalue、rvalue是混合的：

- glvalue = lvalue + xvalue
- rvalue = prvalue + xvalue

## 1，lvalue
下列表达式是lvalue表达式：

- 变量的名字、函数的名字（注意不是函数调用）、数据成员的名字；
- 函数调用，且其返回值类型为lvalue reference，比如：
```c++
std::cout<<"gemfield";
str1 = str2;
++it;
```
- 内置的赋值表达式，比如：
```c++
a = b;
a += b;
a %=b;
```
- 内置的pre-increment、pre-decrement表达式（注意：是pre而不是post）：
```c++
++a;
--a;
```
- 内置的间接寻址运算符（indirection expression）：
```c++
*p;
```
- 内置的下标运算符（subscript expression）:
```c++
a[n];
p[n];
```
- 类的数据成员：
```c++
a.m;
p->m;
```
- 逗号表达式（comma expression）：
```c++
g,e; //e需要为lvalue
```
- 三元条件表达式：
```c++
g ? e : m; //e和m需要是lvalue
```
- 字符串：
```c++
"gemfield";
```
- cast表达式，且cast为lvalue reference type：
```c++
static_cast<int&>(x)
```

## 2，prvalue
下列表达式是prvalue表达式：

- 字符（注意不是字符串）：比如'g'、'e'、true、nullptr、35；
- 函数调用，或重载运算符表达式，且返回值的类型为非引用，比如：
```c++
str.substr(1,2);
str1 + str2;
it++;
```
- 内置的post-increment和post-decrement表达式（注意不是pre）：
```c++
a++;
a--;

//想一下为什么下面的表达式是错的
(gem++)++ //error: lvalue required as increment operand. 
(++gem)++ //正确
++(gem++) //error: lvalue required as increment operand
```
- 内置的算术运算表达式：a + b、a % b、 a & b、 a << b
- 内置的逻辑表达式：a && b、 a || b、 !a
- 内置的比较表达式：a < b、a == b、 a >= b
- 内置的取地址表达式：&a
- 类的非static成员函数：a.m、p->m
- 逗号表达式：a,b ，且b为rvalue；
- cast表达式，且cast为非引用类型，比如：
```c++
static_cast<double>(x);
std::string{};
(int)42;
```c++
- this指针；
- enumerator;
- lambda表达式：
```c++
[](int x){return x + 7030;};
```
- requires表达式：
```c++
requires (T i){typename T::type;};
```
## 3，xvalue
下列表达式是xvalue表达式：

- 函数调用，或者重载运算符表达式，且返回值类型为rvalue reference，比如：std::move(x)；
- rvalue对象的non-reference类型的非静态数据成员：a.m；
- cast表达式，且cast为右值引用，比如：
```c++
static_cast<char&&>(x);
```
- temporary materialization时生成的临时对象：
```c++
struct S { int m; };
int i = S().m; // C++17标准：要访问对象的成员时，期望一个glvalue
               // S() prvalue 被转换为 xvalue
```
- temporary materialization还有其它很多情况，比如右值引用绑定到右值上时会创建xvalue。

# 再谈移动语义

先看一段代码：
```c++
string s1, s2, s3;
s1 = s2; //调用拷贝赋值
s1 = s2 + s3; //调用移动赋值，因为s2 + s3产生prvalue，前面讲过了
```
然后s2 + s3这个prvalue传递给move assignment operator的右值引用形参。假设move assignment operator的实现如下所示：
```c++
string& string::operator=(string&& rhs) {
  ...
  string temp(rhs);
  ...
}
```
那么代码中的string temp(rhs)是调用string类的拷贝构造函数呢，还是移动构造函数呢？答案是拷贝构造，因为rhs这个时候不是rvalue：rhs有名字，且预期在函数结束前它的生命都还在——这是lvalue！

但是有时候，我们编程时，就是想要move一个lvalue——因为程序员了解自己的意图（显然编译器不了解），比如：
```c++
template <typename T>
void swap(T& a, T& b){
  T temp(a);
  a = b;
  b = temp;
}
```
在函数第一行的T temp(a)中，编译器认为a还将继续有生命，但程序员知道过了这行后，a原有的资源已经不需要了（因为要用b填充了），那怎么在这一行调用移动构造而不是拷贝构造呢？这就相当于，如何让编译器知道a不再是个lvalue，而是个要过期的value——也即eXpiring value——也即xvalue——也即一种rvalue呢？那我们就需要做个转换。

前文讲过：“xvalue表达式的一种情况是：函数调用，或者重载运算符表达式，且返回值类型为rvalue reference，比如：std::move(x)”，这就是std::move的意义，可以将lvalue转换为xvalue（一种rvalue）。

# 总结
现在，C++不止有lvalue和rvalue了，而是：
![v2-d93ab4eb8e94623cd2c6054826b25dc6_720w](https://github.com/user-attachments/assets/323a3d30-b907-4edb-9c7a-9df004e5f30f)

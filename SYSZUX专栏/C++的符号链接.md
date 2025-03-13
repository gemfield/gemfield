# 背景
C++程序中的每个名称（比如变量名、函数名、类型名等等），可能具有linkage属性。linkage属性是C++程序中一个名称的四大属性之一（scope、type、storage duration、linkage）：
![图片](https://github.com/user-attachments/assets/e587cdac-36da-4d4b-8f7b-d56b886a0290)

在Gemfield开始说linkage属性之前，我们需要先弄清声明和定义的区别：

- 声明：是一个程序语句，它告诉编译器：“这里有个名称和一些属性，用来指向该程序中的一个实体，该实体可能在别处，也可能就是这里”；
- 定义：是一个程序语句，它告诉编译器：“这里有个名称和所需的完整的属性，用来指向该程序中的一个实体，而且该实体就是在这里”。

可以看到，所有的定义都是声明，但是声明并不一定是定义。为了防止混淆，后续情况下，声明指的是“非定义的声明”。
```c++
void gemfield();     //声明
void gemfield(){};   //定义

//对于变量来说，“定义意味着分配内存 ”
int g;               //定义
extern int e;        //声明
extern int m = 7030; //定义
```
当编译器遇到一个被声明的名称时，会将该名称和它的attribute信息存入符号表（symbol table）。下文在讲述linkage属性的上下文中，“名称”、“符号”指的是同一个意思。

# 四种linkage
如果有多处同名的符号分布在不同的编译单元中，那么在程序编译完之后要将它们链接到同一个定义上（这些同名符号只能有一处是定义，否则就是multi definition错误）。名称的linkage属性有如下四种：

- external linkage：如果一个名称具备external linkage，那么它可以被其它编译单元中的名称所链接，或者同一个编译单元中其它scope中的名称所链接；
- internal linkage：如果一个名称是internal linkage，那么它只能被同一编译单元内的名称所链接；
- module linkage：如果一个名称是module linkage，那么它可以被同一module中其它scope中的名称所链接，或者被其它编译单元中同一个named module中的名称所链接；
- no linkage：如果一个名称没有linkage，那么它只能被同一个scope内的名称所链接。

这里为名称的可见性引入了4种范围：global/namespace scope 、编译单元（TU）、module、block scope/local scope。符号的这些可见范围是给谁看的呢？linker！gcc默认调用的linker就是ld。下面就来分别介绍这些linkage概念。在开始之前首先要先介绍下namespace的linkage属性：

- 匿名namespace（或者直接/间接包含在匿名namespace中的namespace）具有internal linkage；
- 其它namespace具有external linkage。

其次，class scope中的函数成员、static数据成员、named class、enumeration拥有和该class一样的linkage属性。

# internal linkage
具备这种linkage属性的名称只能被同一编译单元内的名称所链接。下面是个internal linkage的例子：
```c++
//file1.cpp
static int gemfield = 7030; //定义，gemfield具有internal linkage属性

//file2.cpp
extern int gemfield; //声明，external linkage，引用的是其它地方的gemfield定义，但不是前述那个7030

//file3.cpp
int gemfield = 824; //定义，external linkage，file2.cpp中的gemfield引用的就是这里的824。
```
什么名称是internal linkage属性呢？

- namespace scope中的变量、函数及其模板，且使用static修饰；
- namespace scope中anonymous union中的data member；
- namespace scope中const-qualified类型的non-volatile、non-template变量，且没有使用extern显式声明；
- namespace scope中const-qualified类型的non-volatile、non-template变量，且不是inline；
- namespace scope中const-qualified类型的non-volatile、non-template变量，且没有被exported；
- namespace scope中的non-volatile const-qualified类型的non-template变量，除非该变量已经在前面声明了，且声明的时候是非internal linkage属性。

上述规则大篇幅的涉及到了const-qualified类型，那是因为在C++中，global scope/namespace scope中的const类型的变量默认为internal linkage属性（而在C语言中是external linkage属性！）：
```c++
//file1.cpp
int const gemfield = 7030;  //internal linkage

//file2.cpp
int const gemfield = 824; //internal linkage

//所以C++中const类型变量可以放到header中被多处include，而C语言不可以
```
上面的规则中还提到了inline，如果头文件中一个函数f被inline修饰，并且被include到了多个地方，那编译器会怎么处理呢？要么调用f的地方被直接替换成f的函数体，要么不替换但全局只维持一份具有external linkage属性的f函数。

再回到规则上，如果名称没有被前述的规则命中，那么对于一个变量、函数、named class、typedef声明中定义的unnamed class（该class具有typedef name）、named enumeration、typedef声明中定义的unnamed enumeration（该enumeration具有typedef name）、unnamed enumeration（that has an enumerator as a name for linkage purpose）、模板来说，如果满足下述第一个条件，也是internal linkage：

- 其所在的namespace具备internal linkage属性；
- 否则，如果其名称的声明被attach到了一个named module 并且没有被exported，那么具备module linkage属性；
- 否则，就是external linkage。

# module linkage
它可以被同一module中其它scope中的名称所链接，或者被其它编译单元中同一个named module中的名称所链接。什么名称具备module linkage属性呢？

- 名称被attach到一个named module上，且没有被export出来。

# no linkage
意思是该名称只能被同一个scope内的名称所链接。
```c++
int f1(){
    int gemfield; //定义，gemfield的linkage属性为no linkage
    ...
}

int f2(){
    int gemfield; //定义，gemfield的linkage属性为no linkage，和上面的gemfield没有啥关系
    ...
}
```
什么名称具有no linkage属性呢？有如下几种：

- 在block scope中声明的变量，且没有显式使用extern关键字（变量上为什么要强调“显式”呢？因为函数默认就是extern声明的）；
- 在block scope中声明的typedefs、enumerations、enumerators；
- local class（声明并定义在函数体内的class）和它的成员函数。

# external linkage
它可以被其它编译单元中的名称所链接，或者同一个编译单元中其它scope中的名称所链接。具备external linkage的变量和函数，也被称作具备language linkage——可以链接不同的计算机语言的编译单元。下面是个external linkage的例子：
```c++
//file1.cpp
extern int gemfield = 7030; //定义

//file2.cpp
extern int gemfield; //声明，引用的是前述的7030.
```
什么名称具备external linkage属性呢？

首先是没有被以上规则所命中的名称，其次是声明在具备external linkage的namespace中（除非它们的声明被attached到named module并且没有被exported）。主要有以下这几种：

- enumerations; 
- class及class内声明的member functions、 static data members、nested classes、enumerations，以及class中使用friend修饰的functions； 
- 没有命中本文前述规则的模板。

首次声明在block scope中的下列名称具有external linkage属性： 

- 使用extern修饰的变量名；
- 函数名。

在block scope中使用extern修饰的函数，如果在此处之前已经有一个internal linkage的前述声明，那么这里也是internal linkage，否则是external linkage。举个例子：
```c++
static int gemfield(); //internal linkage

int main(){
    extern int gemfield(); // internal linkage
    extern int civilnet(); // external linkage
}
```
# 总结
在C++的release编译中，linker只会寻找那些具备external linkage属性的名称。在链接的最后阶段，链接器会扔掉那些被声明为internal linkage或者no linkage的名称。

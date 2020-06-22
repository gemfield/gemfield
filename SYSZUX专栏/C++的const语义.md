##  **背景**

我们都知道，const作为修饰符的时候，用来表明这个变量所代表的内存不可修改。因此，const修饰的变量必须在定义的时候就完成初始化，不然以后也没有机会了：

    
    
    const int gemfield = 7030;
    

但是请注意，这个不可修改是编译期的概念，如果你试图修改gemfield，那么编译器就会报错。而在运行时是没有const的概念的。事实上，在编译的时候，编译器大概率会将用到gemfield的地方直接替换为7030。

有了这个朴素的语法和概念后，我们下面就开始来详细介绍C++中const的语义，特别是在C++11的新标准中，我们新增加了constexpr关键字来强化和丰富const语义。

##  **references to const**

当我们将const概念应用到reference类型上时，会产生两种语义：const reference和reference to
const，一个是说自身是const，一个是说绑定/指向的对象是const类型。但是，因为reference自身本来就是初始化后不能修改的，因此天然具备const语义。由此，上述的两种语义我们只会说第二种，也就是reference
to const。

设想我们要将上面的gemfield绑定到一个reference上，我们可能会这么做：

    
    
    int& r = gemfield;

但不好意思哈，编译器会报错，以Mac上的clang为例，编译器会给出错误binding value of type 'const int' to
reference to type 'int' drops 'const' qualifier：

    
    
    error: binding value of type 'const int' to reference to type 'int' drops 'const' qualifier
        int& r = gemfield;
             ^   ~~~~~~~~

因为要绑定/指向const对象的reference必须也得是const类型，等等，这么说有点奇怪，向上文说过的那样，因为reference本来初始化后就不能修改，天然具有const属性，因此上面那句话的表述应该修正为：绑定/指向const对象的reference必须得是"reference
to const"类型，也就是：

    
    
    const int& r = gemfield;
    

那么reference to const 类型如果指向的是non const类型的变量呢？

    
    
    int not_const_gemfield = 7030;
    const int& r = non_const_gemfield;

这样是可以的，但要注意一点，虽然此时可以通过non_const_gemfield变量来修改其上的值，但通过r是不可能的，不然clang会报如下错误：

    
    
    gemfield.cpp:6:7: error: cannot assign to variable 'r' with const-qualified type 'const int &'
        r = 56;
        ~ ^
    gemfield.cpp:4:16: note: variable 'r' declared const here
        const int& r = gemfield;
        ~~~~~~~~~~~^~~~~~~~~~~~
    1 error generated.

##  **const和临时对象**

在C++中，要进一步理解const就不得不提到临时对象（temporary object）这个概念。 **如果试图将一个临时对象绑定在非reference
to const类型的reference上，那么编译器会给出错误** 。

先看下面的例子：

    
    
    double gemfield = 7030;
    int& r = gemfield;
    

咦？临时对象在哪里呢？这是因为你试图将double类型的gemfield绑定到int型的reference上，编译器就会进行隐含的类型转化，相当于：

    
    
    double gemfield = 7030;
    int temp = gemfield
    int& r = temp;

临时对象temp就产生了。在C++中，如果你将一个引用绑定在临时对象上（temp），编译器会认为这是完全没有道理的事情，肯定不是程序员的意图，因此直截了当的给出错误：

    
    
    error: non-const lvalue reference to type 'int' cannot bind to a value of unrelated type 'double'
        int& r = gemfield;
             ^   ~~~~~~~~
    1 error generated.

但是临时对象可以绑定在reference to
const类型的reference上，因为这种类型的reference显式的向编译器表明了态度：程序员的我将不会通过该reference去改变绑定在其上的对象的值（也就是临时对象上的值），那这种情况下就显得很有道理了，因此编译器会通过：

    
    
    double gemfield = 7030;
    const int& r = gemfield;
    gemfield = 17030;
    std::cout<<r<<std::endl
    

有意思的事情来了，这种情况下你修改了gemfield对象的值：从7030到17030，那么r的输出是什么呢？答案是7030，也就是说根本没发生变化。正如上文所说，这是因为：
**r自始至终绑定的是那个临时对象temp，并不是gemfield** 。

##  **指针和const**

在上文中，我们知道对于reference来说，有两种const语义：一个是const reference，一个是reference to
const，但是因为reference天然的具备const语义，因此我们只会提到reference to const。那么对于指针呢？
**指针自身作为可以实实在在修改的对象，是具备两种const语义的，** 也就是const pointer和pointer to const。

先来一段简单的例子：

    
    
    const int gemfield = 7030;
    int* p = &gemfield;

这段代码会导致编译器报错：error: cannot initialize a variable of type 'int *' with an
rvalue of type 'const int *'。这是因为gemfield是const类型的，因此左侧的pointer的类型必须是pointer
to
const的。为什么呢？还记得文中一开始提到的吗：“事实上，在编译的时候，编译器大概率会将用到gemfield的地方直接替换为7030“。至少从这个小细节上，我们就可以看出，gemfield对象已经或多或少的变成了临时语义，编译器认为用一个普通的指针指向它已经毫无道理了，程序员的你的意图一定不是这样，因此会直截了当的给出错误。

如果要修复上述错误，必须将p的类型变为pointer to const，像下面这样：

    
    
    const int gemfield = 7030;
    const int* p = &gemfield;
    

既然现在我们已经知道了pointer to const类型，我们再来说说const pointer类型。前者pointer to
const类型的指针是说一个指针指向的对象是不可修改的，但是指针本身的值是可以修改的；而后者const
pointer类型的指针则是说，指针本身是不可修改的。const pointer的语法是这样的： **将const关键字放到*之后：**

    
    
    int gemfield = 7030;
    int* const p = &gemfield;

上述p就是const pointer，如果p既是const pointer又是pointer to const的呢？那就是：

    
    
    const int gemfield = 7030;
    const int* const p = &gemfield;

一个比较好的阅读理解方式是从变量名p开始，从右到左看：

    
    
    p //pointer名字
    const p // const pointer
    int* const p //const pointer point to int
    const int* const p //const pointer pointer to const int

##  **top-level const和low-level const**

我们在这里可以提出top-level和low-level这两个概念是因为，这两个概念在好几处都会被使用到：1， **在拷贝对象时，可以无视top-
level的const，但必须尊重low-level的const；2，在类型推导时，top-level的const会被无视/重视；3，在类型转换时，top-
level和low-level的const有不同的方法。**

简单来说，const pointer 是top-level const，pointer to const是low-level
const。从人的眼睛出发，我们是先看到pointer（top level），再看到pointer指向的对象（low level），层层剥开，高屋建瓴。
**对于 reference中的const语义来说，都是low-level的** 。

关于拷贝对象，我们来举个例子：

    
    
    int gemfield = 7030;
    int* const p1 = &gemfield;
    
    const int c_gemfield = 17030;
    const int* p2 = &c_gemfield;
    
    //没问题，top-level被无视
    gemfield = c_gemfield;
    
    //错误！p2是low-level const，但是tmp不是
    int* tmp = p2;

如果不尊重low-level const语义，编译器就会给出下面的错误：

    
    
    error: cannot initialize a variable of type 'int *' with an lvalue of type 'const int *'
        int* tmp = p;
             ^     ~
    1 error generated

关于类型推导，因为过于复杂，放到下面单独的章节理了。请往下看。

##  **constexpr和constant expressions（常量表达式）**

常量表达式（constant
expressions）是说一个表达式的值不会被改变，并且在编译期就能获得这个表达式的值。相对应的，一个表达式是否是constant
expressions就取决于这两个方面：类型（是否const）和初始化方式（编译期是否能拿到值）：

    
    
    //下面是常量表达式
    const int gemfield = 7030;
    const int gemfield2 = gemfield + 1;
    
    //下面不是，至少违反了两条中的一条
    int gemfield3 = 27030;
    const int gemfield4 = func();
    

上面的例子中，gemfield3不是const类型，gemfield4的值，也就是func()不能在编译期得到，因此这两者都不是constant
expression。在C++11的新标准中，我们定义了constexpr关键字，用法如下所示：

    
    
    constexpr int gemfield = 7030;
    constexpr int gemfield2 = gemfield + 1;
    constexpr int gemfield3 = func();

这个关键字告诉编译器，你来帮我确认下这些个变量是否（可以）是constant
expression，不行就报错！上面的例子中，gemfield和gemfield2被编译器裁定为可以是，但是gemfield3是不是呢？当func是一个constexpr的函数时，那就是！如果func是一个普通的函数时，那就不是！

那什么是constexpr函数呢？这是C++11的新标准，一个constexpr函数就是一个普通的函数，再加上这些限制条件：1，参数的形参的类型必须是literal
type（编译期可以参与运算的类型）；2，参数的实参必须是constant
expression；3，函数体只能是一个return语句；4，并且语句中的表达式必须在编译期可以resolve，而不是等到运行时。

因为constexpr函数的目的就是在编译器用它的值来替换到使用它的地方，因此constexpr函数默认具有inline语义，因此需要定义在多个编译单元中，为了保证多个编译单元中的同一个constexpr函数定义一致，我们通常需要把constexpr函数定义在头文件中。

需要说明的是，当指针遇到constexpr时， **constexpr定义的const语义是top-level的** ：

    
    
    constexpr int* gemfield = nullptr;
    const int* gemfield2 = nullptr;

gemfield是const pointer，而gemfield2是pointer to const

##  **const和类型推导**

在C++11中，和const语义相关的，标准包含了两种类型推导：auto、decltype，以及RTTI中的类型识别：typeid。

**1，auto**

先说说auto，当const语义遇到auto后，top-level的const会被auto忽略，这个和reference遇到auto的行为很像：

    
    
    int gemfield = 7030;
    int& r = gemfield;
    auto a = r; //a的类型是int，而不是reference
    
    const int gemfield = 7030;
    auto a = gemfield; //a的类型是int，而不是const int

如果在使用auto的时候想要带reference或者const语义，那就显式的加上：

    
    
    auto& a = r; 
    const auto& a = gemfield;

**2，decltype**

auto的类型推导是根据初始化表达式来的，但有时候我们只想要表达式的类型，而不想用这个表达式来进行初始化，这就是decltype：

    
    
    decltype(func()) gemfield = x;

值得说明的时候，func()并不会被调用，decltype只是通过其推导出它的返回值类型而已。decltype的行为和auto有很大的区别，并且decltype进行类型推导的时候，可以输入一个变量，也可以输入一个表达式。

当decltype的输入是变量的时候，decltype返回这个变量的类型，并且会保留top-level的const语义，也会保留reference语义：

    
    
    const int gemfield = 7030;
    const int& r = gemfield;
    
    decltype(gemfield) x = 0; //x是const int 类型
    decltype(r) y = x; //y是const int&类型，因此必须初始化

当decltype的输入是表达式的时候，decltype得到的类型是这个表达式返回的类型，下面是两个有趣的例子：

    
    
    int gemfield = 7030;
    int* p = &gemfield;
    int& r = gemfield;
    
    decltype(r) x; //x是int&
    decltype(r + 0) x; //x是int，不是int&
    decltype(*p) y; //y是int&，而不是int
    

y之所以是int&，是因为*p是通过一个地址的索引来得到的值，更像是一个引用而不是普通的int。

说完了表达式，我们再回到变量。当把变量用括号扩起来时，编译器就任务这是一个表达式，当作为decltype的输入时，decltype会返回该类型的引用：

    
    
    int gemfield = 7030;
    
    decltype(gemfield) x; //x是int
    decltype((gemfield)) x; //x是int&，不是int

**3，typeid**

typeid是为RTTI提供的第二个operator，意思是问入参：Hi，你的类型是什么呀？typeid的返回值是一个type_info类，在标准库中定义。
**当typeid的入参是const类型时，top-level的const语义会被忽略**
（顺便说一句，当typeid的入参是reference类型时，reference语义也会被忽略）。哇，这个像极了auto类型推导啊！

##  **函数参数中的const语义**

const语义在函数参数的初始化中和变量的初始化中的行为是类似的。形参上的top-level的const会被无视：也即，如果形参是top-
level的const语义，我们可以把const和non const的对象赋给形参。像下面这样：

    
    
    void gemfield(const int i) {/* can read i but not write to i */}

对于low-level的const来说，记住一点： **往更严格的方向转换是没有问题的，反之则不行。**

    
    
    void gemfield(int* i){}
    void gemfield(int& i){}

由此得出一个好的实践：函数的形参尽可能的使用reference to const。这样带来的一个好处就是，什么都可以传。比如下面这样：

    
    
    void gemfield(const string& s1){}
    void gemfield(string& s2){} //不太好

如果是第一种定义，我们的实参类型甚至可以是字符串常量。我们可以这样调用函数：gemfield("gemfield, a civilnet
maintainer")；如果是第二种定义，则会报错。

最后我们还得提到 **函数重载** ，还记得重载的条件吗： **函数名相同、形参列表不同** 。其中，形参列表不同体现在两个地方：
**参数个数不同，参数的类型不同** 。那么有趣的地方来了：

  1. 因为top-level的const被无视了，因此，不同的top-level的const语义，却是相同的形参类型； 
  2. low-level的const语义可以产生不同的形参类型，因此可以产生重载； 

##  **类型转换和const_cast**

众所周知，C++中的类型转换分为隐式和显式转换。

在类型的隐式转换中，我们可以加上low-level的const，如下所示：

    
    
    int gemfield;
    const int& r1 = gemfield; //正确，隐式转换可以加上low-level的const
    const int* p1 = &gemfield; //正确，隐式转换可以加上low-level的const
    
    int& r2 = r1; //错误，隐式转换中不允许去掉low-level的const
    int* p2 = p1; //错误，隐式转换中不允许去掉low-level的const
    

但是，如果是想在类型的隐式转换过程中去掉low-level的const，那则是万万不行的。

我们再来说说显式转换： **const_cast** 。这个是专门用来操作low-
level的const的，并且只能是这三种类型上的const语义：reference, pointer-to-object, or pointer-to-
data-member。我们来看看下面的例子：

    
    
    int gemfield = 7030;
    int& r = gemfield;
    const int& r2 = const_cast<const int&>(r);

const_cast可以加上low-level的const语义，如上面所述；也可以去掉一个low-level的const语义，如下面所示：

    
    
    const int gemfield = 7030;
    const int& r = gemfield;
    int& r2 = const_cast<int&>(r);

这两个的区别是，前者中r2指向的还是gemfield所在的内存；而后者中r2则指向的是临时对象，对r2的改动在标准是未定义的。

另外还有一个有趣的事实，就是显式转换中的 **static_cast，可以强制转换任何类型，就是不能转换low-level的const语义**
。对应的，const_cast可以转换low-level的const语义，但是不能进行其它类型的转换。

##  **类的const成员和const对象**

类的const成员分为数据成员和函数成员，其中数据成员的语义和上述介绍没有什么区别，只不过要注意的是，const数据成员的初始化方式——只能在构造函数之前初始化；如果不对const数据成员显式的进行初始化，编译器将予以拦截并且报错如下：

    
    
    error: constructor for 'Gemfield' must explicitly initialize the const member 'data'

而const函数成员指明了这个函数不会修改该类的任何成员数据的值，称为常量成员函数——如果在const成员函数的定义中出现了任何修改对象成员数据的情况，都会在编译时被编译器拦截住。有了const成员函数，我们就可以实例化const类型的对象（否则也没有意义了），并且我们只能在const对象上调用const成员函数，任何在const对象上调用非const成员函数的行为，都会被编译器拦截住，并且报错：

    
    
    error: 'this' argument to member function 'getV' has type 'const Gemfield', but function is not marked const

##  **模版中const的语义以及完美转发**

这篇文章的内容已经太多了，这一小节的内容将在《C++的perfect forwarding》中进行讲述。


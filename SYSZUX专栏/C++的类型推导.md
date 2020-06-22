##  **背景**

讨论C++类型的推导时，正如Gemfield在以前的文章中说的那样：“因为C++过于复杂和多维度的语法，导致任何一个新增的语法都会显得纷繁冗杂”，没错，单是说到C++的类型推导，Gemfield也不得不将其拆分为基础部分和模板部分。然后在每个部分里，又有更细化的场景。这些细化的场景将会演绎出一些耳熟能详的概念：type
decay、Trailing return types、Universal reference、forwarding reference、reference
collapsing、传值vs传引用等。

在本文中，Gemfield将会从多个方面介绍下C++的类型推导。当写完这篇文章时，gemfield对C++语法的复杂性充满了深深的忧虑。

##  **基础类型推导**

Gemfield将从auto和decltype展开。

**1，auto**

    
    
    auto gemfield = 7030;
    auto civilnet = 7.19;
    auto syszux = gemfield + civilnet;

auto关键字告诉编译器从初始化表达式中自动推导出变量的类型——因此使用auto的地方都隐含着某种初始化表达式。auto语法看着很简单，但其实不然，我们一一说来：

**1.1，类型推导的一致性**

    
    
    auto gemfield = 7030, civilnet = 7.19;

上述的语法对吗？不对！因为auto的类型在前面推导为int，后面又被推导为double，这就很矛盾了，编译器会报错：

    
    
    a.cpp:146:5: error: inconsistent deduction for ‘auto’: ‘int’ and then ‘double’
      146 |     auto gemfield = 7030, civilnet = 7.19;

**1.2，type decay之引用语义的消失**

auto关键字推导出的类型并不总是和初始化表达式的类型一致。以下面的代码为例：

    
    
    int gemfield = 7030;
    int& r = gemfield;
    auto a = r; //a的类型是int，而不是reference

r的类型为int&，而gemfield的类型为int，也就是说，“引用”语义被去掉了！会被去掉语义的不止是“引用”类型，还有top-
level的const语义。

**1.3，type decay之const语义的消失**

当const语义遇到auto后，并且是以传值的方式进行类型推导的话（也就是说传引用的情况不一样），top-level的const会被auto忽略：

    
    
    const int gemfield = 7030;
    auto a = gemfield; //a的类型是int，而不是const int

如果在使用auto的时候想要带reference或者const语义，那就显式的加上：

    
    
    auto& a = r; 
    const auto& a = gemfield;

**1.4，auto在Universal reference的上下文中时**

下文还会有更详细的解释。

    
    
    int x = 7030;
    const int cx = x;
    const int& rx = x;
    
    //gemfield type是int，根据上面所说的type decay，const和引用语义都被移除
    auto gemfield = rx;
    
    //使用引用进行类型推导,各种语义得以保留，gemfield的type是const int&
    auto& gemfield = rx;
    
    
    //universal reference 或者 forwarding reference
    //因为rx是lvalue，因此gemfield的type是const int&
    auto&& gemfield = rx;
    

在看完下文的模板参数的类型推导后，你就会感受到，auto的类型推导和模板参数的类型推导真是一样啊。

**1.5，当auto遇到initializer_list**

**initializer_list没有类型** ，因此auto遇到它想要推导出类型就变得很棘手了，尤其是initializer_list分为direct-
list-initialization和copy-list-
initialization，initializer_list的元素数量又分为1个或多个，因此共四种情况。下面这4个例子就分别表明了这四种情况：

    
    
    //direct-list-initialization，多个元素
    //语法错误，编译不过
    auto gemfield_error{1,719,7030};
    
    //C++14和C++17一样，gemfield的类型为std::initializer_list<int>
    auto gemfield = {1,719,7030};
    
    //gemfield的类型为int；
    auto gemfield{17};
    
    //C++14和C++17一样，gemfield的类型为std::initializer_list<int>
    auto gemfield = {17};

上述第一个例子会导致编译期的错误：

    
    
    a.cpp:171:35: error: direct-list-initialization of ‘auto’ requires exactly one element [-fpermissive]
      171 |     auto gemfield_error{1,719,7030};
          |                                   ^
    a.cpp:171:35: note: for deduction to ‘std::initializer_list’, use copy-list-initialization (i.e. add ‘=’ before the ‘{’)

**2, decltype**

auto的类型推导是根据初始化表达式来的，但有时候我们只想要表达式的类型，而不想用这个表达式来进行初始化，这就是decltype：

    
    
    decltype(func()) gemfield = x;

值得说明的时候， **func()并不会被调用**
，decltype只是通过其推导出它的返回值类型而已。decltype的行为和auto有很大的区别，并且decltype进行类型推导的时候，可以输入一个变量，也可以输入一个表达式。当decltype的输入是变量的时候，decltype返回这个变量的类型，并且会保留top-
level的const语义，也会保留reference语义：

    
    
    const int gemfield = 7030;
    const int& r = gemfield;
    
    decltype(gemfield) x = 0; //x是const int 类型
    decltype(r) y = x; //y是const int&类型，因此必须初始化

可以看出来，decltype和auto的行为有很大的不同。当decltype的输入是表达式的时候，decltype得到的类型是这个表达式返回的类型，下面是两个有趣的例子：

    
    
    int gemfield = 7030;
    int* p = &gemfield;
    int& r = gemfield;
    
    decltype(r) x; //x是int&
    decltype(r + 0) x; //x是int，不是int&
    decltype(*p) y; //y是int&，而不是int

y之所以是int&，是因为*p是通过一个地址的索引来得到的值，更像是一个引用而不是普通的int。说完了表达式，我们再回到变量。当把变量用括号扩起来时，编译器就认为这是一个表达式（expression，而不是name或者id），当作为decltype的输入时，decltype会返回该类型的引用：

    
    
    int gemfield = 7030;
    
    decltype(gemfield) x; //x是int
    decltype((gemfield)) x; //x是int&，不是int

也就是说：

  1. **decltype(lvalue expr of type T) 的值是T & **
  2. **decltype(lvalue expr of type T) 的值是T & **
  3. **decltype(lvalue expr of type T) 的值是T & **

重要的话说3遍。

**3，Reference Collapsing规则：**

需要注意的是，auto、decltype以及后面会提到的模板都适用于Reference Collapsing规则：

  1. A& & \--> A&
  2. A& && \--> A&
  3. A&& & \--> A&
  4. A&& && \--> A&&

    
    
    Gemfield g;
    decltype(g)&& r1 = std::move(g） //Gemfield&&
    decltype((g))&& r2 = g //Gemfield& && -> Gemfield&

**4，typeid**

typeid是为RTTI提供的第二个operator，意思是问入参：Hi，你的类型是什么呀？typeid的返回值是一个type_info类，在标准库中定义。
**当typeid的入参是const类型时，top-level的const语义会被忽略**
（顺便说一句，当typeid的入参是reference类型时，reference语义也会被忽略）。哇，这个像极了auto类型推导啊！

##  **Universal reference（forwarding** reference **）和reference collapsing**

我们都知道lvalue reference和rvalue reference:

  1. 所有类型为lvalue reference的值都是lvalue； 
  2. 所有类型为rvalue reference的值，根据if-it-has-a-name rule:“ **if it has a name, then it is an lvalue. Otherwise, it is an rvalue.** ”; 

一般人是不理解上面两句话的，我还是来举例说明下。一个值是lvalue还是rvalue，是和这个值的类型独立的或者不相关的。比如下面的代码：

    
    
    int gemfield = 7030;
    int syszuxF(){
        int gemfield = 7030;
        return gemfield;
    }

同样都是类型int，一个是直接定义的，一个是从function内部返回的临时变量，前者是lvalue，后者是rvalue。好了，有了这个简单的例子，我们再回到上面的rvalue
reference类型，这个类型的值是rvalue和lvalue并不和它的类型（也就是rvalue reference）必然相关，因此就有了这个if-it-
has-a-name rule：

    
    
    //注意std::move
    void syszuxF(Gemfield&& g){
        ...
        准备使用std::move(g)
        ...
    }

上述代码中，g的类型是rvalue reference，毫无疑问，它说明g就是准备让你move的。但是， **g本身有名有姓的，根据if-it-has-a-
name rule，g是个lvalue！因此，大概率上，你需要在函数内部使用std::move(g)将g变回rvalue！**
不然的话，g就是lvalue，意味这你只能在其上使用copy语义，而不能使用move语义！而syszuxF的参数类型是rvalue
reference类型，意思是你就应该用move语义（是应该，而不是强制）！！！

好了，那什么是Universal reference呢（也叫forwarding reference）？Universal
reference就是lvalue reference和rvalue reference的量子态，呃......也就是说，Universal
reference虽然“既不是lvalue reference又不是rvalue reference”，但是，Universal
reference又“既是lvalue reference又是rvalue reference”......且听Gemfield细说开来。

Universal reference是指必须满足以下两项要求的reference：

  1. 必须具备T&&的语法； 
  2. T必须是deduced的类型（auto、decltype、模板参数类型等）； 

举2个例子(这个例子就符合上面的两项要求，因此都是universal reference)：

    
    
    //模板
    template <typename T>
    void syszuxF(T&& param);
    
    //auto
    auto&& gemfield = xxx;

由于Universal reference的T必须是deduced的类型，因此Universal
reference必须有初始化表达式。而当T的类型被推导出来，也就是一旦被观察到具体的类型，那么Universal
reference就会坍塌为具体的lvalue reference或者rvalue reference，根据 **Reference
Collapsing规则：**

  1. A& & \--> A&
  2. A& && \--> A&
  3. A&& & \--> A&
  4. A&& && \--> A&&

具体说来，就是：

  1. 当初始化表达式推导出T为lvalue，T的类型会deduce为T&，则Universal reference就会坍塌为lvalue reference； 
  2. 当初始化表达式推导出T为rvalue，T的类型会decude为T，则Universal reference就会坍塌为rvalue reference； 

    
    
    Gemfield g;
    //g is lvalue, universal reference坍塌为lvalue reference
    //T被deduce为Gemfield&，模板被实例化为syszuxF(Gemfield& &&)，坍塌为syszuxF(Gemfield&)
    syszuxF(g);
    
    //std::move(g)为rvalue，universal reference坍塌为rvalue reference
    //T被deduce为Gemfield，模板被实例化为syszuxF(Gemfield&&)
    syszuxF(std::move(g));
    
    //Gemfield()是rvalue，universal reference坍塌为rvalue reference
    //T被deduce为Gemfield，模板被实例化为syszuxF(Gemfield&&)
    syszuxF(Gemfield());
    
    ////////////////////////////
    //10为rvalue，因此universal reference坍塌为rvalue reference
    //auto&& 转换为 int&&
    auto&& gemfield = 10;
    
    //v[7]是lvalue，因此universal reference坍塌为lvalue reference
    //auto&& 转换为 double&
    std::vector<double> v;
    auto&& gemfield = v[7];

这个时候该std::forward出场了：

    
    
    //注意std::forward
    template <typename T>
    void syszuxF(T&& param){
        ...
        准备使用std::forward<T>(param);
        ...
    }

因为param的类型是universal reference，很可能collapsing为lvalue
reference，也很可能collapsing为rvalue reference，因此，当坍塌为lvalue
reference的时候，我们希望param的lvalue语义能按照意愿继续传递的下去；而当坍塌为rvalue
reference的时候，我们希望param的rvalue夙愿能通过类似std::move重新找回来。但是，我们处于量子态，不知道会collapsing成什么类型，所以不能想当然使用std::move但又不能不用，那怎么办呢？这种情况下，我们就使用std::forward来对param的“量子态”语义进行完美转发。

##  **函数的模板参数类型推导**

比方说Gemfield定义了如下的模板函数：

    
    
    template <typename T>
    T syszuxMax(T a, T b){
        return a > b ? a : b;
    }
    

如果使用下面的方式调用：

    
    
    ::syszuxMax(7.0, 19);

那么在编译的时候会报如下的错误：

    
    
    a.cpp: In function ‘int main(int, char**)’:
    a.cpp:37:24: error: no matching function for call to ‘syszuxMax(double, int)’
       37 |     ::syszuxMax(7.0, 19);
          |                        ^
    a.cpp:21:3: note: candidate: ‘template<class T> T syszuxMax(T, T)’
       21 | T syszuxMax(T a, T b){
          |   ^~~~~~~~~
    a.cpp:21:3: note:   template argument deduction/substitution failed:
    a.cpp:37:24: note:   deduced conflicting types for parameter ‘T’ (‘double’ and ‘int’)
       37 |     ::syszuxMax(7.0, 19);

这是因为模板实在是无法推到出T的类型，一个是int，一个是double，而参数列表表明两个参数的类型是一模一样的，这就很矛盾了。那怎么解决这个问题呢？情况很复杂，Gemfield一一说来。

函数的模板参数推导包含两个方面：函数参数类型的推导和模板参数类型的推导，参数的传递方式又分为传值和传引用两种。

**1，传值的类型推导**

传值的时候，除了带来的copy操作外，最大的问题就是type decay：

  1. 函数、数组类型会自动转换为（decay）为指针； 
  2. cv修饰符（const、volatile修饰符）会被移除； 
  3. 引用语义会被移除（也就是说，reference会被自动转换为被引用对象的类型）； 

Gemfield来举个例子：

    
    
    template <typename T>
    void syszuxF(T arg){
       ...
    }
    
    std::string str = "gemfield is a civilnet maintainer";
    //T会被推导为std::string
    syszuxF(str);
    
    //参数类型为const char[9],decay为const char* 指针
    syszuxF("gemfield");
    
    int i = 70;
    const int c = 30;
    syszuxMax(i, c); 

那么typename T会是什么类型呢？int还是const
int？根据上面所述，const会被自动去掉，因此T的类型是int。但是，这就在其它方面造成了问题，比如，模板函数里调用模板函数，const等语义如何进一步传递呢（因为被自动去掉了啊）？参考上文中提到的forwarding
reference/Universal reference。

**2，传引用时的类型推导**

先看个模板参数为引用的例子：

    
    
    template<typename T>
    void syszuxF(const T& param);
    
    int x = 7030;
    const int cx = x;
    const int& rx = x;
    
    //T = int, param type = const int&
    syszuxF(x);
    
    //T = int, param type = const int&
    syszuxF(cx);
    
    //T = int, param type = const int&
    syszuxF(rx);

可以看到， **对模板参数T的类型推导，取决于函数参数是如何声明的**
。在syszuxF(cx)调用中，cx已经是const类型了，于是T被推导为int，当然param的类型还是const
int&。当模板参数是指针的时候，情况一样。这个的最大特点就是不会导致type decay，但也有其它问题，比如传字符串时：

    
    
    template<typename T>
    void syszuxStr(const T& str1, const T& str2){
        std::cout<<str1<<" | "<<str2<<std::endl;
    }
    
    //调用syszuxStr函数
    syszuxStr("hello","Gemfield");
    

看起来很简单，也不会有什么问题吧？错了，编译器会给出如下错误：

    
    
    syszux.cpp:186:33: error: no matching function for call to ‘syszuxStr(const char [6], const char [9])’
      186 |     syszuxStr("hello","Gemfield");
          |                                 ^
    syszux.cpp:181:6: note: candidate: ‘template<class T> void syszuxStr(const T&, const T&)’
      181 | void syszuxStr(const T& str1, const T& str2){
          |      ^~~~~~~~~
    syszux.cpp:181:6: note:   template argument deduction/substitution failed:
    syszux.cpp:186:33: note:   deduced conflicting types for parameter ‘const T’ (‘char [6]’ and ‘char [9]’)
      186 |     syszuxStr("hello","Gemfield");

这是因为，传引用的时候，参数的类型被完整保留了下来，也就是在str1参数处，T的类型被推导为 **const char [6]**
，而在参数str2处，T的类型被推导为 **const char [9]** ，前后矛盾了。所以这种情况下，反而需要 **type decay**
（为const char*)，所以解决方案要么是传值，要么是使用std::decay:

    
    
    template<typename T>
    void syszuxStr(std::decay_t<const T&> str1, const T& str2){
        std::cout<<str1<<" | "<<str2<<std::endl;
    }
    

##  **函数返回值类型的推导和Trailing return types**

如果类型推到具体到函数的返回值上时，情况又会不一样了，还是以上面的syszuxMax函数举例，假设此时这个函数的两个参数类型不一样：

    
    
    template <typename T1, typename T2>
    T1 syszuxMax(T1 a, T2 b){
        return a > b ? a : b;
    }

我擦，函数返回值的类型怎么办？返回值的类型要么是T1，要么是T2，但又不确定是T1还是T2，如果在模板参数列表里加一个T3，则又很冗余(因为T3属于T1或T2啊）：

    
    
    template <typename T1, typename T2, typename T3>
    T3 syszuxMax(T1 a, T2 b){
        return a > b ? a : b;
    }

那怎么办呢？C++ 11 提出了个Trailing return types，配合auto关键字，来解决上述的问题：

    
    
    template <typename T1, typename T2>
    auto syszuxMax(T1 a, T2 b) -> decltype(a > b ? a : b){
        return a > b ? a : b;
    }

decltype里面是个lambda表达式。注意这是C++11的语法，还是有局限性的，那就是必须有Trailing return
types，并且decltype中的lambda表达式只能有一句。

而到了C++14，函数返回值类型的推导就可以扩大到任何函数了，而且语法更加简化了：

    
    
    template <typename T1, typename T2>
    auto syszuxMax(T1 a, T2 b){
        return a > b ? a : b;
    }

直接根据函数体中的return表达式来推导返回值类型（但这不意味着Trailing return types就没用了，因为这个语法在Name
lookup方面有着不同的搜索范围，简单来说，就是可以寻找在函数体中定义的符号名字）。当特别针对函数返回值类型的推导时，注意以下两条规则：

  1. 当函数的返回值类型是auto时，使用模板类型的推导规则（注意，不是使用前述auto的类型推导规则）； 
  2. 当函数的返回值类型是decltype(auto)时，使用decltype类型的推导规则； 

    
    
    //返回值类型推导为int
    //因此，syszuxF() = somevalue; 编译错误
    auto syszuxF(){
        static std::vector<int> values = somevalues();
        int idx = someindex;
        return values[idex];
    }
    
    //返回值类型推导为int&
    //因此，syszuxF() = somevalue; 编译通过
    decltype(auto) syszuxF(){
        static std::vector<int> values = somevalues();
        int idx = someindex;
        return values[idex];
    }
    

总结下来就是：

  1. 当函数的返回值不应该使用引用类型时（也就是说，如果返回值是引用类型，则几乎肯定不对），那么使用auto； 
  2. 当函数的返回值可能是引用类型时，使用decltype(auto)； 

##  **类的模板参数类型推导**

在C++17之前，类模板的实例化必须显式指定模板参数类型，而不能deduce出来：

    
    
    Stack <int> s1;
    
    //在每个版本都ok
    Stack <int> s2 = s1;
    
    //C++17之后OK
    Stack s3 = s1;

通过在模板类中定义构造函数来接收相关的初始化参数，C++17就支持类模板类型的deduce。通过定义携带初始化参数的构造函数，在C++17，类模板的类型就可以被推导出来，如下所示：

    
    
    //定义带有初始化参数的构造函数
    template<typename T>
    class Stack{
        private:
            std::vector<T> elems;
        public:
            Stack() = default;
            Stack(const T& elem) : elems({elem}){
            }
    };
    
    //C++17中，类模板的类型就可以被推导出来
    //在以前，你得写成Stack<int> gemfield_stack;
    Stack gemfield_stack = 0;

当然了，携带初始化参数的构造函数很关键，不然编译器就会报错：

    
    
    syszux.cpp: In function ‘int main(int, char**)’:
    syszux.cpp:180:24: error: class template argument deduction failed:
      180 |     Stack init_stack = 0;
          |                        ^
    syszux.cpp:180:24: error: no matching function for call to ‘Stack(int)’
    syszux.cpp:175:9: note: candidate: ‘template<class T> Stack()-> Stack<T>’
      175 |         Stack() = default;
          |         ^~~~~
    syszux.cpp:175:9: note:   template argument deduction/substitution failed:
    syszux.cpp:180:24: note:   candidate expects 0 arguments, 1 provided
      180 |     Stack init_stack = 0;
          |                        ^
    syszux.cpp:171:7: note: candidate: ‘template<class T> Stack(Stack<T>)-> Stack<T>’
      171 | class Stack{
          |       ^~~~~
    syszux.cpp:171:7: note:   template argument deduction/substitution failed:
    syszux.cpp:180:24: note:   mismatched types ‘Stack<T>’ and ‘int’
      180 |     Stack init_stack = 0;
    

而这些“相关的初始化参数”，也有传值和传引用之分。传值会type decay，传引用不会。另外，你也可以在类的定义体后使用deduction
guides，来显式说明，当传递的参数为类型T1时，类模板应该实例化为T2类型：

    
    
    template<typename T>
    class Stack{
        private:
            std::vector<T> elems;
        public:
            Stack() = default;
            Stack(const T& elem) : elems({elem}){}
    };
    //deduction guides
    Stack(double) -> Stack<int>;

##  **Lambda capture type deduction**

如果使用引用的话，和模板的类型推导（传引用部分）一样，此处就不再赘述了；

当使用传值来capture变量值的话，情况有些微妙了。在开始这个话题前，我们先来澄清一些容易混淆的概念：by-value capture 和 by-
value init capture：

当使用by-value capture时，cv属性会被保留。

    
    
    const int gemfield = 0;
    auto lam = [gemfield] {...};
    
    //编译器相当于创建了一个内部类：
    class XXX{
      private:
        const int gemfield;
      ...
    };

当使用by-value init capture时，相当于auto赋值，cv属性会被移除：

    
    
    const int gemfield = 0;
    auto lam = [gemfield = gemfield] {...};
    
    //编译器相当于创建了一个内部类：
    class XXX{
      private:
        int gemfield;
      ...
    };

等号右边的gemfield是外面的const int，等号左边的gemfield相当于使用auto进行类型推导。又因为是传值，因此cv属性无法保留。


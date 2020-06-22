##  **背景**

一切都从函数传参开始说起。我们知道，在C语言中有个神奇的函数：printf：

    
    
    printf("%s : %d\n","gemfield number",7030);
    

这个函数可以传递可变参数，说到“可变”参数，主要是指两点可变：1，参数数量可变；2，参数类型可变。比如上面演示的C库中的printf，数量是可变的，类型也是可变的。

多么好玩的函数参数定义啊！参数的数量居然可变，类型居然也可变！那我们自己可以实现一个类似的函数吗？可以，借助C语言提供的va_list、va_start、va_arg、va_end宏，可以轻松实现类似的可变参数。

    
    
    va_arg：宏定义，用来获取下一个参数
    va_start：宏定义，开始使用可变参数列表
    va_end：宏定义，结束使用可变参数列表
    va_list：类型，存储可变参数的信息

我们用代码试试吧，Gemfield定义了一个syszuxPrint函数，第一个参数指明参数的个数，第二个参数...是parameter pack：

    
    
    #include <cstdarg>
    void syszuxPrint(int n, ...){
        va_list args;
        va_start(args, n);
        while(n--){
            std::cout<<va_arg(args, int)<<", ";
        }
        va_end(args);
        std::cout<<std::endl;
    }
    int main(int argc, char** argv)
    {
        syszuxPrint(3, 719,7030,27030);
    }

程序完美的打印出了：“719, 7030,
27030,”。等等，这里只是实现了参数的可变，参数类型如何可变呢？其实也可以，主要到va_arg宏的第二个参数int了吗？这种硬编码限制了目前我们只能传递int类型。我们稍微简陋的改造下上面的代码：

    
    
    #include <cstdarg>
    void syszuxPrint(int n, ...){
        va_list args;
        va_start(args, n);
        while(n--){
            if(n == 0){
                std::cout<<va_arg(args, const char*)<<", ";
                continue;
            }
            std::cout<<va_arg(args, int)<<", ";
        }
        va_end(args);
        std::cout<<std::endl;
    }
    int main(int argc, char** argv)
    {
        syszuxPrint(3, 719,7030,"civilnet");
    }

程序就可以打印出了字符串了：“719, 7030,
civilnet,”，好了，目前我们已经初步的、简陋的实现了参数的数量可变和参数类型的可变。经历了上面这一过程，我们就自然而然的知道了一个真相，那就是printf这样的函数，为什么第一个参数总是“格式化字符串”，就像文章开头printf("%s
: %d\n","gemfield number",7030);中的"%s : %d\n"？因为：
**格式化字符串告诉了va_*宏这两点关键信息：可变参数的个数（百分号的个数）、可变参数的类型（%s、%d等）。而C++的可变参数模板克服了这些限制！**

##  **可变参数模板的基础原理**

C++的可变参数模板是怎么做到不需要告诉参数个数，也不需要告诉参数类型的呢？这仰仗于C++以下的功能：

  1. 函数重载，依靠参数的pattern去匹配对应的函数； 
  2. 函数模板，依靠调用时传递的参数自动推导出模板参数的类型； 
  3. 类模板，基于partial specialization来选择不同的实现； 

**1，基础语法和例子说明**

可变参数模板的关键字沿用了C语言的ellipsis（...)，并且在3种地方进行了使用：

    
    
    void syszuxPrint(){std::cout<<std::endl;}
    
    template<typename T, typename... Ts>
    void syszuxPrint(T arg1, Ts... arg_left){
        std::cout<<arg1<<", ";
        syszuxPrint(arg_left...);
    }
    
    int main(int argc, char** argv)
    {
        syszuxPrint(719,7030,"civilnet");
    }
    

哇，看起来比C的实现要简单漂亮多了（还没提到其它好处！）Gemfield先做个简单解释：

  1. typename... Ts，这是 **template parameter pack** ，表明这里有多种type； 
  2. Ts... arg_left，这是 **function parameter pack** ，表明这里有多个参数； 
  3. arg_left...，这是 **pack expansion** ，将参数名字展开为逗号分割的参数列表； 

在上述代码中，main函数里调用了syszuxPrint(719,7030,"civilnet");会导致syszuxPrint函数模板首先展开为：

    
    
    void syszuxPrint(int, int, const char*)

在打印第1个参数719后，syszuxPrint **递归**
调用了自己，传递的参数为arg_left...，该参数会展开为【7030,"civilnet"】，syszuxPrint第2次进行了展开：

    
    
    void syszuxPrint(int, const char*)

在打印第1个参数7030后，syszuxPrint **递归**
调用了自己，传递的参数为arg_left...，该参数会展开为【"civilnet"】，syszuxPrint第3次进行了展开：

    
    
    void syszuxPrint(const char*)

在打印第1个参数"civilnet"后，syszuxPrint **递归**
调用了自己，传递的参数为arg_left...，该参数会展开为【】，syszuxPrint准备进行第4次展开：void
syszuxPrint()，但是，我们已经定义了这个函数：

    
    
    void syszuxPrint(){std::cout<<std::endl;}

上面这个函数是函数模板syszuxPrint的“非模板重载”版本，于是展开停止，直接调用这个“非模板重载”版本，递归停止。

**2，换个花样重载**

上面的例子里有个syszuxPrint的“非模板重载”版本，目的就是为了递归能够最终退出，基于这个原理，我们也可以按照如下方式重新实现：

    
    
    template<typename T>
    void syszuxPrint(T arg){std::cout<<arg<<", "<<std::endl;}
    
    template<typename T, typename... Ts>
    void syszuxPrint(T arg1, Ts... arg_left){
        std::cout<<arg1<<", ";
        syszuxPrint(arg_left...);
    }
    
    int main(int argc, char** argv)
    {
        syszuxPrint(719,7030,"civilnet");
    }

这里不再有syszuxPrint的“非模板重载”版本了，而是两个函数模板，区别是模板参数的区别：当两个参数模板都适用某种情况时，优先使用没有“template
parameter pack”的版本。

**3，sizeof...操作符和一些“勇敢但错误”的想法**

上面定义的syszuxPrint可变参数模板比起C语言的VA_*来说，不知道是好到哪里去了，但是还有一点让人不舒服：它总是需要定义2次，目的只是为了让递归退出。有没有更优雅的办法呢？

C++11引入了sizeof...操作符，可以得到可变参数的个数（注意sizeof...的参数只能是parameter
pack，不能是其它类型的参数啊），如下所示：

    
    
    std::cout<<"DEBUG: "<<sizeof...(Ts)<<" | "<<sizeof...(arg_left)<<std::endl;

这样可以打印出parameter的个数。你一定这样想了，如果通过sizeof...判断出arg_left这个parameter
pack的个数为零了，那就退出递归调用不好吗？就像下面这样：

    
    
    template<typename T, typename... Ts>
    void syszuxPrint(T arg1, Ts... arg_left){
        std::cout<<arg1<<", ";
        if(sizeof...(arg_left) > 0){
            syszuxPrint(arg_left...);
        }
    }
    
    int main(int argc, char** argv)
    {
        syszuxPrint(719,7030,"civilnet");
    }

你看，syszuxPrint只定义了1次，我们在函数体里使用了sizeof...，如果parameter
pack为零了，我们就停止递归调用。但不幸的是，编译程序报错：

    
    
    civilnet.cpp: In instantiation of ‘void syszuxPrint(T, Ts ...) [with T = const char*; Ts = {}]’:
    civilnet.cpp:211:20:   recursively required from ‘void syszuxPrint(T, Ts ...) [with T = int; Ts = {const char*}]’
    civilnet.cpp:211:20:   required from ‘void syszuxPrint(T, Ts ...) [with T = int; Ts = {int, const char*}]’
    civilnet.cpp:217:36:   required from here
    civilnet.cpp:211:20: error: no matching function for call to ‘syszuxPrint()’
      211 |         syszuxPrint(arg_left...);
          |         ~~~~~~~~~~~^~~~~~~~~~~~~
    civilnet.cpp:208:6: note: candidate: ‘template<class T, class ... Ts> void syszuxPrint(T, Ts ...)’
      208 | void syszuxPrint(T arg1, Ts... arg_left){
          |      ^~~~~~~~~~~
    civilnet.cpp:208:6: note:   template argument deduction/substitution failed:
    civilnet.cpp:211:20: note:   candidate expects at least 1 argument, 0 provided
      211 |         syszuxPrint(arg_left...);
          |         ~~~~~~~~~~~^~~~~~~~~~~~~

核心错误是这句【 **civilnet.cpp:211:20:error:** no matching function for call to ‘
**syszuxPrint()** ’】，啥意思啊？为什么还在试图调用空的syszuxPrint？为啥sizeof...那个if条件表达式没有生效？

这是因为，可变参数模板syszuxPrint的所有分支都被instandiated了，并不会考虑上面那个if表达式。一个instantiated的代码是否有用是在runtime时决定的，而所有的instantiation是在编译时决定的。所以syszuxPrint()空参数版本照样被instandiated，而当instandiated的时候并没有发现对应的实现，于是编译期报错。

**4，C++17的if constexpr表达式和梦想实现**

C++17中引入了编译期if表达式（if constexpr），可以用来完美的解决这个问题：

    
    
    template<typename T, typename... Ts>
    void syszuxPrint(T arg1, Ts... arg_left){
        std::cout<<arg1<<", ";
        if constexpr(sizeof...(arg_left) > 0){
            syszuxPrint(arg_left...);
        }
    }
    
    int main(int argc, char** argv)
    {
        syszuxPrint(719,7030,"civilnet");
    }

上面的代码中，我们使用了if constexpr，完美编译成功：g++ **-std=c++17** civilnet.cpp -o
civilnet。注意-std=c++17，因为Gemfield所用的g++还没有默认启用C++17的feature。

##  **Fold表达式（C++17的feature）**

C++17中引入了Fold表达式，如下所示：

    
    
    template<typename... T>
    auto syszuxSum(T... s){
        return (... + s);
    }
    int main(int argc, char** argv)
    {
        syszuxSum(719,7030,27030);
    }

当binary operator和parameter pack结合起来后，可以自动循环执行计算。像上述的... + s展开后，就相当于( (719 +
7030) + 27030)。Fold表达式有如下四种形式：

  1. (... op pack)，相当于((( pack1 op pack2 ) op pack3 ) ... op packN) 
  2. (pack op ... )，相当于(pack1 op ( ... ( packN-1 op packN))) 
  3. (init op ... op pack)，相当于((( init op pack1) op pack2) ... op packN) 
  4. (pack op ... op init),相当于(pack1 op ( ... (packN op init))) 

这里的op几乎是所有的binary operator都可以，不止是加减乘除，甚至是
指针操作，甚至是<<，我们现在再来简化下上面的syszuxPrint可变参数模板：

    
    
    template<typename... Ts>
    void syszuxPrint(Ts... arg_left){
        (std::cout<< ... << arg_left) << std::endl;
    }
    
    int main(int argc, char** argv)
    {
        syszuxPrint(719,7030,"civilnet");
    }

我去，已经这么简化和优雅了吗？！只不过还有个小遗憾，就是这种情况下，输出的元素之间没有前文中那种分隔符了，这倒是也可以解决，只不过解决后代码就没现在这样看起来简洁和震撼了，所以Gemfield不在这里演示了。

##  **Variadic Expressions （可变参数表达式）**

你还可以对可变参数进行批量计算（这个可不是C++17的feature）。请看下面的例子：

    
    
    template<typename... T>
    auto foldSum(const T&... s){
        syszuxPrint(s + s...);
    }
    int main(int argc, char** argv)
    {
        foldSum(719,7030, std::string("CivilNet"));
    }

注意看其中的syszuxPrint(s + s...)用法，真是让人瞠目结舌啊。这个表达式就相当于syszuxPrint( (719 + 719),
(7030+7030), (string("CivilNet)+string("CivilNet)) )。同理：syszuxPrint(1 +
s...)相当于将参数展开后的每个参数加1。 **注意这里的语法** ：

  1. syszuxPrint(1 + s...) //正确！ 
  2. syszuxPrint(1 + s ...) //正确！ 
  3. syszuxPrint((1 + s)...) //正确！ 
  4. syszuxPrint(s + 1 ...) //正确，注意1后面有空格！ 
  5. syszuxPrint((s + 1)...) //正确！ 
  6. syszuxPrint(s + 1...) //错误，注意1后面没有空格！ 

Gemfield还是喜欢syszuxPrint((1 + s)...) 和syszuxPrint((s + 1)...) 这样的写法，看起来更易读一些。

##  **Variadic Indices（可变参数索引）**

索引操作也可以和可变参数语法结合起来：

    
    
    template<typename C, typename... Idx>
    auto testVariadicIndices(const C& c, Idx... idx){
        syszuxPrint(c[idx]...);
    }
    int main(int argc, char** argv)
    {
        std::vector<std::string> vec{"gemfield","is","a","civilnet","maintainer"};
        testVariadicIndices(vec,0,3,4);
    }

注意这个语法：syszuxPrint(c[idx]...)，程序会打印出【gemfield, civilnet,
maintainer,】。你也可以使用nontype模板参数来改造下上面的程序：

    
    
    template< int... idx, typename C>
    auto testVariadicIndices(const C& c){
        syszuxPrint(c[idx]...);
    }
    int main(int argc, char** argv)
    {
        std::vector<std::string> vec{"gemfield","is","a","civilnet","maintainer"};
        testVariadicIndices<0,3,4>(vec);
    }

##  **Variadic Class Templates (可变参数类模板)**

可变参数模板可以同样作用到类模板上。一个重要的例子就是Tuple：

    
    
    template<typename... Elements>
    class Tuple;
    ......
    Tuple<int, std::string, char> t;

t现在就可以保存integer、string、character类型的数据。

在著名的日志库log4debug/gemfield.h中：

[ https://  github.com/CivilNet/Gem
field/blob/master/src/cpp/log4debug/gemfield.h
](https://link.zhihu.com/?target=https%3A//github.com/CivilNet/Gemfield/blob/master/src/cpp/log4debug/gemfield.h)

就使用了可变参数类模板。你可以去看看。

##  **Variadic Base Blasses（可变参数基类）**

这个名字就很直截了当了，在类的继承体系中，基类也可以是可变参数，如下所示：

    
    
    class Gemfield
    {
        public:
            void test1(){
                std::cout<<"This is base class Gemfield."<<std::endl;
            }
    };
    
    class CivilNet
    {
        public:
            void test2(){
                std::cout<<"This is base class CivilNet."<<std::endl;
            }
    };
    
    template<typename... Bases>
    class SYSZUX : public Bases...{};
    
    int main(int argc, char** argv)
    {
        SYSZUX<Gemfield, CivilNet> syszux;
        syszux.test1();
        syszux.test2();
    }

注意上述代码中的public Bases... 语法，基类处出现了可变参数。程序输出：

    
    
    gemfield@ThinkPad-X1C:~$ ./civilnet 
    This is base class Gemfield.
    This is base class CivilNet.


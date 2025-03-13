# 背景
这些原则是美国软件工程师Robert C. Martin在他 2000 年的论文设计原则和设计模式中首次介绍的诸多原则的一个子集。SOLID设计原则包含5个原则（SOLID也是这5个原则的首字母的缩写，是后来在 2004 年左右由 Michael Feathers 引入的）：

- 单一责任原则，single-responsibility principle；
- 开放封闭原则，open–closed principle；
- 里氏替换原则，Liskov substitution principle；
- 接口隔离原则，interface segregation principle；
- 依赖倒置原则，dependency inversion principle。

其中，单一责任原则是说，一个类或者函数只应该干一件事情，有自己的特定目的，这个理念比较简单，Gemfield本文就略过了。

# 开放封闭原则
类应该为扩展敞开大门（open），而为修改关闭大门（close）。也就是说，我们设计出来的类最好不要修改，但是可以被扩展。在OOP中，扩展指的就是继承。也就是要通过继承实现我们想要的修改。举个例子，我们有个约会类Dating:
```c++
class Dating
{
public:
    virtual void travel(){}
    virtual void dinner(){}
    virtual void movie(){}
    virtual void sex(){}
    virtual void schedule(){
        movie();
        dinner();
        travel();
        sex();
    }
};
```
后来呢，你因为各种各样的经验或者经历，想要修改schedule方法。久而久之，有过多种需求变动后，也就是代码经过几次改动后，你的schedule方法就会变成下面这个样子：
```c++
virtual void schedule(){
    if(xxx){
        movie();
        dinner();
        travel();
        sex();
    }else if(xxx){
        movie();
        sex();
    }else if(xxx){
        dinner();
    }else{
        sex();
    }
}
```
这就违反了OCP原则了。你不应该修改类，而应该使用继承去扩展，像下面这个样子：
```c++
class Dating1 : public Dating
{
public:
    virtual void schedule(){
        movie();
        sex();
    }
};

class Dating2 : public Dating
{
public:
    virtual void schedule(){
        dinner();
    }
};

class Dating3 : public Dating
{
public:
    virtual void schedule(){
        sex();
    }
};
```
再结合下面提到的里氏替换、接口隔离、依赖倒置等原则，你就可以从容使用不同的Dating实例，游刃有余的应对各种需求变更了。

# 里氏替换原则
当基类的指针（或引用）指向子类1的实例时，我们可以使用子类2来替换子类1，而不影响使用。举个例子，我们有个约会类Dating：
```c++
class Dating
{
public:
    virtual void sex(){}
};
```
现在我要实现自己的Dating：
```c++
class MyDating : public Dating
{
public:
    virtual void sex(){}
};
```
这不好，因为Gemfield的dating绝不会sex，因此，代码应该重构为：
```c++
class Dating {};

class QuickDating : public Dating
{
public:
    virtual void sex(){}
};

class MyDating : public Dating
{
public:
    virtual void dinner() {}
};

class OthersDating : public QuickDating
{
};
```
这样一来：
```c++
QuickDating* qd = new OthersDating();
QuickDating* qd = new OthersDating2();
qd->sex();
```
qd的指向可以从OthersDating替换为OthersDating2，也总是可以像预期的那样调用sex()方法；而MyDating绝不会sex，也正因此它也没有被设计为QuickDating的子类，因此也就不能替换到这里了。

# 接口隔离原则
接口隔离原则( ISP ) 指出，多个具体的接口好过一个无所不容的接口，否则就会导致使用接口时依赖于其中用不到的方法。举个例子，我们有个约会类Dating：
```c++
class Dating
{
public:
    virtual void dinner() = 0;
    virtual void sex() = 0;
    virtual void movie() = 0;
    virtual void travel() = 0;
};
```
这个约会接口就是那种“无所不容”的接口，试图把约会的内容都装进去，但有些约会是用不到其中的接口的。比如Gemfield的Dating：
```c++
class MyDating : public Dating
{
public:
    virtual void dinner(){};
};
```
因为Gemfield的MyDating约会肯定不会用sex方法，如果继承上面那样的Dating基类，就会强迫MyDating类依赖了接口中用不到的方法，很难受。因此应该将代码重构为多个具体的接口，比如：
```c++
class Dating
{
};

class DinnerDating : public Dating
{
public:
    virtual void dinner() = 0;
};

class QuickDating : public Dating
{
public:
    virtual void sex() = 0;
};

class MyDating : public DinnerDating
{
public:
    virtual void dinner(){};
};
```
这样一来，Gemfield的MyDating约会实现就不用依赖一些讨厌的接口，愉快多了。

# 依赖倒置原则
上层类不应该依赖底层实现类，而是两者都应该依赖抽象接口。其实，在CS架构中，像corba、rest api这类实现，客户端和服务端都依赖共同的合约文件，这种思想就是依赖倒置（DIP）。还是用约会类来举例，假设我们有个大学生活类CollegeLife，其有个dating成员：
```c++
class QuickDating1 : public QuickDating
{
public:
    virtual void sex(){}
};

class CollegeLife
{
QuickDating* dating;
public:
    CollegeLife(){
        dating = new QuickDating1();
    }
};
```
这就违反了DIP规则了，因为上层类CollegeLife依赖了具体的实现QuickDating1。根据DIP原则，我们需要让CollegeLife依赖QuickDating接口，同时QuickDating1、QuickDating2、QuickDating3......的实现也依赖QuickDating接口（这是当然）。据此，代码应该重构为：
```c++
class CollegeLife
{
QuickDating* dating;
public:
    CollegeLife(QuickDating* qd){
        dating = qd;
    }
};

QuickDating1 qd1;
QuickDating2 qd2;
......
CollegeLife life(&qd2);
```
这就使得CollegeLife只依赖QuickDating这个接口（有的框架能够根据构造函数参数的类型自动完成实例注入），而具体实现类QuickDating1、QuickDating2、QuickDating3等也依赖QuickDating接口。并且，这也使得在运行时重新绑定CollegeLife类中的QuickDating实例成为了可能（比如运行时从QuickDating1切换为QuickDating2）。

# 总结
SOLID设计原则同其它语境下的设计原则相比，可能名称不同，但不可避免的会出现形似甚至神似。因此除了名字外，最重要的是我们要理解这些设计原则的理念。深刻的认同了这些理念（“道”），并且努力去践行，那么具体的实现手法只不过就是各种小技巧了（“术”）。

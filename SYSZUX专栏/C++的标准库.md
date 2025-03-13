# 背景
一个C++程序想要运行起来，除了离不开C++编译器，还离不开C++的标准库。我们写的C++程序要想被Linux等操作系统运行起来，必须符合一定的规范。以Linux为例，这种规范在基于X86-64处理器的Linux上称之为：System V AMD64 ABI。只有符合这个ABI规范的文件，你的程序才能被Linux的系统调用加载并成为一个进程。

众所周知，我们写的C++程序只是符合C++规范，和System V AMD64 ABI规范之间还有很远的距离。这个距离又是怎么消弭的呢？答案就是C++编译器（含链接器，以下Gemfield所说的“编译”可能包含了“链接”过程，请自行甄别）和标准C++库（当然必须还有标准C库）。

本文中，Gemfield将描述C++的标准库。并主要讨论如下的问题：

- C++标准库是什么？
- C++标准库如何被使用？
- C++标准库的内容有哪些？

# C++标准库是什么？
ISO 14882标准中，在条款20到33和附加章节D中定义的C++应该实现的内容。

这部分内容是C++标准库应该要实现的内容。有了这个标准定义，世界上各个组织才能实现具体的C++标准库。这其中，有影响力的组织及其实现有3个：GNU的libstdc++、LLVM的libc++、我不想提。一般来说：

- 在GNU/Linux上，我们使用的C++库都是GNU实现的libstdc++（/usr/lib/gcc/x86_64-linux-gnu/9/libstdc++.so、/usr/lib/gcc/x86_64-linux-gnu/9/libstdc++.a）；
- 在MacOS、iOS上，我们使用的C++库都是LLVM项目实现的libc++（/usr/lib/libc++.dylib）；
- 在Android上，我们使用的C++库为LLVM的libc++（NDK r18以前还是支持GNU的libstdc++的，在r18上被完全去除）；注意这可不是系统库，你需要将库文件包含在apk中（Android上的系统库是/system/lib/libstdc++.so，这不是GNU的那个，只包含了最小的C++ runtime实现，如new delete等）；
- 在Windows上，我们使用的C++库......算了，谁在乎呢，这年头谁还用windows呀。

# C++库如何被使用
你可能在阅读Gemfield本文的时候察觉到了，在我们平常编译C++程序的时候，并没有显式的去链接标准C++库呀。这是因为编译器自动帮你做了这个事情。如果在g++编译C++源文件的时候加上-v参数：
```bash
g++ -v gemfield.cpp -o gemfield
```
那么日志就会清楚的显示编译的时候默认使用了什么库。

## 1，编译时依赖
Gemfield把加上-v参数之后的编译日志摘要如下：
```
 -m elf_x86_64
 -dynamic-linker /lib64/ld-linux-x86-64.so.2
 -pie
 /usr/lib/gcc/x86_64-linux-gnu/9/../../../x86_64-linux-gnu/Scrt1.o
 /usr/lib/gcc/x86_64-linux-gnu/9/../../../x86_64-linux-gnu/crti.o
 /usr/lib/gcc/x86_64-linux-gnu/9/crtbeginS.o
 -lstdc++
 -lm
 -lgcc_s
 -lgcc
 -lc
 /usr/lib/gcc/x86_64-linux-gnu/9/crtendS.o
 /usr/lib/gcc/x86_64-linux-gnu/9/../../../x86_64-linux-gnu/crtn.o
```
关键的地方有：

- 编译的是elf_x86_64，也就是x86-64上的ELF格式，ELF格式是System V AMD64 ABI中的一部分，讲的是可执行文件的格式，详细内容请参考专栏libGemfield的其它文章；
- 使用的dynamic linker是/lib64/ld-linux-x86-64.so.2，这是ELF格式的一部分；
- pie，这是ASLR的前提；
- 编译时链接了libstdc++、libm、libgcc_s、libgcc、libc库；
- 编译时链接了Scrt1.o、crti.o、crtbeginS.o、crtendS.o、crtn.o。

可以看到g++在背后自动链接了标准C++库、标准C库。这其中：

- 头文件<cstdio>、<cstdlib>（或者C中的stdlib.h和stdio.h）中声明的函数就实现在了上面的libc库中；
- 头文件<cmath>（或者C中的math.h）声明的函数就实现在了上面的libm库中；
- 而libstdc++.so依赖libm.so，因此编译C++程序的时候g++也自动链接了libm.so；
- libgcc和libgcc_s库包含了一些底层的函数，g++编译的时候生成的一些函数调用依赖该库；
- Scrt1.o、crti.o、crtbeginS.o、crtendS.o、crtn.o这些文件帮助编译器生成了最终的ELF文件，更详细解释如下：
```
crt0.o
  Older style of the initial runtime code ?  Usually not generated anymore
  with Linux toolchains, but often found in bare metal toolchains.  Serves
  same purpose as crt1.o (see below).
crt1.o
  Newer style of the initial runtime code.  Contains the _start symbol which
  sets up the env with argc/argv/libc _init/libc _fini before jumping to the
  libc main.  glibc calls this file 'start.S'.
crti.o
  Defines the function prolog; _init in the .init section and _fini in the
  .fini section.  glibc calls this 'initfini.c'.
crtn.o
  Defines the function epilog.  glibc calls this 'initfini.c'.
Scrt1.o
  Used in place of crt1.o when generating PIEs.
gcrt1.o
  Used in place of crt1.o when generating code with profiling information.
  Compile with -pg.  Produces output suitable for the gprof util.
Mcrt1.o
  Like gcrt1.o, but is used with the prof utility.  glibc installs this as
  a dummy file as it's useless on linux systems.
crtbegin.o
  GCC uses this to find the start of the constructors.
crtbeginS.o
  Used in place of crtbegin.o when generating shared objects/PIEs.
crtbeginT.o
  Used in place of crtbegin.o when generating static executables.
crtend.o
  GCC uses this to find the start of the destructors.
crtendS.o
  Used in place of crtend.o when generating shared objects/PIEs.
```
## 2，运行时依赖
程序编译完成之后已经成为了ELF文件，这个时候它就可以在Linux上被执行了：
```bash
gemfield@CivilNet:~$ ./gemfield
```
但由于我们的程序默认链接的是动态库，因此在运行时会对包括C++标准库在内的一些动态库产生依赖，使用ldd命令可以看到这些依赖：
```bash
gemfield@CivilNet:~$ ldd gemfield
        linux-vdso.so.1 (0x00007ffc33380000)
        libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 (0x00007f7193c31000)
        libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007f7193c16000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f7193a24000)
        libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007f71938d5000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f7193e3c000)
```
- linux-vdso.so.1，这是Linux virtual Dynamic Shared Object (vDSO)，是个虚拟共享库，在文件系统上并不存在。Linux vDSO把kernel中的代码通过共享库的形式映射到用户的进程地址空间上。这就实现了一些原本频繁的系统调用可以直接在用户空间完成，加快了速度。内核代码在arch/x86/vdso/vdso.lds.S文件中定义了vDSO中export的函数，共4个（比如常说的gettimeofday系统调用）：
```
/*
 * This controls what userland symbols we export from the vDSO.
 */
VERSION {
        LINUX_2.6 {
        global:
                clock_gettime;
                __vdso_clock_gettime;
                gettimeofday;
                __vdso_gettimeofday;
                getcpu;
                __vdso_getcpu;
                time;
                __vdso_time;
        local: *;
        };
}
```
- /lib64/ld-linux-x86-64.so.2用来动态加载程序依赖的共享库。这是个特殊的库，其路径会直接写在可执行文件的相关字段中。而程序所依赖的其它共享库则是由ld-linux-x86-64.so.2加载进来的；
- 剩下的就是编译时链接的库中的那四个，不再赘述。

如果不想让程序在运行时还有依赖的动态库，则可以使用静态编译。

## 3，静态编译
一个C++程序，如果想静态链接的话，加上-static关键字：
```bash
g++ -v -static gemfield.cpp -o gemfield
```
如此一来，这个库在运行的时候就不依赖任何库了。但是我们不推荐这么做，原因有多个。

- C++库的bug fix，动态编译的程序只需要更新一个C++库就行了，静态编译的则要分别更新每个可执行文件；
- 一些安全相关的功能将无法被使用，比库文件的随机内存地址加载；静态编译也无法产生PIE的代码；
- 使用动态库可以节约物理内存的使用（当多个程序依赖同一个共享库的话）；
- libc库中的某些功能 (locale (through iconv), NSS, IDN, ...)需要动态链接来加载相应的外部代码，静态编译对此支持有限；
- 一些debug工具对动态库加载机制有依赖，静态编译对debug不友好；
- 版权问题，不过听说标准C++库的GPL有个例外？

当然任何事情都不是绝对的，考虑好后想用就用呗。
# C++标准库的内容有哪些？
首先，标准C++库的头文件把标准C的头文件也纳入进来作为了一个子集，如下所示：
```
<cassert>
<cctype>
<cerrno>
<cfenv>
<cfloat>
<cinttypes>
<ciso646>
<climits>
<clocale>
<cmath>
<csetjmp>
<csignal>
<cstdarg>
<cstdbool>
<cstddef>
<cstdint>
<cstdio>
<cstdlib>
<cstring>
<ctgmath>
<ctime>
<cuchar>
<cwchar>
<cwctype>
```
这些c开头的c++头文件都直接include了标准C库的头文件，比如<clocale>包含了#include <locale.h>，只不过是把符号放到了std命名空间下。在C++程序中，当然是推荐include这些标准C的头文件，而不是*.h这样的。

其次，按照不同的功能，C++的标准库包含了如下内容：

## 1，Concepts
C++20新增的。
```
<concepts>
```
## 2，Coroutines
C++20新增的。
```
<coroutine>
```
## 3，Ranges
C++20新增的。
```
<ranges>
```
## 4，工具类
C++17新增了<any> 、<optional>、 <variant>，C++20新增了<compare>、<version>、<source_location>。
```
<cstdlib>
<csignal>
<csetjmp>
<cstdarg>
<typeinfo>
<typeindex>
<type_traits>
<bitset>
<functional>
<utility>
<ctime>
<chrono>
<cstddef>
<initializer_list>
<tuple>
<any>
<optional>
<variant>
<compare>
<version>
<source_location>
```
## 5，容器部分
C++20新增了<span>。
```
<array>
<vector>
<deque>
<list>
<forward_list>
<set>
<map>
<unordered_set>
<unordered_map>
<stack>
<queue>
<span>
```
## 6，iterator
C++20增添了很多iterator类。
```
<iterator>
```
## 7，线程支持
C++20新增了<stop_token>、<semaphore>、<latch>、 <barrier>。
```
<thread>
<stop_token>
<mutex>
<shared_mutex>
<future>
<condition_variable>
<semaphore>
<latch>
<barrier>
<atomic>
```
## 8，通用算法
C++17新增了<execution>。
```
<algorithm>
<execution>
```
<algorithm>中包含的算法有：all_of、any_of、none_of、for_each、find、find_if、find_if_not、find_end、find_first_of、adjacent_find、count、count_if、mismatch、equal、is_permutation、search、search_n、copy、copy_n、copy_if、copy_backward、move、move_backward、swap、swap_ranges、iter_swap、transform、replace、replace_if、replace_copy、replace_copy_if、fill、fill_n、generate、generate_n、remove、remove_if、remove_copy、remove_copy_if、unique、unique_copy、reverse、reverse_copy、rotate、rotate_copy、random_shuffle、shuffle、is_partitioned、partition、stable_partition、partition_copy、partition_point、sort、stable_sort、partial_sort、partial_sort_copy、is_sorted、is_sorted_until、nth_element、lower_bound、upper_bound、equal_range、binary_search、merge、inplace_merge、includes、set_union、set_intersection、set_difference、set_symmetric_difference、push_heap、pop_heap、make_heap、sort_heap、is_heap、is_heap_until、min、max、minmax、min_element、max_element、minmax_element、lexicographical_compare、next_permutation、prev_permutation。
## 9，动态内存和智能指针
C++17新增了memory_resource。
```
<new>
<memory>
<scoped_allocator>
<memory_resource>
```
## 10，字符串
C++17新增了<string_view>、<charconv>，C++20新增了<format>。
```
<cctype>
<cwctype>
<cstring>
<cwchar>
<cuchar>
<string>
<string_view>
<charconv>
<format>
<regex>
```
## 11，本地化
<codecvt>在C++17废弃。
```
<locale>
<clocale>
<codecvt>
```
## 12，stream和io
C++20新增了<syncstream>。
```
<iosfwd>
<ios>
<istream>
<ostream>
<iostream>
<fstream>
<sstream>
<syncstream>
<strstream>
<iomanip>
<streambuf>
<cstdio>
```
## 13，文件系统
C++17新增的。
```
<filesystem>
```
## 14，数值库
C++20新增了<bit>、<numbers>。
```
<climits>
<cfloat>
<cstdint>
<cinttypes>
<limits>
<cmath>
<complex>
<valarray>
<random>
<numeric>
<ratio>
<cfenv>
<bit>
<numbers>
```
## 15，语言特性支持
```
<exception>
<limits>
<new>
<typeinfo>
```
## 16，时间
```
<chrono>
```
## 17，错误和异常处理
```
<exception>
<stdexcept>
<cassert>
<system_error>
<cerrno>
```
最后，不是每个系统上的C++编译都使用了标准的C++特性。这里的系统主要是手机操作系统，比如Android。ndk-build可能默认将异常、RTTI等功能停用。

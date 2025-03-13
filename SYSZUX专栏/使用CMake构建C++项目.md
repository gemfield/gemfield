# 背景
本文中引用了libdeepvac项目的CMakeLists.txt来作为参考：https://github.com/DeepVAC/libdeepvac​

Gemfield本文的结构如下：

- CMake语句；
- CMake中的流程控制；
- CMake中的内置变量；
- CMake的编译过程中详细log的查看；
- CMake的Installation；
- 集成一个CMake项目到另外的CMake项目；
- 现代CMake；

# CMake语句
CMake语句主要有3类用法：

- 设置变量；这样的语句有set、file、list、find_library、aux_source_directory、generator expressions；
- 设置target，也就是构建的目标是什么（你构建个项目总得有个目标吧，一般来说就是库或者可执行文件）；这样的语句有add_library、add_executable；
- 设置target的属性，也就是定义如何生成target（比如源文件的路径、编译选项、要链接什么库......）；这样的语句有add_definitions、target_link_libraries、link_directories、include_directories、target_include_directories；

- ## 1，设置变量的CMake语句
### set
设置变量。你甚至可以直接把多个值直接set给一个变量：
```cmake
set(SYSZUX_HEADERS
    include/detail/class.h
    include/detail/common.h
    include/detail/descr.h
    include/detail/init.h
    include/internals.h
    includedetail/typeid.h)
```
### file
使用正则匹配文件，并将文件路径赋值给第一个参数（为变量）,通常和GLOB搭配：
```cmake
file(GLOB gemfield_src_list ${Root}/*/*.cpp ${Root}/*/*.h ${Root}/*/*.c)
```
### list
针对list进行各种操作，如增删改查，比如：
```cmake
list(REMOVE_ITEM ......)
list(APPEND ......)
```
### find_library
寻找一个库，将找到的库的绝对路径赋值给变量。
```cmake
#简单语法
find_library(<VAR> lib_name1 [path1 path2 ...])
#相当于
find_library(<VAR> lib_name1 [PATHS path1 path2 ...])

#复杂语法
find_library(
             <VAR>
             name | NAMES name1 [name2 ...]
             [HINTS path1 [path2 ... ENV var]]
             [PATHS path1 [path2 ... ENV var]]
             [PATH_SUFFIXES suffix1 [suffix2 ...]]
             [DOC "cache documentation string"]
             [NO_DEFAULT_PATH]
             [NO_CMAKE_ENVIRONMENT_PATH]
             [NO_CMAKE_PATH]
             [NO_SYSTEM_ENVIRONMENT_PATH]
             [NO_CMAKE_SYSTEM_PATH]
             [CMAKE_FIND_ROOT_PATH_BOTH |
              ONLY_CMAKE_FIND_ROOT_PATH |
              NO_CMAKE_FIND_ROOT_PATH]
            )
```
举例：
```cmake
find_library(LIBGEMFIELD_PATH libgemfield.so PATHS ${CUDA_TOOLKIT_ROOT_DIR}/lib64/)
```
### aux_source_directory
```cmake
#语法
aux_source_directory(<dir> <variable>)
```
Collects the names of all the source files in the specified directory and stores the list in the <variable> provided.
```cmake
aux_source_directory(${gemfield_root}/include gemfield_src)
```
比如上面的例子就是，将${gemfield_root}/include目录下的所有源文件找到并且赋值给gemfield_src变量。

### project
设置项目的名字，这个放到这里凑数吧。
```cmake
project(SYSZUXrtp)

#还可以设置更多的参数
project(
    libdeepvac
    LANGUAGES CXX
    VERSION "1.0.0")
```

### generator expressions(生成表达式)
生成表达式的语法是$<...>，注意两点：

- Generator expressions are evaluated during build system generation to produce information specific to each build configuration；
- 主要用在target_link_libraries()、 target_include_directories()、target_compile_definitions() 这些语句中；

生成表达式有这么几种（详情参考：https://cmake.org/cmake/help/latest/manual/cmake-generator-expressions.7.html）：bool型表达式、条件表达式、字符串类型表达式、变量类型表达式、target信息查询表达式、output表达式。

- bool型表达式，表达式被转换为0或1，有如下种类：
```cmake
#逻辑运算，注意以下表达式返回都是0或1
$<BOOL:string>
$<AND:conditions>
$<OR:conditions>
$<NOT:condition>

#字符串比较，注意以下表达式返回都是0或1
$<STREQUAL:string1,string2>
$<EQUAL:value1,value2>
$<IN_LIST:string,list>
$<VERSION_LESS:v1,v2>
$<VERSION_GREATER:v1,v2>
$<VERSION_EQUAL:v1,v2>
$<VERSION_LESS_EQUAL:v1,v2>
$<VERSION_GREATER_EQUAL:v1,v2>

#变量查询和匹配，注意以下表达式返回都是0或1
$<TARGET_EXISTS:target>
$<CONFIG:cfgs>
$<PLATFORM_ID:platform_ids>
$<C_COMPILER_ID:compiler_ids>
$<CXX_COMPILER_ID:compiler_ids>
$<CUDA_COMPILER_ID:compiler_ids>
$<OBJC_COMPILER_ID:compiler_ids>
$<OBJCXX_COMPILER_ID:compiler_ids>
$<Fortran_COMPILER_ID:compiler_ids>
$<ISPC_COMPILER_ID:compiler_ids>
$<C_COMPILER_VERSION:version>
$<CXX_COMPILER_VERSION:version>
$<CUDA_COMPILER_VERSION:version>
$<OBJC_COMPILER_VERSION:version>
$<OBJCXX_COMPILER_VERSION:version>
$<Fortran_COMPILER_VERSION:version>
$<ISPC_COMPILER_VERSION:version>
$<TARGET_POLICY:policy>
$<COMPILE_FEATURES:features>
$<COMPILE_LANG_AND_ID:language,compiler_ids>
$<COMPILE_LANGUAGE:languages>
$<LINK_LANG_AND_ID:language,compiler_ids>
$<LINK_LANGUAGE:languages>
#以下2个表达式返回list或者空
$<DEVICE_LINK:list>
$<HOST_LINK:list>
```
- 条件表达式，根据表达式的条件来做对应的转换，这个条件就是上述bool型表达式：
```cmake
#如果条件为真就是true_string，否则为空
$<condition:true_string>

#如果条件为真就是true_string，否则为false_string
$<IF:condition,true_string,false_string>
```
比如条件表达式：$<$<CONFIG:Debug>:DEBUG_MODE>，这是典型的条件表达式嵌套bool型表达式，意思就是如果当前是Debug配置时，表达式转换为“DEBUG_MODE”，否则转换为空。

- 字符串类型，表达式进行字符串变换
```cmake
#Joins the list with the content of string
$<JOIN:list,string>

$<REMOVE_DUPLICATES:list>

#Includes or removes items from list that match the regular expression regex.
$<FILTER:list,INCLUDE|EXCLUDE,regex>

$<LOWER_CASE:string>
$<UPPER_CASE:string>
$<GENEX_EVAL:expr>
$<TARGET_GENEX_EVAL:tgt,expr>
```
- 变量类型
```cmake
$<CONFIG>
$<CONFIGURATION>
$<PLATFORM_ID>
$<C_COMPILER_ID>
$<CXX_COMPILER_ID>
$<CUDA_COMPILER_ID>
$<OBJC_COMPILER_ID>
$<OBJCXX_COMPILER_ID>
$<Fortran_COMPILER_ID>
$<ISPC_COMPILER_ID>
$<C_COMPILER_VERSION>
$<CXX_COMPILER_VERSION>
$<CUDA_COMPILER_VERSION>
$<OBJC_COMPILER_VERSION>
$<OBJCXX_COMPILER_VERSION>
$<Fortran_COMPILER_VERSION>
$<ISPC_COMPILER_VERSION>
$<COMPILE_LANGUAGE>
$<LINK_LANGUAGE>
```
- target信息查询表达式，target就是add_executable()、add_library()创建的target。下面的语法中用tgt来代表target：
```cmake
$<TARGET_NAME_IF_EXISTS:tgt>

#Full path to the tgt binary file.
$<TARGET_FILE:tgt>

$<TARGET_FILE_BASE_NAME:tgt>
$<TARGET_FILE_PREFIX:tgt>
$<TARGET_FILE_SUFFIX:tgt>
$<TARGET_FILE_NAME:tgt>
$<TARGET_FILE_DIR:tgt>
$<TARGET_LINKER_FILE:tgt>
$<TARGET_LINKER_FILE_BASE_NAME:tgt>
$<TARGET_LINKER_FILE_PREFIX:tgt>
$<TARGET_LINKER_FILE_SUFFIX:tgt>
$<TARGET_LINKER_FILE_NAME:tgt>
$<TARGET_LINKER_FILE_DIR:tgt>
$<TARGET_SONAME_FILE:tgt>
$<TARGET_SONAME_FILE_NAME:tgt>
$<TARGET_SONAME_FILE_DIR:tgt>
$<TARGET_PDB_FILE:tgt>
$<TARGET_PDB_FILE_BASE_NAME:tgt>
$<TARGET_PDB_FILE_NAME:tgt>
$<TARGET_PDB_FILE_DIR:tgt>
$<TARGET_BUNDLE_DIR:tgt>
$<TARGET_BUNDLE_CONTENT_DIR:tgt>

#Value of the property prop on the target tgt.
$<TARGET_PROPERTY:tgt,prop>

#Value of the property prop on the target for which the expression is being evaluated.
$<TARGET_PROPERTY:prop>
$<INSTALL_PREFIX>
```
- output表达式
```cmake
#Marks ... as being the name of a target. 
$<TARGET_NAME:...>

$<LINK_ONLY:...>

#在install(EXPORT)中被转换为...，否则为空
$<INSTALL_INTERFACE:...>

#在export()或者当target被同一个cmake构建会话中的其它target使用时，转换为...，否则为空
$<BUILD_INTERFACE:...>

$<MAKE_C_IDENTIFIER:...>
$<TARGET_OBJECTS:objLib>

#转换为shell path风格
$<SHELL_PATH:...>
```

## 2，设置target的CMake语句

### add_library
```cmake
#语法
add_library(<name> [STATIC | SHARED | MODULE]
            [EXCLUDE_FROM_ALL]
            source1 [source2 ...])

#举例
add_library(gemfield_static STATIC ${gemfield_src_list})
```
Adds a library target called<name>to be built from the source files listed in the command invocation. The<name>corresponds to the logical target name and must be globally unique within a project.

### add_executable
Add an executable to the project using the specified source files.
```cmake
#语法：
add_executable(<name> [WIN32] [MACOSX_BUNDLE]
               [EXCLUDE_FROM_ALL]
               source1 [source2 ...])
```
Adds an executable target called<name>to be built from the source files listed in the command invocation. The<name>corresponds to the logical target name and must be globally unique within a project. The actual file name of the executable built is constructed based on conventions of the native platform (such as<name>.exeor just<name>.举例：
```cmake
add_executable(gemfield_proxy ${gemfield_src_list})
```

## 3，设置target属性的CMake语句
### add_definitions
Adds -D define flags to the compilation of source files.比如：
```cmake
add_definitions(-DENABLE_GEMFIELD)
```
### target_link_libraries
```cmake
#语法
target_link_libraries(<target> [item1 [item2 [...]]]
                      [[debug|optimized|general] <item>] ...)
```
Specify libraries or flags to use when linking a given target. The named <target> must have been created in the current directory by a command such as add_executable() or add_library(). The remaining arguments specify library names or flags. Repeated calls for the same <target> append items in the order called.
If a library name matches that of another target in the project a dependency will automatically be added in the build system to make sure the library being linked is up-to-date before the target links. Item names starting with -, but not -l or -framework, are treated as linker flags.
比如：
```cmake
target_link_libraries(
        gemfield_proxy
        shared_static
        json_static
        mpeg_static
        ${LINK_LIB_LIST})
```
意思是说，要链接出目标gemfield_proxy的时候，需要有后面的库（shared_static、json_static...)或者flag。

### link_directories
指定要搜寻的库所在的目录，相当于link工具的 -L参数。
```cmake
#语法
link_directories(directory1 directory2 ...)
```
注意，这个变量很少必须使用，最好用find_library()来替代。

### include_directories
将目录中加入搜索头文件时的路径，不支持通配符：
```cmake
include_directories(${CMAKE_SOURCE_DIR}/gemfield/include)
```
### target_include_directories
编译target时，指定其需要include的目录。target必须提前使用add_executable()或者add_library()定义。
前面的include_directories影响的是项目级别，而这里的target_include_directories影响的是target级别（而且还可以提供PRIVATE、PUBLIC、INTERFACE关键字），我们应该优先使用target_include_directories。

# CMake中的流程控制
## if else 
if else等条件控制，使用如下的语句：
```cmake
#if
if(逻辑表达式)
...
endif()

#if else
if(逻辑表达式)
...
else()
...
endif()

#if elseif
if(逻辑表达式)
...
elseif(逻辑表达式)
...
endif()
```
if中的逻辑与为AND关键字，非为NOT关键字。
## for循环
for循环使用如下语句：
```cmake
foreach(变量 变量的列表)
...
endforeach()
```
## 跳转到子目录
使用add_subdirectory语句。
参考下面项目的CMakeLists.txt，其重度使用了add_subdirectory：https://github.com/DeepVAC/libdeepvac/blob/master/CMakeLists.txt

# CMake中的内置变量

## 系统变量

- MAKE_MAJOR_VERSION : major version number for CMake, e.g. the "2" in CMake 2.4.3
- CMAKE_MINOR_VERSION : minor version number for CMake, e.g. the "4" in CMake 2.4.3
- CMAKE_PATCH_VERSION : patch version number for CMake, e.g. the "3" in CMake 2.4.3
- CMAKE_TWEAK_VERSION : tweak version number for CMake, e.g. the "1" in CMake X.X.X.1. Releases use tweak < 20000000 and development versions use the date format CCYYMMDD for the tweak level.
- CMAKE_VERSION : The version number combined, eg. 2.8.4.20110222-ged5ba for a Nightly build. or 2.8.4 for a Release build.
- CMAKE_GENERATOR : the generator specified on the commandline.
- BORLAND : is TRUE on Windows when using a Borland compiler
- WATCOM : is TRUE on Windows when using the Open Watcom compiler
- MSVC, MSVC_IDE, MSVC60, MSVC70, MSVC71, MSVC80, CMAKE_COMPILER_2005, MSVC90, MSVC10 (Visual Studio 2010) : Microsoft compiler
- CMAKE_CXX_COMPILER_ID : one of "Clang", "GNU", "Intel", or "MSVC". This works even if a compiler wrapper like ccache is used；
- cmake_minimum_required：设置所需CMake的最小版本；

## 编译相关的变量

- CMAKE_CXX_STANDARD：设置C++标准；
- CMAKE_CXX_FLAGS：设置C++编译参数；
- CMAKE_C_FLAGS：设置C编译参数；
```cmake
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -w")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -w")
```
- BUILD_SHARED_LIBS : if this is set to ON, then all libraries are built as shared libraries by default. SET(BUILD_SHARED_LIBS ON) ；
- CMAKE_BUILD_TYPE : A variable which controls the type of build when using a single-configuration generator like the Makefile generator. It is case-insensitive；If you are using the Makefile generator, you can create your own build type like this:
```cmake
SET(CMAKE_BUILD_TYPE distribution)
SET(CMAKE_CXX_FLAGS_DISTRIBUTION "-O3")
SET(CMAKE_C_FLAGS_DISTRIBUTION "-O3")
```
Note that CMAKE_BUILD_TYPE is not initialized with a readable value at configuration time. This is because the user is free to select a build type at build time. Use CMAKE_CFG_INTDIR if you need a variable that evaluates to the correct build time directory；

- CMAKE_CONFIGURATION_TYPES : When using a multi-configuration generator, such as the one for Visual Studio, this variable contains a list of the available configurations.
- CMAKE_C_COMPILER : the compiler used for C files. Normally it is detected and set during the CMake run, but you can override it at configuration time. Note! It can not be changed after the first cmake or ccmake run. Although the gui allows to enter an alternative, it will be ignored in the next 'configure' run. Use for example: CC=gcc-3.3 CXX=g++-3.3 cmake to set the compiler. (You can also set CMAKE_C_COMPILER_INIT, before any PROJECT() or ENABLE_LANGUAGE() command.) Any other way (like writing make CC=gcc-3.3 CXX=g++-3.3) will not work. When using distcc or similar tools, you need to write: CC="distcc gcc-3.3" CXX="distcc g++-3.3" cmake However, this will empty all your CMAKE_...FLAGS... above.
- CMAKE_C_FLAGS : the compiler flags for compiling C sources. Note you can also specify switches with ADD_COMPILE_OPTIONS().
- CMAKE_C_FLAGS_ : compiler flags for a specific build configuration. Replace "" in the name with a specific build configuration name.
- CMAKE_C_OUTPUT_EXTENSION : what C object files end in. Typically .o or .obj.
- CMAKE_CFG_INTDIR : meta-variable! Please note that this is an important variable, since on multi-configuration generators it will be generated into dynamically switched content based on the configuration that the user currently selected within the generated build environment. Indicates the name of the current configuration (~ directory) for the project. May be used for any purpose which needs per-configuration-dynamic switching of strings, not just OutputDir configuration. For multi-configuration generators (e.g. MSVC) the resulting strings are typically some of "Debug", "Release", "RelWithDebInfo", or "MinSizeRel". For other compiler generators (single-configuration ones) it is typically ".", as they don't use MSVC-style configuration directories.
- CMAKE_CXX_COMPILER : the compiler used for C++ files. Normally it is detected and set during the CMake run, but you can override it at configuration time. Note! It can not be changed after the first cmake or ccmake run. See CMAKE_C_COMPILER above.
- CMAKE_CXX_FLAGS : the compiler flags for compiling C++ sources. Note you can also specify switches with ADD_COMPILE_OPTIONS().
- CMAKE_CXX_FLAGS_ : compiler flags for a specific configuration for C++ sources. Replace "" in the name with a specific build configuration name.
- CMAKE_SHARED_LINKER_FLAGS : additional compiler flags for building shared libraries, e.g.:set(CMAKE_SHARED_LINKER_FLAGS "-Wl,--no-undefined") On Unix systems, this will make linker report any unresolved symbols from object files (which is quite typical when you compile many targets in CMake projects, but do not bother with linking target dependencies in proper order). On mac, the flag is -Wl,-undefined-error；
- CMAKE_SKIP_RULE_DEPENDENCY : set this to true if you don't want to rebuild the object files if the rules have changed, but not the actual source files or headers (e.g. if you changed the some compiler switches)
- CMAKE_SKIP_INSTALL_ALL_DEPENDENCY : since CMake 2.1 the install rule depends on all, i.e. everything will be built before installing. If you don't like this, set this one to true.
- CMAKE_INCLUDE_CURRENT_DIR : automatically add CMAKE_CURRENT_SOURCE_DIR and CMAKE_CURRENT_BINARY_DIR to the include directories in every processed CMakeLists.txt. It behaves as if you had used INCLUDE_DIRECTORIES in every CMakeLists.txt file or your project. The added directory paths are relative to the being-processed CMakeLists.txt, which is different in each directory. (See this thread for more details).
- CMAKE_INCLUDE_DIRECTORIES_PROJECT_BEFORE : order the include directories so that directories which are in the source or build tree always come before directories outside the project.
- CMAKE_VERBOSE_MAKEFILE : set this to true if you are using makefiles and want to see the full compile and link commands instead of only the shortened ones
- CMAKE_SUPPRESS_REGENERATION : this will cause CMake to not put in the rules that re-run CMake. This might be useful if you want to use the generated build files on another machine.
- CMAKE_COLOR_MAKEFILE : create Makefiles with colored output (defaults to on)
- CMAKE_SKIP_PREPROCESSED_SOURCE_RULES : (since 2.4.4) if set to TRUE, the generated Makefiles will not contain rules for creating preprocessed files (foo.i)
- CMAKE_SKIP_ASSEMBLY_SOURCE_RULES : (since 2.4.4) if set to TRUE, the generated Makefiles will not contain rules for creating compiled, but not yet assembled files (foo.s)； 
- INCLUDE_DIRECTORIES：Add the given directories to those the compiler uses to search for include files. Relative paths are interpreted as relative to the current source directory；

## 路径相关的变量
CMake有两类变量，PROJECT_<var> 和 CMAKE_<var>，CMAKE_*系列变量指的是最顶层的CMakeLists.txt所在的目录或者所描述的东西；而PROJECT_*系列变量指的是最近的含有project()命令的CMakeLists.txt所在的目录或者所描述的东西。

- CMAKE_BINARY_DIR : if you are building in-source, this is the same as CMAKE_SOURCE_DIR, otherwise this is the top level directory of your build tree
- CMAKE_COMMAND : this is the complete path of the cmake which runs currently (e.g. /usr/local/bin/cmake). Note that if you have custom commands that invoke cmake -E, it is very important to use CMAKE_COMMAND as the CMake executable, because CMake might not be on the system PATH.
- CMAKE_CURRENT_BINARY_DIR : if you are building in-source, this is the same as CMAKE_CURRENT_SOURCE_DIR, otherwise this is the directory where the compiled or generated files from the current CMakeLists.txt will go to.
- CMAKE_CURRENT_SOURCE_DIR : this is the directory where the currently processed CMakeLists.txt is located in
- CMAKE_CURRENT_LIST_FILE : this is the full path to the listfile currently being processed.
- CMAKE_CURRENT_LIST_DIR : (since 2.8.3) this is the directory of the listfile currently being processed.
- CMAKE_CURRENT_LIST_LINE : this is linenumber where the variable is used.
- CMAKE_FILES_DIRECTORY : the directory within the current binary directory that contains all the CMake generated files. Typically evaluates to "/CMakeFiles". Note the leading slash for the directory. Typically used with the current binary directory, i.e. ${CMAKE_CURRENT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}
- CMAKE_MODULE_PATH : tell CMake to search first in directories listed in CMAKE_MODULE_PATH when you use FIND_PACKAGE() or INCLUDE() SET(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/MyCMakeScripts) FIND_PACKAGE(HelloWorld) ；directories specifying a search path for CMake modules to be loaded by the the include()or find_package()commands before checking the default modules that come with CMake. By default it is empty, it is intended to be set by the project；注意是被include和find_package命令所使用的搜索路径，为list类型（目录列表）。
- CMAKE_ROOT : this is the CMake installation directory
- CMAKE_SOURCE_DIR : this is the directory which contains the top-level CMakeLists.txt, i.e. the top level source directory
- PROJECT_NAME : the name of the project set by PROJECT() command.
- CMAKE_PROJECT_NAME : the name of the first project set by the PROJECT() command, i.e. the top level project.
- PROJECT_BINARY_DIR : contains the full path to the top level directory of your build tree；可以近似认为：执行编译时所在的目录，在哪个目录下编译就是哪个目录。
- PROJECT_SOURCE_DIR : contains the full path to the root of your project source directory, i.e. to the nearest directory where CMakeLists.txt contains the PROJECT() command；
- LIBRARY_OUTPUT_PATH：旧的用法，指定library的路径；现在已经被ARCHIVE_OUTPUT_DIRECTORY、LIBRARY_OUTPUT_DIRECTORY和RUNTIME_OUTPUT_DIRECTORY代替了；
- EXECUTABLE_OUTPUT_PATH：旧的用法，指定可执行文件的路径；现在已经被RUNTIME_OUTPUT_DIRECTORY代替了；


## 环境变量
有一些环境变量影响CMake的行为；另外，你也可以在CMake脚本中主动读取环境变量的值。实际上，你可以在CMake命令执行后，在CMakeCache.txt中看到打印的各种CMake变量的值。

- CMAKE_INCLUDE_PATH : This is used when searching for include files e.g. using the FIND_PATH() command. If you have headers in non-standard locations, it may be useful to set this variable to this directory (e.g. /sw/include on Mac OS X). If you need several directories, separate them by the platform specific separators (e.g. ":" on UNIX)；
- CMAKE_LIBRARY_PATH : This is used when searching for libraries e.g. using the FIND_LIBRARY() command. If you have libraries in non-standard locations, it may be useful to set this variable to this directory (e.g. /sw/lib on Mac OS X). If you need several directories, separate them by the platform specific separators (e.g. ":" on UNIX)；
- CMAKE_PREFIX_PATH : (since CMake 2.6.0) This is used when searching for include files, binaries, or libraries using either the FIND_PACKAGE(), FIND_PATH(), FIND_PROGRAM(), or FIND_LIBRARY() commands. For each path in the CMAKE_PREFIX_PATH list, CMake will check "PATH/include" and "PATH" when FIND_PATH() is called, "PATH/bin" and "PATH" when FIND_PROGRAM() is called, and "PATH/lib" and "PATH" when FIND_LIBRARY() is called. See the documentation for FIND_PACKAGE(), FIND_LIBRARY(), FIND_PATH(), and FIND_PROGRAM() for more details；
- CMAKE_INSTALL_ALWAYS : If set during installation CMake will install all files whether they have changed or not. The default when this is not set is to install only files that have changed since the previous installation. In both cases all files are reported to indicate CMake knows they are up to date in the installed location；
- $ENV{name} : This is not an environment variable , but this is how you can access environment variables from cmake files. It returns the content of the environment variable with the given name (e.g. $ENV{PROGRAMFILES})；
- DESTDIR : If this environment variable is set it will be prefixed to CMAKE_INSTALL_PREFIX in places where it is used to access files during installation. This allows the files to be installed in an intermediate directory tree without changing the final installation path name. Since the value of CMAKE_INSTALL_PREFIX may be included in installed files it is important to use DESTDIR rather than changing CMAKE_INSTALL_PREFIX when it is necessary to install to a intermediate staging directory；

## 变量的打印

可以用MESSAGE语句打印CMake变量：
```cmake
# if you are building in-source, this is the same as CMAKE_SOURCE_DIR, otherwise
# this is the top level directory of your build tree
MESSAGE( STATUS "CMAKE_BINARY_DIR:         " ${CMAKE_BINARY_DIR} )

# if you are building in-source, this is the same as CMAKE_CURRENT_SOURCE_DIR, otherwise this
# is the directory where the compiled or generated files from the current CMakeLists.txt will go to
MESSAGE( STATUS "CMAKE_CURRENT_BINARY_DIR: " ${CMAKE_CURRENT_BINARY_DIR} )

# this is the directory, from which cmake was started, i.e. the top level source directory
MESSAGE( STATUS "CMAKE_SOURCE_DIR:         " ${CMAKE_SOURCE_DIR} )

# this is the directory where the currently processed CMakeLists.txt is located in
MESSAGE( STATUS "CMAKE_CURRENT_SOURCE_DIR: " ${CMAKE_CURRENT_SOURCE_DIR} )

# contains the full path to the top level directory of your build tree
MESSAGE( STATUS "PROJECT_BINARY_DIR: " ${PROJECT_BINARY_DIR} )

# contains the full path to the root of your project source directory,
# i.e. to the nearest directory where CMakeLists.txt contains the PROJECT() command
MESSAGE( STATUS "PROJECT_SOURCE_DIR: " ${PROJECT_SOURCE_DIR} )

......
```

# CMake的编译过程中详细log的查看
我们知道，对于GNU Make来说，要想看编译的详细日志（也就是具体的源文件路径、编译参数、输入路径等），可以使用make命令的VERBOSE参数：
```bash
make VERBOSE=1
```
而因为CMake封装了make，那么如何通过CMake达到同样的效果呢？

## 选项1：自然而然的，还是上面的方法
```bash
cmake .
make VERBOSE=1
```
## 选项2：在cmake命令行上加参数-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON
```bash
cmake -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON .
make

#如果想要减少一些信息量少的打印信息：
cmake -DCMAKE_RULE_MESSAGES:BOOL=OFF -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON .
make --no-print-directory
```
## 选项3：修改CMakeLists.txt
在CMakeLists.txt中加上：
```cmake
set(CMAKE_VERBOSE_MAKEFILE ON)
```
缺点是要修改文件，还要修改每个CMakeLists.txt文件。

# CMake的Installation
使用install语句。一个生动的例子可以参考：https://github.com/DeepVAC/libdeepvac/blob/master/CMakeLists.txt

# 集成一个CMake项目到另外的CMake项目
为了让别的C++项目在CMakeLists.txt中使用find_package来引用自己的C++项目，则需要在自己项目的CMakeLists.txt中使用EXPORT语法和install(EXPORT ...)语法。一个生动的例子可以参考：
https://github.com/DeepVAC/libdeepvac/blob/master/CMakeLists.txt
和：
[DeepVAC/libdeepvac](https://github.com/DeepVAC/libdeepvac/blob/master/cmake/deepvac-config.cmake)

# 现代CMake

现代CMake更强调target和围绕target的属性设置。如果说传统CMake是面向过程的编程，那么现代CMake更像是OOP的编程：有封装、有访问控制、有命名空间。那么现代CMake具体表现在什么地方呢？
## 1，封装
对target属性进行封装，使用如下的方法来对target属性进行操作：

- target_include_directories
- target_compile_options
- target_link_libraries
- ......

## 2，访问控制
有PUBLIC、PRIVATE、INTERFACE关键字。
## 3，命名空间
有export 关键字。

作为例子，可以参考：
https://pabloariasal.github.io/2018/02/19/its-time-to-do-cmake-right/


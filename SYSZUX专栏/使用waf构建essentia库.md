# 背景
最近发现Essentia库设计的不错，于是拿来研究下，顺便把它放到iOS上体验下。

https://github.com/MTG/essentia
​github.com/MTG/essentia
为啥要放到iOS上呢？Essentia库是个音频算法相关的库，因为手机可以方便的通过麦克风获取各种声音，包括Gemfield自己的声音，以及奇怪的人发出的奇怪的声音，就像《口技》里描述的那样：“忽然抚尺一下，群响毕绝。撤屏视之，一人、一桌、一椅、一扇、一抚尺而已“。因此如果把Essentia库放到手机上，就可以方便的进行声音的实时测试和验证。

Essentia库本身支持多种平台，包括Linux、iOS等。Gemfield主要的使用环境是Ubuntu和iOS，因此本文就聚焦在这两个系统上。

# Ubuntu编译
这个比较简单，不多解释了。

1，安装依赖
```
#数学运算库
sudo apt install libeigen3-dev
#音频重采样
sudo apt install libsamplerate0-dev
#音频元数据
sudo apt install libtag1-dev
#音频指纹提取库
sudo apt install libchromaprint-dev
#Gemfield最常用的YAML
sudo apt install libyaml-dev
#傅立叶变换
sudo apt install libfftw3-dev
#Gemfield最喜欢的ffmpeg
sudo apt install libavresample-dev libavcodec-dev libavformat-dev libavutil-dev 

############如果要编译python
sudo apt-get install build-essential libyaml-dev libfftw3-dev libavcodec-dev \
    libavformat-dev libavutil-dev libavresample-dev python-dev libsamplerate0-dev \
    libtag1-dev libchromaprint-dev python-six python3-dev python3-numpy-dev \
    python3-numpy python3-yaml
```
2，配置
```
#将会使用共享库编译
./waf configure  --with-examples

#如果想编译静态的example，使用下面的命令
#但是，这种情况下，就需要链接.a库，上述的apt install的某些库
#只有动态库，比如libtag，比如libchromaprint-dev
./waf configure  --with-static-examples


#如果要编译python，并且使用tensorflow的话
python3 waf configure --build-static --with-python --with-tensorflow
```
3，编译
```
./waf build --verbose
```
# iOS编译
这就需要用到Xcode 工具和iOS SDK了。

1，安装依赖
```
brew install eigen
```
Gemfield的macbook上已经安装过了：
```
Warning: eigen 3.3.7 is already installed and up-to-date
To reinstall 3.3.7, run `brew reinstall eigen`
```
2，配置
```
./waf configure --cross-compile-ios --lightweight= --fft=ACCELERATE --build-static --with-static-examples

#指定prefix
./waf configure --cross-compile-ios --lightweight= --fft=ACCELERATE --build-static --with-static-examples --prefix=/home/gemfield/libgemfield/install

#还可以指定example源文件
./waf configure --cross-compile-ios --lightweight= --fft=ACCELERATE --build-static --with-static-examples --with-example=gemfield
```
这一步是配置，成功后输出：
```
================================ CONFIGURATION SUMMARY ================================
- using Accelerate Framework for FFT

- FFmpeg (or LibAv on debian/ubuntu) seems to be missing.
  The following algorithms will be ignored: ['AudioLoader', 'MonoLoader', 'EqloudLoader', 'EasyLoader', 'MonoWriter', 'AudioWriter']

- libsamplerate seems to be missing.
  The following algorithms will be ignored: ['Resample', 'MonoLoader', 'EqloudLoader', 'EasyLoader']

  Examples requiring FFmpeg / libav and libsamplerate will be ignored

- TagLib seems to be missing.
  The following algorithms will be ignored: ['MetadataReader', 'MusicExtractor', 'FreesoundExtractor']

- libyaml seems to be missing.
  The following algorithms will be ignored: ['YamlInput', 'YamlOutput']

- Essentia is configured without Gaia2.
  The following algorithms will be ignored: ['GaiaTransform', 'MusicExtractorSVM']
  Examples requiring Gaia2 will be ignored

- Essentia is configured without Chromaprint.
  The following algorithms will be ignored: ['Chromaprinter']
- Essentia is configured without Tensorflow.
  The following algorithms will be ignored: ['TensorflowPredict', 'TensorflowPredictMusiCNN', 'TensorflowPredictVGGish']
Building all the algorithms
Ignoring the following algorithms: MonoWriter, FFTW, Resample, MonoLoader, FFTKComplex, FFTWComplex, FFTK, GaiaTransform, EasyLoader, AudioLoader, TensorflowPredict, IFFTK, Chromaprinter, TensorflowPredictMusiCNN, FreesoundExtractor, IFFTWComplex, MetadataReader, TensorflowPredictVGGish, IFFTKComplex, AudioWriter, MusicExtractorSVM, IFFTW, EqloudLoader, YamlOutput, MusicExtractor, YamlInput
Created algorithms registration file
```
总结下来就是：

- 使用苹果的Accelerate来进行FFT计算，这样将会使用源文件src/algorithms/standard/ffta.cpp来进行傅立叶变换的计算。This algorithm computes the positive complex short-term Fourier transform (STFT) of an array using the FFT algorithm. The resulting fft has a size of (s/2)+1, where s is the size of the input frame，FFT computation will be carried out using the Accelerate Framework (vDSP Programming Guide)；
- 没找到FFmpeg，因此读写音频相关的算法都不会参与编译；Gemfield准备在工程中直接使用iOS SDK自身的AVAssetReader来读音频；
- libsamplerate库的源码就那么几个，Gemfield准备直接放到essentia工程中；
- 因为没有指定tensorflow（Gemfield不需要），因此'TensorflowPredict', 'TensorflowPredictMusiCNN', 'TensorflowPredictVGGish'都不会被编译；Gemfield准备在工程中直接替换为iOS自身的ML框架；

3，编译和安装
```
#编译
./waf
#or
./waf build --verbose

#安装
./waf install
```
4，链接（仅供debug使用）

使用如下的命令来链接编译好的essentia库：
```
/usr/bin/clang++  -arch arm64 -miphoneos-version-min=12.0 \
    -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk \
    -framework Accelerate -framework Accelerate \
    src/examples/gemfield_vggish.cpp.1.o \
    -o/Users/civilnet/github/ai1_gemfield_org/libsyszux/build/src/examples/essentia_gemfield_vggish \
    -Lsrc -lessentia
```
如果要debug iOS上的库的话，使用如下命令先将fat类型的静态库变成thin的：
```
lipo libessentia.a -thin arm64 -output arm64.a
```
# Waf扩展
essentia库使用的是waf构建系统（它的构建逻辑写在wscript文件中，就像CMakeLists.txt之于CMake一样），在这个构建系统之上，如果我们产生了一些额外的编译需求，可参考下面的步骤。

1，添加三方库的头文件路径

在wscript文件中
```
ctx.env.INCLUDES += ['/Users/civilnet/github/tmp/samplerate/libsamplerate/src/']
```
2，添加源文件

在wscript文件中，使用
```
#ctx.env.INCLUDES += ['3rdparty/libsamplerate/src']

sources += ctx.path.ant_glob('3rdparty/libsamplerate/src/*.cpp')
#或者
sources += [ ctx.path.find_resource('3rdparty/kiss_fft130/kiss_fft.c')
```
3，编译静态库或者动态库

在wscript文件中，使用stlib：
```
#编译静态库
ctx.stlib(
    source   = sources,
    target   = 'essentia',
    use      = ctx.env.USE_LIBS,
    install_path = '${PREFIX}/lib'
    #includes = ctx.env.includes
)

#编译动态库
ctx.shlib(
    source   = sources,
    target   = 'essentia',
    use      = ctx.env.USE_LIBS,
    includes = ctx.env.INCLUDES,
    cxxflags = [ '-w' ],
    install_path = '${PREFIX}/lib'
)
```
4，递归子目录

在wscript文件中，使用recurse函数
```
ctx.recurse('your_sub_dir')
```

# 评论
1，essentia iOS编译：
- --cross-compile-ios 对应于xcode中真机，arm64
- --cross-compile-ios 对应于xcode中模拟器，x86_64

2，可以通过lipo命令来获取framework支持架构：
```
lipo -info <framework-file-path>
```
同样可以将两种不同架构的同名framework合并为一个文件
```
lipo -create <framework-arm64-path> <framework-x8664-path> -output <framework-arm64-x86_64-path>
```

3，xcode编译支持armv7，armv7s架构framework设置（已xcode12.5为例）：
```
Architectures： armv7s$(ARCHS_STANDARD)
Build Active Architecture Only: No
Dead Code Stripping: No
Link With Standard Libraries: No
Mach-O Type: Static Library
iOS Deployment Target: IOS9.0(armv7 support max version is IOS10)
```

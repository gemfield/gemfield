##  **背景**

在下面的专栏文章中，Gemfield介绍了如何将iOS的图形系统和神经网络结合起来。

[ Gemfield：XCode编程读取图片、视频、摄像头 ](https://zhuanlan.zhihu.com/p/110480572)

Gemfield特别提到了iOS和图像相关的一些类（或者不是类，就是C的指针），这些类的名字有着不一样的前缀：
**CV代表CoreVideo，CI代表CoreImage，CM代表 CoreMedia，CF代表CoreFoundation，CG代表
CoreGraphic，UI代表User Interface。**

这其中，有两个类是最基础最流行的：CVPixelBufferRef和UIImage。相比之下：

  * CVPixelBufferRef更加原始和接近底层（因为可以直接操作原始的图像数据），一般来说，从摄像头系统和本地视频文件中读取一帧数据的时候，这帧数据就会封装在CVPixelBufferRef传递给你；那么写视频也是同样的道理； 
  * UIImage则是当你使用imagePickerController从相册中选取图片的时候，该图片会以UIImage传递给你；又或者，当你显示图片到UI界面上时（通常使用UIImageView），则也需要的是UIImage。 

在Gemfield本文中，相比于前述专栏文章，Gemfield将会更加详细的介绍CVPixelBufferRef（不是说更底层嘛），以及：

  1. 如何通过CVPixelBufferRef读取原始的像素数组（rgb array）； 
  2. 如何通过rgb array 创建CVPixelBufferRef； 
  3. 如何将UIImage转换为CVPixelBufferRef； 
  4. 如何将CVPixelBufferRef转换为UIImage； 
  5. 这些image如何对应到CoreML模型到输入？ 

本文的代码示例全部为Object-C，因为Gemfield需要时不时的将其和C++结合起来，也就是广为人知的Object-C++。

##  **通过CVPixelBufferRef读取原始的像素数组**

通过CVPixelBufferGetBaseAddress可以获得像素数组的指针，该数组中的每个元素应该被解释为unsigned char。参考如下代码：

    
    
    CVPixelBufferRef pixelBuffer;
    //假设我们已经有了一个pixelBuffer
    
    //通过如下API拿到该图像的宽、高、每行的字节数、每个像素的字节数
    size_t w = CVPixelBufferGetWidth(pixelBuffer);
    size_t h = CVPixelBufferGetHeight(pixelBuffer);
    size_t r = CVPixelBufferGetBytesPerRow(pixelBuffer);
    size_t bytesPerPixel = r/w;
    OSType bufferPixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer);
    NSLog(@"GEMFIELD whrb: %zu - %zu - %zu - %zu - %u",w,h,r,bytesPerPixel,bufferPixelFormat);
    
    //通过如下API拿到CVPixelBufferRef的图像格式：
    //比如：kCVPixelFormatType_24RGB、kCVPixelFormatType_32BGRA
    OSType bufferPixelFormat = CVPixelBufferGetPixelFormatType(pixelBuffer);
    
    //准备开始读取裸的像素数组了
    CVPixelBufferLockBaseAddress( pixelBuffer, 0 );
    //gemfield_buffer就是裸的数组
    const unsigned char* gemfield_buffer = (const unsigned char*)CVPixelBufferGetBaseAddress(pixelBuffer);
    //这里你可以对该数组进行读取和处理
    ......
    //结束
    CVPixelBufferUnlockBaseAddress( pixelBuffer, 0 );

拿到裸的像素数组gemfield_buffer后，你就可以进行自己想要的处理了，比如...打印出来。假设bufferPixelFormat的格式是kCVPixelFormatType_24RGB的话，则使用如下的代码来输出每个像素的RGB值：

    
    
    const unsigned char* gemfield_buffer = (const unsigned char*)CVPixelBufferGetBaseAddress(pixelBuffer);
    for(int i=0;i<w*h*bytesPerPixel;i++){
        if(i % (w*bytesPerPixel) == 0){
            std::cout<<std::endl;
            std::cout<<"--------------GEMFIELD"<<int(i/(w*bytesPerPixel))<<"----------------"<<std::endl;
        }
        std::cout<<(unsigned int)gemfield_buffer[i]<<",";
    }

也就是说，当我们从kCVPixelFormatType_24RGB格式的CVPixelBufferRef中拿到原始的像素数组后，数组中的每个数字可以被解释为unsigned
char，并且排列格式为：

  * [R,G,B,R,G,B,R,G,B,R,G,B,R,G,B,R,G,B.....]// w*3个 
  * [R,G,B,R,G,B,R,G,B,R,G,B,R,G,B,R,G,B.....]//w*3个 
  * [R,G,B,R,G,B,R,G,B,R,G,B,R,G,B,R,G,B.....]//w*3个 
  * [R,G,B,R,G,B,R,G,B,R,G,B,R,G,B,R,G,B.....]//w*3个 
  * .....//h行 

有了上面的概念后，我们甚至可以直接在baseAddress指向的内存中，直接对像素进行修改。比如下面的代码就把图像左上角100x100的区域的像素修改成了白色：

    
    
    - (void)captureOutput:(AVCaptureOutput *)captureOutput didOutputSampleBuffer:(CMSampleBufferRef)sampleBuffer fromConnection:(AVCaptureConnection *)connection {
        CVPixelBufferRef pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer);
        CVPixelBufferLockBaseAddress( pixelBuffer, 0 );
        int bufferWidth = (int)CVPixelBufferGetWidth( pixelBuffer );
        int bufferHeight = (int)CVPixelBufferGetHeight( pixelBuffer );
        size_t bytesPerRow = CVPixelBufferGetBytesPerRow( pixelBuffer );
        int kBytesPerPixel = bytesPerRow / bufferWidth;
        uint8_t *baseAddress = CVPixelBufferGetBaseAddress( pixelBuffer );
    
        for ( int row = 0; row < bufferHeight; row++ )
        {
            uint8_t *pixel = baseAddress + row * bytesPerRow;
            for ( int column = 0; column < bufferWidth; column++ )
            {
                if ((row < 100) && (column < 100) {
                    pixel[0] = 255; // BGRA, Blue value
                    pixel[1] = 255; // Green value
                    pixel[2] = 255; // Red value
                }
                pixel += kBytesPerPixel;
            }
        }
    
        CVPixelBufferUnlockBaseAddress( pixelBuffer, 0 );
        //接下来继续你的业务逻辑
    }

##  **使用原始的像素数组创建出新的CVPixelBufferRef**

这正好和上述小节是一个相反的过程。在SYSZUXPalette项目中（很简单的一个项目，用来生成Viridis格式的调色板）：

[ CivilNet/Gemfield
](https://link.zhihu.com/?target=https%3A//github.com/CivilNet/Gemfield/tree/master/src/cpp/palette)

Gemfield展示了如何使用原始的数字组装成为裸的像素数组，一会儿成RGB排列，一会儿成BGR排列，并且还使用OpenCV的API来将其可视化。那么面对这个unsigned
char的像素数组，如何来构建出一个CVPixelBufferRef呢？很简单，使用iOS
SDK提供的CVPixelBufferCreateWithBytes函数可以轻而易举的做到：

    
    
    CVPixelBufferRef pixelBuffer = NULL;
    int width=319;
    int height=64;
    CVPixelBufferCreateWithBytes(kCFAllocatorDefault,width,height,kCVPixelFormatType_24RGB,x.get(),3 * width, NULL, NULL, NULL, &pixelBuffer);

这样就创建了一个CVPixelBufferRef。注意：kCVPixelFormatType_24RGB一定要和原始的像素数组格式匹配，并且一定要意识到，不是所有的PixelFormat都被这个API支持，比如kCVPixelFormatType_24BGR就不被支持。

如何直接对一个CVPixelBufferRef进行crop或者resize呢？可以使用Accelerate框架中的vImageScale_ARGB8888
API：

    
    
    #import <Accelerate/Accelerate.h>
    ......
    CVPixelBufferRef pixelBuffer = CMSampleBufferGetImageBuffer(buffer);
    CVPixelBufferLockBaseAddress( pixelBuffer, 0 );
    bufferWidth = (int)CVPixelBufferGetWidth( pixelBuffer );
    bufferHeight = (int)CVPixelBufferGetHeight( pixelBuffer );
    size_t bytesPerRow = CVPixelBufferGetBytesPerRow( pixelBuffer );
    void* baseAddress = CVPixelBufferGetBaseAddress( pixelBuffer );
    vc.appendFrameRGB((const unsigned char*)baseAddress, bufferWidth, bufferHeight);
    
    //resize begin
    int cropX0 = 0;
    int cropY0 = 0;
    int cropHeight = bufferHeight;
    int cropWidth = bufferWidth;
    
    vImage_Buffer inBuff;
    inBuff.height = cropHeight;
    inBuff.width = cropWidth;
    inBuff.rowBytes = bytesPerRow;
    size_t startpos = cropY0 * bytesPerRow + 4*cropX0;
    inBuff.data = (unsigned char*)baseAddress + startpos;
    
    size_t gemfield_w = 224;
    size_t gemfield_h = 224;
    unsigned char *outImg = (unsigned char*)malloc(4*gemfield_w*gemfield_h);
    vImage_Buffer outBuff = {outImg, gemfield_h, gemfield_w, 4*gemfield_w};
    vImage_Error err = vImageScale_ARGB8888(&inBuff, &outBuff, NULL, 0);
    if (err != kvImageNoError) NSLog(@" error %ld", err);
    //resize end
    CVPixelBufferUnlockBaseAddress( pixelBuffer, 0 );
    NSLog(@"gemfield debug frame counter: %d",frame_count);
    
    //re create pixel buffer
    CVPixelBufferRef gemfield_buffer = NULL;
    CVPixelBufferCreateWithBytes(kCFAllocatorDefault,gemfield_w,gemfield_h,kCVPixelFormatType_32ARGB,outImg,4 * gemfield_w, NULL, NULL, NULL, &gemfield_buffer);
    
    //记住free由malloc创建的资源
    free(outImg)

##  **CVPixelBufferRef转换为UIImage**

可以使用下面的例子来把CVPixelBufferRef转换为UIImage：

    
    
    //假设我们已经有了一个pixelBuffer
    CVPixelBufferRef pixelBuffer;
    
    CIImage *ciImage = [CIImage imageWithCVPixelBuffer:pixelBuffer];
    CIContext *temporaryContext = [CIContext contextWithOptions:nil];
    CGImageRef syszux_cgiimg = [temporaryContext createCGImage:ciImage fromRect:CGRectMake(0, 0,CVPixelBufferGetWidth(pixelBuffer),CVPixelBufferGetHeight(pixelBuffer))];
    UIImage *syszux_uiimg = [UIImage imageWithCGImage:syszux_cgiimg];
    CGImageRelease(syszux_cgiimg);

syszux_uiimg就是转换成功的UIImage。

如何对UIImage进行resize操作呢？可以使用UIImage的drawInRect方法：

    
    
    - (UIImage *)scaleToSize:(UIImage*)image size:(CGSize)size {
        UIGraphicsBeginImageContext(size);
        [image drawInRect:CGRectMake(0, 0, size.width, size.height)];
        UIImage* scaledImage = UIGraphicsGetImageFromCurrentImageContext();
        UIGraphicsEndImageContext();
        return scaledImage;
    }

这个resize操作使用了双线性插值的算法，和Pillow库中Image模块的bilinear resize一样。

##  **UIImage转换为CVPixelBufferRef**

UIImage是CGImage的wrapper，通过CGImage拿到图像的宽、高信息。然后在一个context中，通过CGContextDrawImage函数来将CGImage“渲染”出来，这个时候原始的像素数就保存在了context中CVPixelBufferRef指向的baseAddress上了。

代码如下所示：

    
    
    - (CVPixelBufferRef)syszuxPixelBufferFromUIImage:(UIImage *)originImage {
        CGImageRef image = originImage.CGImage;
        NSDictionary *options = [NSDictionary dictionaryWithObjectsAndKeys:
                                 [NSNumber numberWithBool:YES], kCVPixelBufferCGImageCompatibilityKey,
                                 [NSNumber numberWithBool:YES], kCVPixelBufferCGBitmapContextCompatibilityKey,
                                 nil];
    
        CVPixelBufferRef pxbuffer = NULL;
        CGFloat frameWidth = CGImageGetWidth(image);
        CGFloat frameHeight = CGImageGetHeight(image);
        CVReturn status = CVPixelBufferCreate(kCFAllocatorDefault,
                                              frameWidth,
                                              frameHeight,
                                              kCVPixelFormatType_32ARGB,
                                              (__bridge CFDictionaryRef) options,
                                              &pxbuffer);
    
        NSParameterAssert(status == kCVReturnSuccess && pxbuffer != NULL);
    
        CVPixelBufferLockBaseAddress(pxbuffer, 0);
        void *pxdata = CVPixelBufferGetBaseAddress(pxbuffer);
        NSParameterAssert(pxdata != NULL);
    
        CGColorSpaceRef rgbColorSpace = CGColorSpaceCreateDeviceRGB();
        CGContextRef context = CGBitmapContextCreate(pxdata,
                                                     frameWidth,
                                                     frameHeight,
                                                     8,
                                                     CVPixelBufferGetBytesPerRow(pxbuffer),
                                                     rgbColorSpace,
                                                     (CGBitmapInfo)kCGImageAlphaNoneSkipFirst);
        NSParameterAssert(context);
        CGContextConcatCTM(context, CGAffineTransformIdentity);
        CGContextDrawImage(context, CGRectMake(0,
                                               0,
                                               frameWidth,
                                               frameHeight),
                           image);
        CGColorSpaceRelease(rgbColorSpace);
        CGContextRelease(context);
    
        CVPixelBufferUnlockBaseAddress(pxbuffer, 0);
    
        return pxbuffer;
    }

##  CoreML模型的输入

CoreML模型期待的输入是什么格式的图像呢？我们从3个方面来说：

1，RGB或者BGR？大多数模型训练的时候使用的是RGB像素顺序，而Caffe使用的是BGR。如果你的神经网络框架使用的是OpenCV来加载图像（又没有做其它处理的话），那么大概率使用的也是BGR像素顺序。

2，是否归一化？0～255还是0～1？

3，是否进行normalization？适用normalized = (data - mean) / std 对每个像素进行计算？

关于详情，可以参考专栏文章：

[ Gemfield：转换PyTorch模型到CoreML ](https://zhuanlan.zhihu.com/p/110269410)

##  **总结**

iOS的图像系统中，和CoreML打交道的，最容易接触到的就是UIImage和CVPixelBufferRef。本文中，Gemfield展示了
**[裸的像素数组] <\---> CVPixelBufferRef <\---> UIImage **
之间的两两转换，以及这些图像数据如何最终到达CoreML模型的输入。

如果输入都不对，又怎能得到正确的输出呢？


# 背景
最近使用ffmpeg库在进行一个视频分析的相关项目。因为这个行业内原始视频的编码原因（从历史到硬件到存储空间，各种原因），使用ffmpeg在decode H264的视频的时候，一般都会decode为YUV420格式的raw data。这就需要进一步转换到RGB颜色空间，方便各种python的库或者是神经网络框架做分析。

# YUV420格式的raw data在哪里呢？
经过ffmpeg相关的API进行解码后，YUV420的data就存放在AVFrame结构体里的data成员中，data成员是个指针数组，一共有8个元素（也就是8个指针），其中，每个指针指向的都是一个unsigned char* 的buffer。

当decode为YUV420格式的时候，data只有前3个unsigned char* 指针被使用了，分别存放的是Y、U、V的raw data，其中U、V的raw data长度是Y的四分之一；

当decode为RGB或者BGR的时候，data只有第一个unsigned char* 指针被使用了，存放的就是RGB或者BGR的raw data。

# 转换方式一：逐像素替换
因为YUV和RGB的相关性是可以通过简单的线性公式计算出来的（很容易搜索到相关的介绍）。相关的代码如下所示：
```python3
int buffer_len = pFrame->width * pFrame->height;
img_width = pFrame->width;
img_height = pFrame->height;
buffer = malloc(sizeof(uint8_t)* buffer_len * 3);
int channels = 3;
int index = 0;
for (int y = 0; y < img_height; y++){
    for (int x = 0; x < img_width; x++){
        int indexY = y * img_width + x;
        int indexU = y / 2 * img_width / 2 + x / 2;
        int indexV = y / 2 * img_width / 2 + x / 2;
        uint8_t Y = pFrame->data[0][indexY];
        uint8_t U = pFrame->data[1][indexU];
        uint8_t V = pFrame->data[2][indexV];
        
        int R = Y + 1.402 * (V - 128);
        int G = Y - 0.34413 * (U - 128) - 0.71414*(V - 128);
        int B = Y + 1.772*(U - 128);
        R = (R < 0) ? 0 : R;
        G = (G < 0) ? 0 : G;
        B = (B < 0) ? 0 : B;
        R = (R > 255) ? 255 : R;
        G = (G > 255) ? 255 : G;
        B = (B > 255) ? 255 : B;
        buffer[(y*img_width + x)*channels + 2] = (uint8_t)R;
        buffer[(y*img_width + x)*channels + 1] = (uint8_t)G;
        buffer[(y*img_width + x)*channels + 0] = (uint8_t)B;
    }
}
```
这种方式优点是看起来简单，缺点是慢！想想看，1080p的图片还不得循环百万次以上！还有，鲁棒性差！

# 转换方式二：使用矩阵
这种方式使用矩阵运算来加快运行速度，这种方式速度可以快点，但鲁棒性和上面的一样：
```python
def ConvertYUVtoRGB(yuv_planes)
    plane_y  = yuv_planes[0]
    plane_u  = yuv_planes[1]
    plane_v  = yuv_planes[2]
     
    height = plane_y.shape[0]
    width  = plane_y.shape[1]
     
    # upsample if YV12
    plane_u = ndimage.zoom(plane_u, 2, order=0)
    plane_v = ndimage.zoom(plane_v, 2, order=0)
    # alternativelly can perform upsampling with numpy.repeat()
     
    # reshape
    plane_y  = plane_y.reshape((plane_y.shape[0], plane_y.shape[1], 1))
    plane_u  = plane_u.reshape((plane_u.shape[0], plane_u.shape[1], 1))
    plane_v  = plane_v.reshape((plane_v.shape[0], plane_v.shape[1], 1))
     
    # make YUV of shape [height, width, color_plane]
    yuv = np.concatenate((plane_y, plane_u, plane_v), axis=2)
     
    # according to ITU-R BT.709
    yuv[:,:, 0] = yuv[:,:, 0].clip(16, 235).astype(yuv.dtype) - 16
    yuv[:,:,1:] = yuv[:,:,1:].clip(16, 240).astype(yuv.dtype) - 128
     
    A = np.array([[1.164,  0.000,  1.793],
                  [1.164, -0.213, -0.533],
                  [1.164,  2.112,  0.000]])
     
    # our result
    rgb = np.dot(yuv, A.T).clip(0, 255).astype('uint8')
     
    return rgb
```
# 转换方式三：使用OpenCV
使用opencv的cvtColor函数进行颜色空间的转换：
```python
cv2.cvtColor(crs,dst, cv2.COLOR_YUV2BGR)
```
# 转换方式四：ffmpeg自身的sws_scale
使用sws_scale函数进行转换的效率是极高的。
```c++
#include <libswscale/swscale.h>
SwsContext* swsContext = swsContext = sws_getContext(pFrame->width, pFrame->height, AV_PIX_FMT_YUV420P,pFrame->width, pFrame->height, AV_PIX_FMT_BGR24,
                          NULL, NULL, NULL, NULL);

int linesize[8] = {pFrame->linesize[0] * 3};
int num_bytes = av_image_get_buffer_size(AV_PIX_FMT_BGR24, pFrame->width, pFrame->height, 1);
p_global_bgr_buffer = (uint8_t*) malloc(num_bytes * sizeof(uint8_t));
uint8_t* bgr_buffer[8] = {p_global_bgr_buffer};

sws_scale(swsContext, pFrame->data, pFrame->linesize, 0, pFrame->height, bgr_buffer, linesize);
//bgr_buffer[0] is the BGR raw data
```
# 庆祝
有了RGB或者BGR颜色空间的raw data后，我们就可以为所欲为了。可以送给CV的Mat结构体，可以使用numpy进行构造，也可以啥都不干。

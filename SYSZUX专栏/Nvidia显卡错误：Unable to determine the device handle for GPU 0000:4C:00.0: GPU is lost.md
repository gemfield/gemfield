# 背景
最近一台AI服务器在训练模型的时候突然僵住，然后查看GPU使用情况，发现：
```
gemfield@ai01:~$ nvidia-smi
Unable to determine the device handle for GPU 0000:4C:00.0: GPU is lost.  Reboot the system to recover this GPU
```
这台AI服务器的软硬件信息：
```
Ubuntu 20.04
NVIDIA GTX1080ti
uname -a =
gemfield@ai01:~$ uname -a
Linux ai01 5.4.0-73-generic #82-Ubuntu SMP Wed Apr 14 17:39:42 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux
```
并且已经健康的正常的服役了三年。所以这个错误来的猝不及防。

# 解决
当然是先祭出重启大法了。

重启之后问题消失，但过了一小时相同的问题再次出现。

# 调查分析
因为这个机器上有两个显卡，所以不可能同时都坏，所以首先排除显卡的问题；其次系统其它功能已然很正常，排除cpu和内存问题。分析可能的原因有：

- 主板硬件问题导致的PCI总线问题；
- 英伟达驱动问题；
- 内核驱动问题。

dmesg查看内核报错如下：
```
[16064.882605] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884602] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.884607] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884617] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.884621] pcieport 0000:00:03.0: AER: Multiple Corrected error received: 0000:00:03.0
[16064.884633] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.884727] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884733] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.884739] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.884744] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.884883] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884890] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.884894] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.884896] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.884901] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884906] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.884916] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.884920] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.884923] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.884926] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.884929] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.886911] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.886912] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.886916] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.886917] pcieport 0000:00:03.0: AER: Multiple Corrected error received: 0000:00:03.0
[16064.886924] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.887021] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887024] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887026] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887028] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887151] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887154] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887157] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887159] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887163] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887167] pcieport 0000:00:03.0: AER: can't find device of ID0018
[16064.887241] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887245] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887248] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887251] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887316] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887319] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887321] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887324] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887363] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887367] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887369] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887371] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887407] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887410] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887412] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887414] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887446] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887449] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887452] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001000/00002000
[16064.887454] pcieport 0000:00:03.0: AER:    [12] Timeout               
[16064.887492] pcieport 0000:00:03.0: AER: Corrected error received: 0000:00:03.0
[16064.887497] pcieport 0000:00:03.0: AER: PCIe Bus Error: severity=Corrected, type=Data Link Layer, (Transmitter ID)
[16064.887500] pcieport 0000:00:03.0: AER:   device [8086:2f08] error status/mask=00001100/00002000
[16064.887502] pcieport 0000:00:03.0: AER:    [ 8] Rollover              
[16064.887504] pcieport 0000:00:03.0: AER:    [12] Timeout               
```
毫无头绪。准备按照以下先后顺序进行实验：

- 更新内核驱动、nvidia驱动及所有可用的更新；
- 关机，清灰，重新插拔显卡数据线和电源线；
- 如果上面的方式不管用，拔掉一张显卡，仅保留一张；
- 仅保留另一张；
- 更换电源；
- 更换主板。

# 结果
进过一周实验，结论为：因为机箱风扇损坏导致机箱内过热导致的。

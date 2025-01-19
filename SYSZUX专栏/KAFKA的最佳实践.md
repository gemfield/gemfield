# 背景
一个Python项目中要使用kafka去deliver log，1个producer，5个consumer。单条消息的大小是100KB ～ 500KB，producer要在1秒钟之内能够发送30个这样的message。然后每个consumer也要在1秒钟之内消费30个这样的message。另外，消息不需要持久化（好像kafka没法关闭数据的落盘），消息不需要设置replica。所以你可以看到，这个场景还是比较简单的，非得说一些特点的话，那就是单条消息比较大（但是还没有超越kafka默认的1MB）、实时性要求比较高、数据量比较大（1秒钟平均可能产生200KB * 30 = 6MB的数据量，1秒钟可能要消费6MB * 5 = 30MB的数据量）。

# JVM级别的优化
因为kafka是java写的，所以JVM还是要考虑一些参数设置的。

下面是一个推荐的配置，你可以自己斟酌：
```bash
-Xmx8g -Xms8g -XX:MetaspaceSize=96m -XX:+UseG1GC-XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:G1HeapRegionSize=16M-XX:MinMetaspaceFreeRatio=50 -XX:MaxMetaspaceFreeRatio=80
```
-Xmx8g：最大堆大小是8G，gemfield设置的是16G，有钱任性，哼；
-Xms8g：起始堆大小是8G。

在Gemfield的机器上，启动的服务带的参数如下所示：
```bash
/usr/lib/jvm/java-1.8-openjdk/jre/bin/java -Xmx16G -Xms16G \
-server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 \
-XX:InitiatingHeapOccupancyPercent=35 -XX:+ExplicitGCInvokesConcurrent \
-Djava.awt.headless=true -Xloggc:/opt/kafka/bin/../logs/kafkaServer-gc.log \
......
```
# OS级别的优化
1，磁盘的读写性能通常是个瓶颈，多个磁盘或者更快的磁盘是个更好的选择。可以通过server.properties中的 log.dirs来配置多个硬盘。

2，增大socket buffer size，可以提高kafka的吞吐量：
```bash
gemfield@ubuntu:~$ cat  /proc/sys/net/core/wmem_max
212992
gemfield@ubuntu:~$ cat /proc/sys/net/core/rmem_max
212992
```
Gemfield没有更改。更详细的设置请参考：TCP Tune

# Log flush管理
这个决定消息如何同步到磁盘上。
```bash
# The number of messages to accept before forcing a flush of data to disk                           
#log.flush.interval.messages=10000                                                                                                       
                                                                                                                                
# The maximum amount of time a message can sit in a log before we force a flush                     
#log.flush.interval.ms=1000
```
根据Gemfield的实践，动这些配置没有什么用。还是省省吧。

# Log Retention Policy 消息保留策略
也就是消息保留多久会被清除掉。
```bash
# The following configurations control the disposal of log segments. The policy can                                             
# be set to delete segments after a period of time, or after a given size has accumulated.                               
# A segment will be deleted whenever *either* of these criteria are met. Deletion always happens                                         
# from the end of the log.                                                                                                      
                                                                                                    
# The minimum age of a log file to be eligible for deletion due to age                                                                   
#log.retention.hours=168
log.retention.hours=1                                                                                                         
                                                                                 
# A size-based retention policy for logs. Segments are pruned from the log unless the remaining                                          
# segments drop below log.retention.bytes. Functions independently of log.retention.hours.                                      
#log.retention.bytes=1073741824                                                                                                        
                                                                                                                                                                
# The maximum size of a log segment file. When this size is reached a new log segment will be created.                          
log.segment.bytes=1073741824                                                                                                           
                                                                                                                                                                                             
# The interval at which log segments are checked to see if they can be deleted according                                        
# to the retention policies                                                                                                            
log.retention.check.interval.ms=300000
```
gemfield将log.retention.hours设置为了1，并不需要将消息保留多久。

# 使用的文件系统
- 1，推荐EXT4 或者 XFS，XFS文件系统上Kafka会有更好的performance表现；
- 2，不要使用网络分区；
- 3，如果对持久化不做要求的话，可以使用内存文件系统，避免在磁盘IO上的浪费。比如gemfield就在某docker compose编排的系统中使用tmpfs文件系统（使用的是目前排名第一的wurstmeister/kafka做的docker镜像）：
```yaml
version: '3'
services:
  zookeeper:
    image: wurstmeister/zookeeper
    restart: always
    ports:
      - "2181:2181"
  kafka:
    image: wurstmeister/kafka
    restart: always
    ports:
      - "9092:9092"
    environment:
      KAFKA_MESSAGE_MAX_BYTES: 5000000
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
      KAFKA_ADVERTISED_HOST_NAME: localhost
      KAFKA_CREATE_TOPICS: "football_live_1:1:1"
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LOG_DIRS: '/kafka/gemfield'
    tmpfs:
      - /kafka/gemfield
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```
注意啊，tmpfs内存型文件系统上的数据在容器重启后就丢了。

# Zookeeper
不要把zookeeper部署到和kafka broker同一台机器上。

# Topic/Partitions
- 1，增加partitions增加并行吞吐量；
- 2，但是增加partition会（轻微）增加延迟。
- 3，Message.max.bytes 设置单条消息的最大字节，特别重要的是，如果你设置了replica，确保replica.fetch.max.bytes要大于或者等于message.max.bytes。

# Producer
- 1，Batch.size ，多少个消息发送一次。
- 2，Linger.ms ，多长时间发送一次。
- 3，Compression.type，压缩类型，这是producer端的一个主要工作。
- 4，Max.in.flight.requests.per.connection；
- 5，Acks；比方说0表示无需应答，所以速度很快（但是稍微不那么可靠点）。
- 6，更大的消息体积可以提高吞吐量。

# Consumer
好像没啥需要设置的。Consumer的速度一般是producer的好几倍，所以不是什么瓶颈。

# KAFKA的python客户端
好了，重点来了。上面说了那么多看似有道理的配置，但其实你只要知道，90%的情况下上面的配置对提高performance没什么卵用。比方说在Python社区最流行的3个kafka客户端分别是pykafka、kafka-python、confluent-kafka-python。这里有一篇文章Python Kafka Client Benchmarking，介绍了这三者之间的性能比较（PK的版本是pykafka 2.3.1、kafka-python 1.1.1和confluent-kafka-python 0.9.1)。

以三者的producer为例，confluent-kafka-python >> pykafka(librdkafka backend) >> pykafka > kafka-python；以三者的consumer为例，confluent-kafka-python >> pykafka(librdkafka backend) >> kafka-python > pykafka。

## 1，kafka-python

最初在调研的时候，因为kafka-python排在搜索结果的第一名，并且github上的star数量最多，所以首先选择了kafka-python。在最新的kafka-python 1.4.2版本中，本来预期producer一秒能发送20MB的数据（基于本文开始背景中的上下文），但实际上只能发送3~4MB左右。这就导致一种情况，就是producer异步发送的东西cache在一个buffer里，由于网路来不及将其发送出去，于是导致buffer越攒越多，当达到buffer_memory的限制时，数据会被清空（也就是还未发送就被扔掉了），并且producer会阻塞住好一会儿......

buffer_memory (int) – The total bytes of memory the producer should use to buffer records waiting to be sent to the server. If records are sent faster than they can be delivered to the server the producer will block up to max_block_ms, raising an exception on timeout. In the current implementation, this setting is an approximation. Default: 33554432 (32MB)
在kafka-python的github上找到了这么一条issue：Slower producer throughput on 1.4.1 than on 1.3.5 · Issue #1412 · dpkp/kafka-python

这个问题在1.4.1中出现，有人解释了原因是因为没有crc32的硬解码。

在最新版（截止2018年5月15日）的1.4.2中可以通过安装crc32来解决这个performance问题：
```bash
pip install crc32
```
安装了crc32之后，这个问题就解决了。然而Gemfield要转向confluent了。

## 2，confluent-kafka-python

在最新版的confluent-kafka-python 上（反正2018年5月已经是了），pip install安装confluent-kafka-python时使用的 manylinux wheels中已经嵌入了librdkafka的so库了，比如：
```bash
gemfield@gemfield.org:~# find / -name "librdkafka*" 
/usr/local/lib/python2.7/dist-packages/confluent_kafka/.libs/librdkafka-6f63ed6f.so.1
```
在使用的时候，因为速度太他瞄的快了，所以很可能会看到“BufferError: Local: Queue full”这样的错误，这就是本地的producer的buffer满了，为什么满了？因为网络来不及将越攒越多的数据送出去。这个buffer是靠两个config属性来指定的：
```python
gemfield_config = {'bootstrap.servers': 'kafka',
                   'queue.buffering.max.kbytes': 2000000,
                   'queue.buffering.max.messages': 1000000}
```
-queue.buffering.max.kbytes 来指定能够缓存多大的信息，默认是400MB，最大能提高到2097151KB，也就是大约2GB（因为缓存不是100%你的消息，还有key或者其他meta信息，所以实际可用的到不了2GB）。
-queue.buffering.max.messages来指定能够缓存多少个信息，默认是10万个吧，够用了。

可以通过更改这两个属性和优化程序的流程控制来避免BufferError: Local: Queue full这样的错误。

# 3，Gemfield自己的比较

下面是发送3000个200KB的消息的PK结果：
```bash
#这个使用的是confluent-kafka-python
gemfield@gemfield.org:~# time python kf_producer.py 
real    0m3.609s
user    0m0.360s
sys     0m0.684s

#这个使用的是kafka-python
gemfield@gemfield.org:~# time python producer.py 
real    0m7.121s
user    0m3.976s
sys     0m2.392s
```

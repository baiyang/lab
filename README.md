lab
===

实践各种小算法和工具

在socks5中，我的设计思路请参考以下网址：
http://www.ibaiyang.org/2012/08/18/redesign-socks5-proxy-framework/

注意在传输数据的时，要处理socket各种异常错误，比如Connection reset by peer.

在编写网络应用程序时，对每一个关于网路的（socket）的系统调用，都要处理异常。因为很难预测客户端的请求情况，

发现，这个框架不合适视频流播放，貌似有点延时。还需要改进。
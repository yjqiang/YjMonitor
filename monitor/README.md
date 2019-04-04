# YjMonitor
b站 上船风暴监控  
作者自用，更新不频繁，bug基本没有，但是更新慢，衍生自https://github.com/yjqiang/bilibili-live-tools  
1.ctrl.toml 最后那里定义了发送目标房间，结果都会发到指定房间里面，默认3号房间；start end控制监控范围，房间取自正在播的房间（按照热度排序）  
2.由于python性能问题，推荐（1000-1500）一个机器，需要几台机器协同一起监控，之后考虑golang（flag）  
3.数据格式为多进制进制，房间号和raffleid间隔为特殊符号  

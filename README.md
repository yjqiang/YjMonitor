# YjMonitor
b站 上船风暴监控 范围版本  
作者自用，更新不频繁，bug基本没有，但是更新慢，衍生自https://github.com/yjqiang/bilibili-live-tools  
user.toml 最后那里定义了发送目标房间，结果都会发到指定房间里面，默认3号房间；start end控制监控范围，房间取自正在播的房间（按照热度排序），超出范围默认填充为conf/roomid.toml，里面数据是6k左右的热门房间  
由于python性能问题，推荐500左右一个机器，需要几台机器协同一起监控，之后考虑golang（flag）
数据格式为62进制，房间号和raffleid间隔为特殊符号

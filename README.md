YjMonitor
===========
b站 上船风暴监控  
作者自用，更新不频繁，bug基本没有，但是更新慢，衍生自https://github.com/yjqiang/bilibili-live-tools  

monitor部分
------------
1. ctrl.toml 最后那里定义了发送目标房间，结果都会发到指定房间里面，默认3号房间；start end控制监控范围，房间取自正在播的房间（按照热度排序)
1. 由于python性能问题，推荐（1000-1500）一个机器，需要几台机器协同一起监控，之后考虑golang（flag)
1. 数据格式为多进制进制，房间号和raffleid间隔为特殊符号

ws_client部分
-------------
1. req_check.py 负责监控 websocket 服务器的状态。
1. req_create_key.py 负责让 websocket 服务器产生新的 key ，需要超管权限。
1. req_post_raffle.py 负责向 websockets 服务器推送 raffle (仅作为示例)。
1. global_var.py 里面的 `URL` 是 websocket 服务器的地址以及端口，控制以上的服务器请求目标。
1. key 文件夹里面的 create_key.py 是单独运行的产生公钥私钥，密钥用于验证身份等。其中 super_admin 是超管， admin 是普通管理员。不同 websocket 控制内容有不同的身份控制，状态检查和推送抽奖需要普通管理员，而产生 key 需要超管身份。

ws_server部分
-------------
1. run.py 负责运行。
1. db 负责存储与验证 ws 的链接 key 。key 在服务器端产生，保存特殊 hash 用于验证客户端的 ws 连接请求，同时真正的 key 加密之后返回到发出该请求的服务端。
1. key 文件夹里面存贮**公钥**以验证身份等。其中 super_admin 是超管， admin 是普通管理员。

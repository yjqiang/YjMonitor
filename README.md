YjMonitor
===========
b站 上船风暴监控  
作者自用，更新不频繁，bug基本没有，但是更新慢，衍生自https://github.com/yjqiang/bilibili-live-tools  

monitor部分
------------
1. ctrl.toml 最后那里定义了发送目标房间，结果都会发到指定房间里面；start end控制监控范围。
1. 由于python性能问题，推荐（1000-1500）一个机器，需要几台机器协同一起监控，之后考虑golang（flag)。
1. 如果使用ws_server作为中转，[guard](https://github.com/yjqiang/YjMonitor/blob/master/monitor/tasks/guard_raffle_handler.py#L11)和[storm](https://github.com/yjqiang/YjMonitor/blob/master/monitor/tasks/storm_raffle_handler.py#L9)需要均把`check_v1`改成`check_v2`，同时设置ctrl.toml里面的url为有效值, key 文件夹内只需要 admin_privkey.pem 即可；默认使用b站服务器作为中转点，需要ctrl.toml里面目标房间有效。**目前无论是否需要ws_server作为服务器，都需要一个有效 admin_privkey.pem 作为填充。**


ws_client部分
-------------
1. ws_client.py 是 websocket 接收端示例， 采用了 ping 作为心跳。
1. tcp_client.py 是 tcp 接收端，自定义心跳，同时把 websocket 的 json 发送编码后加一个 header 作为数据发送（就像 bilibili 弹幕那样）。
1. req_check.py 负责监控 websocket 服务器的状态，需要管理员权限。
1. req_create_key.py 负责让 websocket 服务器产生新的 key ，需要超管权限。max_users 表示该 key 的最大同时使用人数。
1. req_post_raffle.py 负责向 websockets 服务器推送 raffle (仅作为示例)，需要管理员权限。
1. global_var.py 里面的 `URL` 是 websocket 服务器的地址以及端口，控制以上的请求目标。
1. key 文件夹里面的 create_key.py 是单独运行的产生公钥私钥，密钥用于验证身份等。其中 super_admin_privkey.pem 是超管， admin_admin_privkey.pem 是普通管理员。不同 websocket 控制内容有不同的身份控制，状态检查和推送抽奖需要普通管理员，而产生 key 需要超管身份。

ws_server部分
-------------
1. run.py 负责运行。
1. db 负责存储与验证 websocket 或者 tcp 的链接 key 。key 在服务器端产生，保存特殊 hash 用于验证客户端的 ws 连接请求，同时真正的 key 加密之后返回到发出该请求(req_post_raffle.py)的客户端。
1. key 文件夹里面**只**存贮**公钥**以验证身份等。其中 super_admin_pubkey.pem 是超管， admin_pubkey.pem 是普通管理员。

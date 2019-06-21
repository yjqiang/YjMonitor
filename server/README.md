server部分（转发 monitor 发送的抽奖信息）
-------------
1. run.py 负责运行。
1. db 负责存储与验证链接 key。key 在服务器端产生，保存特殊 hash 用于验证客户端的 tcp 连接请求。server 收到产生 key 的请求后同时会把原始的 key 加密之后返回到发出该请求(req_post_raffle.py)的客户端。
1. key 文件夹里面***只存贮公钥***以验证身份等。使用签名验证来保证不会被他人恶意随意推送垃圾数据，其中 super_admin_pubkey.pem 是超管， admin_pubkey.pem 是普通管理员。
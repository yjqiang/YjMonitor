1. req_check.py 负责监控 websocket 服务器的状态。
1. req_create_key.py 负责让 websocket 服务器产生新的 key。
1. req_post_raffle.py 负责向 websockets 服务器推送 raffle (仅作为示例)。
1. global_var.py 里面的 `URL` 是 websocket 服务器的地址以及端口，控制以上的服务器请求目标。
1. key 文件夹里面的 create_key.py 是单独运行的产生公钥私钥，密钥用于验证身份等。其中 super_admin 是超管， admin 是普通管理员。不同 websocket 控制内容有不同的身份控制，状态检查和推送抽奖需要普通管理员，而产生 key 需要超管身份。

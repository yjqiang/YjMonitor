# monitor 子监控
## 监控弹幕房间
1. conf/ctrl.toml 中的 `post_office` 定义了 server 的服务器地址（方法是直接 POST，这是 server 自定义中转服务器模式）；`START` 与 `END` 控制监控房间的范围。
1. key 文件夹内只需要 admin_privkey.pem 即可，为了防止恶意推送，这个 key 用于验证推送者身份的正确性。
1. 由于python性能问题，推荐 4000 左右个房间/机器，需要几台机器协同一起监控，之后考虑golang（flag)。
1. 运行 `run.py`。
## 补足部分（暴力轮询）
1. conf/ctrl.toml 中的 `post_office` 定义了 server 的服务器地址（方法是直接 POST，这是 server 自定义中转服务器模式）；`yjmonitor_tcp_addr` 和 `yjmonitor_tcp_key` 需要填写好，用来去除重复推送。
1. key 文件夹内只需要 admin_privkey.pem 即可，为了防止恶意推送，这个 key 用于验证推送者身份的正确性。
1. 运行 `run_polling.py`。
## 实时获取更新（几乎实时）
1. conf/ctrl.toml 中的 `post_office` 定义了 server 的服务器地址（方法是直接 POST，这是 server 自定义中转服务器模式）。
1. key 文件夹内只需要 admin_privkey.pem 即可，为了防止恶意推送，这个 key 用于验证推送者身份的正确性。
1. 运行 `run_realtime.py`。
## 分布式部分（几乎实时，其实不是分布式，就是起了个高大上的名字）
1. conf/ctrl.toml 中的 `post_office` 定义了 server 的服务器地址（方法是直接 POST，这是 server 自定义中转服务器模式）。
1. key 文件夹内需要 admin_privkey.pem 和 admin_pubkey.pem，admin_privkey 用于验证推送者身份的正确性，admin_pubkey 用于中心服务器身份验证。
1. 需要公网 IP 的服务器（因为的代码写得比较 233）。
1. 本项目内的是分服务，需要中心服务器运行 [run_distributed.py](https://github.com/yjqiang/bili_utils/blob/master/fetch_roomids/refresh_rooms_hub/run_distributed.py) 不间断推送房间。[distributed_clients](https://github.com/yjqiang/bili_utils/blob/master/fetch_roomids/refresh_rooms_hub/run_distributed.py#L16) 处填写客户端的 IP，中心服务器需要 admin_privkey 用于检验。
1. 运行 `run_distributed.py`。
1. monitor 自定义 ws_server 作为中转模式
1. conf/ctrl.toml 中的 `post_office` 定义了 ws_server 的服务器地址（方法是直接 POST ，这是 ws_server 自定义中转服务器模式）；START 与 END 控制监控房间的范围。
1. 使用方法：如果使用 ws_server 作为中转，设置 ctrl.toml 里面的 `post_office` 为有效值, key 文件夹内只需要 admin_privkey.pem 即可，为了防止恶意推送，这个 key 用于验证推送者身份的正确性。
1. 由于python性能问题，推荐 2000 左右个房间/机器，需要几台机器协同一起监控，之后考虑golang（flag)。
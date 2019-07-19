from typing import Optional

from receiver import TcpReceiverConn


class TcpReqError(Exception):
    RSP_SUGGESTED = {}

    def __init__(self, conn: TcpReceiverConn, msg: Optional[str] = None, others=None):
        self.conn = conn
        self.msg = msg
        self.others = others


class DataError(TcpReqError):  # Json数据格式等错误（缺失值/值不是规定格式等等错误）
    RSP_SUGGESTED = {'code': -1, 'type': 'error', 'data': {'msg': '数据错误'}}


class VerificationError(TcpReqError):  # KEY错误
    RSP_SUGGESTED = {'code': -1, 'type': 'error', 'data': {'msg': 'KEY错误'}}


class MaxError(TcpReqError):  # 该用户的key同时使用过多错误
    RSP_SUGGESTED = {'code': -1, 'type': 'error', 'data': {'msg': '该key的用户过多'}}


class BanError(TcpReqError):  # 该用户的被 ban
    RSP_SUGGESTED = {'code': -1, 'type': 'error', 'data': {'msg': '服务器拉黑了你'}}


class OtherError(TcpReqError):  # 其他未知错误
    RSP_SUGGESTED = {'code': -1, 'type': 'error', 'data': {'msg': 'NULL'}}

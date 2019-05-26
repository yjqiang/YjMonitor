from typing import Optional


class JsonReqError(Exception):
    RSP_SUGGESTED = {}

    def __init__(self, msg: Optional[str] = None, others=None):
        self.msg = msg
        self.others = others


class DataError(JsonReqError):  # Json数据格式等错误（缺失值/值不是规定格式等等错误）
    RSP_SUGGESTED = {'code': -1, 'type': '', 'data': {'msg': '数据错误'}}


class VerificationError(JsonReqError):  # 签名校验错误
    RSP_SUGGESTED = {'code': -1, 'type': '', 'data': {'msg': '签名错误'}}


class TimeError(JsonReqError):  # 签名时间错误
    RSP_SUGGESTED = {'code': -1, 'type': '', 'data': {'msg': '时间错误'}}


class ReqFormatError(JsonReqError):  # request格式错误（request不是json格式等）
    RSP_SUGGESTED = {'code': -1, 'type': '', 'data': {'msg': '数据格式错误'}}


class OtherError(JsonReqError):  # 其他未知错误
    RSP_SUGGESTED = {'code': -1, 'type': '', 'data': {'msg': 'NULL'}}

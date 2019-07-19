import base64
from os import path

import rsa

import utils


class RsaHandlerError(Exception):
    pass


class RsaHandlerVerificationError(RsaHandlerError):  # 签名校验错误
    pass


class RsaHandlerTimeError(RsaHandlerError):  # 签名时间错误
    pass


class RsaHandler:
    __slots__ = ('_super_admin_pubkey', '_admin_pubkey',)

    def __init__(self):
        key_path = f'{path.dirname(path.realpath(__file__))}'
        with open(f'{key_path}/super_admin_pubkey.pem', 'rb') as f:
            self._super_admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())
        with open(f'{key_path}/admin_pubkey.pem', 'rb') as f:
            self._admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())

    @staticmethod
    def _verify(pubkey: rsa.PublicKey, name: str, time: int, signature: str) -> bool:
        try:
            cur_time0 = time
            cur_time1 = utils.curr_time()
            if -1200 <= cur_time0 - cur_time1 <= 1200:
                # 缺省name表示为super_admin，需要使用超管签名校验，其他的用管理员校验
                text = f'Hello World. This is {name} at {cur_time0}.'.encode('utf-8')
                rsa.verify(
                    text,
                    base64.b64decode(signature.encode('utf8')),
                    pubkey)
                return True
            else:
                raise RsaHandlerTimeError()
        except rsa.VerificationError:
            raise RsaHandlerVerificationError()

    @staticmethod
    def _encrypt(pubkey: rsa.PublicKey, orig_text: str) -> str:
        return base64.b64encode(
            rsa.encrypt(orig_text.encode('utf8'), pubkey)
        ).decode('utf8')

    def verify_super_admin(self, name: str, time: int, signature: str) -> bool:
        return self._verify(self._super_admin_pubkey, name, time, signature)

    def verify_admin(self, name: str, time: int, signature: str) -> bool:
        return self._verify(self._admin_pubkey, name, time, signature)

    def encrypt_super_admin(self, orig_text: str) -> str:
        return self._encrypt(self._super_admin_pubkey, orig_text)

    def encrypt_admin(self, orig_text: str) -> str:
        return self._encrypt(self._admin_pubkey, orig_text)


rsa_handler = RsaHandler()

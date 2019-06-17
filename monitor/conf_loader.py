from os import path
import toml
import rsa
    
    
class ConfLoader:
    def __init__(self):
        root_path = path.dirname(path.realpath(__file__))
        path_conf = f'{root_path}/conf'
        self.file_user = f'{path_conf}/user.toml'
        self.file_bili = f'{path_conf}/bili.toml'
        self.file_ctrl = f'{path_conf}/ctrl.toml'
        self.file_roomid = f'{path_conf}/roomid.toml'
        self.key_path = f'{root_path}/key/admin_privkey.pem'
        self.admin_pubkey_path = f'{root_path}/key/admin_pubkey.pem'
        
    @staticmethod
    def toml_load(path):
        with open(path, encoding="utf-8") as f:
            return toml.load(f)
    
    @staticmethod
    def toml_dump(object, path):
        with open(path, 'w', encoding="utf-8") as f:
            toml.dump(object, f)
    
    def write_user(self, dict_new, user_id):
        dict_user = self.toml_load(self.file_user)
        for i, value in dict_new.items():
            dict_user['users'][user_id][i] = value
        self.toml_dump(dict_user, self.file_user)
            
    def read_bili(self):
        return self.toml_load(self.file_bili)
     
    def read_user(self):
        return self.toml_load(self.file_user)
        
    def read_ctrl(self):
        return self.toml_load(self.file_ctrl)

    def read_roomid(self):
        return self.toml_load(self.file_roomid)

    def read_key(self):
        with open(self.key_path, 'rb') as f:
            admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())
        return admin_privkey

    def read_pubkey(self):
        with open(self.admin_pubkey_path, 'rb') as f:
            admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())
        return admin_pubkey
        
                
var = ConfLoader()


def write_user(dict_new, user_id):
    var.write_user(dict_new, user_id)

        
def read_bili():
    return var.read_bili()

      
def read_user():
    return var.read_user()

        
def read_ctrl():
    return var.read_ctrl()


def read_key():
    return var.read_key()


def read_pubkey():
    return var.read_pubkey()


def read_roomid():
    return var.read_roomid()

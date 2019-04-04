class LoginStatus:
    @staticmethod
    def check_status():
        # print('因为已经正常登陆')
        return True

                
class LogoutStatus:
    @staticmethod
    def check_status():
        # print('因为未正常登陆')
        return False
        
        
class UserStatus:
    def __init__(self, user):
        self.log_status = LoginStatus
        self.user = user
        
    def logout(self):
        # print('{未登陆}')
        self.log_status = LogoutStatus
        
    def login(self):
        # print('{已经登陆}')
        self.log_status = LoginStatus
        
    def check_log_status(self):
        # print('正在检查', request)
        code = self.log_status.check_status()
        return code

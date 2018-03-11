
def totp_text():
    return  """
                
                Your ONE TIME PASSWORD IS %s 
                
            """

def signup_text():
    return  """
                Click the link to confirm your email \n
                %s
            """


class Constants:
    def __init__(self):
        self.dialect = 'mysql'
        self.username = {
            'test' : 'root',
            'development' :  'kirana',
            'prod' : ''
        }
        self.password = {
            'test' : 'Santi_39',
            'development' : 'kirana@123',
            'prod' : ''
        }
        self.host = {
            'test' : 'localhost',
            'development' : '139.59.80.74',
            'prod' : ''
            }
        self.database = {
            'test' : 'KoreTask' ,
            'development' : 'test',
            'prod' : ''
            }
        self.jwt_token = 'kore_task'

    def get_env_config(self,env):
        return self.dialect + '://' + self.username[env] + ':' + self.password[env]  + '@' + self.host[env] + '/' + self.database[env]
    
    def get_jwt_secret(self):
        return self.jwt_token

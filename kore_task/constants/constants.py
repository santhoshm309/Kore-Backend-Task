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
    def get_env_config(self,env):
        return self.dialect + '://' + self.username[env] + ':' + self.password[env]  + '@' + self.host[env] + '/' + self.database[env]
    

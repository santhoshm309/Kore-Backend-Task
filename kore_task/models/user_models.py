from . import Base, Session
from sqlalchemy.orm import relationship
import random, string
import bcrypt

class Users(Base):
    __tablename__ = 'Users'
    __table_args__ = { 'autoload' : True}
    link_hash =  relationship('LinkHash',cascade='all,delete',backref='Users') 
    auth = relationship('Auth',cascade='all,delete',backref='Users')
    user_totp = relationship('UserTotp',cascade='all,delete',backref='Users')
    user_tokens = relationship('UserTokens',cascade='all,delete',backref='Users')

class LinkHash(Base):
	__tablename__ = 'LinkHash'
	__table_args__ = {'autoload' : True }

class Auth(Base):
	__tablename__ = 'Auth'
	__table_args__ = {'autoload' : True }

class UserTotp(Base):
	__tablename__ = 'UserTotp'
	__table_args__ = {'autoload' : True }


class UserTokens(Base):
	__tablename__ = 'UserTokens'
	__table_args__ = {'autoload' : True }



class UserModel:



	def get_user_obj(self,request_body):
		return {
			'name' : request_body['name'],
			'email' : request_body['email'],
			'password' : bcrypt.hashpw(request_body['password'].encode('utf8'), bcrypt.gensalt()),
			'dob' : request_body['dob'],
			'mobile_no' : int(request_body['mobile_no']),
			'gender' : int(request_body['gender']),
			'college' : request_body['college']
			}

	def random_hash(self,type):
		if type == 0:
			return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
		else:
			return ''.join(["%s" % random.randint(0, 9) for num in range(0, 6)]) # Get 6 digit totp
			
	def gen_hash(self):
		session = Session()
		while True:
			hashv = self.random_hash(0)
			result = session.query(LinkHash).filter(LinkHash.hash == hashv).all()
			session.close()
			if len(result)>0 :
				hashv = random_hash(0)
			else:
				return hashv


	def gen_totp(self):
		session = Session()
		while True:
			totp = self.random_hash(1)
			result = session.query(UserTotp).filter(UserTotp.totp == totp).all()
			session.close()
			if len(result)>0 :
				totp = random_hash(1)
			else:
				return totp

	def gen_token(self):
		session = Session()
		while True:
			token = self.random_hash(0)
			result = session.query(UserTokens).filter(UserTokens.token == token).all()
			session.close()
			if len(result)>0 :
				token = random_hash(0)
			else:
				return token





			

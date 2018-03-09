from . import Base, Session
from sqlalchemy.orm import relationship
import random, string
import bcrypt

class Users(Base):
    __tablename__ = 'Users'
    __table_args__ = { 'autoload' : True}
    link_hash =  relationship('LinkHash',cascade='all,delete',backref='Users') 

class LinkHash(Base):
	__tablename__ = 'LinkHash'
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

	def random_hash(self):
		return  ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
			
	def gen_hash(self):
		session = Session()
		while True:
			hashv = self.random_hash()
			result = session.query(LinkHash).filter(LinkHash.hash == hashv).all()
			print(len(result))
			if len(result)>0 :
				hashv = random_hash()
			else:
				return hashv


from ..constants.helper import Helper
from pyramid.view import view_config
from ..models.user_models import UserModel,Users,LinkHash,UserTokens,UserTotp,Auth
import bcrypt
from ..models import Session
from sqlalchemy.exc import DBAPIError
user_model = UserModel()
from .auth_controller import add_auth
import jwt
import datetime
from ..constants.constants import Constants
import datetime

constants = Constants()	
@view_config(route_name='home',request_method="GET")
def home(request):
	return Helper.construct_response(200,"Success",{'message':"Success"})
	

def delete_expired_totps(session):
	result = session.query(UserTotp).filter(UserTotp.expiry <= datetime.datetime.now())
	if result.count() > 0:
		result.delete()
	return 

def delete_expired_tokens(session):
	result = session.query(UserTokens).filter(UserTokens.expiry <= datetime.datetime.now())
	if result.count() > 0:
		result.delete()
	return 


@view_config(route_name='login', request_method="POST")
def login(request):
	code = 500
	message = ''
	response = ''
	try :	
		session = Session()

		# Check payload
		request_body = request.json_body
		if not 'username' in request_body or not 'password' in request_body:
			return Helper.construct_response(400,'Invalid Data','')	

		result_set = session.query(Users)\
		.filter((Users.email == request_body['username'] )).first()

		if not result_set:
			return Helper.construct_response(404,'User not found','')

		# Acount not yet verified .......................................................	

		if result_set.is_active == 0:
			return Helper.construct_response(401,'Account not yet verified')




		# Retrive passwords to compare ...................................................
			
		passw = request_body['password'].encode('utf8')
		hashed = result_set.password.encode('utf8')	
		
		if not bcrypt.checkpw(passw,hashed):
			return Helper.construct_response(401,'Unauthorized')


		# If everything is ok generate JWT token ...........................................

		is_2fa = session.query(Auth).filter(Auth.user_id == result_set.id).first()

		

		if not is_2fa:
			delete_expired_tokens(session)
			token = user_model.gen_token()

			expiry = datetime.datetime.now()
			expiry = expiry + datetime.timedelta(minutes = 360)
			expiry = expiry.strftime("%Y-%m-%d %H:%M")

			user_token = {
				'user_id' : result_set.id,
				'token': token,
				'expiry' : expiry		}

			user_token = Helper.created_at(user_token)

			token_obj = UserTokens(**user_token)
			session.add(token_obj)
			code = 200
			message = 'Success'
			response = {'token' : token, 'expiry':expiry, 'auth' : False}



		else:

			hashv = {'user_id' : result_set.id, 'hash': user_model.gen_hash(),'type' : 1}
			hashv = Helper.created_at(hashv)
			hash_obj = LinkHash(**hashv)
			session.add(hash_obj) 
			code = 201
			message = 'Success'
			response = {'auth' : True, 'token' : hashv['hash']}

		session.commit()
		session.close()
		return Helper.construct_response(code,message,response)

	except DBAPIError as dbErr:
		'''
			SQL error ..................................................................
		'''
		print("MYSQL Error --------------------------------" + str(dbErr.orig))

		# print("MYSQL Error-------------------------" + code,message)
		return Helper.construct_response(500,'Internal Error','')	
	

	except Exception as e:

		print("Server Error ................................." + str(e))
		return Helper.construct_response(500,'Server Error','')	

		




@view_config(route_name='signup', request_method="POST")
def signup(request):
	'''
		Signup API

	'''
	try:
		session = Session()
		request_body = request.json_body

		# Check for correct payload ....................................

		required = {'name','email','password','mobile_no','gender','college','dob','auth'}
		present = set(request_body.keys())
		missing = required - present
		if len(missing) > 0:
			return Helper.construct_response(404,'Data Missing', list(missing))

		# Check if user has already registered ..............................................	

		result = session.query(Users).filter((Users.email == request_body['email']) | (Users.mobile_no == request_body['mobile_no'])).all()

		if len(result) > 0:
			return Helper.construct_response(400,'User already exixts with that email/mobile_no','')


		# Create user object ...........................................................	

		
		user_obj = user_model.get_user_obj(request_body)

		user_obj = Helper.created_at(user_obj)

		user = Users(**user_obj)

		# Create a unique hash for the user .............................................

		hashv = {'hash' : user_model.gen_hash()}

		hashv = Helper.created_at(hashv)

		link_hash = LinkHash(**hashv)

		
		# Append the hash to the user ....................................................

		user.link_hash.append(link_hash)

		auth_obj = {}
		if int(request_body['auth']) == 1:
			auth_obj = add_auth(request_body)
			user.auth.append(auth_obj)


		# Insert and commit the results ..................................................  

		session.add(user)

		# Send confirmation email .......................................................

		flag = Helper.send_mail(request_body['email'],'Email Confirmation | Kore Task','signup','http://localhost:3030/#/verify?link='+hashv['hash'])
		if not flag:
			session.rollback()
			session.close()
			return Helper.construct_response(500,'Mail cannot be sent at the moment','')


		session.commit()

		#Closing session ................................................................

		session.close()

		return Helper.construct_response(200,'Success','')
	
	except DBAPIError as dbErr:
		'''
			SQL error ..................................................................
		'''
		print("MYSQL Error --------------------------------" + str(dbErr.orig))

		# print("MYSQL Error-------------------------" + code,message)
		return Helper.construct_response(500,'Internal Error','')	
	

	except Exception as e:

		print("Server Error ................................." + str(e))
		return Helper.construct_response(500,'Server Error','')	




@view_config(route_name='verify_email', request_method='GET')
def verify_email(request):
	try:
		# Get the query params.......................................................

		link_hash = dict(request.GET)

		session=Session()


		# Get the status of User for the hash in param...............................

		result = session.query(LinkHash,Users).join(Users, Users.id == LinkHash.user_id)\
						.filter(LinkHash.hash == link_hash['link'])\
						.filter(LinkHash.type == 0).first()


		# No result fetched -> no user found.........................................

		print(link_hash)

		if not result:
			return Helper.construct_response(404,'Invalid link','')

		# Already verified ..........................................................	

		if result.Users.is_active == 1:
			return Helper.construct_response(201,'User email already verified','')


		# Update status ............................................................	

		result.Users.is_active = 1

		# delete hash now .........................................................

		delete = session.query(LinkHash).filter(LinkHash.hash == link_hash['link']).delete()

		# Commit and close .........................................................

		session.commit()

		session.close()

		return Helper.construct_response(200,'Email verified. Redirecting to Login','')	

	except Exception as e:
		
		print("Server Error ................................." + str(e))
		return Helper.construct_response(500,'Server Error','')	

@view_config(route_name='signout', request_method="POST")
def signout(request):
	try:
		session = Session()

		request_body = request.json_body
		delete_expired_tokens(session)

		# Check payload

		if not 'token' in request_body:
			return Helper.construct_response(400,'Invalid Data','')		



		result = session.query(UserTokens).filter(UserTokens.token == request_body['token']).first()

		if not result:
			return Helper.construct_response(400,'Token expired','')			

		session.query(UserTokens).filter(UserTokens.user_id == result.user_id).delete()

		session.commit()
		session.close()

		return Helper.construct_response(200,'Success','')



	except DBAPIError as dbErr:
		'''
			SQL error ..................................................................
		'''
		print("MYSQL Error --------------------------------" + str(dbErr.orig))

		# print("MYSQL Error-------------------------" + code,message)
		return Helper.construct_response(500,'Internal Error','')	
	

	except Exception as e:

		print("Server Error ................................." + str(e))
		return Helper.construct_response(500,'Server Error','')	


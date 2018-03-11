
from ..constants.helper import Helper
from pyramid.view import view_config
from ..models.user_models import UserModel,Users,LinkHash,Auth,UserTotp,UserTokens
import bcrypt
from ..models import Session
from sqlalchemy.exc import DBAPIError
import datetime
user_model = UserModel()


def delete_expired_tokens(session):
	result = session.query(UserTokens).filter(UserTokens.expiry <= datetime.datetime.now())
	if result.count() > 0:
		result.delete()
	return

def delete_expired_totps(session):
	result = session.query(UserTotp).filter(UserTotp.expiry <= datetime.datetime.now())
	if result.count() > 0:
		result.delete()
	return 


def add_auth(request_obj, user_id=None):
	
	
	# Check payload..............................................................
	telegram_obj = {}
	telegram_obj = Helper.created_at(telegram_obj)
				
	# User if supplied ..........................................................			

	if user_id:
		telegram_obj['user_id'] = user_id

	# Attach telegram number if needed ..........................................	

	if 'telegram_number' in request_obj:
		telegram_obj['telegram_number'] = int(request_obj['telegram_number'])	

	auth_obj = Auth(**telegram_obj)

	return auth_obj

@view_config(route_name='send_totp', request_method="POST")
def send_totp(request):

	try:
		request_body=request.json_body

		session = Session()

		if not 'auth_type' in request_body or not 'token' in request_body:
			return (400,'Incomplete Data','')

		# Check if the user has attempted login first ...................................
		
		result = session.query(LinkHash,Users).join(Users,Users.id == LinkHash.user_id).filter(LinkHash.hash == request_body['token']).filter(LinkHash.type == 1).first()

		if not result:
			return Helper.construct_response(401,'Unauthorized','')			

		delete_expired_totps(session)	
			
		is_exist = session.query(UserTotp).filter(UserTotp.user_id == result.Users.id).first()
		totp = ''
		if not is_exist:


			totp = 	user_model.gen_totp()


			expiry = datetime.datetime.now()
			expiry = expiry + datetime.timedelta(minutes = 360)
			expiry = expiry.strftime("%Y-%m-%d %H:%M")

			totph = {'totp' : totp, 'expiry': expiry, 'user_id': result.LinkHash.user_id }

			totph = Helper.created_at(totph)

			totp_obj = UserTotp(**totph)
			session.add(totp_obj)
		else:
			totp = is_exist.totp



		if int(request_body['auth_type']) == 1:
			flag = Helper.send_mail(result.Users.email,'Email Confirmation | Kore Task','totp',totp)
			if not flag:
				return Helper.construct_response(500,'Mail cannot be sent , try after some time','')

		

		session.commit()

		session.close()

		return Helper.construct_response(200,'OTP Sent','')


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

			

	

@view_config(route_name="check_totp", request_method="POST")
def check_totp(request):
	try:

		request_body = request.json_body

		if not 'totp' in request_body or not 'token' in request_body:
			return Helper.construct_response(400,'Incomplete Data','')

		

		session = Session()

		delete_expired_totps(session)


		result  = session.query(Users,LinkHash,UserTotp)\
		.join(LinkHash,LinkHash.user_id == Users.id)\
		.join(UserTotp,UserTotp.user_id == Users.id)\
		.filter(LinkHash.hash == request_body['token']).first()

		

		if not result:
			return Helper.construct_response(401,'Unauthorized','')


		if result.UserTotp.totp != int(request_body['totp']):
			return Helper.construct_response(401,'OTP incorrect','')


		delete_expired_tokens(session)
		token = user_model.gen_token()

		expiry = datetime.datetime.now()
		expiry = expiry + datetime.timedelta(minutes = 360)
		expiry = expiry.strftime("%Y-%m-%d %H:%M")

		user_token = {
			'user_id' : result.Users.id,
			'token': token,
			'expiry' : expiry		}

		user_token = Helper.created_at(user_token)

		token_obj = UserTokens(**user_token)
		session.add(token_obj)
		code = 200
		message = 'Success'
		response = {'token' : token, 'expiry':expiry}

		delete = session.query(UserTotp).filter(UserTotp.user_id == result.Users.id).delete()

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

		
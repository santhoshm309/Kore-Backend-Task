
from ..constants.helper import Helper
from pyramid.view import view_config
from ..models.user_models import UserModel,Users,UserTokens
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



@view_config(route_name="password_token", request_method=("POST","GET"))
def password_token(request):
	try:
		# for verifying token ..............................................

		if request.method == "GET":
			session = Session()
			delete_expired_totps(session)

			token = dict(request.GET)

			if not 'token' in token:
				session.close()
				return Helper.construct_response(400,'Invalid link','')

			token  = token['token']

			result = session.query(UserTotp).filter(UserTotp.totp == token).filter(UserTotp.type == 1).first()

			if not result:
				session.close()
				return Helper.construct_response(401,'Unauthorized','')

			delete = session.query(UserTotp).filter(UserTotp.user_id == result.user_id).delete()

			session.commit()

			session.close()

			return Helper.construct_response(200,'Success','')

		# For generating token .............................................

		elif request.method == "POST":

			session = Session()

			request_body = request.json_body

			if not 'email' in request_body:
				return Helper.construct_response(400,'Invalid Data','')

			result = session.query(Users).filter(Users.email == request_body['email']).first()

			if not result:
				return Helper.construct_response(404, "User not found", '')			
				
			
			delete_expired_totps(session)

			is_exist = session.query(Users,UserTotp).join(UserTotp,UserTotp.user_id == Users.id).filter(Users.email == request_body['email']).filter(UserTotp.type == 1).first()
			token = ''

			if not is_exist:



				token = user_model.gen_totp()

				expiry = datetime.datetime.now()
				expiry = expiry + datetime.timedelta(minutes = 360)
				expiry = expiry.strftime("%Y-%m-%d %H:%M")

				user_token = {
					'user_id' : result.id,
					'totp': token,
					'expiry' : expiry,
					'type' : 1		
					}

				user_token = Helper.created_at(user_token)

				token_obj = UserTotp(**user_token)
				session.add(token_obj)
				
			else:
				token = is_exist.UserTotp.totp 

			
			flag = Helper.send_mail(result.email,'Change Password | Kore Task','totp','http://localhost:3030/#/password?token='+str(token))
			if not flag:
				return Helper.construct_response(500,'Mail cannot be sent , try after some time','')

			session.commit()
			session.close()	
			return Helper.construct_response(200,'Mail sent to registered email','')



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
		

@view_config(route_name="change_password", request_method="POST")
def change_password(request):
	try:

		request_body  = request.json_body
		session = Session()
		delete_expired_totps(session)

		if not 'token' in request_body or not 'password' in request_body:
			session.close()
			return Helper.construct_response(404, 'Invalid Data','')

	

		existing_token = session.query(UserTotp,Users)\
		.join(Users,Users.id == UserTotp.user_id)\
		.filter(UserTotp.totp == int(request_body['token'])).filter(UserTotp.type == 1).first()

		if not existing_token:
			session.close()
			return Helper.construct_response(401, 'Unauthorized','')


		existing_token.Users.password = bcrypt.hashpw(request_body['password'].encode('utf8'), bcrypt.gensalt())

		session.commit()
		session.close()

		return Helper.construct_response(200,'Password changed successfully','')


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


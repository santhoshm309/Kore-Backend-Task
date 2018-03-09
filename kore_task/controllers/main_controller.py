
from ..constants.helper import Helper
from pyramid.view import view_config
from ..models.user_models import UserModel,Users,LinkHash
import bcrypt
from ..models import Session
from sqlalchemy.exc import DBAPIError
user_model = UserModel()
	
@view_config(route_name='home',request_method="GET")
def home(request):
	return Helper.construct_response(200,"Success",{'message':"Success"})
	


@view_config(route_name='signup', request_method="POST")
def signup(request):
	'''
		Signup API

	'''
	try:
		session = Session()
		request_body = request.json_body

		# Check for correct payload ....................................

		required = {'name','email','password','mobile_no','gender','college','dob'}
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

		# Insert and commit the results ..................................................  

		session.add(user)

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


		return Helper.construct_response(500,'Server Error','')	




@view_config(route_name='verify_email', request_method='GET')
def verify_email(request):
	try:
		link_hash = dict(request.GET)

		session=Session()

		result = session.query(LinkHash,Users).join(Users, Users.id == LinkHash.id)\
						.filter(LinkHash.hash == link_hash['link']).first()

		if not result:
			return Helper.construct_response(404,'Invalid link','')

		if result.Users.is_active == 1:
			return Helper.construct_response(201,'User email already verified')

		result.Users.is_active = 1

		session.commit()

		session.close()

		return Helper.construct_response(200,'Email verified. Redirecting to Login','')	

	except Exception as e:
		print("Server Error ................................." + str(e))
		return Helper.construct_response(500,'Server Error','')	
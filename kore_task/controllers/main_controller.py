from ..constants.helper import Helper
from pyramid.view import view_config
from ..models.user_models import *
import bcrypt
from ..models import Session
from sqlalchemy.exc import DBAPIError

user_model = UserModel()
import jwt
import datetime
from ..constants.constants import Constants
import datetime

constants = Constants()


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
    try:
        session = Session()
        user_model = UserModel()
        # Check payload
        request_body = request.json_body
        if not 'username' in request_body or not 'password' in request_body:
            return Helper.construct_response(400, 'Invalid Data', '')

        result_set = session.query(Users) \
            .filter((Users.email == request_body['username'])).first()

        if not result_set:
            return Helper.construct_response(404, 'User not found', '')

        # Retrive passwords to compare ...................................................

        passw = request_body['password']
        correct = result_set.password

        if not passw == correct:
            return Helper.construct_response(401, 'Unauthorized')

        token = user_model.gen_token();
        expiry = datetime.datetime.now()
        expiry = expiry + datetime.timedelta(minutes=3600)
        expiry = expiry.strftime("%Y-%m-%d %H:%M")

        user_token = {
            'user_id': result_set.id,
            'token': token,
            'expiry': expiry

        }

        user_token = Helper.created_at(user_token)

        user_obj = UserTokens(**user_token)

        session.add(user_obj)

        response = {
            'token': token,
            'expiry': expiry,
            'role': result_set.role

        }

        session.commit()
        session.close()
        return Helper.construct_response(code, message, response)

    except DBAPIError as dbErr:
        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))
        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')


    except Exception as e:

        print("Server Error ................................." + str(e))
        return Helper.construct_response(500, 'Server Error', '')


@view_config(route_name='signout', request_method="POST")
def signout(request):
    try:
        session = Session()

        request_body = request.json_body
        delete_expired_tokens(session)

        # Check payload

        if not 'token' in request_body:
            return Helper.construct_response(400, 'Invalid Data', '')

        result = session.query(UserTokens).filter(UserTokens.token == request_body['token']).first()

        if not result:
            return Helper.construct_response(400, 'Token expired', '')

        session.query(UserTokens).filter(UserTokens.user_id == result.user_id).delete()

        session.commit()
        session.close()

        return Helper.construct_response(200, 'Success', '')



    except DBAPIError as dbErr:
        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))

        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')


    except Exception as e:

        print("Server Error ................................." + str(e))
        return Helper.construct_response(500, 'Server Error', '')


@view_config(route_name='outflows', request_method="POST")
def init(request):
    session = Session()
    try:
        request_body = request.json_body

        if not 'token' in request_body:
            session.close()
            return Helper.construct_response(401, 'Unauthorized')

        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == request_body['token']).first()

        if not user:
            return Helper.construct_response(401, 'Unauthorized')

        # Individual user ..............................................................................

        if user.Users.role == 0:
            all_bills = session.query(UserOutflow).filter(UserOutflow.user_id == user.Users.id).all()
            res = user_model.user_outflows(all_bills)
            session.close()
            return Helper.construct_response(200, '', res)

        if user.Users.role == 1:
            all_bills = session.query()

    except DBAPIError as dbErr:
        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))
        session.close()
        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')


    except Exception as e:
        session.close()
        print("Server Error ................................." + str(e))
        return Helper.construct_response(500, 'Server Error', '')

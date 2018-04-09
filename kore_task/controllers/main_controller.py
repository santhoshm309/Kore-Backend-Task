from sqlalchemy import extract

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
        return Helper.construct_response(200, message, response)

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


def user_of(session, request_body, user):
    all_bills = session.query(UserTransaction).filter(UserTransaction.user_id == user.Users.id).filter(
        extract('month', UserTransaction.dob) == request_body['month']).order_by(
        UserTransaction.dob.asc()).all()
    res = user_model.user_outflows(all_bills, 0) 
    session.close()
    return res


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

        if user.Users.role == 0:
            # For a single user ........................................................
            if not 'month' in request_body:
                session.close()
                return Helper.construct_response(400, 'Invalid Data')
            res = user_of(session, request_body, user)
            res['balance'] = float(user.Users.current)
            session.close()
            return Helper.construct_response(200, 'Success', res)

        if user.Users.role == 1:
            # For admin ..............................
            if not 'user_id' in request_body:
                if not 'month' in request_body:
                    return Helper.construct_response(400, 'Invalid Data')
                else:
                    res = user_of(session, request_body, user)
                    res['balance'] = float(user.Users.current)
                    session.close()
                    return Helper.construct_response(200, 'Success', res)
            elif int(request_body['user_id']) == user.Users.id:
                return Helper.construct_response(400, 'Invalid Data')
            else:
                all_bills = session.query(UserTransaction).filter(
                    UserTransaction.user_id == request_body['user_id']).order_by(UserTransaction.dob.asc()).all()
                res = user_model.user_outflows(all_bills, 1)
                res['balance'] = float(user.Users.current)
                session.close()
                return Helper.construct_response(200, 'Success', res)





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


@view_config(route_name="users", request_method="POST")
def users(request):
    session = Session()
    request_body = request.json_body
    try:
        if not 'token' in request_body:
            return Helper.construct_response(401, 'Unauthorized')

        delete_expired_tokens(session)
        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == request_body['token']).first()

        if not user or user.Users.role == 0:
            return Helper.construct_response(401, 'Unauthorized')

        result_set = session.query(Users).all()

        return Helper.construct_response(200, 'Success', user_model.get_users(result_set))


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


@view_config(route_name="raise_reimbursement_ticket", request_method="POST")
def raise_reimbursement(request):
    session = Session()
    try:

        request_body = request.json_body

        if not 'token' in request_body:
            return Helper.construct_response(401, 'Unauthorized')

        delete_expired_tokens(session)

        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == request_body['token']).first()

        if not user:
            return Helper.construct_response(401, 'Unauthorized')

        if user.Users.role == 1:
            return Helper.construct_response(400, 'Invalid request')

        if float(user.Users.current) >= 0:
            return Helper.construct_response(400, 'Invalid Request')

        existing = session.query(UserReimbursementTicket).filter(
            UserReimbursementTicket.user_id == user.Users.id).first()

        if existing:
            return Helper.construct_response(400, 'Already requested')

        reimbursement = {
            'user_id': user.Users.id,
            'requested_amount': -float(user.Users.current)
        }

        re_obj = UserReimbursementTicket(**reimbursement)

        session.add(re_obj)

        session.commit()

        return Helper.construct_response(200, 'Success')



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


@view_config(route_name='approve_ticket', request_method="POST")
def approve_ticket(request):
    session = Session()

    try:
        request_body = request.json_body

        if not 'token' in request_body:
            session.close()
            return Helper.construct_response(401, 'Unauthorized')

        if not 'amount' in request_body or float(request_body['amount']) <= 0 or not 'user_id' in request_body:
            session.close()
            return Helper.construct_response(400, 'Invalid Data')

        delete_expired_tokens(session)
        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == request_body['token']).first()

        if not user or user.Users.role == 0:
            session.close()
            return Helper.construct_response(401, 'Unauthorized')

        ticket = session.query(UserReimbursementTicket, Users).join(Users,
                                                                    Users.id == UserReimbursementTicket.user_id).filter(
            UserReimbursementTicket.user_id == request_body['user_id']).first()

        if not ticket:
            session.close()
            return Helper.construct_response(404, 'Ticket not raised')

        ticket.UserReimbursementTicket.approved_amount = float(request_body['amount'])
        ticket.UserReimbursementTicket.status = 1

        trans = {
            'user_id': user.Users.id,
            'paid_for': "Reimbursement for - " + ticket.Users.name,
            'amount': request_body['amount'],
            'reason': None,
            'dob': datetime.datetime.now().strftime("%Y-%m-%d")
        }

        trans = Helper.created_at(trans)

        trans_obj = UserTransaction(**trans)

        session.add(trans_obj)

        user.Users.current = float(user.Users.current) - float(request_body['amount'])

        session.commit()

        session.close()

        return Helper.construct_response(200, 'Success')

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

import os
from magic import Magic
from pyramid.response import FileResponse
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError

from kore_task.constants.helper import Helper
from .main_controller import delete_expired_tokens
from ..models import Session
from ..models.user_models import *
from PIL import Image
from io import BytesIO
import PyPDF2 as pyPdf
import datetime

user_model = UserModel()


def delete_file(file_path):
    os.remove(file_path)
    return


@view_config(route_name='capture_bill', request_method="POST")
def capture_bill(request):
    session = Session()
    if not 'token' in request.POST:
        return Helper.construct_response(401, 'Unauthorized User', '')

    token = request.POST['token']

    if not 'paid_for' in request.POST or not 'total_amount' in request.POST or not 'bill' in request.POST or not 'dob' in request.POST:
        return Helper.construct_response(400, 'Invalid data', '')

    paid_for = request.POST['paid_for']
    total_amount = request.POST['total_amount']
    reason = request.POST['reason'] if 'reason' in request.POST else None
    delete_expired_tokens(session)

    user = session.query(UserTokens).filter(UserTokens.token == token).first()

    if not user:
        return Helper.construct_response(401, 'Unauthorized', '')

    file_name = user_model.gen_file_name()

    file_path = os.path.join(os.getcwd(), 'kore_task/files/' + file_name)

    # Check to see if its a valid image file...............................................

    try:
        img = Image.open(BytesIO(request.POST['bill'].file.read()))
        if img.format != "JPEG" and img.format != "PNG":
            raise Exception('Not a valid image format')

        with open(file_path, 'w') as f:
            img.save(f, img.format)

    except Exception as e:
        # Check to see if its a pdf ........................................................

        try:
            pdf = pyPdf.PdfFileReader(request.POST['bill'].file)
            writer = pyPdf.PdfFileWriter()
            for i in range(0, pdf.getNumPages()):
                writer.addPage(pdf.getPage(i))
            with open(file_path, 'wb') as f:
                writer.write(f)

        except Exception as pdfErr:
            print(pdfErr)
            session.close()
            return Helper.construct_response(400, 'Unsupported file', '')

    try:
        # Write to database .................................................................



        user_outflow = {
            'user_id': user.user_id,
            'hash': file_name,
            'bill_url': '/bill/' + file_name,
            'amount': float(total_amount),
            'paid_for': paid_for,
            'reason': reason,
            'dob': datetime.datetime.strptime(request.POST['dob'], "%d/%m/%Y").strftime("%Y-%m-%d %H:%M")
        }
        user_outflow = Helper.created_at(user_outflow)

        obj = UserTransaction(**user_outflow)

        session.add(obj)

        # Subtract from total balance ........................................................

        user = session.query(Users).filter(Users.id == user.user_id).first()

        if not user:
            session.close()
            return Helper.construct_response(401, 'Unauthorized')

        # Updating balance .........................................

        user.current = float(user.current) - float(total_amount)

        session.commit()
        session.close()

    except DBAPIError as dbErr:
        session.close()
        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))
        delete_file(file_path)
        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')

    except Exception as e:
        session.close()
        print(e)
        return Helper.construct_response(500)

    return Helper.construct_response(200, 'Success', '')


@view_config(route_name='view_bill', request_method="POST")
def view_bill(request):
    session = Session()
    try:
        request_body = request.json_body
        if not 'token' in request_body:
            return Helper.construct_response(401, 'Unauthorized')

        token = request_body['token']
        param = request.matchdict['hash']
        delete_expired_tokens(session)
        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == token).first()

        if not user:
            return Helper.construct_response(401, 'Unauthorized')

        hashObj = session.query(UserTransaction).filter(UserTransaction.hash == param).first()

        if user.Users.role == 0 and not hashObj.user_id == user.Users.id:
            return Helper.construct_response(401, 'Unauthorized')

        if not hashObj:
            return Helper.construct_response(404, 'Not found')

        mime = Magic(mime=True)
        mime_type = mime.from_file(os.path.join(os.getcwd(), "kore_task/files/" + param))
        session.close()

        return FileResponse(os.path.join(os.getcwd(), "kore_task/files/" + param), content_type=mime_type)

    except DBAPIError as dbErr:
        session.close()
        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))
        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')


    except Exception as e:
        session.close()
        print(e)
        return Helper.construct_response()


@view_config(route_name='add_money', request_method="POST")
def add_money(request):
    try:
        request_body = request.json_body

        if not 'token' in request_body:
            return Helper.construct_response(401, 'Unauthorized')

        if not 'details' in request_body and not len(request_body['details']) > 0:
            return Helper.construct_response(400, 'Invalid data')

        session = Session()
        delete_expired_tokens(session)
        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(
            UserTokens.token == request_body['token']).first()

        if not user or user.Users.role == 0:
            session.close()
            return Helper.construct_response(401, 'Unauthorized')

        for team in request_body['details']:
            # Admin adding money to his account ............................
            if not 'id' in team or not 'amount' in team:
                session.close()
                return Helper.construct_response(400, 'Invalid data')
            if float(team['amount']) < 0:
                return Helper.construct_response(400, 'Invalid data')
            if team['id'] == user.Users.id:
                user_trans = {
                    'paid_for': user.Users.name,
                    'amount': team['amount'],
                    'type': 1,
                    'dob': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'user_id': user.Users.id,
                    'reason': request_body['reason'] if 'reason' in request_body else None

                }

                user_trans = Helper.created_at(user_trans)

                user_trans_obj = UserTransaction(**user_trans)

                session.add(user_trans_obj)

                user.Users.current = float(user.Users.current) + float(team['amount'])

                session.commit()

            elif team['id'] != user.Users.id:
                paid_for = session.query(Users).filter(Users.id == team['id']).first()

                if not paid_for:
                    session.close()
                    return Helper.construct_response(404, ' Invalid to user ')
                admin_trans = {
                    'paid_for': paid_for.name,
                    'amount': float(team['amount']),
                    'reason': team['reason'] if 'reason' in team else None,
                    'dob': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'user_id': user.Users.id
                }

                admin_trans = Helper.created_at(admin_trans)

                admin_trans_obj = UserTransaction(**admin_trans)

                session.add(admin_trans_obj)

                for_trans = {
                    'paid_for': paid_for.name,
                    'amount': float(team['amount']),
                    'reason': team['reason'] if 'reason' in team else None,
                    'dob': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'type': 1,
                    'user_id': paid_for.id

                }

                for_trans = Helper.created_at(for_trans)

                for_trans_obj = UserTransaction(**for_trans)

                session.add(for_trans_obj)

                user.Users.current = float(user.Users.current) - float(team['amount'])

                paid_for.current = float(paid_for.current) + float(team['amount'])

                session.commit()

        session.close()

        return Helper.construct_response(200, 'Success')

    except DBAPIError as dbErr:

        '''
            SQL error ..................................................................
        '''
        print("MYSQL Error --------------------------------" + str(dbErr.orig))
        # print("MYSQL Error-------------------------" + code,message)
        return Helper.construct_response(500, 'Internal Error', '')


    except Exception as e:

        print(e)
        return Helper.construct_response()



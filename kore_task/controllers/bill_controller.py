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

    # if not 'paid_for' in request.POST or not 'total_amount' in request.POST or not 'reason' in request.POST or not 'bill' in request.POST or not 'dob' in request.POST:
    #     return Helper.construct_response(400, 'Invalid data', '')

    paid_for = "San"
    total_amount = "10000"
    reason = "Test"



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
            return Helper.construct_response(401, 'Unsupported file', '')

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

        obj = UserOutflow(**user_outflow)

        session.add(obj)

        # Subtract from total balance ........................................................

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
        user = session.query(Users, UserTokens).join(UserTokens, UserTokens.user_id == Users.id).filter(UserTokens.token==token).first()


        if not user:
            return Helper.construct_response(401,'Unauthorized')

        hashObj = session.query(UserOutflow).filter(UserOutflow.hash == param).first()

        if user.Users.role == 0 and not hashObj.user_id == user.Users.id :
            return Helper.construct_response(401,'Unauthorized')

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

from pyramid.response import Response
import json
import datetime
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .constants import signup_text, totp_text

class Helper:
    
    @staticmethod
    def construct_response(code=500, message='Unexpected Server Error',
                             response_body=None):
        
        '''
                A function that returns a Pyramid Response Object
                Note : Use json_body instead of body in response objects
                    
        '''
        
        
        data = {
            'code' : code,
            'message' : message,
            'data' : response_body
            }
        data_bytes = json.dumps(data)
        return Response(json_body=data, status=code, content_type='application/json')
    
    @staticmethod
    def created_at(object):
        

        '''
                A function to append time stamp details to mysql insert object
        '''

        now = datetime.datetime.now()
        created_at = now.strftime("%Y-%m-%d %H:%M")
        object['created_at'] = created_at     
        return object


    @staticmethod
    def send_mail(recipient, subject,t,text):

        FROM = 'kore.task19@gmail.com'
        TO = recipient if type(recipient) is list else [recipient]
        SUBJECT = subject
        TEXT = signup_text() % text if t is 'signup' else totp_text() % text


        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, ", ".join(TO), SUBJECT, TEXT)


        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login('kore.task19@gmail.com','madhu143')
            server.sendmail(FROM, TO, message)
            server.close()
            return True
        except Exception as e:
            print("Mail Error ................................................." + str(e))
            return False
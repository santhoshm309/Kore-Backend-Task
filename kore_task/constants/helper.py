from pyramid.response import Response
import json
import datetime

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

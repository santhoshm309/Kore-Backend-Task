from . import Base, Session
from sqlalchemy.orm import relationship
import random, string
import bcrypt

BASE_URI = 'https://server.kirana-pyramid.tk'


class Users(Base):
    __tablename__ = 'Users'
    __table_args__ = {'autoload': True}
    user_totp = relationship('UserTotp', cascade='all,delete', backref='Users')
    user_tokens = relationship('UserTokens', cascade='all,delete', backref='Users')


class UserTotp(Base):
    __tablename__ = 'UserTotp'
    __table_args__ = {'autoload': True}


class UserTokens(Base):
    __tablename__ = 'UserTokens'
    __table_args__ = {'autoload': True}


class UserTransaction(Base):
    __tablename__ = 'UserTransaction'
    __table_args__ = {'autoload': True}


class UserReimbursementTicket(Base):
    __tablename__ = 'UserReimbursementTicket'
    __table_args__ = {'autoload': True}


class UserModel:
    def get_users(self, result_set):
        res = []
        for result in result_set:
            user = {
                'id' : result.id,
                'name' : result.name
            }

            res.append(user)
        return res

    def get_user_obj(self, request_body):
        return {
            'name': request_body['name'],
            'email': request_body['email'],
            'password': bcrypt.hashpw(request_body['password'].encode('utf8'), bcrypt.gensalt()),
            'dob': request_body['dob'],
            'mobile_no': int(request_body['mobile_no']),
            'gender': int(request_body['gender']),
            'college': request_body['college']

        }

    def random_hash(self, type):
        if type == 0:
            return ''.join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        else:
            return ''.join(["%s" % random.randint(0, 9) for num in range(0, 6)])  # Get 6 digit totp

    def gen_totp(self):
        session = Session()
        while True:
            totp = self.random_hash(1)
            result = session.query(UserTotp).filter(UserTotp.totp == totp).all()
            session.close()
            if len(result) > 0:
                totp = self.random_hash(1)
            else:
                return totp

    def gen_token(self):
        session = Session()
        while True:
            token = self.random_hash(0)
            result = session.query(UserTokens).filter(UserTokens.token == token).all()
            session.close()
            if len(result) > 0:
                token = self.random_hash(0)
            else:
                return token

    def gen_file_name(self):
        session = Session()
        while True:
            filename = self.random_hash(0)
            result = session.query(UserTransaction).filter(UserTransaction.hash == filename).first()
            if not result:
                return filename

    def user_outflows(self, result_set, flag):

        response_body = {}
        for result in result_set:
            outflow = {
                'reason': result.reason if result.reason else None,
                'paid_for': result.paid_for,
                'dob': result.dob.strftime("%d/%m/%Y"),
                'id': result.id,
                'bill_url': BASE_URI + result.bill_url if result.bill_url else None,
                'amount': float(result.amount),
                'upload_date': result.created_at.strftime("%d/%m/%Y"),
                'type': result.type
            }
            month = 'month' if flag == 0 else result.dob.strftime("%B")
            if not month in response_body:
                response_body[month] = {}
                response_body[month]['outflows'] = []
                response_body[month]['outflows'].append(outflow)
                response_body[month]['spent'] = float(result.amount) if result.type == 0 else 0

                response_body[month]['earned'] = float(result.amount) if result.type == 1 else 0


            else:

                response_body[month]['outflows'].append(outflow)
                if result.type == 0:
                    response_body[month]['spent'] += float(result.amount)
                if result.type == 1:
                    response_body[month]['earned'] += float(result.amount)

        return response_body

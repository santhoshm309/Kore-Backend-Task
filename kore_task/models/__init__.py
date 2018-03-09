
from sqlalchemy import create_engine
from ..constants.constants import Constants
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import sessionmaker

'''
        Initialize DB base object, engine, metadata
   ##########################################################     
'''
constant = Constants()
engine = create_engine(constant.get_env_config('test'), pool_recycle=100)
metadata = MetaData(bind=engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)
print("Db Connection Successfull")

def includeme(config):
    pass

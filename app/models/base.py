from sqlalchemy.orm import DeclarativeBase

'''
Base model to connect with the databases
This creates a shared metadata that registers al children models
Each model establishes a Python object that is mapped to the database table
'''
class Base(DeclarativeBase):
    pass
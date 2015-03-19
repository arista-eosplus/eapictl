import os

HERE = os.path.abspath(os.path.dirname(__file__))

def fixtures_path():
    return os.path.join(HERE, '../fixtures')

def get_fixture(name):
    return os.path.join(fixtures_path(), name)




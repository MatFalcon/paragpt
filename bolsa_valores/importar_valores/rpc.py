import os

from configparser import ConfigParser
import xmlrpc.client

os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')

XMLRPC_CONFIG = {
    'HOST': config['xmlrpc']['host'],
    'PORT': config['xmlrpc']['port'],
    'DB': config['xmlrpc']['db'],
    'USER': config['xmlrpc']['user'],
    'PWD': config['xmlrpc']['pwd'],
}


class XMLRPC():
    def __init__(self):
        self.uid = None
        self.models = None

    def setup(self):
        url = f'{XMLRPC_CONFIG["HOST"]}:{XMLRPC_CONFIG["PORT"]}'
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.uid = common.authenticate(XMLRPC_CONFIG['DB'], XMLRPC_CONFIG['USER'], XMLRPC_CONFIG['PWD'], {})
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def execute_kw(self, *args):
        return self.models.execute_kw(XMLRPC_CONFIG['DB'], self.uid, XMLRPC_CONFIG['PWD'], *args)

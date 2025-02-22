from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
}

XMLRPC_CONFIG = {
    'HOST': config['xmlrpc']['host'],
    'PORT': config['xmlrpc']['port'],
    'DB': config['xmlrpc']['db'],
    'USER': config['xmlrpc']['user'],
    'PWD': config['xmlrpc']['pwd'],
}
print(SQL_SERVER_CONFIG)

print(XMLRPC_CONFIG)






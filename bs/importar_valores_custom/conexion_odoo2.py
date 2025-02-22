import os
from configparser import ConfigParser
import xmlrpc.client

os.chdir(os.path.dirname(__file__))
# se obtiene las credenciales para las bases de datos

XMLRPC_CONFIG = {
    'HOST': "http://localhost",
    'PORT': "8069",
    'DB': "bolsa2",
    'USER': "admin",
    'PWD': "3capzadmin",
}
print("Conexion odoo")
print(XMLRPC_CONFIG)


class OdooXMLRPCClient:
    """
    Cliente XML-RPC para interactuar con Odoo.
    """
    def __init__(self):
        self.uid = None #usuario autenticado
        self.models = None # modelos odoo


    def setup(self):
        """
                Configura la conexión XML-RPC con Odoo y autentica al usuario.
        """
        url = f'{XMLRPC_CONFIG["HOST"]}:{XMLRPC_CONFIG["PORT"]}'
        # se crea la conexion (aparentemente utilizando un endpoint standar de odoo)
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        # common.authenticate obtiene el uid de sesion de usuario que permite las operaciones crud
        self.uid = common.authenticate(XMLRPC_CONFIG['DB'], XMLRPC_CONFIG['USER'], XMLRPC_CONFIG['PWD'], {})

        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # este es el metodo que se usa en los demas scripts por ejemplo importar valores para hacer las llamadas al odoo
    # se puede ejecutar metodos de modelos
    # en importar_sen por ejemplo
    # if novedades:
    #     xr.execute_kw('pbp.novedades_sen', 'write', [novedades, obj]) <--- metodo write del modelo pnp.noveddes_sen
    def execute_kw(self, *args):
        """
                Ejecuta métodos en los modelos de Odoo.

                Args:
                    *args: Argumentos para la llamada execute_kw de Odoo.

                Returns:
                    Resultado de la ejecución del método en Odoo.
        """
        return self.models.execute_kw(XMLRPC_CONFIG['DB'], self.uid, XMLRPC_CONFIG['PWD'], *args)

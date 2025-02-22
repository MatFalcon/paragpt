import os
import jaydebeapi
from configparser import ConfigParser


# lee las configuraciones para sql en el archivo config ini
config = ConfigParser()
config.read('config.ini')
SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
    'DB': config['sqlserver']['db']
}
print(SQL_SERVER_CONFIG)
# Configura los detalles de conexión
url = f"jdbc:sqlserver://{SQL_SERVER_CONFIG['HOST']};encrypt=true;trustServerCertificate=true"
driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
jar_file = "/home/user/Escritorio/EntornosClientes/odoo17/Bolsa/importar_valores/mssql-jdbc-12.8.1.jre11.jar"  # O jre8 si tienes Java 8
user = "sati"
password = "D1@8I1$W9\\mt"
def conectar_base_sql():

    try:
        # Conexión a la base de datos
        conn = jaydebeapi.connect(driver, url, [user, password], jar_file)

        # Crear un cursor y ejecutar una consulta
        #cursor = conn.cursor()

        # cursor.execute("select TOP 1 * from Bvpasa_Publicacion.Registro.vValores ;")
        # result = cursor.fetchall()
        #
        # print("Resultado de la consulta:")
        # for row in result:
        #     print(row[6])
        #
        # # Cerrar la conexión
        # cursor.close()
        # conn.close()
        return conn
    except Exception as e:
        print(f"Error: {e}")
        return False

def conectar_base_elejir(base):
    try:
        # Conexión a la base de datos
        url_con_base = (url + f';databaseName={base};')
        print("URL Personalizada")
        print(url_con_base)
        conn = jaydebeapi.connect(driver, url_con_base, [user, password], jar_file)

        # Crear un cursor y ejecutar una consulta
        #cursor = conn.cursor()

        # cursor.execute("select TOP 1 * from Bvpasa_Publicacion.Registro.vValores ;")
        # result = cursor.fetchall()
        #
        # print("Resultado de la consulta:")
        # for row in result:
        #     print(row[6])
        #
        # # Cerrar la conexión
        # cursor.close()
        # conn.close()
        return conn
    except Exception as e:
        print(f"Error: {e}")
        return False
import jaydebeapi

# Configura los detalles de conexión
url = "jdbc:sqlserver://192.168.210.60:1433;databaseName=master;encrypt=true;trustServerCertificate=true"
driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
jar_file = "/home/user/Escritorio/EntornosClientes/odoo17/Bolsa/importar_valores/mssql-jdbc-12.8.1.jre11.jar"  # O jre8 si tienes Java 8
user = "sati"
password = "D1@8I1$W9\\mt"

try:
    # Conexión a la base de datos
    conn = jaydebeapi.connect(driver, url, [user, password], jar_file)

    # Crear un cursor y ejecutar una consulta
    cursor = conn.cursor()
    cursor.execute("select TOP 1 * from Bvpasa_Publicacion.Registro.vValores ;")
    result = cursor.fetchall()

    print("Resultado de la consulta:")
    for row in result:
        print(row[6])

    # Cerrar la conexión
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")

from configparser import ConfigParser
import datetime
import dateutil.relativedelta
from decimal import Decimal
import os


from conexion_odoo import OdooXMLRPCClient
from conexion_sql import conectar_base_sql, conectar_base_elejir
os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config_test.ini')

# SQL_SERVER_CONFIG = {
#     'HOST': config['sqlserver']['host'],
#     'USER': config['sqlserver']['user'],
#     'PWD': config['sqlserver']['pwd'],
# }

xr = OdooXMLRPCClient()
xr.setup()


today = datetime.datetime.now()
from_date = today.replace(hour=0, minute=0)
from_date = from_date.strftime('%Y-%m-%d %H:%M')

to_date = today.replace(hour=23, minute=59)
to_date = to_date.strftime('%Y-%m-%d %H:%M')

#from_date = "2025-02-01 00:00"
#to_date = "2025-03-28 23:59"
print("Inicio", from_date)
print("Fin", to_date)


LOTE_ENVIO = 200


def sincronizar_transferencia_cartera():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_transferencia_cartera_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")

        enviar_transferencia_cartera_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_transferencia_cartera_desde_BD():
    """
    Obtenemos los datos de desde la base de datos. Dejamos todo en memoria
    """
    conn = conectar_base_elejir("Bvpasa_Clearing")
    cursor = conn.cursor()

    cursor.execute(
        "select MensajeID, MensajeCodigo, Fecha, CuentaOrigen, CuentaDestino, "
        f"Mensajes.vMensajesTransferenciasEntreComitentes.Observaciones, "
        f"C.MiembroCompensadorID as Origen, D.MiembroCompensadorID as Destino, "
        f"E.PersonaID as PersonaOrigen, F.PersonaID as PersonaDestino, "
        f"C.CuentaCompensacionDescripcion as CompensacionOrigen, "
        f"A.CuentaNeteoDescripcion as NeteoOrigen, "
        f"D.CuentaCompensacionDescripcion as CompensacionDestino, "
        f"B.CuentaNeteoDescripcion as NeteoDestino "
        f"from Mensajes.vMensajesTransferenciasEntreComitentes "
        f"LEFT JOIN Personas.CuentaNeteo A on A.CuentaNeteoCodigo = CuentaOrigen "
        f"LEFT JOIN Personas.CuentaNeteo B on B.CuentaNeteoCodigo = CuentaDestino "
        f"LEFT JOIN Personas.CuentaCompensacion C on C.CuentaCompensacionID = A.CuentaCompensacionID "
        f"LEFT JOIN Personas.CuentaCompensacion D on D.CuentaCompensacionID = B.CuentaCompensacionID "
        f"LEFT JOIN Personas.MiembroCompensador E on E.MiembroCompensadorID = C.MiembroCompensadorID "
        f"LEFT JOIN Personas.MiembroCompensador F on F.MiembroCompensadorID = D.MiembroCompensadorID "
        f"WHERE Fecha >= '{from_date}' AND fecha <= '{to_date}' "
        'ORDER BY Fecha DESC;'
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:
        print(r)
        id_pbp = r['MensajeID']
        fecha = datetime.datetime.strptime(r['Fecha'], "%Y-%m-%d")
        fecha = fecha.strftime("%Y-%m-%d")
        emisor_id = r['PersonaOrigen']
        receptor_id = r['PersonaDestino']
        motivo = r['Observaciones']
        obj = {
            'id_pbp': int(id_pbp),
            'receptor_id': int(receptor_id),
            'emisor_id': int(emisor_id),
            'motivo': motivo,
            'fecha': fecha,
            # 'monto': row['monto'],
        }
        objects.append(obj)
    return objects


def enviar_transferencia_cartera_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.transferencia_cartera', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_transferencia_cartera()

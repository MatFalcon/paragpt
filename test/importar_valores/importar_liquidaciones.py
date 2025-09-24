from configparser import ConfigParser
import datetime
import dateutil.relativedelta
from decimal import Decimal
import os

import pyodbc

from rpc import XMLRPC

os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')

SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
}

xr = XMLRPC()
xr.setup()

today = datetime.datetime.now()
fecha_vencimiento = today.replace(hour=0, minute=0)
fecha_vencimiento = fecha_vencimiento.strftime('%Y-%m-%d %H:%M')

LOTE_ENVIO = 200


def sincronizar_liquidaciones():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_liquidaciones_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_liquidaciones_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_liquidaciones_desde_BD():
    """
    Obtenemos los datos de desde la base de datos. Dejamos todo en memoria
    """
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={SQL_SERVER_CONFIG["HOST"]};'
        f'DATABASE=Bvpasa_Clearing;'
        f'UID={SQL_SERVER_CONFIG["USER"]};'
        f'PWD={SQL_SERVER_CONFIG["PWD"]};'
        'ENCRYPT=no;'
    )
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT EventoCorporativoFecha, "
        f"Personas.Emisor.EmisorDescripcion, "
        f"MonedaID, "
        f"Vista_EECC.ActivoDescripcion, Vista_EECC.ActivoID, Vista_EECC.TotalSerie, "
        f"Personas.Emisor.PersonaID "
        f"FROM Vista_EECC "
        f"INNER JOIN Activos.Activo ON Activo.ActivoID = Vista_EECC.ActivoID "
        f"INNER JOIN Productos.vReporteSeries ON Activo.ActivoDescripcion = vReporteSeries.CodNegociacion "
        f"INNER JOIN Personas.Emisor ON Productos.vReporteSeries.EmisorDescripcion = Personas.Emisor.EmisorDescripcion "
        f"WHERE EventoCorporativoFecha = '{fecha_vencimiento}' "
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:
        obj = {
            'id_pbp': r.get('ActivoID'),
            'moneda_id': r.get('MonedaID'),
            'cliente_id': r.get('PersonaID'),
            'monto': r.get('TotalSerie'),
            'fecha_vencimiento': r.get('EventoCorporativoFecha').strftime('%Y-%m-%d') if r.get('EventoCorporativoFecha') else False,
            'serie': r.get('ActivoDescripcion'),
        }
        objects.append(obj)
    return objects


def enviar_liquidaciones_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.liquidaciones', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_liquidaciones()

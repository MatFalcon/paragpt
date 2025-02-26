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
from_date = today.replace(hour=0, minute=0)
from_date = from_date.strftime('%Y-%m-%d %H:%M')
#from_date = "2023-09-01"

to_date = today.replace(hour=23, minute=59)
to_date = to_date.strftime('%Y-%m-%d %H:%M')
#to_date = "2023-08-31"

LOTE_ENVIO = 200


def sincronizar_control_pago():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_control_pago_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_control_pago_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_control_pago_desde_BD():
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
        "select vista_Control_Pagos.*, Personas.Emisor.PersonaID as EmisorID, Personas.MiembroCompensador.PersonaID as MiembroCompensadorID "
        "from dbo.vista_Control_Pagos vista_Control_Pagos "
        "LEFT JOIN Personas.Emisor on Personas.Emisor.EmisorDescripcion = vista_Control_Pagos.EmisorDescripcion "
        "LEFT JOIN Personas.MiembroCompensador on Personas.MiembroCompensador.MiembroCompensadorDescripcion = vista_Control_Pagos.MiembroCompensadorDescripcion "
        f"where EventoCorporativoFecha >= '{from_date}' and EventoCorporativoFecha <= '{to_date}' "
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
            'emisor_id_sis': r.get("EmisorID"),
            'miembro_compensador_id_sis': r.get('MiembroCompensadorID'),
            'moneda_id': r.get('MonedaDescripcion'),
            'fecha': r.get('EventoCorporativoFecha').strftime('%Y-%m-%d') if r.get('EventoCorporativoFecha') else False,
            'importe_total': r.get('Total_Importe')
        }
        objects.append(obj)
    return objects


def enviar_control_pago_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.control_pagos', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_control_pago()

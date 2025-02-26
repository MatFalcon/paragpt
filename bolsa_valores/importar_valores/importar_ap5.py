from configparser import ConfigParser
import datetime
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

to_date = today.replace(hour=23, minute=59)
to_date = to_date.strftime('%Y-%m-%d %H:%M')

LOTE_ENVIO = 200


def sincronizar_operacion_futuro():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_operacion_futuro_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_operacion_futuro_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_operacion_futuro_desde_BD():
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
        "select * from Registro.vOperaciones "
        "where TipoContratoDescripcion = 'Futuro' "
        f"and Fecha >= '{from_date}' and Fecha <= '{to_date}' "
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
            'operacion_cartera_id' : r.get('OperacionCarteraID'),
            'mercado': r.get('TipoContratoDescripcion'),
            'fecha': r.get('Fecha').strftime('%Y-%m-%d'),
            'precio': r.get('Precio'),
            'cantidad': r.get('Cantidad'),
            'importe': r.get('Cantidad') * r.get('Precio'),
            'producto_descripcion':  r.get('ProductoDescripcion'),
            'currency_id':  False,
            'miembro_compensador_id': r.get('MiembroCompensadorCodigo'),
            'cuenta_registro_cod': r.get('CuentaRegistroCodigo'),
            'contrato': r.get('ContratoDescripcion'),
            'volumen': r.get('Volumen'),
            'tipo_operacion': r.get('TipoOperacionDescripcion'),
            'hora_ingreso': r.get('HoraIngreso').strftime("%H:%M:%S"),
            'proceso_descripcion': r.get('ProcesoDescripcion'),
            'fecha_liquidacion_contrato': r.get('FechaLiquidacionContrato').strftime('%Y-%m-%d')
        }
        objects.append(obj)
    return objects


def enviar_operacion_futuro_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.operacion_futuro', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_operacion_futuro()

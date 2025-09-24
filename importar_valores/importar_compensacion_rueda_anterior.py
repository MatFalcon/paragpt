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
#from_date = "2023-08-01"

to_date = today.replace(hour=23, minute=59)
to_date = to_date.strftime('%Y-%m-%d %H:%M')
#to_date = "2023-07-31"

LOTE_ENVIO = 200


def sincronizar_compensacion_rueda_anterior():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_compensacion_rueda_anterior_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_compensacion_rueda_anterior_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_compensacion_rueda_anterior_desde_BD():
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
        "select Compensacion_RuedaAnterior.*, COALESCE(Personas.Emisor.PersonaID, MC.PersonaID) AS BeneficiarioID "
        "from dbo.Compensacion_RuedaAnterior Compensacion_RuedaAnterior "
        "LEFT JOIN Personas.Emisor on Personas.Emisor.EmisorDescripcion = Compensacion_RuedaAnterior.Beneficiario "
        "LEFT JOIN Personas.MiembroCompensador MC on MC.MiembroCompensadorDescripcion = Compensacion_RuedaAnterior.Beneficiario "
        f"where Fecha >= '{from_date}' and Fecha <= '{to_date}' "
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
            'beneficiario_id': r.get('BeneficiarioID'),
            'fecha': r.get('Fecha').strftime('%Y-%m-%d') if r.get('Fecha') else False,
            'importe_gs': r.get('ImporteGs'),
            'importe_usd': r.get('ImporteUSD'),
            'cuenta_usd': r.get('CuentaUSD'),
            'cuenta_gs': r.get('CuentaGS'),
            'segmento_mercado': r.get('SegmentoMercado'),
            'tcero': False
        }
        objects.append(obj)
    return objects


def enviar_compensacion_rueda_anterior_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.compensacion_rueda_anterior', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_compensacion_rueda_anterior()

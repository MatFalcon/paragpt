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


def sincronizar_reporte_series():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_reporte_series_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_reporte_series_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_reporte_series_desde_BD():
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
        "select Productos.vReporteSeries.*, Personas.Emisor.PersonaID, EmisorCodigo, MonedaID from Productos.vReporteSeries "
        f"JOIN Personas.Emisor on Personas.Emisor.EmisorDescripcion = Productos.vReporteSeries.EmisorDescripcion "
        f"JOIN General.Moneda on General.Moneda.MonedaDescripcion = Productos.vReporteSeries.MonedaDescripcion;"
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:
        if r.get('FechaColocacion'):
            inicio_colocacion = r.get('FechaColocacion').strftime('%Y-%m-%d')
        else:
            inicio_colocacion = False
        if r.get('FechaVencimiento'):
            fecha_vencimiento = r.get('FechaVencimiento').strftime('%Y-%m-%d')
        else:
            fecha_vencimiento = False
        if fecha_vencimiento and inicio_colocacion:
            plazo = r.get('FechaVencimiento') - r.get('FechaColocacion')
            plazo = plazo.days
        else:
            plazo = 0
        obj = {
            'name': r.get('CodNegociacion'),
            'cod_emisor': r.get('EmisorCodigo'),
            'monto_original': r.get('MontoEmisionTotal'),
            'inicio_colocacion': inicio_colocacion,
            'fecha_vencimiento': fecha_vencimiento,
            'moneda_id': r.get('MonedaID'),
            'instrumento': r.get('Instrumento'),
            'tasa_instrumento': r.get('TasaInteresNominal'),
            'emisor_id': r.get('PersonaID'),
            'plazo': plazo
        }
        objects.append(obj)
    return objects


def enviar_reporte_series_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('emisiones.series', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_reporte_series()

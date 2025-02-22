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


def sincronizar_sen(table):
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_sen_desde_BD(table)

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_sen_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_sen_desde_BD(table):
    """
    Obtenemos los datos de desde la base de datos. Dejamos todo en memoria
    """

    date_field = 'FechaEmision'
    if table in ('SerieRentaFija', 'SerieRentaVariableAccion'):
        date_field += 'Serie'
    else:
        date_field += 'FondoInversion'

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
        'SELECT DISTINCT '
        f'Productos.{table}.*, '
        'Productos.vContrato.ContratoDescripcion, '
        'Productos.vContrato.MonedaCotizacionID, '
        'Productos.vContrato.TipoContratoCodigo, '
        'Productos.vContrato.TipoContratoDescripcion, '
        'Personas.Emisor.EmisorDescripcion, '
        'Personas.Emisor.PersonaID, '
        'Productos.Emision.EmisorID, '
        'Productos.Emision.MontoEmision, '
        'Productos.vReporteSeries.Instrumento '
        f'FROM Productos.{table} '
        f'LEFT JOIN Productos.vContrato ON Productos.{table}.ContratoID = Productos.vContrato.ContratoID '
        f'LEFT JOIN Productos.Emision ON Productos.{table}.EmisionID = Productos.Emision.EmisionID '
        'LEFT JOIN Personas.Emisor ON Productos.Emision.EmisorID = Personas.Emisor.EmisorID '
        'LEFT JOIN Productos.vReporteSeries ON Productos.vReporteSeries.EmisionCodigo = Productos.Emision.EmisionCodigo '
        f"WHERE Productos.{table}.{date_field} >= '{from_date}' AND Productos.{table}.{date_field} <= '{to_date}'"
        f'ORDER BY Productos.{table}.{date_field} DESC;'
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:

        date_field = 'FechaEmision'
        if table in ('SerieRentaFija', 'SerieRentaVariableAccion'):
            date_field += 'Serie'
        else:
            date_field += 'FondoInversion'

        fecha_emision = r.get('FechaEmisionSerie')
        if not fecha_emision:
            fecha_emision = r.get('FechaEmisionFondoInversion')

        fecha_vencimiento = r.get('FechaVencimiento')
        if not fecha_vencimiento:
            fecha_vencimiento = r.get('FechaMaximaColocacion')

        if fecha_vencimiento.year > fecha_emision.year:
            if fecha_vencimiento.year == 2023:
                fecha_emision = datetime.date(fecha_vencimiento.year, 1, 1)
            elif fecha_vencimiento.year > 2023:
                fecha_emision = False

        fecha_vencimiento = fecha_vencimiento.strftime('%Y-%m-%d')
        if fecha_emision:
            fecha_emision = fecha_emision.strftime('%Y-%m-%d')

        obj = {
            'emisor_descripcion': r.get('EmisorDescripcion'),
            'emisor_id': r.get('EmisorID'),
            'cod_negociacion': r.get('ContratoDescripcion'),
            'tipo_contrato_descripcion': r.get('TipoContratoDescripcion'),
            'tipo_contrato_codigo': r.get('TipoContratoCodigo'),
            'contrato_descripcion': r.get('ContratoDescripcion'),
            'contrato_id': r.get('ContratoID'),
            'currency_id': 2 if r.get('MonedaCotizacionID') == 'Dólar' else 155,
            'persona_id': r.get('PersonaID'),
            'instrumento': r.get('Instrumento'),
            'fecha_emision': fecha_emision,
            'fecha_inicial': fecha_emision,
            'fecha_vencimiento': fecha_vencimiento,
            'monto_emitido': r.get('MontoEmision'),
            'cantidad_emitida': r.get('Cantidad'),
            'partner_id': False,
            'product_id': 165,
        }
        objects.append(obj)
    return objects


def enviar_sen_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.novedades_sen', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_sen('SerieRentaFija')
    sincronizar_sen('SerieRentaVariableAccion')
    sincronizar_sen('FondoInversion')
    xr.execute_kw('pbp.novedades_sen', 'calcular_valores', [False])
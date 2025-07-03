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


def get_registros(table):
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={SQL_SERVER_CONFIG["HOST"]};'
        f'DATABASE=Bvpasa_Clearing;'
        f'UID={SQL_SERVER_CONFIG["USER"]};'
        f'PWD={SQL_SERVER_CONFIG["PWD"]};'
        'ENCRYPT=no;'
    )
    cursor = conn.cursor()

    date_field = 'FechaEmision'
    if table in ('SerieRentaFija', 'SerieRentaVariableAccion'):
        date_field += 'Serie'
    else:
        date_field += 'FondoInversion'

    today = datetime.date.today()
    #from_date = today.strftime('%Y-%m-%d')
    #prev_month = today - dateutil.relativedelta.relativedelta(months=1)
    #from_date = prev_month.replace(day=26)
    #from_date = from_date.strftime('%Y-%m-%d')

    prev_month = today - dateutil.relativedelta.relativedelta(months=1)
    from_date = prev_month.replace(day=26)
    from_date = from_date.strftime('%Y-%m-%d')
    #from_date = '2010-09-26'
    #from_date = '2023-04-26'
    #from_date = '2010-09-26'

    #to_date = today - dateutil.relativedelta.relativedelta(months=2)
    to_date = today.replace(day=25)
    to_date = to_date.strftime('%Y-%m-%d')
    #to_date = '2023-03-25'
    #to_date = '2023-05-25'


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
        f"WHERE Productos.{table}.{date_field} >= '{from_date}' AND Productos.{table}.{date_field} <= '{to_date}' AND Personas.Emisor.PersonaID = 20"
        f'ORDER BY Productos.{table}.{date_field} DESC;'
    )
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    print(len(results))
    return results


def create_novedades(registros, table):
    for row in registros:
        try:
            create_novedad(row, table)
        except Exception as error:
            print(f'Error: {error}')


def create_novedad(row, table):
    contrato_id = row['ContratoID']
    novedades = xr.execute_kw('pbp.novedades_sen', 'search', [[['contrato_id', '=', contrato_id]]])

    persona_id = row['PersonaID']
    partner_ids = xr.execute_kw('res.partner', 'search', [[['id_cliente_pbp', '=', persona_id]]])
    partner_id = partner_ids[0] if partner_ids else False

    """
    vat = row['CuitCuil']
    if vat:
        vat = vat.strip()
    if vat:
        partner_ids = xr.execute_kw('res.partner', 'search', [[['vat', '=', vat]]])
        partner_id = partner_ids[0] if partner_ids else False
    """

    tipo_contrato_descripcion = row['TipoContratoDescripcion']
    product_id = 165
    """
    if tipo_contrato_descripcion == 'Fondo Inversión':
        product_id = 190
        #product_name = 'Fondo de Inversión'
    elif tipo_contrato_descripcion == 'Serie Renta Fija':
        product_id = 153
        #product_name = 'Arancel CBSA por Rentas Fijas - S.E.N'
        #product_id = 155
        #product_name = 'Arancel por Repos'
    elif tipo_contrato_descripcion == 'Serie Renta Variable Acción':
        product_id = 154
        #product_name = 'Arancel CBSA por Rentas Variables - S.E.N'
    #product_ids = xr.execute_kw('product.product', 'search', [[['name', '=', product_name]]], {'context': {'lang': 'es_PY'}})
    #product_id = product_ids[0] if product_ids else False
    """

    moneda_cotizacion_id = row['MonedaCotizacionID']
    """
    if moneda_cotizacion_id == 1:
        currency_name = 'PYG'
    else:
        currency_name = 'USD'
    currency_id = xr.execute_kw('res.currency', 'search', [[['name', '=', currency_name]]])[0]
    """
    if moneda_cotizacion_id == 1:
        currency_id = 155
    elif moneda_cotizacion_id == 2:
        currency_id = 2
    else:
        return

    date_field = 'FechaEmision'
    if table in ('SerieRentaFija', 'SerieRentaVariableAccion'):
        date_field += 'Serie'
    else:
        date_field += 'FondoInversion'

    fecha_emision = row.get('FechaEmisionSerie')
    if not fecha_emision:
        fecha_emision = row.get('FechaEmisionFondoInversion')

    fecha_vencimiento = row.get('FechaVencimiento')
    if not fecha_vencimiento:
        fecha_vencimiento = row.get('FechaMaximaColocacion')

    if fecha_vencimiento.year > fecha_emision.year:
        if fecha_vencimiento.year == 2023:
            fecha_emision = datetime.date(fecha_vencimiento.year, 1, 1)
        elif fecha_vencimiento.year > 2023:
            fecha_emision = False
    elif novedades:
        return False

    fecha_vencimiento = fecha_vencimiento.strftime('%Y-%m-%d')
    if fecha_emision:
        fecha_emision = fecha_emision.strftime('%Y-%m-%d')

    obj = {
        'emisor_descripcion': row['EmisorDescripcion'],
        'emisor_id': row['EmisorID'],
        'cod_negociacion': row['ContratoDescripcion'],
        'tipo_contrato_descripcion': tipo_contrato_descripcion,
        'tipo_contrato_codigo': row['TipoContratoCodigo'],
        'contrato_descripcion': row['ContratoDescripcion'],
        'contrato_id': contrato_id,
        'currency_id': currency_id,
        'persona_id': persona_id,
        'instrumento': row['Instrumento'],
        'fecha_emision': fecha_emision,
        'fecha_inicial': fecha_emision,
        'fecha_vencimiento': fecha_vencimiento,
        'monto_emitido': row['MontoEmision'],
        'cantidad_emitida': row['Cantidad'],
        'partner_id': partner_id,
        'product_id': product_id,
    }

    if novedades:
        xr.execute_kw('pbp.novedades_sen', 'write', [novedades, obj])
        print(f'NOVEDAD UPDATED: {novedades[0]} {obj}')
    else:
        id = xr.execute_kw('pbp.novedades_sen', 'create', [obj])
        print(f'NOVEDAD CREATED: {id} {obj}')


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return False
    return value


def sync_novedades(table):
    valores = get_registros(table)
    create_novedades(valores, table)


if __name__ == '__main__':
    sync_novedades('SerieRentaFija')
    sync_novedades('SerieRentaVariableAccion')
    sync_novedades('FondoInversion')
    xr.execute_kw('pbp.novedades_sen', 'calcular_valores', [False])

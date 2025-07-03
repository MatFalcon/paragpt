from configparser import ConfigParser
import datetime
import dateutil.relativedelta
from decimal import Decimal
import os

import mariadb
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


def get_miembros_compensadores():
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
        'SELECT DISTINCT *, '
        'Personas.vReporteMiembrosCompensadores.Email, '
        'Personas.vReporteMiembrosCompensadores.Domicilio, '
        'Personas.vReporteMiembrosCompensadores.Localidad, '
        'Personas.vReporteMiembrosCompensadores.Telefono, '
        'Personas.vReporteMiembrosCompensadores.[Razón Social / Apellido] '
        'FROM Personas.vCuentaFacturacion '
        'LEFT JOIN Personas.vReporteMiembrosCompensadores '
        'ON Personas.vCuentaFacturacion.MiembroCompensadorID = Personas.vReporteMiembrosCompensadores.MiembroCompensadorID; '
    )
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    return results


def get_registros():
    conn = mariadb.connect(
        user="tradicional",
        password="junjuisPl4tf0rm$",
        host="192.168.210.23",
        port=3006,
        database="tradicional_migracion"
    )
    cursor = conn.cursor()

    today = datetime.date.today()
    #from_date = today.strftime('%Y-%m-%d')
    #prev_month = today - dateutil.relativedelta.relativedelta(months=1)
    #from_date = prev_month.replace(day=26)
    #from_date = from_date.strftime('%Y-%m-%d')

    from_date = today - dateutil.relativedelta.relativedelta(months=1)
    from_date = from_date.replace(day=26)
    from_date = from_date.strftime('%Y-%m-%d')
    #from_date = '2022-12-26'

    to_date = today
    to_date = to_date.replace(day=25)
    to_date = to_date.strftime('%Y-%m-%d')
    #to_date = today.strftime('%Y-%m-%d')
    #to_date = '2023-03-25'

    cursor.execute(
        'SELECT * '
        'FROM operaciones '
        f"WHERE FechaHora >= '{from_date}' AND FechaHora <= '{to_date}' AND idEliminacion IS NULL "
        'ORDER BY FechaHora DESC;'
    )
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    return results


def create_novedades(rows):
    miembros_compensadores = get_miembros_compensadores()

    novedades = []
    for row in rows:
        try:
            id_casa_bolsa_compra = row['IdCasaDeBolsaCompra']
            if id_casa_bolsa_compra:
                novedad = create_novedad(row, id_casa_bolsa_compra, miembros_compensadores)
                if novedad:
                    novedades.append(novedad)

            id_casa_bolsa_venta = row['IdCasaDeBolsaVenta']
            if id_casa_bolsa_venta:
                novedad = create_novedad(row, id_casa_bolsa_venta, miembros_compensadores)
                if novedad:
                    novedades.append(novedad)
        except Exception as error:
            print(f'Error: {error}')

        if len(novedades) > 500:
            ids = xr.execute_kw('pbp.novedades_series', 'create', [novedades])
            print('CREATED')
            novedades = []

    if len(novedades):
        ids = xr.execute_kw('pbp.novedades_series', 'create', [novedades])
        print('CREATED')


def create_novedad(row, id_casa_bolsa, miembros_compensadores):
    id_operacion = row['IdOperacion']

    observacion = row['Observacion']
    if observacion and not observacion.startswith('Migracion'):
        return False

    partner_id = False
    persona_id = False
    miembro_compensador = next(
        (item for item in miembros_compensadores if int(item['MiembroCompensadorCodigo']) == id_casa_bolsa), False)
    if miembro_compensador:
        persona_id = miembro_compensador['PersonaID']
        partner_ids = xr.execute_kw('res.partner', 'search', [[['id_cliente_pbp', '=', persona_id]]])
        partner_id = partner_ids[0] if partner_ids else False

    novedades = xr.execute_kw('pbp.novedades_series', 'search', [[['id_operacion', '=', id_operacion], ['persona_id', '=', persona_id]]])

    product_id = 152
    fecha = row['FechaHora'].strftime('%Y-%m-%d')
    cantidad = row['Cantidad']
    valor_nominal = row['ValorNominal']
    volumen = float(cantidad * valor_nominal)
    total_arancel = (volumen * 0.02) / 100
    iva = (10 * total_arancel) / 100
    total = total_arancel + iva

    obj = {
        'id_operacion': id_operacion,
        'tipo_contrato_descripcion': '',
        'currency_id': 155,
        'persona_id': persona_id,
        'fecha': fecha,
        'valor_nominal': valor_nominal,
        'cantidad': cantidad,
        'partner_id': partner_id,
        'product_id': product_id,
        'volumen': volumen,
        'total_arancel': total_arancel,
        'iva': iva,
        'total': total,
    }

    if novedades:
        xr.execute_kw('pbp.novedades_series', 'write', [novedades, obj])
        print(f'NOVEDAD UPDATED: {novedades[0]} {obj}')
        return False
    else:
        #id = xr.execute_kw('pbp.novedades_series', 'create', [obj])
        #print(f'NOVEDAD CREATED: {id} {obj}')
        return obj


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return False
    return value


def sync_novedades():
    valores = get_registros()
    create_novedades(valores)


if __name__ == '__main__':
    sync_novedades()
    #xr.execute_kw('pbp.novedades_series', 'calcular_valores', [False])

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
from_date = "2024-01-26"

to_date = today.replace(hour=23, minute=59)
to_date = to_date.strftime('%Y-%m-%d %H:%M')

LOTE_ENVIO = 200


def get_clientes():
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
        'SELECT DISTINCT Personas.vCuentaFacturacion.*, '
        'Personas.vReporteMiembrosCompensadores.Email, '
        'Personas.vReporteMiembrosCompensadores.Domicilio, '
        'Personas.vReporteMiembrosCompensadores.Localidad, '
        'Personas.vReporteMiembrosCompensadores.Telefono, '
        'Personas.vReporteMiembrosCompensadores.[Razón Social / Apellido] '
        'FROM Personas.vCuentaFacturacion '
        'LEFT JOIN Personas.vReporteMiembrosCompensadores '
        'ON Personas.vCuentaFacturacion.MiembroCompensadorID = Personas.vReporteMiembrosCompensadores.MiembroCompensadorID;'
    )
    # 'ON Personas.vCuentaFacturacion.MiembroCompensadorID = Personas.vReporteMiembrosCompensadores.MiembroCompensadorID WHERE Personas.vCuentaFacturacion.PersonaID = 20;'
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    return results


def create_clientes(clientes):
    for row in clientes:
        try:
            create_cliente(row)
        except Exception as error:
            print(f'Error: {error}')


def create_cliente(row):
    vat = row['CuitCuil']
    if not vat:
        print('RUC vacío')

    vat = vat.strip()
    vat = vat.replace('/', '-')
    if not vat:
        print('RUC vacío')
        return

    if vat.endswith(' 0'):
        vat = vat[:-2]
    if '-' not in vat and len(vat) > 8 and len(vat) < 11:
        vat = vat[:-1] + '-' + vat[-1]

    cliente_id = row['PersonaID']
    address = row['Domicilio']

    obj = {
        'name': row['PersonaDescripcion'],
        'vat': vat,
        'email': row['Email'] if row['Email'] else False,
        'id_cliente_pbp': cliente_id,
        'contact_address': address if address else False,
        'contact_address_complete': address if address else False,
        'city': row['Localidad'] if row['Localidad'] else False,
        'phone': row['Telefono'] if row['Telefono'] else False,
        'obviar_validacion': True,
    }

    # partner_ids = xr.execute_kw('res.partner', 'search', [['|', ['id_cliente_pbp', '=', cliente_id], ['vat', '=', vat]]])
    partner_ids = xr.execute_kw('res.partner', 'search', [[['vat', '=', vat], ['id_cliente_pbp', '=', cliente_id]]])
    partner_id = partner_ids[0] if partner_ids else None
    if partner_id:
        del obj['name']
        print(obj)
        xr.execute_kw('res.partner', 'write', [[partner_id], obj])
        print(f'PARTNER UPDATED: {partner_id}')
    else:
        print(obj)
        partner_id = xr.execute_kw('res.partner', 'create', [obj])
        print(f'PARTNER CREATED: {partner_id}')

    # novedades = xr.execute_kw('pbp.novedades', 'search', [[['partner_id', '=', partner_id]]])
    # xr.execute_kw('res.partner', 'write', [novedades, {'cliente_id': cliente_id}])
    # xr.execute_kw('res.partner', 'update_novedades', [partner_id, partner_id])


def sync_clientes():
    clientes = get_clientes()
    create_clientes(clientes)


def sincronizar_novedades():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_novedades_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_novedades_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_novedades_desde_BD():
    """
    Obtenemos los datos de desde la base de datos. Dejamos todo en memoria
    """
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={SQL_SERVER_CONFIG["HOST"]};'
        f'DATABASE=Bvpasa_Publicacion;'
        f'UID={SQL_SERVER_CONFIG["USER"]};'
        f'PWD={SQL_SERVER_CONFIG["PWD"]};'
        'ENCRYPT=no;'
    )
    cursor = conn.cursor()

    cursor.execute(
        'SELECT '
        'Registro.vValores.*, '
        'Productos.vContrato.TipoContratoDescripcion, '
        'Productos.SerieRentaFijaPublicacion.TasaInteres, '
        'Personas.MiembroCompensador.PersonaID '
        'FROM Registro.vValores '
        'LEFT JOIN Productos.vContrato ON Registro.vValores.ContratoID = Productos.vContrato.ContratoID '
        'LEFT JOIN Productos.SerieRentaFijaPublicacion ON Registro.vValores.ContratoID = Productos.SerieRentaFijaPublicacion.ContratoID '
        'LEFT JOIN Personas.MiembroCompensador ON Registro.vValores.MiembroCompensadorID = Personas.MiembroCompensador.MiembroCompensadorID '
        f"WHERE FechaOperacion >= '{from_date}' AND FechaOperacion <= '{to_date}'"
        'ORDER BY Registro.vValores.FechaOperacion DESC;'
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:
        moneda_id = r.get('MonedaID')
        if r.get('FechaOperacion'):
            fecha_operacion = r.get('FechaOperacion').strftime('%Y-%m-%d')
        else:
            fecha_operacion = False
        if r.get('FechaVencimiento'):
            fecha_vencimiento = r.get('FechaVencimiento').strftime('%Y-%m-%d')
        else:
            fecha_vencimiento = False
        if fecha_vencimiento and fecha_operacion:
            plazo = r.get('FechaVencimiento') - r.get('FechaOperacion')
            plazo = plazo.days
        else:
            plazo = 0
        currency_id = 2 if r.get('MonedaID') == 2 else 155
        obj = {
            'id_vvalores': r.get('OperacionCarteraNumero'),
            'cantidad': r.get('Cantidad'),
            'total': False,
            'total_iva': False,
            'subtotal': False,
            'contrato_descripcion': r.get('ContratoDescripcion'),
            'contrato_id': r.get('ContratoID'),
            'contrato_tipo_descripcion': r.get('TipoContratoDescripcion'),
            'product_id': False,
            'currency_id': currency_id,
            'fecha_operacion': fecha_operacion,
            'fecha_vencimiento': fecha_vencimiento,
            'plazo': plazo,
            'cliente_id': r.get('PersonaID'),
            'partner_id': False,
            'mercado': r.get('MercadoDescripcion'),
            'volumen_gs': r.get('VolumenGS') if moneda_id == 1 else r.get('SubTotal'),
            'volumen_gs_usd': r.get('VolumenGS'),
            'instrumento': r.get('Instrumento'),
            'tipo_operacion': r.get('TipoOperacionDescripcion')
        }
        objects.append(obj)
    return objects


def enviar_novedades_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.novedades', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_novedades()
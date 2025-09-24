from configparser import ConfigParser
import datetime
from decimal import Decimal
import os

import mariadb

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


def sincronizar_series():
    """
    Obtenemos los datos necesarios y enviamos al odoo, en grupos de LOTE_ENVIO
    """

    # Obtenemos los datos de la proforma
    datos = obtener_series_desde_BD()

    registros = len(datos)
    print(f"Se obtuvieron {registros} registros")

    # Enviamos los datos al odoo en grupos de LOTE_ENVIO
    for i in range(0, registros, LOTE_ENVIO):
        lote = datos[i: i + LOTE_ENVIO]
        print(f"Enviando registros {i} a {i + LOTE_ENVIO}")
        enviar_series_xmlrpc(xr, lote)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if value is None:
        return False
    return value


def obtener_series_desde_BD():
    """
    Obtenemos los datos de desde la base de datos. Dejamos todo en memoria
    """
    conn = mariadb.connect(
        user="tradicional",
        password="junjuisPl4tf0rm$",
        host="192.168.210.23",
        port=3006,
        database="tradicional_migracion"
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
    objects = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))

    for r in results:
        obj = {
            'repo_id': r.get('RepoID'),
            'reportador_id': r.get('ReportadorID'),
            'reportado_id': r.get('ReportadoID'),
            'tipo_operacion': 'directa' if r.get('ReportadoID') == r.get('ReportadorID') else 'comun',
            'currency_id': 2 if r.get('MonedaDescripcion') == 'Dólar' else 155,
            'fecha_operacion': r.get('FechaOperacion').strftime('%Y-%m-%d') if r.get('FechaOperacion') else False,
            'fecha_vencimiento': r.get('FechaVencimiento').strftime('%Y-%m-%d'),
            'comitente_reportado_codigo': r.get('ComitenteReportadoCodigo'),
            'comitente_reportador_codigo': r.get('ComitenteReportadorCodigo'),
            'cod_negociacion': r.get('CodigoNegociacionID'),
            'contrato': r.get('ContratoDescripcion'),
            'cantidad': r.get('CantidadTitulos'),
            'precio_venta': r.get('PrecioVenta'),
            'tasa_interes': r.get('TasaInteres'),
            'plazo': r.get('PlazoOperacion'),
            'state': str(r.get('EstadoRepoID')),
            'monto_inicial': r.get('MontoInicial'),
            'precio_recompra': r.get('PrecioRecompra'),
            'monto_operacion_a_termino': r.get('MontoOperacionATermino'),
            'aforo': r.get('Aforo'),
            'tipo_repo_descripcion': r.get('TipoRepoDescripcion')
        }
        objects.append(obj)
    return objects


def enviar_series_xmlrpc(xr, data):
    """
    Enviamos los datos al odoo a través de XMLRPC
    """
    try:
        result = xr.execute_kw('pbp.novedades_series', 'sincronizar_registros', [data])
        print(result)
    except Exception as e:
        print(e)
        print("Error al enviar datos al odoo")
        return None


if __name__ == '__main__':
    sincronizar_series()
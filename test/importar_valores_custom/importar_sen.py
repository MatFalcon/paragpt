from configparser import ConfigParser
import datetime
from decimal import Decimal
import os
import time
from conexion_sql import conectar_base_sql, conectar_base_elejir

from conexion_odoo import OdooXMLRPCClient

os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')


xr = OdooXMLRPCClient()
xr.setup()
# Obtener la fecha actual
# Definir la fecha manualmente
today = datetime.datetime(year=2025, month=6, day=5)  # Puedes modificar año, mes y día según necesites

# Obtener el primer día de mayo
first_day_may = today.replace(month=10, day=1)

# Establecer la fecha de inicio como el primer momento del primer día de mayo
from_date = datetime.datetime.combine(first_day_may, datetime.time.min)

# Establecer la fecha de finalización como la fecha y hora actuales
to_date = today

# Formatear las fechas en el formato deseado ('YYYY-MM-DD HH:MM:SS')
from_date_str = from_date.strftime('%Y-%m-%d %H:%M:%S')
to_date_str = to_date.strftime('%Y-%m-%d %H:%M:%S')

# Imprimir las fechas para verificar
from_date_str = '2025-08-08 00:00:00'
to_date_str = '2025-08-08 23:59:59'
print("Fecha de inicio:", from_date_str)
print("Fecha de finalización:", to_date_str)

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
        print(f"Enviando registros1 {i} a {i + LOTE_ENVIO}")
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

    conn = conectar_base_elejir("Bvpasa_Clearing")
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
        'PersonasGeneral.Persona.CuitCuil, '  # Añadir CuitCuil de la tabla PersonasGeneral.Persona
        'Productos.Emision.EmisorID, '
        'Productos.Emision.MontoEmision, '
        'Productos.vReporteSeries.Instrumento, '
        'Productos.vReporteSeries.FechaColocacion '
        f'FROM Productos.{table} '
        f'LEFT JOIN Productos.vContrato ON Productos.{table}.ContratoID = Productos.vContrato.ContratoID '
        f'LEFT JOIN Productos.Emision ON Productos.{table}.EmisionID = Productos.Emision.EmisionID '
        'LEFT JOIN Personas.Emisor ON Productos.Emision.EmisorID = Personas.Emisor.EmisorID '
        'LEFT JOIN Productos.vReporteSeries ON Productos.vReporteSeries.EmisionCodigo = Productos.Emision.EmisionCodigo '
        'LEFT JOIN PersonasGeneral.Persona ON Personas.Emisor.PersonaID = PersonasGeneral.Persona.PersonaID '  # JOIN para obtener el CuitCuil
        f"where Productos.vContrato.ContratoDescripcion = 'PYBAM04F1569'"
        # f"WHERE Productos.SerieRentaFija.FechaEmisionSerie >= '2025-08-08 00:00' AND Productos.SerieRentaFija.FechaEmisionSerie <= '2025-08-08 23:59'"
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
        print("FECHA EMISION TESt", fecha_emision)
        if not fecha_emision:
            fecha_emision = r.get('FechaEmisionFondoInversion')

        fecha_vencimiento = r.get('FechaVencimiento')
        if not fecha_vencimiento:
            fecha_vencimiento = r.get('FechaMaximaColocacion')

        fecha_vencimiento = fecha_vencimiento.split("-")
        fecha_vencimiento = datetime.datetime(int(fecha_vencimiento[0]), int(fecha_vencimiento[1]),int(fecha_vencimiento[2]), 0, 0, 0)
        fecha_emision = fecha_emision.split("-")
        fecha_emision = datetime.datetime(int(fecha_emision[0]), int(fecha_emision[1]),int(fecha_emision[2]), 0, 0, 0)

        if fecha_vencimiento.year > fecha_emision.year:
            if fecha_vencimiento.year == 2023:
                print("FECHA VENCIMIENTO 2023", fecha_vencimiento.year,fecha_emision.year)
                fecha_emision = datetime.date(fecha_vencimiento.year, 1, 1)
            elif fecha_vencimiento.year > 2023:
                print("FECHA EMISION MAYOR A 2023", fecha_vencimiento.year,fecha_emision.year)
                fecha_emision = False

        fecha_vencimiento = fecha_vencimiento.strftime('%Y-%m-%d')
        if fecha_emision:
            fecha_emision = fecha_emision.strftime('%Y-%m-%d')

        inicio_colocacion = r.get('FechaColocacion')  # Obtener FechaColocacion de Productos.vReporteSeries
        print("INICIO COLOCACION 1", inicio_colocacion, fecha_emision)

        if inicio_colocacion:
            inicio_colocacion = inicio_colocacion.split("-")
            inicio_colocacion = datetime.datetime(int(inicio_colocacion[0]), int(inicio_colocacion[1]),int(inicio_colocacion[2]), 0, 0, 0)
            inicio_colocacion = inicio_colocacion.strftime('%Y-%m-%d')
        inicio_colocacion = fecha_emision if fecha_emision else inicio_colocacion
        print("INICIO COLOCACION 2", inicio_colocacion, fecha_emision)
        obj = {
            'emisor_descripcion': r.get('EmisorDescripcion'),
            'emisor_id': int(r.get('EmisorID')),
            'cod_negociacion': r.get('ContratoDescripcion'),
            'tipo_contrato_descripcion': r.get('TipoContratoDescripcion'),
            'tipo_contrato_codigo': r.get('TipoContratoCodigo'),
            'contrato_descripcion': r.get('ContratoDescripcion'),
            'contrato_id': int(r.get('ContratoID')),
            'currency_id': 2 if r.get('MonedaCotizacionID') == 'Dólar' else 155,
            'persona_id': int(r.get('PersonaID')),
            'instrumento': r.get('Instrumento'),
            'fecha_emision': fecha_emision,
            'fecha_inicial': fecha_emision,
            'fecha_vencimiento': fecha_vencimiento,
            'monto_emitido': float(r.get('MontoEmision')),
            'cantidad_emitida': int(r.get('Cantidad')),
            'partner_id': False,
            'product_id': 165,
            'inicio_colocacion': inicio_colocacion,
            'ruc': r.get('CuitCuil')
        }
        objects.append(obj)
    print("OBJECTS",len(objects))
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
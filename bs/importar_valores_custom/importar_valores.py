import os
import pyodbc
import datetime
import jaydebeapi
import dateutil.relativedelta
from decimal import Decimal
from jpype.types import JDouble, JInt
from configparser import ConfigParser

from pandas.core.interchange.dataframe_protocol import DataFrame

from conexion_odoo import OdooXMLRPCClient
from conexion_sql import conectar_base_sql, conectar_base_elejir
import pandas as pd
os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')

SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
    'DB': config['sqlserver']['db']
}
########### Se intancia cliente de odoo ############
xr = OdooXMLRPCClient()
xr.setup()

today = datetime.date.today()

from_date = today - dateutil.relativedelta.relativedelta(months=1)
from_date = from_date.replace(day=26)
from_date = from_date.strftime('%Y-%m-%d')
#from_date = "2023-06-26"
ids_pbp = []

to_date = today
to_date = to_date.replace(day=25)
to_date = to_date.strftime('%Y-%m-%d')
#to_date = "2023-07-25"
# Configura los detalles de conexión
url = f"jdbc:sqlserver://{SQL_SERVER_CONFIG['HOST']};databaseName={SQL_SERVER_CONFIG['DB']};encrypt=true;trustServerCertificate=true"
driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
jar_file = "/home/user/Escritorio/EntornosClientes/odoo17/Bolsa/importar_valores/mssql-jdbc-12.8.1.jre11.jar"  # O jre8 si tienes Java 8
user = "sati"
password = "D1@8I1$W9\\mt"

def get_clientes():
    print("Se trata de conectar con la base de datos")
    conn = conectar_base_sql()
    cursor = conn.cursor()
    print("Se conecto con la base de datos")

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
    print("Se realizo la consulta")
    #'ON Personas.vCuentaFacturacion.MiembroCompensadorID = Personas.vReporteMiembrosCompensadores.MiembroCompensadorID WHERE Personas.vCuentaFacturacion.PersonaID = 20;'
    columns = [column[0] for column in cursor.description]
    print("Columnas: \n", columns)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    input("Continuar?")
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

    #partner_ids = xr.execute_kw('res.partner', 'search', [['|', ['id_cliente_pbp', '=', cliente_id], ['vat', '=', vat]]])
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

    #novedades = xr.execute_kw('pbp.novedades', 'search', [[['partner_id', '=', partner_id]]])
    #xr.execute_kw('res.partner', 'write', [novedades, {'cliente_id': cliente_id}])
    #xr.execute_kw('res.partner', 'update_novedades', [partner_id, partner_id])


def get_registro_valores():
    print("Se trata de conectar a Bvpasa_Publicacion")
    conn = conectar_base_elejir('Bvpasa_Publicacion')
    print("Se conecto correctamente")
    cursor = conn.cursor()
    print("Se realiza una consulta")
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
        'where Registro.vValores.ContratoDescripcion = \'PYTAU03F4028\''
        'ORDER BY Registro.vValores.FechaOperacion DESC;'
    )

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    results = []
    for row in rows:
        values = [clean_value(value) for value in row]
        results.append(dict(zip(columns, values)))
    return results


def create_novedades(rows):
    print("Entra en create_novedades")
    df = pd.DataFrame(rows)
    df.to_csv("Novedades.csv", index=False)
    df.to_excel("Novedades.xlsx", index=False)
    print("Se genero el csv y excel")
    novedades = []
    for row in rows:
        novedad = create_novedad(row)
        if novedad:
            novedades.append(novedad)
        # try:
        #
        #     if novedad:
        #         novedades.append(novedad)
        # except Exception as error:
        #     print(f'Error 1: {error}')

        if len(novedades) == 500:
            ids = xr.execute_kw('pbp.novedades', 'create', [novedades])
            print('CREATED')
            novedades = []

    if len(novedades):
        ids = xr.execute_kw('pbp.novedades', 'create', [novedades])
        print('CREATED')


def create_novedad(row):
    print("Entra en create_novedad")
    id_pbp = False
    data = {
        'id_pbp': [],
        'id_vvalores': [],
        'mercado': [],
        'instrumento': [],
        'currency_id': [],
        'volumen_negociado': [],
        'fecha_operacion': [],
        'fecha_vencimiento': [],
        'cliente_id': [],
        'partner_id': [],
        'plazo': [],
        'calculo': []
    }
    id_vvalores = int(row['OperacionCarteraNumero'])
    moneda_id = row['MonedaID']
    if moneda_id == 2:
        # currency_name = 'USD'
        currency_id = 2
    elif moneda_id == 1:
        # currency_name = 'PYG'
        currency_id = 155
    else:
        return False
    volumen_gs = row['VolumenGS']
    mercado = row['MercadoDescripcion']
    contrato_id = row['ContratoID']
    contrato_descripcion = row['ContratoDescripcion']
    contrato_tipo_descripcion = row['TipoContratoDescripcion']
    product_id = False
    if contrato_tipo_descripcion == 'Fondo Inversión':
        product_id = 190
    elif contrato_tipo_descripcion == 'Serie Renta Fija':
        product_id = 153
        if mercado == 'Repos':
            product_id = 155
    elif contrato_tipo_descripcion == 'Serie Renta Variable Acción':
        product_id = 154
    else:
        return False
    instrumento = row['Instrumento']
    if row['FechaOperacion']:
        fecha_operacion = datetime.datetime.strptime(row['FechaOperacion'], '%Y-%m-%d')
    else:
        fecha_operacion = False
    if row['FechaVencimiento']:
        fecha_vencimiento = datetime.datetime.strptime(row['FechaVencimiento'], '%Y-%m-%d')
    else:
        fecha_vencimiento = False

    if fecha_vencimiento != False  and fecha_operacion != False:
        plazo = fecha_vencimiento - fecha_operacion
        plazo = plazo.days
    else:
        plazo = 0
    cliente_id = int(row['PersonaID'])
    print("Se obtienen las novedades", id_vvalores)
    novedades = xr.execute_kw('pbp.novedades', 'search', [[['id_vvalores', '=', id_vvalores]]])
    print(novedades)
    #fondo_garantia = xr.execute_kw('pbp.calculo_fondo_garantia', 'search', [[['id_vvalores', '=', id_vvalores]]])


    partner_id = False
    partners = xr.execute_kw('res.partner', 'search_read', [[['id_cliente_pbp', '=', cliente_id]]])
    partner = partners[0] if partners else False
    if partner:
        partner_ruc = partner['vat']
        partner_ids = xr.execute_kw('res.partner', 'search', [[['vat', '=', partner_ruc]]])
        if len(partner_ids) > 1:
            max_total = 0
            for pid in partner_ids:
                partner_novedades_total = xr.execute_kw('pbp.novedades', 'search_count', [[['partner_id', '=', pid]]])
                if partner_novedades_total > max_total:
                    partner_id = pid
                    max_total = partner_novedades_total
            if not max_total:
                partner_id = partner['id']
        else:
            partner_id = partner['id']

    cantidad = row['Cantidad']
    print("Cantidad", cantidad)
    tasa_interes = row['TasaInteres']

    if row['EmisorDescripcion'] == 'MINISTERIO DE HACIENDA' or mercado == 'Mercado Primario':
        total = (volumen_gs / 100) * 0.01
    elif (mercado == 'Mercado Primario' or mercado == 'Mercado Secundario') and (instrumento == 'Fondos de Inversión' or instrumento == 'Acciones'):
        if moneda_id == 1:
            total = volumen_gs
        else:
            total = row['SubTotal']
        total = (total/100) * 0.02
    elif (mercado == 'Mercado Primario' or mercado == 'Mercado Secundario') and 'bono' in instrumento.lower():
        if moneda_id == 1:
            total = volumen_gs
        else:
            total = row['SubTotal']
        if row['EmisorDescripcion'] == 'MINISTERIO DE HACIENDA' or mercado == 'Mercado Primario':
            total = (total / 100) * 0.01
        else:
            total = (total / 100) * 0.02
    elif mercado == 'Repos':
        if moneda_id == 1:
            volumen_negociado = volumen_gs
        else:
            volumen_negociado = row['SubTotal']
        arancel_anual = tasa_interes * volumen_negociado
        total = arancel_anual/365 * plazo
        iva = total * 0.10

        ### Calculo Fondo de Garantia
        calculo = total / 100 * 0.005 / 365 * plazo
        calculo_obj = {
            'id_pbp': id_pbp,
            'id_vvalores': id_vvalores,
            'mercado': mercado,
            'instrumento': instrumento,
            'currency_id': currency_id,
            'volumen_negociado': volumen_negociado,
            'fecha_operacion': fecha_operacion,
            'fecha_vencimiento': fecha_vencimiento,
            'cliente_id': cliente_id,
            'partner_id': partner_id,
            'plazo':plazo,
            'calculo':calculo
        }


        # if fondo_garantia:
        #     xr.execute_kw('pbp.calculo_fondo_garantia', 'write', [[fondo_garantia[0]], calculo_obj])
        #     print(f'CALCULO FONDO DE GARANTIA UPDATED: {id_vvalores} {calculo_obj}')
        # else:
        #     id = xr.execute_kw('pbp.calculo_fondo_garantia', 'create', [calculo_obj])
        #     print(f'CALCULO FONDO DE GARANTIA CREATED: {id} {calculo_obj}')

    obj = {
        'id_pbp': id_pbp,
        'id_vvalores': id_vvalores,
        # 'precio_unitario': row['Precio'],
        'cantidad': cantidad,
        'total': total,
        'contrato_descripcion': contrato_descripcion,
        'contrato_id': contrato_id,
        'contrato_tipo_descripcion': contrato_tipo_descripcion,
        'product_id': product_id,
        'currency_id': currency_id,
        'fecha_operacion': fecha_operacion,
        'cliente_id': cliente_id,
        'partner_id': partner_id,
        'mercado': mercado,
        'volumen_gs': volumen_gs,
    }
    print("++++++++++++++Novedades+++++++++++++++++++++")
    #print(novedades)
    #print(obj)
    if novedades:
        print("If")
        xr.execute_kw('pbp.novedades', 'write', [[novedades[0]], obj])
        print(f'NOVEDAD UPDATED: {id_vvalores} {obj}')
    else:
        print("else")
        for key in obj:
            if isinstance(obj[key], JDouble):
                obj[key] = float(obj[key])
            else:
                try:
                    obj[key] = int(obj[key])
                except:
                    pass
            #print(type(obj[key]))
        print(obj)

        #id = xr.execute_kw('pbp.novedades', 'create', [obj])
        #print(f'NOVEDAD CREATED: {id} {obj}')






def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return False
    return value


def sync_clientes():
    clientes = get_clientes()
    create_clientes(clientes)


def sync_novedades():
    valores = get_registro_valores()
    create_novedades(valores)


if __name__ == '__main__':
    #sync_clientes()
    sync_novedades()

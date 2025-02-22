import os
import time

import datetime
from tarfile import data_filter

import jaydebeapi
import dateutil.relativedelta
from decimal import Decimal
from jpype.types import JDouble, JInt
from configparser import ConfigParser

from pandas.core.interchange.dataframe_protocol import DataFrame

from conexion_odoo import OdooXMLRPCClient
from conexion_sql import conectar_base_sql, conectar_base_elejir
import pandas as pd

import mariadb

CASA_BOLSA = {
    "VALORES CBSA": 202,
    "REGIONAL CBSA": 191,
    "FAMILIAR CBSA": 1625,
    "AVALON CBSA": 122,
    "CADIEM CBSA": 137,
    "CAPITAL MARKETS CBSA": 139,
    "ASU CAPITAL CBSA": 118,
    "ITAU INVEST CBSA": 173,
    "FAIS CBSA": 564,
    "INVESTOR CBSA": 172,
    "BASA CBSA": 132,
    "PUENTE CBSA": 189,
}
os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')

SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
}
# conexion del odoo
xr = OdooXMLRPCClient()
xr.setup()
print(f"UID obtenido: {xr.uid}")
# conexion del sql
conn = conectar_base_sql()
cursor = conn.cursor()

conexion_base_2 = conectar_base_elejir("Bvpasa_Clearing")
cursor_base2  = conexion_base_2.cursor()

instrumentos = {
    'Bono Subordinado':'bonos_subordinados',
    'Bono Financiero':'bonos_financieros',
    "Bono":'bonos'
}
monedas = {
    'Guaraní': 155,
    'Dólar':2
}

def obtener_vencimientos(serie):

    """"
    Retorna los vencimientos
    Fecha,Interes,Estado,Serie
    """

    consulta = (f"SELECT [EventoCorporativoFecha],"
                f"[Interes],"
                f"[EstadoDescripcion],"
                f"[ActivoDescripcion],"
                f"[Amortizacion],"
                f"[TotalTitulo]"
                f"FROM [Bvpasa_Clearing].[Activos].[vEventosCorporativos]  "
                f"WHERE ActivoDescripcion= '{serie}' order by EventoCorporativoFecha asc")

    filas_vencimiento = {}
    cursor.execute(consulta)
    resultado = cursor.fetchall()

    contador_registro = 1
    for res in resultado:
        filas_vencimiento[contador_registro] = {
            'fecha_vencimiento': res[0],
            'interes_titulo': res[1],
            'estado':res[2],
            'serie':res[3],
            'tipo':'vtoInt',
        }
        print("Interes \t Interes Total \t Amotizacion \t AmotizacionTotal")
        print(f"{res[1]}r\t{res[1]*30}\t{res[4]}\t{res[4]*30}")
        #print("Interes:",res[1]*20)
        if int(res[4])>0:
            contador_registro += 1
            filas_vencimiento[contador_registro] = {
                'fecha_vencimiento': res[0],
                'interes_titulo': float(res[4]),
                'estado': res[2],
                'serie': res[3],
                'tipo':'pagocap'
            }
            #print("Capital:", res[4], "Total: ", (res[4] * 200))

        contador_registro += 1
    return filas_vencimiento
def obtener_datos_cabecera(serie):


    """"
        retorna
        fecha de compra
        fecha de vencimiento,
        Calificacion riesgo,
        Tasa interes,
        importe valorizado,
        moneda,
        Periodo pago
        Descripcion del Emisor
        partner_id(Emisor) si es que existe
    """

    query = ("select [Bvpasa_Clearing].[Productos].[vReporteSeries].FechaColocacion as FechaCompra,"
             "[Bvpasa_Clearing].[Productos].[vReporteSeries].FechaVencimiento as FechaVencimiento,"
             "[Bvpasa_Clearing].[Productos].[Emision].CalificacionRiesgo,"
             "[Bvpasa_Clearing].[Productos].[vReporteSeries].TasaInteresNominal,"
             "[Bvpasa_Clearing].[Productos].[Emision].ValorNominal as ImporteValorizado,"
             "[Bvpasa_Clearing].[Productos].[vReporteSeries].Instrumento,[Bvpasa_Clearing].[Productos].[vReporteSeries].MonedaDescripcion,"
             "[Bvpasa_Clearing].[Productos].[vReporteSeries].PeriodicidadIntereses,"
             "Bvpasa_Clearing.Personas.Emisor.EmisorDescripcion,"
             "Bvpasa_Clearing.Personas.Emisor.PersonaID "
             "FROM [Bvpasa_Clearing].[Productos].[Emision]"
             "INNER JOIN [Bvpasa_Clearing].[Personas].[Emisor]"
             "ON [Bvpasa_Clearing].[Productos].[Emision].[EmisorID] = [Bvpasa_Clearing].[Personas].[Emisor].[EmisorID]"
             "INNER JOIN [Bvpasa_Clearing].[Productos].[vReporteSeries]"
             "ON[Bvpasa_Clearing].[Productos].[Emision].[EmisionCodigo] = [Bvpasa_Clearing].[Productos].[vReporteSeries].[EmisionCodigo]"
             f"where [Productos].[vReporteSeries].CodNegociacion= '{serie}'")

    cursor_base2.execute(query)
    result = cursor_base2.fetchall()

    return result[0]

def importar_cartera(data_dict):
    """"
        Recibe el dic procesado con los datos de inversion
    """
    for key, data in data_dict.items():
        cartera_vals = {
                'emision':data.get('emision'),
                'serie': data.get('serie'),
                'fecha_compra': data.get('fecha_compra'),
                'fecha_vencimiento': data.get('fecha_vencimiento'),
                'calificacion_riesgo': data.get('calificacion_riesgo'),
                'tasa_interes': float(data.get('tasa_interes')),
                'importe_valorizado': float(data.get('importe_valorizado')),
                'capital':float(data.get('importe_valorizado')),
                'instrumento': data.get('instrumento'),
                'currency_id': data.get('moneda'),
                'comitente': data.get('comitente'),
                'intereses':data.get('intereses'),
                'partner_id':data.get('partner_id'),
                'casa_bolsa':data.get("casa_bolsa"),
                'banco_account_id':data.get('banco_account_id'),
                'inversion_journal_id':data.get('inversion_journal_id'),
                'inversion_account_id':data.get('inversion_account_id'),
                'initial_debit_account_id':data.get('initial_debit_account_id'),
                'initial_debit_account_id_lp':data.get('initial_debit_account_id_lp'),
                'initial_credit_account_id':data.get('initial_credit_account_id'),
                'initial_credit_largo_plazo_account_id':data.get('initial_credit_largo_plazo_account_id'),
                'initial_journal_id':data.get('initial_journal_id'),
                'credit_account_id':data.get('credit_account_id'),
                'debit_account_id':data.get('debit_account_id'),
                'tipo_mercado': 'primario' if data.get('mercado') == 'Mercado Primario' else 'secundario',
                'plazo_pago_intereses':1,
                'tipo':'capital',
                'fecha_inicio_devengamiento': data.get('fecha_compra'),
                'fecha_final_devengamiento':data.get('fecha_vencimiento'),

            }
        print("Cartera vals")
        print(cartera_vals)
        # crea el registro en el odoo
        try:
            cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])
        except:
            print("Sin Fecha Inicio devengamiento")
            cartera_vals['fecha_inicio_devengamiento'] = False
            cartera_vals['fecha_final_devengamiento'] = False
            cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])

        print("Cartera", cartera_id)
        # crear los vencimientos
        vencimientos_vals = []
        for venc_id, vencimiento in data.get('vencimientos', {}).items():
            total_intereses = float(vencimiento.get('interes_titulo')) * data.get('cantidad')
            print("Creando Vencimiento")
            print(vencimiento.get('tipo'),"InteresTitulo:",vencimiento.get('interes_titulo'), "Total:", total_intereses)
            venc_vals = {
                'name':data.get('serie'),
                'fecha_vencimiento': vencimiento.get('fecha_vencimiento'),
                'registros': cartera_id,
                'state': 'cobrado' if vencimiento.get('estado') == 'Acreditado' else 'pendiente',
                'amortizacion':vencimiento.get('tipo') ,
                'total': total_intereses,
                'cuenta':data.get('debit_account_id'),
                #'intereses': float(vencimiento.get('interes_titulo'))
            }
            print("Vencimiento valores")


            vencimiento_id = xr.execute_kw('pbp.vencimiento_capital_interes', 'create', [venc_vals])
            vencimientos_vals.append(vencimiento_id)


def obtener_partner_segun_codigo_pbp(codigo_pbp):
    """
    Retorna el partner_id buscando por codigo pbp
    """
    resultado_busqueda = xr.execute_kw('res.partner', 'search',[[['id_cliente_pbp', '=', codigo_pbp]]])
    print("Partner Pbp", codigo_pbp)
    print(resultado_busqueda)

    return resultado_busqueda[0] if (len(resultado_busqueda) != 0) else False

def sincronizar_cartera():

    #registros_creados = xr.execute_kw('pbp.cartera_inversion', 'search', [[]])
    # consulta de registros de cartera
    cursor.execute(
        'select top 10 ContratoDescripcion,CuentaRegistroCodigo,Mercado,Cantidad'
        ',MiembroCompensadorDescripcion'
        ' from Bvpasa_Publicacion.Registro.vValores vv '
        "where CuentaRegistroCodigo in ("
        " '36947','26544','26543','21812','17035','15517','10834','10667','9243'"
        ",'9242','3844','3253','2475','1057','593','25','8','4') and Instrumento in ('Bono Subordinado', 'Bono', 'Bono Financiero')"#'Bono Subordinado',
        #"and ContratoDescripcion = 'PYTAU03F4028';"
    )
    registros_cartera_pbp = cursor.fetchall()
    print("Registros", len(registros_cartera_pbp))
    #serie y comitentes pendientes
    registros_pendientes = {}

    contador = 1
    for registro in registros_cartera_pbp:
        print("Registro", registro)
        # se consultan que no halla registros ya creados, los que ya estan se omiten la carga
        registros_creados = xr.execute_kw('pbp.cartera_inversion', 'search',[[['serie', '=', registro[0]], ['comitente', '=', registro[1]]]])

        # print(registros_creados)
        # se anaden a la lista de registros pendientes solo si no se encuentran registros en el odoo
        if len(registros_creados) == 0:
            print("Entra en el if")
            #obtiene los datos cabecera
            cabecera = obtener_datos_cabecera(registro[0])
            # se consulta un
            # print("Cuentas)registro del mismo instrumento que el registro nuevo que se quiere cargar
            registro_con_cuenta = xr.execute_kw(
                'pbp.cartera_inversion', 'search_read',
                [[
                    ['instrumento', '=', instrumentos[cabecera[5]]],
                    ['inversion_journal_id', '!=', False],
                    ['banco_account_id', '!=', False],
                    ['currency_id', '=', monedas[cabecera[6]]],
                    ['inversion_account_id', '!=', False],
                    ['initial_debit_account_id', '!=', False],
                    ['initial_debit_account_id_lp', '!=', False],
                    ['initial_credit_account_id', '!=', False],
                    ['initial_credit_largo_plazo_account_id', '!=', False],
                    ['initial_journal_id', '!=', False],
                    ['credit_account_id', '!=', False],
                    ['debit_account_id', '!=', False]
                ]],
                {'fields': ['inversion_journal_id',  # diario de inversion
                            'banco_account_id',  # cuenta de banco
                            'inversion_account_id',  # cuenta de inversion
                            'initial_debit_account_id',  # cuenta deudora inicial al devengar cp
                            'initial_debit_account_id_lp',  # cuenta deudora inicial a devengar lp
                            'initial_credit_account_id',  # cuenta acreedora inicial a devengar
                            'initial_credit_largo_plazo_account_id',  ##cuenta acreedora inicial a devengar lp
                            'initial_journal_id',  # diario de asiento a devengar
                            'credit_account_id',  # cuenta de ingresos
                            'debit_account_id',
                            'currency_id'
                            ], 'limit': 1}
            )

            partner_id = obtener_partner_segun_codigo_pbp(int(cabecera[9]))
            try:
                casa_bolsa_partener_id = CASA_BOLSA[registro[4]]
            except: # En caso que se tenga se tenga que agregar una nueva casa de bolsa
                casa_bolsa_partener_id = False
            registros_pendientes[contador] = {'serie':registro[0],
                                              'fecha_compra':cabecera[0],
                                              'fecha_vencimiento':cabecera[1],
                                              'calificacion_riesgo':cabecera[2],
                                              'tasa_interes':cabecera[3],
                                              'importe_valorizado':(cabecera[4] * registro[3]),
                                              'instrumento':instrumentos[cabecera[5]],
                                              'moneda':monedas[cabecera[6]],
                                              'periodo':cabecera[7],
                                              'emision':cabecera[8],
                                              'partner_id': partner_id,
                                              'casa_bolsa':casa_bolsa_partener_id,
                                              'inversion_journal_id':registro_con_cuenta[0]['inversion_journal_id'][0] if len(registro_con_cuenta) else False,
                                              'banco_account_id':registro_con_cuenta[0]['banco_account_id'][0] if len(registro_con_cuenta) else False,
                                              'inversion_account_id':registro_con_cuenta[0]['inversion_account_id'][0] if len(registro_con_cuenta) else False,
                                              'initial_debit_account_id':registro_con_cuenta[0]['initial_debit_account_id'][0] if len(registro_con_cuenta) else False,
                                              'initial_debit_account_id_lp':registro_con_cuenta[0]['initial_debit_account_id_lp'][0] if len(registro_con_cuenta) else False,
                                              'initial_credit_account_id':registro_con_cuenta[0]['initial_credit_account_id'][0] if len(registro_con_cuenta) else False,
                                              'initial_credit_largo_plazo_account_id':registro_con_cuenta[0]['initial_credit_largo_plazo_account_id'][0] if len(registro_con_cuenta) else False,
                                              'initial_journal_id':registro_con_cuenta[0]['initial_journal_id'][0] if len(registro_con_cuenta) else False,
                                              'credit_account_id':registro_con_cuenta[0]['credit_account_id'][0] if len(registro_con_cuenta)else False,
                                              'debit_account_id':registro_con_cuenta[0]['debit_account_id'][0] if len(registro_con_cuenta)else False,
                                       'comitente':registro[1],
                                       'mercado':registro[2],
                                       'cantidad':registro[3],
                                       'intereses':0,
                                       'vencimientos':{}}
            print("Registro Final")
            print(registros_pendientes[contador])



            registros_pendientes[contador]['vencimientos'] = obtener_vencimientos(registro[0])

            # calcular total interes recorriendo los vencimientos cargados
            total_intereses = 0
            for id_vencimiento in registros_pendientes[contador]['vencimientos']:
                interes_titulo = registros_pendientes[contador]['vencimientos'][id_vencimiento]['interes_titulo']
                total = (float(interes_titulo) * int(registros_pendientes[contador]['cantidad']))
                total_intereses += total

            registros_pendientes[contador]['intereses'] = total_intereses
            print("Registro")
            print(registros_pendientes[contador])
            contador += 1

    importar_cartera(registros_pendientes)

sincronizar_cartera()
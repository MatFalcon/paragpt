from configparser import ConfigParser
from conexion_odoo import OdooXMLRPCClient
import pandas as pd
import json

# conexion del odoo
xr = OdooXMLRPCClient()
xr.setup()
print(f"UID obtenido: {xr.uid}")

# excel = pd.read_excel("Cartera2412.xlsx")
# excel.to_csv("Cartera.xlsx")
# Diccionarios de mapeo
INSTRUMENTOS = {
    'Bonos Subordinados':'bonos_subordinados',
    'Bonos Financieros':'bonos_financieros',
    "Bonos":'bonos'
}


REGISTROS_NO_VALIDOS = 0
MONEDAS = {
    'Guaraníes': 155,
    'Dólares americanos':2
}

ESTADOS = {
            'Activo':'pendiente',
            'Vencido | Cobrado':'cobrado',
            'Cobrado | No renovado':'cobrado',
            'Pendiente':'pendiente',
            'Acreditado':'cobrado',
            'pendiente':'pendiente',
            'Activo | Reestructurado': 'pendiente',
            'Reestructurado':'pendiente'
        }

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


# tabla generada
tabla_cartera = pd.read_excel("CarteraFinal.xlsx")
tabla_cartera.to_csv("carterafinal.csv")
tabla_cartera = pd.read_csv("carterafinal.csv")
print(tabla_cartera)

tabla_bonos = tabla_cartera[
    (pd.notna(tabla_cartera['Serie'])) &
    (tabla_cartera['Serie'] == 'PYCAF02F9117') &
    (tabla_cartera['Instrumento'].isin(['Bonos Subordinados', 'Bonos Financieros', 'Bonos']))
]# se filtran solo los bonos de la tabla de cartera

# vamos a inicializar o filtrar los numeros de serie y comitentes para facilitar la select de datos
series = {}
contador_series_agregadas = 0
for indice in tabla_bonos.index:
    fila = tabla_bonos.loc[indice]  # se inicializa el registro(fila de la tabla)
    if fila['Serie'] in series.keys():  #
        if fila['Casa de bolsa '] in series[
            fila['Serie']]:  # se valida si ya existe esta serie con el mismo comitente (casa de bolsa)
            pass
        else:
            if pd.notna(fila['Casa de bolsa ']) or str(fila['Casa de bolsa ']) != 'nan' and str(
                    fila['Casa de bolsa ']) != 'None':
                series[fila['Serie']].append(fila['Casa de bolsa '])
                contador_series_agregadas += 1
    else:
        series[fila['Serie']] = []

print(f"Se van a procesar {contador_series_agregadas} series")


def obtener_fecha_compra(registros):
    for indice in registros.index:
        if pd.notna(registros.loc[indice]['Fecha Compra']) and str(registros.loc[indice]['Fecha Compra']) != 'nan' and str(fila['Casa de bolsa ']) != 'None':
            return str(registros.loc[indice]['Fecha Compra'])


def obtener_fecha_vencimiento_max(capitales):

    return str(capitales['Fecha Vencimiento Serie'].max()).split(' ')[0]



def validar_registro(registros, serie, casa):
    """Valida que los registros cumplan con los requisitos:
       - Que tenga fecha de compra
       - Que tenga fecha de vencimiento
       - Que existan registros de vencimientos y capital
    """
    global REGISTROS_NO_VALIDOS
    valido = True
    capital = registros.loc[registros['Tipo'] == 'Capital']
    # Validar fecha_compra
    mensaje = ''
    if obtener_fecha_compra(registros) is None or str(obtener_fecha_compra(registros)) == 'nan' or pd.isna(obtener_fecha_compra(registros)):
        valido = False
        mensaje += 'No se encontro la fecha de compra \n'

    # Validar fecha_vencimiento
    if obtener_fecha_vencimiento_max(registros) is None or str(obtener_fecha_vencimiento_max(capital)) == 'nan' or pd.isna(obtener_fecha_vencimiento_max(capital)):
        valido = False
        mensaje += 'No se pudo obtener la fecha de vencimiento \n'

    if not valido:
        print(f"No valido {serie} - {casa} \n{mensaje}")
        REGISTROS_NO_VALIDOS += 1

    return valido

def obtener_datos_de_cabecera(capital):
    """Obtiene los datos para la cabecera o registro principla"""
    calificacion = ''
    tasa_interes = 0
    instrumento = None  # Definir por defecto
    moneda = None
    emisor = None
    comitente = None
    for index in capital.index:
        if capital.loc[index]['Calificacion de riesgo']:
            calificacion = capital.loc[index]['Calificacion de riesgo']
            # Limpieza de la tasa de interes
            tasa_interes_str = str(capital.loc[index]['Tasa Interes'])  # Convertir a string
            tasa_interes_str = tasa_interes_str.split('\\')[0]  # Quitar caracteres extranios
            tasa_interes_str = tasa_interes_str.replace(',', '.')  # Cambiar coma por punto
            tasa_interes_str = tasa_interes_str.replace('\xa0', '')  # Eliminar espacios invisibles
            tasa_interes_str = tasa_interes_str.replace('%', '')  # Eliminar el simbolo de porcentaje
            try:
                tasa_interes = float(tasa_interes_str)  # Convertir a float
            except ValueError:
                print(f"Error al convertir '{tasa_interes_str}' a float")
                tasa_interes = None

            instrumento = capital.loc[index]['Instrumento']
            moneda = capital.loc[index]['Moneda']
            emisor = capital.loc[index]['Emisor']
            comitente = capital.loc[index]['Comitente']
    return calificacion, tasa_interes,instrumento, moneda, emisor, comitente


registros_para_bonos = []


# se iteran los registros y se procesan los datos que se van a pasar al odoo
for serie in series:
    # se iteran las series y la casa de bolsa
    for casa_bolsa in series[serie]:
        # se inicializan solos los registros relacionados con la cartera que vamos a procesar
        registros = tabla_bonos.loc[(tabla_bonos['Serie'] == serie) & (tabla_bonos['Casa de bolsa '] == casa_bolsa)]
        registros['Importe Valorizado'] = pd.to_numeric(registros['Importe Valorizado'], errors='coerce')

        # dependiendo de la cartera tiene solo un registro de capital o varios
        # de ese o esos registros podemos obtener el importe valorizado
        # Lo demas son los intereses, tambien se suman obteniendo los intereses, aunque ahora hay un campo computado para calcular
        capitales = registros.loc[registros['Tipo'] == 'Capital']
        intereses = registros.loc[registros['Tipo'] == 'Intereses']
        calificacion, tasa_intereses, instrumento, moneda, emisor, comitente = obtener_datos_de_cabecera(capitales)
        if validar_registro(registros, serie, casa_bolsa):  # logear despues los que estan facllando
            registro_con_cuenta = xr.execute_kw(
                'pbp.cartera_inversion', 'search_read',
                [[
                    ['instrumento', '=', INSTRUMENTOS[instrumento]],
                    ['inversion_journal_id', '!=', False],
                    ['banco_account_id', '!=', False],
                    ['currency_id', '=', MONEDAS[moneda]],
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
            cabecera = {
                'serie': serie,
                'fecha_compra': obtener_fecha_compra(registros),
                'fecha_vencimiento': obtener_fecha_vencimiento_max(capitales),
                'calificacion_riesgo': calificacion,
                'tasa_interes': tasa_intereses,
                'importe_valorizado': capitales['Importe Valorizado'].sum(),
                'instrumento': INSTRUMENTOS[instrumento],
                'moneda': MONEDAS[moneda],
                'cambio_utilizado': 7812.22 if MONEDAS[moneda] == 2 else False,
                'emision': emisor,
                'partner_id': False,
                'comitente': comitente,
                'vencimietos': [],
                'casa_bolsa': CASA_BOLSA[casa_bolsa.strip().lstrip()],
                'inversion_journal_id': registro_con_cuenta[0]['inversion_journal_id'][0] if len(
                    registro_con_cuenta) else False,
                'banco_account_id': registro_con_cuenta[0]['banco_account_id'][0] if len(
                    registro_con_cuenta) else False,
                'inversion_account_id': registro_con_cuenta[0]['inversion_account_id'][0] if len(
                    registro_con_cuenta) else False,
                'initial_debit_account_id': registro_con_cuenta[0]['initial_debit_account_id'][0] if len(
                    registro_con_cuenta) else False,
                'initial_debit_account_id_lp': registro_con_cuenta[0]['initial_debit_account_id_lp'][0] if len(
                    registro_con_cuenta) else False,
                'initial_credit_account_id': registro_con_cuenta[0]['initial_credit_account_id'][0] if len(
                    registro_con_cuenta) else False,
                'initial_credit_largo_plazo_account_id':
                    registro_con_cuenta[0]['initial_credit_largo_plazo_account_id'][0] if len(
                        registro_con_cuenta) else False,
                'initial_journal_id': registro_con_cuenta[0]['initial_journal_id'][0] if len(
                    registro_con_cuenta) else False,
                'credit_account_id': registro_con_cuenta[0]['credit_account_id'][0] if len(
                    registro_con_cuenta) else False,
                'debit_account_id': registro_con_cuenta[0]['debit_account_id'][0] if len(
                    registro_con_cuenta) else False,

            }
            # si el capital se cobra fraccionado
            if len(capitales.index) > 1:
                for indice in capitales.index:
                    vencimiento = {
                        'name': serie,
                        'fecha_vencimiento': capitales.loc[indice]['Fecha Vencimiento Serie'],
                        'state': ESTADOS[capitales.loc[indice]['Estado']],
                        'amortizacion': 'pagocap',
                        'total': capitales.loc[indice]['Importe Valorizado']
                    }
                    cabecera['vencimietos'].append(vencimiento)
            else:
                for indice in capitales.index:
                    vencimiento = {
                        'name': serie,
                        'fecha_vencimiento': capitales.loc[indice]['Fecha Vencimiento Serie'],
                        'state': ESTADOS[capitales.loc[indice]['Estado']],
                        'amortizacion': 'pagocap',
                        'total': capitales.loc[indice]['Importe Valorizado']
                    }
                    cabecera['vencimietos'].append(vencimiento)
            # cobro de intereses
            for indice in intereses.index:
                vencimiento = {
                    'fecha_vencimiento': intereses.loc[indice]['Fecha Vencimiento Serie'],
                    'interes_titulo': 0,
                    'estado': ESTADOS[intereses.loc[indice]['Estado']],
                    'amortizacion': 'vtoInt',
                    'total': intereses.loc[indice]['Importe Valorizado']
                }
                cabecera['vencimietos'].append(vencimiento)
            registros_para_bonos.append(cabecera)



print()
contador = 0

for reg in registros_para_bonos:
    for venc in reg['vencimietos']:
        contador += 1
print("#"*30)
print(f"Registros de cartera {len(registros_para_bonos)}")
print(f"Registros de vencimientos {contador}")
print(f"Registros no validos {REGISTROS_NO_VALIDOS}")



# COMNEZAR LA CARGA EN EL ODOO


for data in registros_para_bonos:
    # despues hay que agregar para que no se creen repetidos
    cartera_vals = {
        'emision': data.get('emision'),
        'serie': data.get('serie'),
        'fecha_compra': data.get('fecha_compra'),
        'fecha_vencimiento': data.get('fecha_vencimiento'),
        'calificacion_riesgo': data.get('calificacion_riesgo'),
        'tasa_interes': float(data.get('tasa_interes')),
        'importe_valorizado': float(data.get('importe_valorizado')),
        'capital': float(data.get('importe_valorizado')),
        'instrumento': data.get('instrumento'),
        'currency_id': data.get('moneda'),
        'cambio_utilizado': data.get('cambio_utilizado'),
        'comitente': False,
        'intereses': 0,
        'partner_id': data.get('partner_id'),
        'casa_bolsa': data.get("casa_bolsa"),
        'banco_account_id': data.get('banco_account_id'),
        'inversion_journal_id': data.get('inversion_journal_id'),
        'inversion_account_id': data.get('inversion_account_id'),
        'initial_debit_account_id': data.get('initial_debit_account_id'),
        'initial_debit_account_id_lp': data.get('initial_debit_account_id_lp'),
        'initial_credit_account_id': data.get('initial_credit_account_id'),
        'initial_credit_largo_plazo_account_id': data.get('initial_credit_largo_plazo_account_id'),
        'initial_journal_id': data.get('initial_journal_id'),
        'credit_account_id': data.get('credit_account_id'),
        'debit_account_id': data.get('debit_account_id'),
        'tipo_mercado': 'primario' if data.get('mercado') == 'Mercado Primario' else 'secundario',
        'plazo_pago_intereses': 1,
        'tipo': 'capital',
        'fecha_inicio_devengamiento': data.get('fecha_compra'),
        'fecha_final_devengamiento': data.get('fecha_vencimiento'),

    }
    print(cartera_vals)
    try:
        cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])
    except:
        cartera_vals['fecha_inicio_devengamiento'] = False
        cartera_vals['fecha_final_devengamiento'] = False
        cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])

    vencimientos_vals = []
    for vencimiento in data.get('vencimietos'):
        venc_vals = {
            'name': data.get('serie'),
            'fecha_vencimiento': vencimiento.get('fecha_vencimiento'),
            'registros': cartera_id,
            'state': 'cobrado' if vencimiento.get('estado') == 'Acreditado' else 'pendiente',
            'amortizacion': vencimiento.get('amortizacion'),
            'total': float(vencimiento.get('total')),
            # 'cuenta': data.get('debit_account_id'),
            # 'intereses': float(vencimiento.get('interes_titulo'))
        }

        try:
            vencimiento_id = xr.execute_kw('pbp.vencimiento_capital_interes', 'create', [venc_vals])
            print("\t", venc_vals)
        except:
            print("No se pudo crear el retistro de vencimiento con los siguientes valores:")
            print(venc_vals)
        vencimientos_vals.append(vencimiento_id)










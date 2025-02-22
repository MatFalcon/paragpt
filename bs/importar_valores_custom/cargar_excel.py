import pandas as pd
from configparser import ConfigParser
from conexion_odoo import OdooXMLRPCClient


xr = OdooXMLRPCClient()#PYTAU01F4962
xr.setup()
print(f"UID obtenido: {xr.uid}")



# excel = pd.read_excel("Cartera_excel.xlsx")
#
# excel.to_csv("cartera_cda.csv")
monedas = {
    'Guaraníes': 155,
    'Dólares americanos':2
}

tabla = pd.read_csv("cartera_cda.csv")

# filtra solo cda y fondos
CDA_TABLA = tabla.loc[
    (pd.notna(tabla['Serie'])) &
    (tabla['Serie'] != 'nan') &
    (tabla['Instrumento'] == 'CDA')
]
FONDO_TABLA = tabla.loc[
    (pd.notna(tabla['Serie'])) &
    (tabla['Serie'] != 'nan') &
    (tabla['Instrumento'] == 'Fondo')
]

# agrupar las series
series_cda = []
for serie in CDA_TABLA['Serie'].to_list():
    if serie not in series_cda:
        series_cda.append(serie)

print("Series total:",series_cda)
# Procesar CDA
print(CDA_TABLA.columns)
for serie in series_cda:
    capital = CDA_TABLA.loc[(CDA_TABLA['Serie'] == serie) & (CDA_TABLA['Tipo'] == 'Capital')]
    # ver con dani despues como hacer los que no tienen capital
    if len(capital) > 0:
        capital = CDA_TABLA.loc[
            (CDA_TABLA['Serie'] == serie) &
            (CDA_TABLA['Tipo'] == 'Capital')
            ]
        vencimientos = CDA_TABLA.loc[
            (CDA_TABLA['Serie'] == serie) &
            (CDA_TABLA['Tipo'] == 'Intereses')
            ]

        registro_con_cuenta = xr.execute_kw(
            'pbp.cartera_inversion', 'search_read',
            [[
                ['instrumento', '=', 'cda'],
                ['inversion_journal_id', '!=', False],
                ['banco_account_id', '!=', False],
                ['currency_id', '=', monedas[capital['Moneda'].to_list()[0]]],
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


        vencimientos_cartera = {}

        contador = 1

        for indice in vencimientos.index.to_list():
            vencimientos_cartera[contador] = {
                'fecha_vencimiento': vencimientos.loc[indice]['Fecha Vencimiento Serie'].split(" ")[0],
                'interes_titulo': vencimientos.loc[indice]['Importe Valorizado'],
                'estado': vencimientos.loc[indice]['Estado de cupon / Capital'],
                'serie': vencimientos.loc[indice]['Serie'],
                'tipo': 'vtoInt'
            }
            contador += 1



        # sumar intereses
        intereses_total = 0
        for key in vencimientos_cartera:
            print(vencimientos_cartera[key]['interes_titulo'])
            intereses_total += float(vencimientos_cartera[key]['interes_titulo'])

        cartera_vals = {
            'serie':  capital['Serie'].to_list()[0],
            'fecha_compra': capital['Fecha Compra'].to_list()[0].split(" ")[0],
            'fecha_vencimiento': capital['Fecha Vencimiento Serie'].to_list()[0].split(" ")[0],
            'calificacion_riesgo': capital['Calificacion de riesgo'].to_list()[0] if str(capital['Calificacion de riesgo'].to_list()[0]) != 'nan' else False,
            'tasa_interes': float(capital['Tasa Interes'].to_list()[0]) * 100,
            'importe_valorizado': float(capital['Importe Valorizado'].to_list()[0]),
            'instrumento': 'cda',
            'emision':capital['Emisor'].to_list()[0],
            'currency_id': monedas[capital['Moneda'].to_list()[0]],
            'tipo': 'capital',
            'intereses': intereses_total,
            'fecha_inicio_devengamiento': capital['Fecha Compra'].to_list()[0].split(" ")[0],
            'fecha_final_devengamiento': capital['Fecha Vencimiento Serie'].to_list()[0].split(" ")[0],
            'inversion_journal_id': registro_con_cuenta[0]['inversion_journal_id'][0] if len(registro_con_cuenta) else False,
            'banco_account_id': registro_con_cuenta[0]['banco_account_id'][0] if len(registro_con_cuenta) else False,
            'inversion_account_id': registro_con_cuenta[0]['inversion_account_id'][0] if len(registro_con_cuenta) else False,
            'initial_debit_account_id': registro_con_cuenta[0]['initial_debit_account_id'][0] if len(registro_con_cuenta) else False,
            'initial_debit_account_id_lp': registro_con_cuenta[0]['initial_debit_account_id_lp'][0] if len(registro_con_cuenta) else False,
            'initial_credit_account_id': registro_con_cuenta[0]['initial_credit_account_id'][0] if len(registro_con_cuenta) else False,
            'initial_credit_largo_plazo_account_id': registro_con_cuenta[0]['initial_credit_largo_plazo_account_id'][0] if len(registro_con_cuenta) else False,
            'initial_journal_id': registro_con_cuenta[0]['initial_journal_id'][0] if len(registro_con_cuenta) else False,
            'credit_account_id': registro_con_cuenta[0]['credit_account_id'][0] if len(registro_con_cuenta) else False,
            'debit_account_id': registro_con_cuenta[0]['debit_account_id'][0] if len(registro_con_cuenta) else False,
            'plazo_pago_intereses':1
        }


        try:
            cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])
        except:
            cartera_vals['fecha_inicio_devengamiento'] = False
            cartera_vals['fecha_final_devengamiento'] = False
            cartera_id = xr.execute_kw('pbp.cartera_inversion', 'create', [cartera_vals])

        print("Cartera", cartera_id)
        estados = {
            'Activo':'pendiente',
            'Vencido | Cobrado':'cobrado',
            'Cobrado | No renovado':'cobrado',
            'Pendiente':'pendiente',
            'Acreditado':'cobrado',
            'pendiente':'pendiente'
        }
        for key in vencimientos_cartera:
            print("Estado",vencimientos_cartera[key]['estado'] )
            venc_vals = {
                'name': vencimientos_cartera[key]['serie'],
                'fecha_vencimiento': vencimientos_cartera[key]['fecha_vencimiento'],
                'registros': cartera_id,
                'state': estados[vencimientos_cartera[key]['estado']],
                'amortizacion': 'vtoInt',
                'total': vencimientos_cartera[key]['interes_titulo'],
                'cuenta': registro_con_cuenta[0]['debit_account_id'][0] if len(registro_con_cuenta) else False,
                # 'intereses': float(vencimiento.get('interes_titulo'))
            }

            vencimiento_id = xr.execute_kw('pbp.vencimiento_capital_interes', 'create', [venc_vals])
        # crear venc de capital
        cap_vals = {
            'name':  capital['Serie'].to_list()[0],
            'fecha_vencimiento': capital['Fecha Vencimiento Serie'].to_list()[0].split(" ")[0],
            'registros': cartera_id,
            'state': estados[capital['Estado de cupon / Capital'].to_list()[0]],
            'amortizacion': 'pagocap',
            'total': float(capital['Importe Valorizado'].to_list()[0]),
            'cuenta': registro_con_cuenta[0]['inversion_account_id'][0] if len(registro_con_cuenta) else False,
        }
        print("CAP")
        print(cap_vals)
        cap_pago_id = xr.execute_kw('pbp.vencimiento_capital_interes', 'create', [cap_vals])

    else:

        pass
    print("#"*50)



# Procesar Fondos

from configparser import ConfigParser
from conexion_odoo import OdooXMLRPCClient
import pandas as pd
import json



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
    202:"VALORES CBSA",
    191:"REGIONAL CBSA",
    1625:"FAMILIAR CBSA",
    122:"AVALON CBSA",
    137:"CADIEM CBSA",
    139:"CAPITAL MARKETS CBSA",
    118:"ASU CAPITAL CBSA",
    173:"ITAU INVEST CBSA",
    564:"FAIS CBSA",
    172:"INVESTOR CBSA",
    132:"BASA CBSA",
    189:"PUENTE CBSA",
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


CARTERA = pd.read_excel("CarteraFinal2.xlsx")
# print(CARTERA['Estado'])
# conexion del odoo
xr = OdooXMLRPCClient()
xr.setup()
print(f"UID obtenido: {xr.uid}")



    #print(CasaBolsaPartner)
dic_tipo = {
    'pagocap': 'Capital',
    'vtoInt': 'Intereses'
}
vencimientos = xr.execute_kw(
        'pbp.vencimiento_capital_interes', 'search_read',
        [[
            ['serie', '!=', False],
            ['fecha_vencimiento', '>', '01-01-2025']
        ]],
        {'fields': ['id','name', 'amortizacion', 'fecha_vencimiento', 'casa_bolsa', 'serie', 'state'
                    ], }#'limit': 1}
    )
print("Vencimeintos 2025", len(vencimientos))


#{'id': 52044, 'name': 'PYCAF02F9117', 'amortizacion': 'pagocap', 'fecha_vencimiento': '2028-12-11', 'casa_bolsa': [137, 'CADIEM CASA DE BOLSA S.A. :80026712-5']}
for ven in vencimientos:
    registro = CARTERA[
    (CARTERA['Serie']==ven.get('serie')) &
    (CARTERA['Fecha Vencimiento Serie'] == f"{ven.get('fecha_vencimiento')} 00:00:00") &
    (CARTERA['Tipo'] == dic_tipo[ven.get('amortizacion')]) &
    (CARTERA['Casa de bolsa '] == CASA_BOLSA[ven.get('casa_bolsa')[0]])
    ]
    if len(registro) == 1:
        #print(ven.get("serie"), ven.get('casa_bolsa')[0])
        #print(ven.get('serie') ,ven.get('state'),'///', str(registro['Estado'].to_list()[0]))
        if ven.get('state') == 'pendiente' or ven.get('state') == 'vencido':
            print(ven.get('serie'), ven.get('state'), '///', str(registro['Estado'].to_list()[0]))
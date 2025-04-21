from configparser import ConfigParser
from conexion_odoo import OdooXMLRPCClient
import pandas as pd
import json

# conexion del odoo
xr = OdooXMLRPCClient()
xr.setup()
print(f"UID obtenido: {xr.uid}")

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



tabla_fondos = tabla_cartera[
    (pd.notna(tabla_cartera['Serie'])) &
    (tabla_cartera['Serie'] != 'nan') &
    (tabla_cartera['Instrumento'].isin(['Fondos']))
]# se filtran solo los bonos de la tabla de cartera


print(tabla_fondos)
for indice in tabla_fondos.index:
    print("Indice:", indice)
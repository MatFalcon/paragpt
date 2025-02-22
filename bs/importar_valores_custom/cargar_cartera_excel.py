from configparser import ConfigParser
from conexion_odoo import OdooXMLRPCClient
import pandas as pd
import json

# Diccionarios de mapeo
instrumentos = {
    'Bono Subordinado': 'bonos_subordinados',
    'Bono Financiero': 'bonos_financieros',
    "Bono": 'bonos'
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

monedas = {
    'Guaraníes': 155,
    'Dólares americanos': 2
}

# Cargar la tabla desde el archivo CSV
tabla_principal = pd.read_csv("Cartera.csv", dtype=str)

# Convertir los nombres de columnas a formato estándar (eliminar espacios extra)
tabla_principal.columns = tabla_principal.columns.str.strip()

# Definir los instrumentos a filtrar
instrumentos_filtrados = ["Bonos Subordinados", "Bonos", "Bonos Financieros"]

# Filtrar solo los registros que pertenezcan a los instrumentos deseados
tabla_filtrada = tabla_principal[tabla_principal["Instrumento"].isin(instrumentos_filtrados)]

# Filtrar solo registros de tipo "Capital"
capital_filtrado = tabla_filtrada[tabla_filtrada["Tipo"] == "Capital"]

# Contar cuántos registros de tipo "Capital" existen por cada combinación de Serie y Casa de Bolsa
conteo_series_casa = capital_filtrado.groupby(["Serie", "Casa de bolsa"]).size().reset_index(name="Cantidad")

# Filtrar solo las combinaciones donde hay exactamente un registro de "Capital"
series_un_capital = conteo_series_casa[conteo_series_casa["Cantidad"] == 1]

# Lista para almacenar la salida estructurada
bonos_estructurados = []

for _, capital in series_un_capital.iterrows():
    capital_tabla = tabla_principal[
        (tabla_principal["Serie"] == capital["Serie"]) &
        (tabla_principal["Casa de bolsa"] == capital["Casa de bolsa"]) &
        (tabla_principal["Tipo"] == "Capital")
    ]

    if capital_tabla.empty:
        continue

    # Convertir "Importe Valorizado" a float antes de sumar
    capital_tabla["Importe Valorizado"] = capital_tabla["Importe Valorizado"].astype(float)

    bono_data = {
        "fecha_compra": capital_tabla.iloc[0]["Fecha Compra"],  # Obtener el primer valor de la serie
        "capital": capital_tabla["Importe Valorizado"].sum(),  # Sumamos los importes
        "importe_valorizado": float(capital_tabla.iloc[0]["Importe Valorizado"]),  # Convertir a número
        "instrumento": str(capital_tabla.iloc[0]["Instrumento"]),  # Convertir a string
        "currency_id": monedas.get(capital_tabla.iloc[0]["Moneda"], None),  # Evitar KeyError
        "casa_bolsa": CASA_BOLSA[str(capital_tabla.iloc[0]["Casa de bolsa"]).strip().lstrip()],
        'tipo': 'capital',
        "detalles": []
    }

    # Buscar todas las líneas de vencimiento asociadas a la misma Serie y Casa de Bolsa
    vencimientos = tabla_principal[
        (tabla_principal["Serie"] == capital["Serie"]) &
        (tabla_principal["Casa de bolsa"] == capital["Casa de bolsa"])
    ]

    for _, vencimiento in vencimientos.iterrows():
        bono_data["detalles"].append({
            "serie": vencimiento["Serie"],
            "importe_valorizado": float(vencimiento["Importe Valorizado"]) if vencimiento["Importe Valorizado"].replace('.', '', 1).isdigit() else 0,
            "fecha_vencimiento": vencimiento["Fecha Vencimiento Serie"],
            "tipo": 'vtoInt' if vencimiento['Tipo'] == "Intereses" else 'pagocap',
        })

    bonos_estructurados.append(bono_data)

# ✅ Imprimir los bonos estructurados en formato JSON sin errores
print(json.dumps(bonos_estructurados, indent=4, ensure_ascii=False))

# Verificar los nombres de columnas disponibles
print(tabla_principal.columns)

# xr = OdooXMLRPCClient()
# xr.setup()
# print(f"UID obtenido: {xr.uid}")

"""
    Cuando es solo de bonos los instrumentos son:
        'Bonos Subordinados' - 'Bonos' - 'Bonos Financieros' 
"""

import pandas as pd


tabla_base = pd.read_csv("LineasFacturaModaNull.csv")

indices = tabla_base.index.to_list()

# id_no_repetidos = []
#
# for indice in indices:
#     id = int(tabla_base.loc[indice]['id'])
#     product_id = tabla_base.loc[indice]['product_id']
#
#     # Verifica si product_id es NaN
#     if pd.isna(product_id) or not isinstance(product_id, (int, float)):
#
#         continue
#
#     if product_id in id_no_repetidos:
#         pass
#     else:
#         id_no_repetidos.append(product_id)
# contador_queryes = 0
# for id_producto in id_no_repetidos:
#
#     registros_con_producto = tabla_base.loc[tabla_base['product_id'] == id_producto]
#     ids = registros_con_producto['id'].to_list()
#     # print(ids)
#     id_lineas = ""
#     for id_account_move_line in ids:
#
#         id_lineas += f"{id_account_move_line} ,"
#
#
#     select = (f"update account_move_line"
#               f" set product_id = {int(id_producto)} "
#               f"where id in ({id_lineas});"
#               )
#     select = select.replace(",);", ");")
#     print(select)
#     if contador_queryes % 25 == 0:
#         print("\n\n\n\n")
#     contador_queryes += 1
contador_ids = 0
ids_FactNull = "update account_move_line set product_id = null where id in("
for indice in indices:
    id = int(tabla_base.loc[indice]['id'])
    ids_FactNull += f"{id},"

    if contador_ids % 30 == 0:
        ids_FactNull +="\n"

        if contador_ids % 100 == 0:
            ids_FactNull += ");"
            ids_FactNull = ids_FactNull.replace(",);", ");")
            ids_FactNull += "\n\n\n"
            ids_FactNull = ids_FactNull + "update account_move_line set product_id = null where id in ("


    contador_ids += 1
ids_FactNull += ");"
ids_FactNull = ids_FactNull.replace(",);", ");")
print(ids_FactNull)
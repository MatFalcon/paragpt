from collections import defaultdict
import datetime
import dateutil.relativedelta


def generar_facturas(env, novedades):
    # Agrupar novedades por cliente y por moneda
    clients = defaultdict(lambda: defaultdict(list))
    novedades_sin_partners = []
    novedades_sin_productos = []
    novedades_sin_cuentas = []
    for novedad in novedades:
        currency_name = novedad['currency_id'][1]
        if not novedad['partner_id']:
            novedades_sin_partners.append(novedad)
            continue
        if not novedad['product_id']:
            novedades_sin_productos.append(novedad)
            continue

        # Cuenta
        product = env['product.product'].browse([novedad['product_id'][0]])[0]
        account_id = product['property_account_income_id']
        if account_id:
            account_id = account_id['id']
        if not account_id:
            category_id = product['categ_id'][0]
            category = env['product.category'].browse([category_id])[0]
            account_id = category['property_account_income_categ_id']['id']
        if not account_id:
            novedades_sin_cuentas.append(novedad)
            continue

        novedad['account_id'] = account_id

        partner_id = novedad['partner_id'][0]
        clients[partner_id][currency_name].append(novedad)

    # Ignorar cliente si tiene alguna novedad sin producto
    for novedad_sin_producto in novedades_sin_productos:
        partner_id = novedad_sin_producto['partner_id']
        if partner_id and partner_id[0] in clients.keys():
            del clients[partner_id[0]]

    # Ignorar cliente si tiene alguna novedad sin cuenta
    for novedad_sin_cuenta in novedades_sin_cuentas:
        partner_id = novedad_sin_cuenta['partner_id']
        if partner_id and partner_id[0] in clients.keys():
            del clients[partner_id[0]]

    facturas_ids = []
    novedades_publicadas_ids = []
    novedades_sen_publicadas_ids = []
    novedades_series_publicadas_ids = []
    cartera_inversion_publicadas_ids = []
    for partner_id, currency_groups in clients.items():
        for novedades in currency_groups.values():
            try:
                factura_id = generar_factura(env, partner_id, novedades)
                facturas_ids.append(factura_id)
                for novedad in novedades:
                    if novedad.get('fecha_operacion') is not None:
                        novedades_publicadas_ids.append(novedad['id'])
                    elif novedad.get('total_custodia') is not None:
                        novedades_sen_publicadas_ids.append(novedad['id'])
                    elif novedad.get('importe_valorizado') is not None:
                        cartera_inversion_publicadas_ids.append(novedad['id'])
                    else:
                        novedades_series_publicadas_ids.append(novedad['id'])
            except Exception as error:
                print(f'Error: {error}')

    # TODO: separar previamente novedades por tipo
    return {
        'facturas_ids': facturas_ids,

        'novedades_sin_partners_ids': [
            novedad['id'] for novedad in novedades_sin_partners
            if novedad.get('fecha_operacion') is not None
        ],
        'novedades_sin_productos_ids': [
            novedad['id'] for novedad in novedades_sin_productos
            if novedad.get('fecha_operacion') is not None
        ],
        'novedades_sin_cuentas_ids': [
            novedad['id'] for novedad in novedades_sin_cuentas
            if novedad.get('fecha_operacion') is not None
        ],
        'novedades_publicadas_ids': novedades_publicadas_ids,

        'novedades_series_sin_partners_ids': [
            novedad['id'] for novedad in novedades_sin_partners
            if novedad.get('fecha_operacion') is None and novedad.get('total_custodia') is None
        ],
        'novedades_series_sin_productos_ids': [
            novedad['id'] for novedad in novedades_sin_productos
            if novedad.get('fecha_operacion') is None and novedad.get('total_custodia') is None
        ],
        'novedades_series_sin_cuentas_ids': [
            novedad['id'] for novedad in novedades_sin_cuentas
            if novedad.get('fecha_operacion') is None and novedad.get('total_custodia') is None
        ],
        'novedades_series_publicadas_ids': novedades_series_publicadas_ids,

        'novedades_sen_sin_partners_ids': [
            novedad['id'] for novedad in novedades_sin_partners
            if novedad.get('total_custodia') is not None
        ],
        'novedades_sen_sin_productos_ids': [
            novedad['id'] for novedad in novedades_sin_productos
            if novedad.get('total_custodia') is not None
        ],
        'novedades_sen_sin_cuentas_ids': [
            novedad['id'] for novedad in novedades_sin_cuentas
            if novedad.get('total_custodia') is not None
        ],
        'novedades_sen_publicadas_ids': novedades_sen_publicadas_ids,

        'cartera_inversion_sin_partners_ids': [
            novedad['id'] for novedad in novedades_sin_partners
            if novedad.get('importe_valorizado') is not None
        ],
        'cartera_inversion_sin_productos_ids': [
            novedad['id'] for novedad in novedades_sin_productos
            if novedad.get('importe_valorizado') is not None
        ],
        'cartera_inversion_sin_cuentas_ids': [
            novedad['id'] for novedad in novedades_sin_cuentas
            if novedad.get('importe_valorizado') is not None
        ],
        'cartera_inversion_publicadas_ids': cartera_inversion_publicadas_ids,

    }


def generar_factura(env, partner_id, novedades):
    # Agrupar por productos
    products = defaultdict(list)
    for novedad in novedades:
        product_id = novedad['product_id'][0]
        products[product_id].append(novedad)

    # Preparar líneas por producto. Sumar montos y aplicar arancel
    lines = []
    for product_id, novedades in products.items():
        # Sumar montos
        subtotal = 0
        for novedad in novedades:
            if novedad.get('total_custodia') is not None:
                subtotal += novedad['total_custodia']
            elif novedad.get('importe_valorizado') is not None:
                subtotal += novedad['importe_valorizado']
            elif novedad.get('fecha_operacion') is not None:
                subtotal += novedad['subtotal']
            else:
                subtotal += novedad['total']

        product = env['product.product'].browse([product_id])[0]

        # Arancel
        #porcentaje_arancel = product['porcentaje_arancel']
        #subtotal = (porcentaje_arancel * subtotal) / 100

        tax_ids = False
        if product.taxes_id:
            tax_ids = product.taxes_id

        line = {
            'product_id': product_id,
            'name': product['name'],
            'quantity': 1,
            'price_unit': subtotal,
            'price_subtotal_raw': subtotal,
            'credit': subtotal,
            'debit': 0,
            'account_id': novedades[0]['account_id'],
            'from_novedades': True,
            'tax_ids': tax_ids,
        }
        lines.append(line)

    # Monto total de la factura
    amount_total = 0
    for line in lines:
        amount_total += line['price_subtotal_raw']

    # Crear factura
    today = datetime.datetime.now()
    invoice_due_date = novedades[0].get(
        'fecha_vencimiento', today + dateutil.relativedelta.relativedelta(months=1))
    move = {
        'move_type': 'out_invoice',
        'date': today.strftime('%Y-%m-%d'),
        'invoice_date': today.strftime('%Y-%m-%d'),
        'partner_id': partner_id,
        'currency_id': novedades[0]['currency_id'][0],
        'amount_total': amount_total,
        'state': 'draft',
        'payment_state': 'not_paid',
        'invoice_date_due': invoice_due_date,
    }
    move = env['account.move'].with_context(check_move_validity=False).create([move])

    # OPTIMIZE: crear todas las lineas de una sola vez
    # Crear líneas
    for line in lines:
        move.write({'invoice_line_ids': [(0, 0, line)]})

    # Relacionar factura a novedades
    novedades_ids = []
    novedades_sen_ids = []
    novedades_series_ids = []
    cartera_inversion_ids = []
    for novedad in novedades:
        if novedad.get('fecha_operacion') is not None:
            novedades_ids.append(novedad['id'])
        elif novedad.get('total_custodia') is not None:
            novedades_sen_ids.append(novedad['id'])
        elif novedad.get('importe_valorizado') is not None:
            cartera_inversion_ids.append(novedad['id'])
        else:
            novedades_series_ids.append(novedad['id'])

    if novedades_ids:
        novedades = env['pbp.novedades'].browse(novedades_ids)
        novedades.write({'invoice_id': move.id})
    if novedades_sen_ids:
        novedades = env['pbp.novedades_sen'].browse(novedades_sen_ids)
        novedades.write({'invoice_id': move.id})
    if novedades_series_ids:
        novedades = env['pbp.novedades_series'].browse(novedades_series_ids)
        novedades.write({'invoice_id': move.id})
    if cartera_inversion_ids:
        novedades = env['pbp.cartera_inversion'].browse(cartera_inversion_ids)
        novedades.write({'invoice_id': move.id})

    return move.id

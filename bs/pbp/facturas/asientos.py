from collections import defaultdict
import datetime
import dateutil.relativedelta


def generar_asientos(env, carteras):
    series = defaultdict(list)
    cartera_inversion_fallidas_ids = []
    for cartera in carteras:
        if not (
            cartera['serie'] and
            cartera['casa_bolsa'] and
            cartera['debit_account_id'] and
            cartera['credit_account_id'] and
            cartera['casa_bolsa'] and
            cartera['currency_id']
        ):
            cartera_inversion_fallidas_ids.append(cartera['id'])
        else:
            series[cartera['serie']].append(cartera)

    asientos_ids = []
    cartera_inversion_publicadas_ids = []
    for serie, carteras in series.items():
        try:
            asiento_id = generar_asiento(env, carteras)
            asientos_ids.append(asiento_id)
            for cartera in carteras:
                cartera_inversion_publicadas_ids.append(cartera['id'])
        except Exception as error:
            print(f'Error: {error}')
            for cartera in carteras:
                cartera_inversion_fallidas_ids.append(cartera['id'])

    return {
        'cartera_inversion_publicadas_ids': cartera_inversion_publicadas_ids,
        'cartera_inversion_fallidas_ids': cartera_inversion_fallidas_ids,
    }


def generar_asiento(env, carteras):
    debit_lines = []
    credit_lines = []
    PYG = env['res.currency'].search([('name', '=', 'PYG')])
    USD = env['res.currency'].search([('name', '=', 'USD')])
    for cartera in carteras:
        liquidity_balance = cartera['valor_calculado']

        debit_line = {
            'debit': liquidity_balance,
            'credit': 0.0,
            'account_id': cartera['debit_account_id'][0],
            'partner_id': cartera['casa_bolsa'][0],
            'currency_id': cartera['currency_id'][0],
            'amount_currency': liquidity_balance,
        }
        debit_lines.append(debit_line)

        credit_line = {
            'credit': liquidity_balance,
            'debit': 0.0,
            'account_id': cartera['credit_account_id'][0],
            'partner_id': cartera['casa_bolsa'][0],
            'currency_id': cartera['currency_id'][0],
            'amount_currency': -liquidity_balance,
        }
        credit_lines.append(credit_line)

    today = datetime.datetime.now()
    move = {
        'ref': carteras[0]['serie'],
        'date': today.strftime('%Y-%m-%d'),
        'currency_id': carteras[0]['currency_id'][0],
        'move_type': 'entry',
    }
    move = env['account.move'].with_context(check_move_validity=False).create([move])

    for line in debit_lines:
        move.write({'line_ids': [(0, 0, line)]})
    for line in credit_lines:
        move.write({'line_ids': [(0, 0, line)]})

    cartera_inversion_ids = []
    for cartera in carteras:
        cartera_inversion_ids.append(cartera['id'])
    carteras = env['pbp.cartera_inversion'].browse(cartera_inversion_ids)
    carteras.write({'move_id': move.id})

    return move.id

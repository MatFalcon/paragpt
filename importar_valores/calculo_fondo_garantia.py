from configparser import ConfigParser
import datetime
import dateutil.relativedelta
import os

from rpc import XMLRPC

os.chdir(os.path.dirname(__file__))
config = ConfigParser()
config.read('config.ini')

SQL_SERVER_CONFIG = {
    'HOST': config['sqlserver']['host'],
    'USER': config['sqlserver']['user'],
    'PWD': config['sqlserver']['pwd'],
}

xr = XMLRPC()
xr.setup()

today = datetime.date.today()

from_date = today - dateutil.relativedelta.relativedelta(months=1)
from_date = from_date.replace(day=26)
from_date = from_date.strftime('%Y-%m-%d %H:%M')

to_date = today
to_date = to_date.replace(day=25)
to_date = to_date.strftime('%Y-%m-%d %H:%M')


def create_fondo_garantia():
    novedades = xr.execute_kw('pbp.novedades', 'search_read',
                              [[['fecha_operacion', '>=', from_date], ['fecha_operacion', '<=', to_date]]])
    partners_novedades = []
    for n in novedades:
        if n['partner_id'] not in partners_novedades:
            partners_novedades.append(n['partner_id'])
            novedades_gs = filter(lambda c: c['partner_id'] == n['partner_id'] and c['currency_id'][0] == 155 and
                                            (c['product_id'][0] != 155), novedades)
            novedades_usd = filter(lambda c: c['partner_id'] == n['partner_id'] and c['currency_id'][0] == 2 and
                                             (c['product_id'][0] != 155), novedades)
            fondo_garantia_gs = filter(lambda c: c['partner_id'] == n['partner_id'] and c['currency_id'][0] == 155 and
                                                 (c['product_id'][0] == 155), novedades)
            fondo_garantia_usd = filter(lambda c: c['partner_id'] == n['partner_id'] and c['currency_id'][0] == 2 and
                                                  (c['product_id'][0] == 155), novedades)
            novedades_gs_total = 0
            novedades_usd_total = 0
            fondo_garantia_gs_total = 0
            fondo_garantia_usd_total = 0
            sistema_tradicional_gs_total = 0
            sistema_tradicional_usd_total = 0
            for x in novedades_gs:
                novedades_gs_total = novedades_gs_total + x['volumen_gs']
            for x in novedades_usd:
                novedades_usd_total = novedades_usd_total + x['volumen_gs']
            for x in fondo_garantia_gs:
                fondo_garantia_gs_total = fondo_garantia_gs_total + (
                            x['volumen_gs'] * ((0.005 / 100 / 365) * x['plazo']))
            for x in fondo_garantia_usd:
                fondo_garantia_usd_total = fondo_garantia_usd_total + (
                            x['volumen_gs'] * ((0.005 / 100 / 365) * x['plazo']))
            sistema_tradicional = xr.execute_kw('pbp.novedades_series', 'search_read', [[['fecha', '>=', from_date],
                                                                                         ['fecha', '<=', to_date],
                                                                                         ['partner_id', '=',
                                                                                          n['partner_id'][0]]]])
            sistema_tradicional_gs = filter(lambda c: c['currency_id'][0] == 155, sistema_tradicional)
            sistema_tradicional_usd = filter(lambda c: c['currency_id'][0] == 2, sistema_tradicional)
            for x in sistema_tradicional_gs:
                sistema_tradicional_gs_total = sistema_tradicional_gs_total + x['volumen']
            for x in sistema_tradicional_usd:
                sistema_tradicional_usd_total = sistema_tradicional_usd_total + x['volumen']
            sum_gs = (novedades_gs_total + sistema_tradicional_gs_total) / 100 * 0.005 + round(fondo_garantia_gs_total)
            sum_usd = (novedades_usd_total + sistema_tradicional_usd_total) / 100 * 0.005 + fondo_garantia_usd_total
            fg_usd = xr.execute_kw('pbp.calculo_fondo_garantia', 'search', [[['inicio_periodo', '=', from_date],
                                                                             ['fin_periodo', '=', to_date],
                                                                             ['currency_id', '=', 2],
                                                                             ['partner_id', '=', n['partner_id'][0]]]])
            fg_pyg = xr.execute_kw('pbp.calculo_fondo_garantia', 'search', [[['inicio_periodo', '=', from_date],
                                                                             ['fin_periodo', '=', to_date],
                                                                             ['currency_id', '=', 155],
                                                                             ['partner_id', '=', n['partner_id'][0]]]])
            obj_gs = {
                'partner_id': n['partner_id'][0],
                'total': sum_gs,
                'currency_id': 155,
                'inicio_periodo': from_date,
                'fin_periodo': to_date
            }
            obj_usd = {
                'partner_id': n['partner_id'][0],
                'total': sum_usd,
                'currency_id': 2,
                'inicio_periodo': from_date,
                'fin_periodo': to_date
            }
            if fg_pyg:
                xr.execute_kw('pbp.calculo_fondo_garantia', 'write', [[fg_pyg[0]], obj_gs])
            else:
                xr.execute_kw('pbp.calculo_fondo_garantia', 'create', [obj_gs])
            if fg_usd:
                xr.execute_kw('pbp.calculo_fondo_garantia', 'write', [[fg_usd[0]], obj_usd])
            else:
                xr.execute_kw('pbp.calculo_fondo_garantia', 'create', [obj_usd])


if __name__ == '__main__':
    create_fondo_garantia()

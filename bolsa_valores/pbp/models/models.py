from odoo import api, fields, models
from odoo.osv import osv


class DialogBox(osv.osv_memory):
    _name = 'pbp.dialog.box'

    error_msg = fields.Char(readonly=True)

    novedades_sin_partners_ids = fields.Many2many('pbp.novedades', 'novedades_sin_partners', readonly=True)
    novedades_sin_productos_ids = fields.Many2many('pbp.novedades', 'novedades_sin_productos', readonly=True)
    novedades_sin_cuentas_ids = fields.Many2many('pbp.novedades', 'novedades_sin_cuentas', readonly=True)
    invoice_ids = fields.Many2many('account.move')
    novedades_publicadas_ids = fields.Many2many('pbp.novedades', 'novedades_publidadas', readonly=True)

    novedades_sen_sin_partners_ids = fields.Many2many('pbp.novedades_sen', 'novedades_sen_sin_partners', readonly=True)
    novedades_sen_sin_productos_ids = fields.Many2many('pbp.novedades_sen', 'novedades_sen_sin_productos',
                                                       readonly=True)
    novedades_sen_sin_cuentas_ids = fields.Many2many('pbp.novedades_sen', 'novedades_sen_sin_cuentas', readonly=True)
    invoice_sen_ids = fields.Many2many('account.move', 'novedades_sen_facturas')
    novedades_sen_publicadas_ids = fields.Many2many('pbp.novedades_sen', 'novedades_sen_publidadas', readonly=True)

    novedades_series_sin_partners_ids = fields.Many2many('pbp.novedades_series', 'novedades_series_sin_partners',
                                                         readonly=True)
    novedades_series_sin_productos_ids = fields.Many2many('pbp.novedades_series', 'novedades_series_sin_productos',
                                                          readonly=True)
    novedades_series_sin_cuentas_ids = fields.Many2many('pbp.novedades_series', 'novedades_series_sin_cuentas',
                                                        readonly=True)
    invoice_series_ids = fields.Many2many('account.move', 'novedades_series_facturas')
    novedades_series_publicadas_ids = fields.Many2many('pbp.novedades_series', 'novedades_series_publidadas',
                                                       readonly=True)

    invoice_cartera_inversion_ids = fields.Many2many('account.move', 'cartera_inversion_facturas')
    cartera_inversion_publicadas_ids = fields.Many2many('pbp.cartera_inversion', 'cartera_inversion_publidadas',
                                                        readonly=True)
    cartera_inversion_fallidas_ids = fields.Many2many('pbp.cartera_inversion', 'cartera_inversion_fallidas',
                                                      readonly=True)

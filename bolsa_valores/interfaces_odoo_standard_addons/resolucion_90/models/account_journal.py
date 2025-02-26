from odoo import models,fields,api,exceptions


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    res90_tipo_comprobante = fields.Selection([('101', 'Autofactura'),
                                               ('102', 'Boleta de Transporte Público de Pasajeros'),
                                               ('103', 'Boleta de Venta'),
                                               ('104', 'Boleta Resimple'),
                                               ('105', 'Boletos de Loterías, Juegos de Azar'),
                                               ('106', 'Boleto o ticket de Transporte aéreo'),
                                               ('107', 'Despacho de importación'),
                                               ('108', 'Entrada a espectáculos públicos'),
                                               ('109', 'Factura'),
                                               ('110', 'Nota de crédito'),
                                               ('111', 'Nota de débito'),
                                               ('112', 'Ticket de máquina registradora'),
                                               ('201', 'Comprobante de egresos por compras a crédito'),
                                               ('202', 'Comprobante del exterior legalizado'),
                                               ('203', 'Comprobante de ingreso por ventas a crédito'),
                                               ('204', 'Comprobante de ingreso de Entidades Públicas, Religiosas o de Beneficio Público'),
                                               ('205', 'Extracto de cuenta - Billetaje electrónico'),
                                               ('206', 'Extracto de cuenta - IPS'),
                                               ('207', 'Extracto de cuenta - TC/TD'),
                                               ('208', 'Liquidación de Salario'),
                                               ('209', 'Otros comprobantes de egresos'),
                                               ('210', 'Otros comprobantes de ingresos'),
                                               ('211', 'Transferencias o giros bancarios / Boleta de depósito'),
                                               ])

    excluir_res90=fields.Boolean(string="Excluir de Resolucion 90",copy=False,help="Los registros de este diario no serán incluídos en la resolucion 90")

    @api.onchange('type')
    @api.depends('type')
    def asignar_tipo_comprobante(self):
        for i in self:
            if i.type in ['sale','purchase']:
                i.res90_tipo_comprobante='109'
            else:
                i.res90_tipo_comprobante=None